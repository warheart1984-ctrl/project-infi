# AAIS - Uncensored Multi-Modal AI System

An uncensored AI system for text generation and image analysis/generation without content restrictions.

## Features

- **Text Generation**: Generate uncensored text on any topic
- **Image Analysis**: Analyze and describe images in detail
- **Image Generation**: Create images from text descriptions
- **Multi-Modal**: Combine text and image processing
- **GPU Support**: Optimized for CUDA with CPU fallback
- **REST API**: Flask-based API for easy integration
- **CLI**: Command-line interface for direct usage

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### API Server

```bash
python -m src.main --mode api --host 0.0.0.0 --port 5000
```

**Endpoints:**

- `GET /health` - Health check
- `POST /api/text/generate` - Generate text
- `POST /api/image/analyze` - Analyze image
- `POST /api/image/generate` - Generate image
- `POST /api/multimodal/query` - Multi-modal query

### Command-Line Interface

```bash
# Generate text
python -m src.cli text --prompt "Your prompt here"

# Analyze image
python -m src.cli image-analyze --image path/to/image.jpg

# Generate image
python -m src.cli image-generate --prompt "Image description"

# Multi-modal query
python -m src.cli multimodal --prompt "Your question" --image path/to/image.jpg
```

## API Examples

### Generate Text

```bash
curl -X POST http://localhost:5000/api/text/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Write a story about...", "max_length": 512, "temperature": 0.7}'
```

### Analyze Image

```bash
curl -X POST http://localhost:5000/api/image/analyze \
  -F "image=@path/to/image.jpg"
```

### Generate Image

```bash
curl -X POST http://localhost:5000/api/image/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A beautiful sunset", "num_inference_steps": 50}'
```

## Configuration

Create a `.env` file based on `.env.example`:

```
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=INFO
```

## Models Used

- **Text Generation**: Mistral-7B (uncensored)
- **Vision**: OpenAI CLIP
- **Image Generation**: Stable Diffusion 2

## Hardware Requirements

- **GPU**: NVIDIA GPU with CUDA support (recommended)
- **CPU**: Fallback support (slower)
- **RAM**: 16GB+ recommended
- **Storage**: 50GB+ for models

## Notes

This system is designed to operate without content filters. Use responsibly.
