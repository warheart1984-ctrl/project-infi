"""Streaming response support using Server-Sent Events (SSE)

Optimized with KV cache reuse and autocast for faster token generation.
"""

import json
import torch
from src.logger import get_logger

logger = get_logger(__name__)


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
    ):
        """Generator that yields tokens one at a time with KV cache reuse

        Yields:
            dict with 'token', 'text_so_far', and 'finished' keys
        """
        logger.info(f"Starting streaming generation for: {prompt[:50]}...")

        inputs = self.tokenizer(
            prompt, return_tensors="pt", truncation=True
        ).to(self.device)
        input_ids = inputs["input_ids"]
        attention_mask = inputs.get("attention_mask", None)

        generated_ids = input_ids.clone()
        generated_text = ""
        past_key_values = None

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

                # Apply temperature
                if temperature > 0:
                    logits = logits / temperature

                # Apply top-p (nucleus) sampling
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

            generated_ids = torch.cat([generated_ids, next_token], dim=-1)

            token_text = self.tokenizer.decode(
                next_token[0], skip_special_tokens=True
            )
            generated_text += token_text

            if next_token.item() == self.tokenizer.eos_token_id:
                yield {
                    "token": "",
                    "text_so_far": generated_text,
                    "finished": True,
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
            }

        # Free KV cache memory
        del past_key_values
        if self.device == "cuda":
            torch.cuda.empty_cache()

        logger.info("Streaming generation complete")


def sse_format(data: dict) -> str:
    """Format a dict as a Server-Sent Event string"""
    return f"data: {json.dumps(data)}\n\n"


def create_sse_generator(stream_generator):
    """Wrap a streaming generator to produce SSE-formatted output"""
    for chunk in stream_generator:
        yield sse_format(chunk)
    yield sse_format({"event": "done"})
