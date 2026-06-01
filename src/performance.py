"""Performance optimization utilities for AAIS

Centralized module for quantization, compilation, device management,
inference caching, and model warm-up.
"""

import os
import time
import hashlib
import json
import functools
from contextlib import contextmanager
from src.logger import get_logger

logger = get_logger(__name__)


# ──────────────────────────────────────────────────
# Device & Precision Helpers
# ──────────────────────────────────────────────────

def get_optimal_device():
    """Detect the best available device"""
    import torch

    if torch.cuda.is_available():
        device = "cuda"
        gpu_name = torch.cuda.get_device_name(0)
        properties = torch.cuda.get_device_properties(0)
        total_vram = getattr(properties, "total_memory", None)
        if total_vram is None:
            total_vram = getattr(properties, "total_mem", 0)
        vram_gb = total_vram / (1024 ** 3)
        logger.info(f"GPU detected: {gpu_name} ({vram_gb:.1f} GB VRAM)")
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = "mps"
        logger.info("Apple MPS device detected")
    else:
        device = "cpu"
        logger.info("Using CPU")
    return device


def get_optimal_dtype(device: str):
    """Select the best dtype for the given device"""
    import torch

    precision = os.getenv("MODEL_PRECISION", "auto")

    if precision == "fp32":
        return torch.float32
    elif precision == "fp16":
        return torch.float16
    elif precision == "bf16":
        return torch.bfloat16

    # Auto-detect
    if device == "cuda":
        if torch.cuda.is_bf16_supported():
            logger.info("Using BF16 precision (auto-detected)")
            return torch.bfloat16
        logger.info("Using FP16 precision (auto-detected)")
        return torch.float16
    elif device == "mps":
        return torch.float16

    logger.info("Using FP32 precision (CPU)")
    return torch.float32


def get_quantization_config(device: str):
    """Build a BitsAndBytes quantization config if available and on CUDA"""
    if device != "cuda":
        return None

    quant_mode = os.getenv("QUANTIZATION", "none").lower()
    if quant_mode == "none":
        return None

    try:
        from transformers import BitsAndBytesConfig

        if quant_mode == "int8":
            logger.info("Enabling INT8 quantization")
            return BitsAndBytesConfig(load_in_8bit=True)
        elif quant_mode == "int4":
            logger.info("Enabling INT4 quantization (NF4)")
            return BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=get_optimal_dtype(device),
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
            )
    except ImportError:
        logger.warning("bitsandbytes not installed; skipping quantization")

    return None


# ──────────────────────────────────────────────────
# Model Compilation
# ──────────────────────────────────────────────────

def try_compile_model(model, mode: str = None):
    """Attempt torch.compile() for faster inference

    Args:
        model: PyTorch model
        mode: Compile mode ('reduce-overhead', 'max-autotune', 'default')
              Set via TORCH_COMPILE_MODE env var or pass directly.

    Returns:
        Compiled model, or original model if compilation fails/unavailable
    """
    import torch

    if os.getenv("DISABLE_TORCH_COMPILE", "false").lower() == "true":
        return model

    mode = mode or os.getenv("TORCH_COMPILE_MODE", "reduce-overhead")

    try:
        if hasattr(torch, "compile"):
            logger.info(f"Compiling model with torch.compile(mode='{mode}')")
            compiled = torch.compile(model, mode=mode)
            logger.info("Model compiled successfully")
            return compiled
    except Exception as e:
        logger.warning(f"torch.compile() failed, using eager mode: {e}")

    return model


# ──────────────────────────────────────────────────
# Inference Cache
# ──────────────────────────────────────────────────

