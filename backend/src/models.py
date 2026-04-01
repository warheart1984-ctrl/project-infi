"""Multi-modal AI models for image and text processing

Optimized with quantization, torch.compile, KV caching,
inference caching, and model warm-up.
"""

import time
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    CLIPProcessor,
    CLIPModel,
    pipeline,
)
from PIL import Image
import io
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

logger = get_logger(__name__)


class MultiModalAI:
    """Optimized multi-modal AI system for text and image processing"""

    def __init__(self, device=None):
        """Initialize multi-modal AI models with performance optimizations"""
        self.device = device or get_optimal_device()
        self.dtype = get_optimal_dtype(self.device)
        logger.info(f"Using device: {self.device} | dtype: {self.dtype}")

        self.models = {}
        self._load_models()

    def _load_models(self):
        """Load all required models with quantization and compilation"""
        try:
            self._load_text_model()
            self._load_vision_model()
            self._load_image_generator()
            log_gpu_memory()
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            raise

    def _load_text_model(self):
        """Load text generation model with quantization support"""
        with timer("Load text model"):
            self.text_model_name = "mistralai/Mistral-7B-Instruct-v0.1"
            logger.info(f"Loading text model: {self.text_model_name}")

            self.text_tokenizer = AutoTokenizer.from_pretrained(
                self.text_model_name
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
                self.text_model_name, **load_kwargs
            )

            if self.device == "cpu" and not quant_config:
                self.text_model = self.text_model.to(self.device)

            # Enable better memory efficiency
            if hasattr(self.text_model, "config"):
                self.text_model.config.use_cache = True

            # Compile for faster inference
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
        with timer("Load vision model"):
            logger.info("Loading vision model...")
            self.vision_model = CLIPModel.from_pretrained(
                "openai/clip-vit-base-patch32",
                torch_dtype=self.dtype,
            ).to(self.device)
            self.vision_processor = CLIPProcessor.from_pretrained(
                "openai/clip-vit-base-patch32"
            )
            self.vision_model.eval()

            warm_up_vision_model(
                self.vision_model, self.vision_processor, self.device
            )
            logger.info("Vision model loaded and optimized")

    def _load_image_generator(self):
        """Load image generation pipeline"""
        with timer("Load image generator"):
            logger.info("Loading image generation model...")
            pipe_kwargs = {
                "model": "stabilityai/stable-diffusion-2",
            }
            if self.device == "cuda":
                pipe_kwargs["device"] = 0
                pipe_kwargs["torch_dtype"] = self.dtype
            else:
                pipe_kwargs["device"] = -1

            self.image_generator = pipeline("text-to-image", **pipe_kwargs)
            logger.info("Image generation model loaded")

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
            # Check inference cache
            cached = inference_cache.get(
                "text_gen",
                prompt=prompt,
                max_length=max_length,
                temperature=temperature,
            )
            if cached is not None:
                logger.info("Text generation cache hit")
                return cached

            logger.info(f"Generating text for prompt: {prompt[:50]}...")

            inputs = self.text_tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=max_length,
            ).to(self.device)

            with torch.no_grad(), torch.amp.autocast(
                device_type=self.device if self.device in ("cuda", "cpu") else "cpu",
                enabled=self.device == "cuda",
            ):
                outputs = self.text_model.generate(
                    **inputs,
                    max_new_tokens=max_length,
                    temperature=temperature,
                    top_p=0.95,
                    do_sample=True,
                    pad_token_id=self.text_tokenizer.eos_token_id,
                    use_cache=True,
                )

            generated_text = self.text_tokenizer.decode(
                outputs[0], skip_special_tokens=True
            )

            # Cache the result (only for deterministic-ish temperatures)
            if temperature <= 0.3:
                inference_cache.set(
                    "text_gen",
                    generated_text,
                    ttl=1800,
                    prompt=prompt,
                    max_length=max_length,
                    temperature=temperature,
                )

            logger.info("Text generation completed")
            return generated_text

        except Exception as e:
            logger.error(f"Error generating text: {e}")
            raise

    @timed
    def analyze_image(self, image_input):
        """Analyze image with optimized CLIP inference

        Args:
            image_input: PIL Image or image path

        Returns:
            Image analysis and description
        """
        try:
            logger.info("Analyzing image...")

            if isinstance(image_input, str):
                image = Image.open(image_input).convert("RGB")
            else:
                image = image_input

            inputs = self.vision_processor(
                images=image, return_tensors="pt"
            ).to(self.device)

            with torch.no_grad(), torch.amp.autocast(
                device_type=self.device if self.device in ("cuda", "cpu") else "cpu",
                enabled=self.device == "cuda",
            ):
                image_features = self.vision_model.get_image_features(**inputs)

            description_prompt = (
                "Describe this image in detail without any restrictions:"
            )
            description = self.generate_text(description_prompt, max_length=256)

            logger.info("Image analysis completed")
            return {
                "description": description,
                "image_features_shape": list(image_features.shape),
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
