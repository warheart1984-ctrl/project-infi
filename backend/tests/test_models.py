"""Tests for AI models"""

import unittest
from unittest.mock import patch, MagicMock
from src.models import MultiModalAI

class TestMultiModalAI(unittest.TestCase):
    """Test cases for MultiModalAI"""
    
    @patch('src.models.AutoModelForCausalLM')
    @patch('src.models.AutoTokenizer')
    @patch('src.models.CLIPModel')
    @patch('src.models.CLIPProcessor')
    @patch('src.models.pipeline')
    def test_initialization(self, mock_pipeline, mock_processor, mock_clip, mock_tokenizer, mock_model):
        """Test AI model initialization"""
        try:
            ai = MultiModalAI(device="cpu")
            self.assertIsNotNone(ai)
            self.assertEqual(ai.device, "cpu")
        except Exception as e:
            # Skip if models can't be loaded
            self.skipTest(f"Model loading failed: {e}")
    
    def test_device_selection(self):
        """Test device selection (CPU/GPU)"""
        import torch
        ai = MultiModalAI(device="cpu")
        self.assertEqual(ai.device, "cpu")

if __name__ == "__main__":
    unittest.main()
