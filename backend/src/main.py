"""Main application entry point"""

from src.logger import get_logger
from src.config import get_config
from src.api import run_api
import argparse

logger = get_logger(__name__)
config = get_config()

def main():
    """Main application function"""
    parser = argparse.ArgumentParser(description="AAIS - Uncensored Multi-Modal AI")
    parser.add_argument(
        "--mode",
        choices=["api", "cli"],
        default="api",
        help="Run mode: api (Flask server) or cli (command-line)"
    )
    parser.add_argument("--host", default="0.0.0.0", help="API host")
    parser.add_argument("--port", type=int, default=5000, help="API port")
    
    args = parser.parse_args()
    
    logger.info("Starting AAIS application")
    logger.info(f"Debug mode: {config.DEBUG}")
    
    if args.mode == "api":
        logger.info(f"Starting API server on {args.host}:{args.port}")
        run_api(host=args.host, port=args.port, debug=config.DEBUG)
    else:
        logger.info("CLI mode - use 'python -m src.cli --help' for commands")

if __name__ == "__main__":
    main()
