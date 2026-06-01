"""Streaming response support using Server-Sent Events (SSE)

Optimized with KV cache reuse and autocast for faster token generation.
"""

import json
import torch
from src.generation_utils import prepare_generation_prompt
from src.logger import get_logger
from src.models import clean_response

logger = get_logger(__name__)


def _estimate_output_tokens(text: str) -> int:
    normalized = str(text or "").strip()
    if not normalized:
        return 0
    return max(1, len(normalized) // 4)


class StreamingTextGenerator:
    """Generate text token-by-token with KV cache optimization"""

    def __init__(self, model, tokenizer, device="cpu"):
        self.model = model
        self.tokenizer = tokenizer
        self.device = device
        self._autocast_enabled = device == "cuda"
        self._autocast_device = device if device in ("cuda", "cpu") else "cpu"

    def generate_stream(
        self,
        prompt: str,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.95,
        routing_profile=None,
        do_sample=None,
        input_max_length=None,
    ):
        """Generator that yields tokens one at a time with KV cache reuse

        Yields:
            dict with 'token', 'text_so_far', and 'finished' keys
        """
        logger.info(f"Starting streaming generation for: {prompt[:50]}...")

        route_overrides = (routing_profile or {}).get("generation_overrides") or {}
        if route_overrides.get("temperature_max") is not None:
            temperature = min(temperature, route_overrides["temperature_max"])
        if route_overrides.get("top_p") is not None:
            top_p = route_overrides["top_p"]
        prompt_limit = input_max_length or route_overrides.get("input_max_length")

        rendered_prompt = prepare_generation_prompt(self.tokenizer, prompt)
        tokenize_kwargs = {
            "return_tensors": "pt",
            "truncation": True,
        }
        if prompt_limit:
            tokenize_kwargs["max_length"] = int(prompt_limit)
        inputs = self.tokenizer(rendered_prompt, **tokenize_kwargs).to(self.device)
        input_ids = inputs["input_ids"]
        attention_mask = inputs.get("attention_mask", None)

        generated_ids = input_ids.clone()
        generated_text = ""
        past_key_values = None
        output_tokens_used = 0

        should_sample = (temperature > 0.18) if do_sample is None else bool(do_sample)

        for step in range(max_new_tokens):
            with torch.no_grad(), torch.amp.autocast(
                device_type=self._autocast_device,
                enabled=self._autocast_enabled,
            ):
                if past_key_values is not None:
                    outputs = self.model(
                        input_ids=generated_ids[:, -1:],
                        attention_mask=torch.ones(
                            (1, generated_ids.shape[1]),
                            device=self.device,
                            dtype=torch.long,
                        ),
                        past_key_values=past_key_values,
                        use_cache=True,
                    )
                else:
                    outputs = self.model(
                        input_ids=generated_ids,
                        attention_mask=attention_mask,
                        use_cache=True,
                    )

                past_key_values = outputs.past_key_values
                logits = outputs.logits[:, -1, :].float()  # Always sample in FP32

                if should_sample:
                    if temperature > 0:
                        logits = logits / temperature

                    sorted_logits, sorted_indices = torch.sort(
                        logits, descending=True
                    )
                    cumulative_probs = torch.cumsum(
                        torch.softmax(sorted_logits, dim=-1), dim=-1
                    )
                    sorted_indices_to_remove = cumulative_probs > top_p
                    sorted_indices_to_remove[:, 1:] = (
                        sorted_indices_to_remove[:, :-1].clone()
                    )
                    sorted_indices_to_remove[:, 0] = False

                    indices_to_remove = sorted_indices_to_remove.scatter(
                        1, sorted_indices, sorted_indices_to_remove
                    )
                    logits[indices_to_remove] = float("-inf")

                    probs = torch.softmax(logits, dim=-1)
                    next_token = torch.multinomial(probs, num_samples=1)
                else:
                    next_token = torch.argmax(logits, dim=-1, keepdim=True)

            generated_ids = torch.cat([generated_ids, next_token], dim=-1)

            token_text = self.tokenizer.decode(
                next_token[0], skip_special_tokens=True
            )
            generated_text += token_text
            output_tokens_used = step + 1

            if next_token.item() == self.tokenizer.eos_token_id:
                yield {
                    "token": "",
                    "text_so_far": generated_text,
                    "finished": True,
                    "stop_reason": "eos_token",
                    "finish_reason": "stop",
                    "output_tokens_used": int(output_tokens_used),
                    "output_token_budget": int(max_new_tokens or 0),
                }
                break

            yield {
                "token": token_text,
                "text_so_far": generated_text,
                "finished": False,
            }
        else:
            yield {
                "token": "",
                "text_so_far": generated_text,
                "finished": True,
                "stop_reason": "max_new_tokens",
                "finish_reason": "length",
                "output_tokens_used": int(output_tokens_used or _estimate_output_tokens(generated_text)),
                "output_token_budget": int(max_new_tokens or 0),
            }

        # Free KV cache memory
        del past_key_values
        if self.device == "cuda":
            torch.cuda.empty_cache()

        logger.info("Streaming generation complete")


def sse_format(data: dict) -> str:
    """Format a dict as a Server-Sent Event string"""
    return f"data: {json.dumps(data)}\n\n"


def create_sse_generator(stream_generator, final_emitter=None):
    """Wrap a streaming generator to produce SSE-formatted output.

    If `final_emitter` is provided it will be called with the cleaned
    final text (useful for console handlers like `ai._emit_clean_response`).
    Otherwise a terminal SSE "final" event is yielded with the cleaned
    text so HTTP clients can receive the polished answer.
    """
    final_text = ""
    for chunk in stream_generator:
        final_text = chunk.get("text_so_far", final_text) or final_text
        yield sse_format(chunk)

    # Emit a final cleaned payload so the front-end can display a single
    # final message without scaffolding. The client may still choose to
    # use incremental chunks, but the final event contains the polished
    # answer.
    cleaned = clean_response(final_text)
    if final_emitter:
        try:
            final_emitter(cleaned)
        except Exception:
            # Don't let emitter failures break the stream; fall back to SSE
            yield sse_format({"event": "final", "text": cleaned})
    else:
        yield sse_format({"event": "final", "text": cleaned})

    yield sse_format({"event": "done"})
