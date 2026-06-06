"""Multi-modal AI models for image and text processing

Optimized with quantization, torch.compile, KV caching,
inference caching, and model warm-up.
"""

import os
import time

try:
    from huggingface_hub import snapshot_download
except ImportError:
    def snapshot_download(*args, **kwargs):
        raise ImportError(
            "huggingface_hub is required for AAIS local model inference."
        )

try:
    from transformers import (
        AutoTokenizer,
        AutoModelForCausalLM,
        CLIPProcessor,
        CLIPModel,
    )
except ImportError:
    class _MissingModelRuntime:
        @staticmethod
        def from_pretrained(*args, **kwargs):
            raise ImportError(
                "transformers is required for AAIS local model inference. "
                "Install the model runtime extras before loading text or vision models."
            )

    AutoTokenizer = _MissingModelRuntime
    AutoModelForCausalLM = _MissingModelRuntime
    CLIPProcessor = _MissingModelRuntime
    CLIPModel = _MissingModelRuntime

try:
    import torch
except ImportError:
    torch = None


def _require_torch():
    if torch is None:
        raise ImportError(
            "PyTorch is required for AAIS local model inference. "
            "Install the model runtime extras before loading text, vision, or image models."
        )
    return torch


def clean_response(raw_response: str) -> str:
    """Return a cleaned final answer with all scaffolding removed.

    This is a pure helper so streaming or HTTP handlers can produce a
    final, client-friendly event instead of printing directly from
    the model instance.
    """
    if not raw_response:
        return ""

    # If scaffolding markers are present, strip everything up to the
    # first non-scaffolding content block.
    if any(keyword in raw_response for keyword in [
        "Response Trace", "Think Contract", "God Brain", "Plan Pass",
        "Memory Cues", "Council Deliberation", "Model Route", "Specialists",
        "workspace:", "memory:", "Answer Shape:"
    ]):
        lines = raw_response.splitlines()
        clean_lines = []
        in_scaffolding = True
        for line in lines:
            if any(keyword in line for keyword in [
                "Response Trace", "Think Contract", "God Brain", "Plan Pass",
                "Memory Cues", "Council Deliberation", "Model Route", "Specialists",
                "workspace:", "memory:", "Answer Shape:"
            ]):
                in_scaffolding = True
                continue
            if in_scaffolding and not line.strip():
                continue
            in_scaffolding = False
            clean_lines.append(line)
        return "\n".join(clean_lines).strip()

    return raw_response


