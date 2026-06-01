"""Configuration management"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration"""
    DEBUG = os.getenv("DEBUG", "False") == "True"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")

    # Performance settings
    MODEL_PRECISION = os.getenv("MODEL_PRECISION", "auto")  # auto, fp32, fp16, bf16
    QUANTIZATION = os.getenv("QUANTIZATION", "none")  # none, int8, int4
    TORCH_COMPILE_MODE = os.getenv("TORCH_COMPILE_MODE", "reduce-overhead")
    SKIP_WARMUP = os.getenv("SKIP_WARMUP", "false").lower() == "true"
    BATCH_MAX_WORKERS = int(os.getenv("BATCH_MAX_WORKERS", "4"))
    BATCH_TIMEOUT = int(os.getenv("BATCH_TIMEOUT", "120"))


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False


def get_config():
    """Get configuration based on environment"""
    env = os.getenv("ENVIRONMENT", "development")
    if env == "production":
        return ProductionConfig()
    return DevelopmentConfig()