class InferenceCache:
    """Cache inference results to avoid redundant computation.

    Uses Redis if available, falls back to an in-memory LRU dict.
    """

    def __init__(self, max_memory_items: int = 2048, default_ttl: int = 3600):
        self.default_ttl = default_ttl
        self._redis = None
        self._memory_cache = {}
        self._max_memory = max_memory_items
        self._access_order = []
        self._try_redis()

    def _try_redis(self):
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            return
        try:
            import redis
            self._redis = redis.from_url(redis_url)
            self._redis.ping()
            logger.info("InferenceCache: Redis connected")
        except Exception:
            self._redis = None

    @staticmethod
    def _make_key(prefix: str, **kwargs) -> str:
        raw = json.dumps(kwargs, sort_keys=True, default=str)
        h = hashlib.sha256(raw.encode()).hexdigest()[:24]
        return f"icache:{prefix}:{h}"

    def get(self, prefix: str, **kwargs):
        key = self._make_key(prefix, **kwargs)

        # Try Redis first
        if self._redis:
            try:
                val = self._redis.get(key)
                if val:
                    return json.loads(val)
            except Exception:
                pass

        # Fallback to memory
        return self._memory_cache.get(key)

    def set(self, prefix: str, value, ttl: int = None, **kwargs):
        key = self._make_key(prefix, **kwargs)
        ttl = ttl or self.default_ttl

        if self._redis:
            try:
                self._redis.setex(key, ttl, json.dumps(value, default=str))
                return
            except Exception:
                pass

        # Memory fallback with LRU eviction
        if len(self._memory_cache) >= self._max_memory and key not in self._memory_cache:
            if self._access_order:
                evict_key = self._access_order.pop(0)
                self._memory_cache.pop(evict_key, None)

        self._memory_cache[key] = value
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)


inference_cache = InferenceCache()


# ──────────────────────────────────────────────────
# Timing Utilities
# ──────────────────────────────────────────────────

@contextmanager
def timer(label: str):
    """Context manager that logs elapsed time"""
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    logger.info(f"[PERF] {label}: {elapsed:.3f}s")


def timed(func):
    """Decorator that logs function execution time"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.info(f"[PERF] {func.__qualname__}: {elapsed:.3f}s")
        return result
    return wrapper


# ──────────────────────────────────────────────────
# Model Warm-up
# ──────────────────────────────────────────────────

def warm_up_model(model, tokenizer, device, num_runs: int = 3):
    """Run dummy inferences to warm up the model and CUDA kernels"""
    import torch

    if os.getenv("SKIP_WARMUP", "false").lower() == "true":
        logger.info("Skipping model warm-up (SKIP_WARMUP=true)")
        return

    logger.info(f"Warming up model with {num_runs} dummy inferences...")
    dummy = "Hello, this is a warm-up prompt."
    inputs = tokenizer(dummy, return_tensors="pt").to(device)

    with torch.no_grad():
        for i in range(num_runs):
            model.generate(
                **inputs,
                max_new_tokens=16,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )

    # Sync CUDA if applicable
    if device == "cuda":
        torch.cuda.synchronize()

    logger.info("Model warm-up complete")


def warm_up_vision_model(model, processor, device, num_runs: int = 2):
    """Warm up the CLIP vision model"""
    import torch
    from PIL import Image
    import numpy as np

    if os.getenv("SKIP_WARMUP", "false").lower() == "true":
        return

    logger.info("Warming up vision model...")
    dummy_image = Image.fromarray(np.zeros((224, 224, 3), dtype=np.uint8))
    inputs = processor(images=dummy_image, return_tensors="pt").to(device)

    with torch.no_grad():
        for _ in range(num_runs):
            model.get_image_features(**inputs)

    if device == "cuda":
        torch.cuda.synchronize()

    logger.info("Vision model warm-up complete")


# ──────────────────────────────────────────────────
# Memory Management
# ──────────────────────────────────────────────────

def log_gpu_memory():
    """Log current GPU memory usage"""
    import torch

    if not torch.cuda.is_available():
        return

    allocated = torch.cuda.memory_allocated() / (1024 ** 3)
    reserved = torch.cuda.memory_reserved() / (1024 ** 3)
    logger.info(f"[GPU] Allocated: {allocated:.2f} GB | Reserved: {reserved:.2f} GB")


def clear_gpu_cache():
    """Free unused GPU memory"""
    import torch

    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        logger.info("GPU cache cleared")