def _estimate_token_count(text: str) -> int:
    normalized = str(text or "").strip()
    if not normalized:
        return 0
    return max(1, len(normalized) // 4)


import io
from src.generation_utils import (
    decode_generated_text,
    looks_like_prompt_echo,
    prepare_generation_prompt,
    render_messages_for_model,
    resolve_input_token_limit,
)
from src.document_vision import DocumentVisionUnavailable, document_vision
from src.logger import get_logger
from src.performance import (
    get_optimal_device,
    get_optimal_dtype,
    get_quantization_config,
    try_compile_model,
    warm_up_model,
    warm_up_vision_model,
    log_gpu_memory,
    inference_cache,
    timer,
    timed,
)
from src.ui_vision import UIVisionUnavailable, ui_vision

logger = get_logger(__name__)

VISION_LABEL_PROMPTS = (
    {"label": "portrait", "prompt": "a portrait photo of a person"},
    {"label": "people", "prompt": "a photo of several people"},
    {"label": "animal", "prompt": "a photo of an animal"},
    {"label": "dog", "prompt": "a photo of a dog"},
    {"label": "cat", "prompt": "a photo of a cat"},
    {"label": "food", "prompt": "a photo of food"},
    {"label": "product", "prompt": "a product shot"},
    {"label": "vehicle", "prompt": "a photo of a car or vehicle"},
    {"label": "building", "prompt": "a photo of a building or architecture"},
    {"label": "city", "prompt": "a city scene"},
    {"label": "nature", "prompt": "a nature scene"},
    {"label": "landscape", "prompt": "a wide outdoor landscape"},
    {"label": "indoor", "prompt": "an indoor scene"},
    {"label": "outdoor", "prompt": "an outdoor scene"},
    {"label": "night", "prompt": "a night scene"},
    {"label": "close-up", "prompt": "a close-up image"},
    {"label": "document", "prompt": "a document or printed page"},
    {"label": "text-heavy", "prompt": "an image with a lot of readable text"},
    {"label": "screenshot", "prompt": "a computer or phone screenshot"},
    {"label": "code", "prompt": "a code editor screenshot"},
    {"label": "chart", "prompt": "a chart, graph, or diagram"},
    {"label": "illustration", "prompt": "a digital illustration"},
    {"label": "painting", "prompt": "a painting or artwork"},
    {"label": "poster", "prompt": "a poster or designed graphic"},
    {"label": "photo", "prompt": "a natural photograph"},
)


class MultiModalAI:
    """Optimized multi-modal AI system for text and image processing"""

    def __init__(self, device=None):
        """Initialize multi-modal AI models with performance optimizations"""
        self.device = device or get_optimal_device()
        self.dtype = get_optimal_dtype(self.device)
        logger.info(f"Using device: {self.device} | dtype: {self.dtype}")

        self.profile = os.getenv("AAIS_MODEL_PROFILE", "full").strip().lower()
        self.models = {}
        self.text_model = None
        self.text_tokenizer = None
        self.vision_model = None
        self.vision_processor = None
        self.image_generator = None
        self.text_adapter_aliases = {}
        self.active_text_adapter = None
        self.adapter_governance = {}
        self.last_generation_metadata = {}
        self._load_models()

    def _load_models(self):
        """Retained as a no-op hook for compatibility with existing tests."""
        return None

    def _resolve_model_name(self, env_key, full_default, lite_default):
        """Resolve model names from env vars with an optional lightweight profile."""
        explicit = os.getenv(env_key)
        if explicit:
            return explicit
        if self.profile == "lite":
            return lite_default
        return full_default

    def _resolve_local_model_source(self, model_name):
        """Prefer a cached local Hugging Face snapshot when one is available."""
        try:
            return snapshot_download(repo_id=model_name, local_files_only=True)
        except Exception:
            return model_name

    def _load_text_adapter(self, adapter_path, adapter_name="default"):
        """Load an optional PEFT adapter on top of the base text model."""
        from peft import PeftModel

        return PeftModel.from_pretrained(
            self.text_model,
            adapter_path,
            adapter_name=adapter_name,
            is_trainable=False,
        )

    def _resolve_text_adapter_paths(self):
        """Resolve default and mode-specific adapter paths from the environment."""
        # Parse enable/disable flag explicitly. Treat missing value as enabled by default.
        adapters_enabled = os.getenv("AAIS_ENABLE_TEXT_ADAPTERS", "1")
        if str(adapters_enabled).strip().lower() not in {"1", "true", "yes", "on"}:
            logger.info("Text adapters disabled by AAIS_ENABLE_TEXT_ADAPTERS")
            return {}

        default_path = os.getenv("AAIS_TEXT_ADAPTER_PATH", "").strip()
        mode_paths = {
            "tiny": os.getenv("AAIS_TEXT_ADAPTER_TINY_PATH", "").strip(),
            "fast": os.getenv("AAIS_TEXT_ADAPTER_FAST_PATH", "").strip(),
            "think": os.getenv("AAIS_TEXT_ADAPTER_THINK_PATH", "").strip(),
            "debug": os.getenv("AAIS_TEXT_ADAPTER_DEBUG_PATH", "").strip(),
            "builder": os.getenv("AAIS_TEXT_ADAPTER_BUILDER_PATH", "").strip(),
            "research": os.getenv("AAIS_TEXT_ADAPTER_RESEARCH_PATH", "").strip(),
            "operator": os.getenv("AAIS_TEXT_ADAPTER_OPERATOR_PATH", "").strip(),
        }
        mode_fallbacks = {
            "tiny": ("tiny", "fast", "default"),
            "fast": ("fast", "default"),
            "think": ("think", "default"),
            "debug": ("debug", "think", "default"),
            "builder": ("builder", "fast", "default"),
            "research": ("research", "think", "default"),
            "operator": ("operator", "fast", "default"),
        }

        adapter_paths = {}
        # If a default adapter path is provided, make sure a 'fast' alias
        # is registered so the primary adapter loads under the 'fast' name
        # (this keeps behavior deterministic when only AAIS_TEXT_ADAPTER_PATH
        # is present).
        if default_path:
            adapter_paths["fast"] = default_path
            adapter_paths["default"] = default_path

        for mode, candidates in mode_fallbacks.items():
            for candidate in candidates:
                if candidate == "default" and default_path:
                    adapter_paths[mode] = default_path
                    break
                candidate_path = mode_paths.get(candidate, "")
                if candidate_path:
                    adapter_paths[mode] = candidate_path
                    break

        return {key: value for key, value in adapter_paths.items() if value}

    def _read_adapter_metadata(self, adapter_path: str):
        """Load adapter metadata when present."""
        from pathlib import Path
        import json

        metadata_path = Path(adapter_path) / "adapter_metadata.json"
        if not metadata_path.is_file():
            return None
        try:
            return json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def _filter_adapter_paths_by_governance(self, adapter_paths: dict[str, str]) -> dict[str, str]:
        """Drop adapter paths that fail governed load checks."""
        from src.jarvis_lora_training_validator import evaluate_adapter_load_gate

        runtime_base_model = str(getattr(self, "text_model_name", "") or os.getenv("AAIS_TEXT_MODEL_NAME", "")).strip()
        allowed_paths: dict[str, str] = {}
        blocked: list[dict] = []

        for mode, adapter_path in adapter_paths.items():
            metadata = self._read_adapter_metadata(adapter_path)
            allowed, reason, governance = evaluate_adapter_load_gate(
                metadata,
                runtime_base_model,
                label=f"{mode}:{adapter_path}",
            )
            if allowed:
                allowed_paths[mode] = adapter_path
            else:
                blocked.append({"mode": mode, "adapter_path": adapter_path, "reason": reason, **governance})
                logger.warning(
                    "Skipping text adapter for %s (%s): %s",
                    mode,
                    adapter_path,
                    reason,
                )

        self.adapter_governance = {
            "runtime_base_model": runtime_base_model,
            "allowed_paths": allowed_paths,
            "blocked": blocked,
        }
        return allowed_paths

    def _maybe_apply_text_adapter(self):
        """Attach a fine-tuned adapter when one is configured."""
        adapter_paths = self._resolve_text_adapter_paths()
        if not adapter_paths:
            self.adapter_governance = {}
            return

        adapter_paths = self._filter_adapter_paths_by_governance(adapter_paths)
        if not adapter_paths:
            logger.warning("No governed text adapters passed load gate")
            return

        primary_key = "fast" if adapter_paths.get("fast") else next(iter(adapter_paths))
        primary_path = adapter_paths[primary_key]

        logger.info(f"Loading text adapter ({primary_key}) from: {primary_path}")
        try:
            self.text_model = self._load_text_adapter(primary_path, adapter_name=primary_key)
        except ImportError as exc:
            raise ImportError(
                "peft is required to load AAIS text adapters. "
                "Install it with the training extras."
            ) from exc
        self.text_adapter_aliases = {
            key: primary_key if path == primary_path else key
            for key, path in adapter_paths.items()
        }

        for adapter_key, adapter_path in adapter_paths.items():
            if adapter_key == primary_key or adapter_path == primary_path:
                continue
            logger.info(f"Loading additional text adapter ({adapter_key}) from: {adapter_path}")
            try:
                self.text_model.load_adapter(
                    adapter_path,
                    adapter_name=adapter_key,
                    is_trainable=False,
                )
            except TypeError:
                self.text_model.load_adapter(adapter_path, adapter_name=adapter_key)
            self.text_adapter_aliases[adapter_key] = adapter_key

        self.active_text_adapter = self.text_adapter_aliases.get(primary_key, primary_key)
        logger.info("Text adapter(s) attached successfully")

    def _select_text_adapter(self, response_mode=None):
        """Switch to the adapter that matches the current response mode."""
        if not self.text_adapter_aliases:
            return

        cleaned_mode = " ".join(str(response_mode or "").lower().split()).replace("-", "_")
        if cleaned_mode not in {"tiny", "fast", "think", "debug", "builder", "research", "operator"}:
            cleaned_mode = "fast"

        target_adapter = (
            self.text_adapter_aliases.get(cleaned_mode)
            or self.text_adapter_aliases.get("default")
            or self.active_text_adapter
        )
        if not target_adapter or target_adapter == self.active_text_adapter:
            return

        if hasattr(self.text_model, "set_adapter"):
            self.text_model.set_adapter(target_adapter)
            self.active_text_adapter = target_adapter
            logger.info(f"Activated text adapter for {cleaned_mode}: {target_adapter}")

    def _load_text_model(self):
        """Load text generation model with quantization support"""
        if self.text_model is not None and self.text_tokenizer is not None:
            return

        with timer("Load text model"):
            self.text_model_name = self._resolve_model_name(
                "AAIS_TEXT_MODEL_NAME",
                "mistralai/Mistral-7B-Instruct-v0.1",
                "Qwen/Qwen2.5-0.5B-Instruct",
            )
            logger.info(f"Loading text model: {self.text_model_name}")
            text_model_source = self._resolve_local_model_source(self.text_model_name)

            self.text_tokenizer = AutoTokenizer.from_pretrained(
                text_model_source
            )
            # Ensure pad token is set
            if self.text_tokenizer.pad_token is None:
                self.text_tokenizer.pad_token = self.text_tokenizer.eos_token

            quant_config = get_quantization_config(self.device)

            load_kwargs = {
                "torch_dtype": self.dtype,
                "low_cpu_mem_usage": True,
            }

            if quant_config:
                load_kwargs["quantization_config"] = quant_config
                load_kwargs["device_map"] = "auto"
            elif self.device == "cuda":
                load_kwargs["device_map"] = "auto"

            self.text_model = AutoModelForCausalLM.from_pretrained(
                text_model_source, **load_kwargs
            )

            if self.device == "cpu" and not quant_config:
                self.text_model = self.text_model.to(self.device)

            self._maybe_apply_text_adapter()

            # Enable better memory efficiency
            if hasattr(self.text_model, "config"):
                self.text_model.config.use_cache = True

            # Compile for faster inference
            if len(set(self.text_adapter_aliases.values())) > 1:
                logger.info("Skipping torch.compile so mode-specific adapters can switch safely")
            else:
                self.text_model = try_compile_model(self.text_model)

            # Set to eval mode
            self.text_model.eval()

            # Warm up
            warm_up_model(
                self.text_model, self.text_tokenizer, self.device
            )

            logger.info("Text model loaded and optimized")

    def _load_vision_model(self):
        """Load CLIP vision model"""
        if self.vision_model is not None and self.vision_processor is not None:
            return

        with timer("Load vision model"):
            self.vision_model_name = self._resolve_model_name(
                "AAIS_VISION_MODEL_NAME",
                "openai/clip-vit-base-patch32",
                "openai/clip-vit-base-patch32",
            )
            logger.info(f"Loading vision model: {self.vision_model_name}")
            vision_model_source = self._resolve_local_model_source(self.vision_model_name)
            self.vision_model = CLIPModel.from_pretrained(
                vision_model_source,
                torch_dtype=self.dtype,
            ).to(self.device)
            self.vision_processor = CLIPProcessor.from_pretrained(
                vision_model_source
            )
            self.vision_model.eval()

            warm_up_vision_model(
                self.vision_model, self.vision_processor, self.device
            )
            logger.info("Vision model loaded and optimized")

    @staticmethod
    def _extract_dominant_colors(image, limit=4):
        """Return a compact dominant-color palette from an RGB image."""
        palette_image = image.convert("RGB").resize((96, 96)).quantize(colors=max(limit * 2, 8))
        palette = palette_image.getpalette() or []
        color_counts = sorted(palette_image.getcolors() or [], reverse=True)
        total = sum(count for count, _ in color_counts) or 1

        colors = []
        seen = set()
        for count, palette_index in color_counts:
            base = palette_index * 3
            rgb = tuple(int(channel) for channel in palette[base: base + 3])
            if len(rgb) != 3 or rgb in seen:
                continue
            seen.add(rgb)
            colors.append(
                {
                    "hex": "#{:02X}{:02X}{:02X}".format(*rgb),
                    "rgb": list(rgb),
                    "share": round(count / total, 3),
                }
            )
            if len(colors) >= limit:
                break

        return colors

    @staticmethod
    def _describe_image_shape(size):
        """Describe image orientation from pixel dimensions."""
        width, height = size
        if width == height:
            return "square"
        if width > height:
            return "landscape"
        return "portrait"

    @staticmethod
    def _build_grounded_image_description(top_matches, dominant_colors, image_size):
        """Render a grounded, compact summary from ranked labels and palette data."""
        orientation = MultiModalAI._describe_image_shape(image_size)
        width, height = image_size
        label_names = [match["label"] for match in top_matches[:3]]
        score_bits = [
            f"{match['label']} ({int(round(match['score'] * 100))}%)"
            for match in top_matches[:3]
        ]
        color_names = [color["hex"] for color in dominant_colors[:3]]

        if not label_names:
            base = f"This is a {orientation} image sized {width}x{height}."
        elif len(label_names) == 1:
            base = (
                f"This looks like a {orientation} image most strongly matching "
                f"{label_names[0]}."
            )
        else:
            base = (
                f"This looks like a {orientation} image with the strongest cues for "
                f"{label_names[0]}, then {label_names[1]}"
            )
            if len(label_names) > 2:
                base += f", with some signal for {label_names[2]}"
            base += "."

        details = [f"Resolution is {width}x{height}."]
        if score_bits:
            details.append(f"Top visual matches: {', '.join(score_bits)}.")
        if color_names:
            details.append(f"Dominant colors: {', '.join(color_names)}.")

        details.append(
            "This is a grounded CLIP-style visual read, so treat it as fast scene tagging rather than OCR or dense captioning."
        )
        return " ".join([base] + details)

    def _rank_image_labels(self, image, candidate_labels=None, top_k=5):
        """Rank simple label prompts against the current image using CLIP similarity."""
        torch_module = _require_torch()
        self._load_vision_model()
        label_specs = list(candidate_labels or VISION_LABEL_PROMPTS)
        prompts = [spec["prompt"] for spec in label_specs]

        image_inputs = self.vision_processor(images=image, return_tensors="pt").to(self.device)
        text_inputs = self.vision_processor(
            text=prompts,
            return_tensors="pt",
            padding=True,
            truncation=True,
        ).to(self.device)

        with torch_module.no_grad(), torch_module.amp.autocast(
            device_type=self.device if self.device in ("cuda", "cpu") else "cpu",
            enabled=self.device == "cuda",
        ):
            image_features = self.vision_model.get_image_features(**image_inputs)
            text_features = self.vision_model.get_text_features(**text_inputs)
            if hasattr(image_features, "image_embeds"):
                image_features = image_features.image_embeds
            elif hasattr(image_features, "pooler_output"):
                image_features = image_features.pooler_output
            if hasattr(text_features, "text_embeds"):
                text_features = text_features.text_embeds
            elif hasattr(text_features, "pooler_output"):
                text_features = text_features.pooler_output

            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            scores = (100.0 * image_features @ text_features.T).softmax(dim=-1).squeeze(0)

        top_values, top_indices = torch_module.topk(scores, k=min(top_k, len(label_specs)))
        top_matches = []
        for score, index in zip(top_values.tolist(), top_indices.tolist()):
            spec = label_specs[index]
            top_matches.append(
                {
                    "label": spec["label"],
                    "prompt": spec["prompt"],
                    "score": round(float(score), 4),
                }
            )

        return image_features, top_matches

    def _load_image_generator(self):
        """Load image generation pipeline"""
        if self.image_generator is not None:
            return

        if os.getenv("AAIS_DISABLE_IMAGE_GENERATION", "false").lower() == "true":
            raise RuntimeError("Image generation is disabled for this deployment")

        with timer("Load image generator"):
            self.image_model_name = self._resolve_model_name(
                "AAIS_IMAGE_MODEL_NAME",
                "stabilityai/stable-diffusion-2",
                "optimum-intel-internal-testing/tiny-stable-diffusion-torch",
            )
            logger.info("Loading image generation model...")
            image_model_source = self._resolve_local_model_source(self.image_model_name)
            try:
                from diffusers import AutoPipelineForText2Image
            except ImportError as exc:
                raise ImportError(
                    "diffusers is required for image generation. "
                    "Install with: pip install diffusers"
                ) from exc

            pipe_kwargs = {"torch_dtype": self.dtype}
            self.image_generator = AutoPipelineForText2Image.from_pretrained(
                image_model_source,
                **pipe_kwargs,
            ).to(self.device)
            logger.info("Image generation model loaded")

    def _generate_from_rendered_prompt(
        self,
        rendered_prompt,
        cache_prefix,
        cache_kwargs,
        max_length=512,
        temperature=0.7,
        min_new_tokens=0,
        do_sample=None,
        repetition_penalty=1.05,
        input_max_length=None,
        top_p=0.95,
        no_repeat_ngram_size=0,
    ):
        """Run generation from a fully rendered prompt string."""
        self._load_text_model()

        cached = inference_cache.get(
            cache_prefix,
            max_length=max_length,
            temperature=temperature,
            **cache_kwargs,
        )
        if cached is not None:
            logger.info("Text generation cache hit")
            self.last_generation_metadata = {
                "stop_reason": "cache_hit",
                "finish_reason": "stop",
                "input_tokens": 0,
                "output_tokens": _estimate_token_count(cached),
                "output_token_budget": int(max_length or 0),
                "cache_hit": True,
                "adapter_governance": dict(self.adapter_governance or {}),
            }
            return cached

        prompt_token_limit = input_max_length or resolve_input_token_limit(
            self.text_tokenizer,
            max_length,
        )

        inputs = self.text_tokenizer(
            rendered_prompt,
            return_tensors="pt",
            truncation=True,
            max_length=prompt_token_limit,
        ).to(self.device)
        prompt_length = inputs["input_ids"].shape[1]
        self.last_generation_metadata = {
            "stop_reason": None,
            "finish_reason": None,
            "input_tokens": int(prompt_length),
            "output_tokens": 0,
            "output_token_budget": int(max_length or 0),
            "cache_hit": False,
            "adapter_governance": dict(self.adapter_governance or {}),
        }

        sample_tokens = max(0, int(min_new_tokens or 0))
        should_sample = bool(temperature > 0.45) if do_sample is None else bool(do_sample)

        generation_kwargs = {
            **inputs,
            "max_new_tokens": max_length,
            "min_new_tokens": sample_tokens,
            "pad_token_id": self.text_tokenizer.eos_token_id,
            "use_cache": True,
            "repetition_penalty": repetition_penalty,
        }
        if no_repeat_ngram_size and int(no_repeat_ngram_size) > 0:
            generation_kwargs["no_repeat_ngram_size"] = int(no_repeat_ngram_size)

        if should_sample:
            generation_kwargs.update(
                {
                    "temperature": temperature,
                    "top_p": top_p,
                    "do_sample": True,
                }
            )
        else:
            generation_kwargs.update(
                {
                    "do_sample": False,
                }
            )

        torch_module = _require_torch()
        with torch_module.no_grad(), torch_module.amp.autocast(
            device_type=self.device if self.device in ("cuda", "cpu") else "cpu",
            enabled=self.device == "cuda",
        ):
            outputs = self.text_model.generate(**generation_kwargs)

        generated_text = decode_generated_text(
            self.text_tokenizer,
            outputs[0],
            prompt_length,
        )
        generated_tokens = outputs[0][prompt_length:]
        stop_reason = "eos_token"
        finish_reason = "stop"
        if generated_tokens.numel() > 0 and generated_tokens[-1].item() != self.text_tokenizer.eos_token_id:
            stop_reason = "max_new_tokens"
            finish_reason = "length"
        self.last_generation_metadata = {
            "stop_reason": stop_reason,
            "finish_reason": finish_reason,
            "input_tokens": int(prompt_length),
            "output_tokens": int(generated_tokens.shape[0]),
            "output_token_budget": int(max_length or 0),
            "cache_hit": False,
        }

        if temperature <= 0.3:
            inference_cache.set(
                cache_prefix,
                generated_text,
                ttl=1800,
                max_length=max_length,
                temperature=temperature,
                **cache_kwargs,
            )

        return generated_text

    @staticmethod
    def _chat_generation_profile(response_mode, temperature, max_length, routing_profile=None):
        """Choose deterministic generation defaults for Jarvis chat modes."""
        cleaned_mode = " ".join(str(response_mode or "").lower().split()).replace("-", "_")
        if cleaned_mode == "tiny":
            profile = {
                "temperature": min(temperature, 0.4),
                "do_sample": False,
                "min_new_tokens": min(max(10, max_length // 10), max_length),
                "repetition_penalty": 1.03,
                "input_max_length": 1280,
                "top_p": 0.95,
                "no_repeat_ngram_size": 0,
            }
        elif cleaned_mode == "think":
            profile = {
                "temperature": min(temperature, 0.25),
                "do_sample": False,
                "min_new_tokens": min(max(32, max_length // 4), max_length),
                "repetition_penalty": 1.08,
                "input_max_length": 2048,
                "top_p": 0.95,
                "no_repeat_ngram_size": 0,
            }
        elif cleaned_mode == "debug":
            profile = {
                "temperature": min(temperature, 0.2),
                "do_sample": False,
                "min_new_tokens": min(max(28, max_length // 4), max_length),
                "repetition_penalty": 1.1,
                "input_max_length": 2048,
                "top_p": 0.95,
                "no_repeat_ngram_size": 0,
            }
        elif cleaned_mode == "builder":
            profile = {
                "temperature": min(temperature, 0.3),
                "do_sample": False,
                "min_new_tokens": min(max(20, max_length // 5), max_length),
                "repetition_penalty": 1.06,
                "input_max_length": 1792,
                "top_p": 0.95,
                "no_repeat_ngram_size": 0,
            }
        elif cleaned_mode == "research":
            profile = {
                "temperature": min(temperature, 0.18),
                "do_sample": False,
                "min_new_tokens": min(max(28, max_length // 4), max_length),
                "repetition_penalty": 1.07,
                "input_max_length": 2304,
                "top_p": 0.95,
                "no_repeat_ngram_size": 0,
            }
        elif cleaned_mode == "operator":
            profile = {
                "temperature": min(temperature, 0.2),
                "do_sample": False,
                "min_new_tokens": min(max(16, max_length // 5), max_length),
                "repetition_penalty": 1.06,
                "input_max_length": 1792,
                "top_p": 0.95,
                "no_repeat_ngram_size": 0,
            }
        else:
            profile = {
                "temperature": min(temperature, 0.35),
                "do_sample": False,
                "min_new_tokens": min(max(8, max_length // 12), max_length),
                "repetition_penalty": 1.05,
                "input_max_length": 1536,
                "top_p": 0.95,
                "no_repeat_ngram_size": 0,
            }

        route_overrides = (routing_profile or {}).get("generation_overrides") or {}
        if route_overrides:
            if route_overrides.get("temperature_max") is not None:
                profile["temperature"] = min(profile["temperature"], route_overrides["temperature_max"])
            if route_overrides.get("min_new_tokens_floor") is not None:
                profile["min_new_tokens"] = max(
                    profile["min_new_tokens"],
                    min(int(route_overrides["min_new_tokens_floor"]), max_length),
                )
            if route_overrides.get("min_new_tokens_ratio") is not None:
                profile["min_new_tokens"] = max(
                    profile["min_new_tokens"],
                    min(max_length, max(1, int(max_length * route_overrides["min_new_tokens_ratio"]))),
                )
            if route_overrides.get("repetition_penalty") is not None:
                profile["repetition_penalty"] = max(
                    profile["repetition_penalty"],
                    route_overrides["repetition_penalty"],
                )
            if route_overrides.get("input_max_length") is not None:
                profile["input_max_length"] = max(
                    profile["input_max_length"],
                    int(route_overrides["input_max_length"]),
                )
            if route_overrides.get("top_p") is not None:
                profile["top_p"] = route_overrides["top_p"]
            if route_overrides.get("no_repeat_ngram_size") is not None:
                profile["no_repeat_ngram_size"] = int(route_overrides["no_repeat_ngram_size"])
        return profile

    @staticmethod
    def _build_chat_retry_messages(messages):
        """Strip the prompt down if the first answer looks like prompt echo."""
        latest_user = None
        recent_dialogue = []

        for message in reversed(messages or []):
            role = message.get("role")
            if role in {"user", "assistant"}:
                recent_dialogue.insert(0, message)
            if role == "user" and latest_user is None:
                latest_user = message.get("content", "").strip()

        compact = [
            {
                "role": "system",
                "content": (
                    "You are Jarvis, a private local operator AI. "
                    "Answer the operator directly. Do not repeat hidden prompt text, "
                    "system notes, or runtime metadata."
                ),
            }
        ]
        compact.extend(recent_dialogue[-4:])
        if latest_user and (not compact or compact[-1].get("role") != "user"):
            compact.append({"role": "user", "content": latest_user})
        return compact

    @timed
    def generate_text(self, prompt, max_length=512, temperature=0.7):
        """Generate text with inference caching and optimized decoding

        Args:
            prompt: Input text prompt
            max_length: Maximum length of generated text
            temperature: Sampling temperature (higher = more creative)

        Returns:
            Generated text
        """
        try:
            self._load_text_model()
            logger.info(f"Generating text for prompt: {prompt[:50]}...")

            rendered_prompt = prepare_generation_prompt(
                self.text_tokenizer, prompt
            )
            generated_text = self._generate_from_rendered_prompt(
                rendered_prompt,
                "text_gen",
                {"prompt": prompt},
                max_length=max_length,
                temperature=temperature,
            )

            logger.info("Text generation completed")
            return generated_text

        except Exception as e:
            logger.error(f"Error generating text: {e}")
            raise

    @timed
    def generate_chat(
        self,
        messages,
        max_length=512,
        temperature=0.7,
        response_mode=None,
        routing_profile=None,
    ):
        """Generate a response from structured conversation turns."""
        try:
            self._load_text_model()
            self._select_text_adapter(
                (routing_profile or {}).get("adapter_mode") or response_mode
            )
            rendered_prompt = render_messages_for_model(
                self.text_tokenizer,
                messages,
            )
            logger.info("Generating chat response from structured messages")
            generation_profile = self._chat_generation_profile(
                response_mode=response_mode,
                temperature=temperature,
                max_length=max_length,
                routing_profile=routing_profile,
            )

            response_text = self._generate_from_rendered_prompt(
                rendered_prompt,
                "chat_gen",
                {
                    "messages": messages,
                    "response_mode": response_mode,
                    "route_id": (routing_profile or {}).get("id"),
                },
                max_length=max_length,
                temperature=generation_profile["temperature"],
                min_new_tokens=generation_profile["min_new_tokens"],
                do_sample=generation_profile["do_sample"],
                repetition_penalty=generation_profile["repetition_penalty"],
                input_max_length=generation_profile["input_max_length"],
                top_p=generation_profile.get("top_p", 0.95),
                no_repeat_ngram_size=generation_profile.get("no_repeat_ngram_size", 0),
            )

            if not response_text or looks_like_prompt_echo(response_text):
                logger.warning("Chat response looked empty or echoed the prompt; retrying compactly")
                retry_messages = self._build_chat_retry_messages(messages)
                retry_prompt = render_messages_for_model(
                    self.text_tokenizer,
                    retry_messages,
                )
                retry_profile = dict(generation_profile)
                retry_profile["min_new_tokens"] = min(
                    max(24, retry_profile["min_new_tokens"]),
                    max_length,
                )
                retry_profile["temperature"] = min(retry_profile["temperature"], 0.2)
                retry_profile["do_sample"] = False
                response_text = self._generate_from_rendered_prompt(
                    retry_prompt,
                    "chat_gen_retry",
                    {
                        "messages": retry_messages,
                        "response_mode": response_mode,
                        "route_id": (routing_profile or {}).get("id"),
                    },
                    max_length=max_length,
                    temperature=retry_profile["temperature"],
                    min_new_tokens=retry_profile["min_new_tokens"],
                    do_sample=retry_profile["do_sample"],
                    repetition_penalty=retry_profile["repetition_penalty"],
                    input_max_length=retry_profile["input_max_length"],
                    top_p=retry_profile.get("top_p", 0.95),
                    no_repeat_ngram_size=retry_profile.get("no_repeat_ngram_size", 0),
                )

            if not response_text:
                response_text = (
                    "I am live, but that answer came back empty. "
                    "Ask me again and I will keep the response tighter."
                )
                self.last_generation_metadata = {
                    "stop_reason": "empty_output",
                    "finish_reason": "empty_output",
                    "input_tokens": int((self.last_generation_metadata or {}).get("input_tokens") or 0),
                    "output_tokens": _estimate_token_count(response_text),
                    "output_token_budget": int(max_length or 0),
                    "cache_hit": bool((self.last_generation_metadata or {}).get("cache_hit")),
                }
            else:
                self.last_generation_metadata = {
                    **dict(self.last_generation_metadata or {}),
                    "output_tokens": int(
                        (self.last_generation_metadata or {}).get("output_tokens")
                        or _estimate_token_count(response_text)
                    ),
                    "output_token_budget": int(max_length or 0),
                }

            logger.info("Chat generation completed")
            return response_text

        except Exception as e:
            logger.error(f"Error generating chat response: {e}")
            raise

    @timed
    def analyze_image(self, image_input, include_ocr=False, include_ui=False):
        """Analyze image with optimized CLIP inference

        Args:
            image_input: PIL Image or image path
            include_ocr: Whether to attach OCR/document-vision output when available
            include_ui: Whether to attach screenshot/UI understanding output when available

        Returns:
            Image analysis and description
        """
        try:
            logger.info("Analyzing image...")

            if isinstance(image_input, str):
                from PIL import Image
                image = Image.open(image_input).convert("RGB")
            else:
                image = image_input

            image_features, top_matches = self._rank_image_labels(image)
            dominant_colors = self._extract_dominant_colors(image)
            description = self._build_grounded_image_description(
                top_matches,
                dominant_colors,
                image.size,
            )
            should_attempt_ocr = include_ocr or include_ui
            ocr_result = None
            if should_attempt_ocr:
                try:
                    ocr_result = document_vision.extract_document_text(
                        image,
                        top_matches=top_matches,
                    )
                    if ocr_result.get("status") == "available":
                        description = (
                            f"{description} {ocr_result['summary']}"
                        ).strip()
                except DocumentVisionUnavailable as exc:
                    ocr_result = document_vision.describe_unavailable(
                        requested=True,
                        top_matches=top_matches,
                        message=str(exc),
                    )
            else:
                ocr_result = document_vision.describe_unavailable(
                    requested=False,
                    top_matches=top_matches,
                    message=(
                        "Document vision is wired, but this analysis did not request OCR."
                    ),
                )
            ui_result = None
            if include_ui:
                try:
                    ui_result = ui_vision.analyze(
                        image,
                        top_matches=top_matches,
                        ocr_result=ocr_result,
                    )
                    if ui_result.get("status") == "available":
                        description = f"{description} {ui_result['summary']}".strip()
                except UIVisionUnavailable as exc:
                    ui_result = ui_vision.describe_unavailable(
                        requested=True,
                        top_matches=top_matches,
                        message=str(exc),
                    )
            else:
                ui_result = ui_vision.describe_unavailable(
                    requested=False,
                    top_matches=top_matches,
                    message=(
                        "UI understanding is wired, but this analysis did not request it."
                    ),
                )

            logger.info("Image analysis completed")
            return {
                "description": description,
                "analysis_method": "clip-grounded-label-ranking",
                "top_matches": top_matches,
                "dominant_colors": dominant_colors,
                "image_size": {
                    "width": int(image.size[0]),
                    "height": int(image.size[1]),
                    "orientation": self._describe_image_shape(image.size),
                },
                "image_features_shape": list(image_features.shape),
                "ocr": ocr_result,
                "ui": ui_result,
            }

        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            raise

    @timed
    def generate_image(self, prompt, num_inference_steps=50):
        """Generate image from text prompt

        Args:
            prompt: Text description of desired image
            num_inference_steps: Number of inference steps

        Returns:
            Generated PIL Image
        """
        try:
            logger.info(f"Generating image for prompt: {prompt}")
            self._load_image_generator()

            image = self.image_generator(
                prompt,
                num_inference_steps=num_inference_steps,
                guidance_scale=7.5,
            ).images[0]

            logger.info("Image generation completed")
            return image

        except Exception as e:
            logger.error(f"Error generating image: {e}")
            raise

    @timed
    def multimodal_query(self, text_prompt, image_input=None):
        """Process combined text and image query

        Args:
            text_prompt: Text query
            image_input: Optional image for context

        Returns:
            Combined analysis and response
        """
        try:
            logger.info("Processing multi-modal query...")

            result = {
                "text_response": self.generate_text(text_prompt),
                "image_analysis": None,
            }

            if image_input:
                result["image_analysis"] = self.analyze_image(image_input)

            logger.info("Multi-modal query completed")
            return result

        except Exception as e:
            logger.error(f"Error processing multi-modal query: {e}")
            raise

    def _emit_clean_response(self, raw_response: str) -> None:
        """HARD OUTPUT GATE: Suppress all scaffolding and emit only the final answer.

        This implementation delegates to the pure `clean_response` helper so
        streaming or HTTP handlers can reuse the same cleaning logic.
        """
        if not raw_response or not raw_response.strip():
            return

        cleaned = clean_response(raw_response)
        if not cleaned:
            return

        print(cleaned)
