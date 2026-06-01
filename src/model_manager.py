"""Model management for switching between different models"""

from src.logger import get_logger
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

logger = get_logger(__name__)

class ModelManager:
    """Manage multiple models"""
    
    def __init__(self):
        """Initialize model manager"""
        self.loaded_models = {}
        self.available_models = {
            "text": [
                "mistralai/Mistral-7B-Instruct-v0.1",
                "meta-llama/Llama-2-7b-chat-hf",
                "gpt2"
            ],
            "image": [
                "stabilityai/stable-diffusion-2",
                "runwayml/stable-diffusion-v1-5"
            ],
            "vision": [
                "openai/clip-vit-base-patch32",
                "openai/clip-vit-large-patch14"
            ]
        }
    
    def list_available_models(self, task_type: str):
        """List available models"""
        return self.available_models.get(task_type, [])

model_manager = ModelManager()
