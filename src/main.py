"""Main application entry point"""

import argparse
import os

from src.config import get_config
from src.logger import get_logger

logger = get_logger(__name__)
config = get_config()


RUNTIME_PRESETS = {
    "default": {
        "AAIS_MODEL_MODE": "real",
        "AAIS_BOOTSTRAP_REAL_AT_STARTUP": "1",
        "AAIS_MESH_ENABLED": "0",
    },
    "production": {
        "AAIS_MODEL_MODE": "real",
        "AAIS_BOOTSTRAP_REAL_AT_STARTUP": "1",
        "ENVIRONMENT": "production",
        "AAIS_ALLOW_STARTUP_FALLBACK": "0",
        "AAIS_HEALTH_SKIP_CONTRACTOR_PROBES": "1",
        # Standalone desktop/server: no mesh gossip unless deploy/mesh/peers.json is configured.
        "AAIS_MESH_ENABLED": "0",
        # Local torch path when no remote API keys: lite profile boots on CPU in minutes,
        # not Mistral-7B. Override AAIS_TEXT_MODEL_NAME in .env for a heavier local model.
        "AAIS_MODEL_PROFILE": "lite",
        "AAIS_TEXT_MODEL_NAME": "Qwen/Qwen2.5-0.5B-Instruct",
        "AAIS_DISABLE_IMAGE_GENERATION": "true",
        "AAIS_ENABLE_DOCUMENT_VISION": "0",
        "AAIS_ENABLE_UI_VISION": "0",
        "AAIS_DEFAULT_MAX_LENGTH": "96",
        "AAIS_MAX_TEXT_TOKENS": "160",
        "AAIS_RESPONSE_TOKEN_SCALE": "0.25",
        "AAIS_DEFAULT_TEMPERATURE": "0.6",
        "AAIS_ENABLE_TEXT_ADAPTERS": "0",
        "QUANTIZATION": "int4",
        "SKIP_WARMUP": "true",
        "DISABLE_TORCH_COMPILE": "true",
        "MODEL_PRECISION": "fp16",
    },
    "laptop": {
        "AAIS_MODEL_MODE": "real",
        "AAIS_MESH_ENABLED": "0",
        "AAIS_MODEL_PROFILE": "lite",
        "AAIS_TEXT_MODEL_NAME": "Qwen/Qwen2.5-0.5B-Instruct",
        "AAIS_DISABLE_IMAGE_GENERATION": "true",
        "AAIS_ENABLE_DOCUMENT_VISION": "0",
        "AAIS_ENABLE_UI_VISION": "0",
        "AAIS_HF_LOCAL_ONLY": "1",
        "AAIS_DEFAULT_MAX_LENGTH": "96",
        "AAIS_MAX_TEXT_TOKENS": "160",
        "AAIS_RESPONSE_TOKEN_SCALE": "0.25",
        "AAIS_DEFAULT_TEMPERATURE": "0.6",
        "AAIS_ENABLE_TEXT_ADAPTERS": "0",
        "QUANTIZATION": "int4",
        "SKIP_WARMUP": "true",
        "DISABLE_TORCH_COMPILE": "true",
        "MODEL_PRECISION": "fp16",
    },
    "mock": {
        "AAIS_MODEL_MODE": "mock",
        "AAIS_DISABLE_IMAGE_GENERATION": "true",
        "SKIP_WARMUP": "true",
        "DISABLE_TORCH_COMPILE": "true",
    },
}


def parse_args(argv=None):
    """Parse CLI arguments for the application entrypoint."""
    parser = argparse.ArgumentParser(description="AAIS - Uncensored Multi-Modal AI")
    parser.add_argument(
        "--mode",
        choices=["api", "cli"],
        default="api",
        help="Run mode: api (Flask server) or cli (command-line)"
    )
    parser.add_argument("--host", default="0.0.0.0", help="API host")
    parser.add_argument("--port", type=int, default=5000, help="API port")
    parser.add_argument(
        "--preset",
        choices=sorted(RUNTIME_PRESETS.keys()),
        default="default",
        help="Runtime preset: default, production (strict real AI), laptop, or mock",
    )

    return parser.parse_args(argv)


def _prepare_mock_local_loop() -> None:
    """Clear governance containment that blocks chat in local mock loops."""
    try:
        from src.otem_ceiling import otem_ceiling

        otem_ceiling.clear_local_containment()
    except Exception:
        logger.warning("Could not clear OTEM ceiling containment for mock preset", exc_info=True)
    try:
        from src.cognitive_bridge import cognitive_bridge_service

        cognitive_bridge_service.detachment_guard.reset()
    except Exception:
        logger.warning("Could not reset detachment guard for mock preset", exc_info=True)


def apply_runtime_preset(preset):
    """Apply a runtime preset without overwriting explicit env vars."""
    preset_config = RUNTIME_PRESETS[preset]
    applied = {}

    for key, value in preset_config.items():
        if os.getenv(key) is None:
            os.environ[key] = value
            applied[key] = value

    if str(preset or "").strip().lower() == "mock":
        _prepare_mock_local_loop()

    return applied


def run_api(*args, **kwargs):
    """Import and run the Flask API lazily."""
    from src.api import run_api as _run_api

    return _run_api(*args, **kwargs)


def main(argv=None):
    """Main application function."""
    args = parse_args(argv)
    applied_preset = apply_runtime_preset(args.preset)

    logger.info("Starting AAIS application")
    logger.info(f"Debug mode: {config.DEBUG}")
    if applied_preset:
        logger.info(
            "Applied runtime preset '%s': %s",
            args.preset,
            ", ".join(f"{key}={value}" for key, value in applied_preset.items()),
        )

    if args.mode == "api":
        logger.info(f"Starting API server on {args.host}:{args.port}")
        run_api(host=args.host, port=args.port, debug=config.DEBUG)
    else:
        logger.info("CLI mode - use 'python -m src.cli --help' for commands")

    return args.mode

if __name__ == "__main__":
    main()
