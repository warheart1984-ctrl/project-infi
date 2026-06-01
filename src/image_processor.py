"""Advanced image processing utilities"""

from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
from src.logger import get_logger

logger = get_logger(__name__)

class ImageProcessor:
    """Advanced image processing"""
    
    @staticmethod
    def upscale(image, scale_factor=2):
        """Upscale image"""
        try:
            logger.info(f"Upscaling image by {scale_factor}x")
            width, height = image.size
            new_size = (width * scale_factor, height * scale_factor)
            upscaled = image.resize(new_size, Image.Resampling.LANCZOS)
            return upscaled
        except Exception as e:
            logger.error(f"Error upscaling: {e}")
            raise
    
    @staticmethod
    def style_transfer(image, style_strength=0.5):
        """Apply style transfer"""
        try:
            logger.info("Applying style transfer")
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1 + style_strength)
            image = image.filter(ImageFilter.GaussianBlur(radius=style_strength))
            return image
        except Exception as e:
            logger.error(f"Error: {e}")
            raise
    
    @staticmethod
    def adjust_brightness(image, factor=1.0):
        """Adjust brightness"""
        try:
            enhancer = ImageEnhance.Brightness(image)
            return enhancer.enhance(factor)
        except Exception as e:
            logger.error(f"Error: {e}")
            raise
    
    @staticmethod
    def adjust_contrast(image, factor=1.0):
        """Adjust contrast"""
        try:
            enhancer = ImageEnhance.Contrast(image)
            return enhancer.enhance(factor)
        except Exception as e:
            logger.error(f"Error: {e}")
            raise
    
    @staticmethod
    def apply_filter(image, filter_type="blur"):
        """Apply filters"""
        try:
            if filter_type == "blur":
                return image.filter(ImageFilter.GaussianBlur(radius=2))
            elif filter_type == "sharpen":
                return image.filter(ImageFilter.SHARPEN)
            elif filter_type == "edge":
                return image.filter(ImageFilter.FIND_EDGES)
            elif filter_type == "smooth":
                return image.filter(ImageFilter.SMOOTH)
            return image
        except Exception as e:
            logger.error(f"Error: {e}")
            raise
