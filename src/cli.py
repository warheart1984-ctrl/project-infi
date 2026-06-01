"""Command-line interface for AAIS"""

import argparse
import sys
from pathlib import Path
from src.models import MultiModalAI
from src.logger import get_logger
from PIL import Image
import json

logger = get_logger(__name__)


class AAISCLI:
    """Command-line interface for multi-modal AI"""

    def __init__(self):
        """Initialize CLI and AI model"""
        self.ai = MultiModalAI()

    def generate_text(self, args):
        """Handle text generation command"""
        try:
            result = self.ai.generate_text(
                args.prompt,
                max_length=args.max_length,
                temperature=args.temperature,
            )
            print("\n=== Generated Text ===")
            print(result)
            print()
        except Exception as e:
            logger.error(f"Error: {e}")
            sys.exit(1)

    def analyze_image(self, args):
        """Handle image analysis command"""
        try:
            if not Path(args.image).exists():
                print(f"Error: Image file not found: {args.image}")
                sys.exit(1)

            result = self.ai.analyze_image(args.image)
            print("\n=== Image Analysis ===")
            print(json.dumps(result, indent=2))
            print()
        except Exception as e:
            logger.error(f"Error: {e}")
            sys.exit(1)

    def generate_image(self, args):
        """Handle image generation command"""
        try:
            image = self.ai.generate_image(
                args.prompt, num_inference_steps=args.steps
            )

            output_path = args.output or "generated_image.png"
            image.save(output_path)
            print(f"\nImage saved to: {output_path}")
        except Exception as e:
            logger.error(f"Error: {e}")
            sys.exit(1)

    def multimodal_query(self, args):
        """Handle multi-modal query command"""
        try:
            image = None
            if args.image:
                if not Path(args.image).exists():
                    print(f"Error: Image file not found: {args.image}")
                    sys.exit(1)
                image = Image.open(args.image).convert("RGB")

            result = self.ai.multimodal_query(args.prompt, image)
            print("\n=== Multi-Modal Query Result ===")
            print(json.dumps(result, indent=2, default=str))
            print()
        except Exception as e:
            logger.error(f"Error: {e}")
            sys.exit(1)

    def transcribe_audio(self, args):
        """Handle audio transcription command"""
        try:
            from src.speech import speech_to_text

            if not Path(args.audio).exists():
                print(f"Error: Audio file not found: {args.audio}")
                sys.exit(1)

            result = speech_to_text.transcribe(
                args.audio, language=args.language
            )
            print("\n=== Transcription ===")
            print(result["text"])
            if args.segments:
                print("\n--- Segments ---")
                for seg in result["segments"]:
                    print(f"  [{seg['start']:.1f}s - {seg['end']:.1f}s] {seg['text']}")
            print()
        except Exception as e:
            logger.error(f"Error: {e}")
            sys.exit(1)

    def synthesize_speech(self, args):
        """Handle text-to-speech command"""
        try:
            from src.speech import text_to_speech

            output_path = args.output or "speech_output.wav"
            wav_bytes = text_to_speech.synthesize_to_wav_bytes(args.text)

            with open(output_path, "wb") as f:
                f.write(wav_bytes)
            print(f"\nSpeech saved to: {output_path}")
        except Exception as e:
            logger.error(f"Error: {e}")
            sys.exit(1)

    def analyze_sentiment(self, args):
        """Handle sentiment analysis command"""
        try:
            from src.text_classifier import text_classifier

            result = text_classifier.analyze_sentiment(args.text)
            print("\n=== Sentiment Analysis ===")
            print(f"  Label: {result['label']}")
            print(f"  Score: {result['score']}")
            print()
        except Exception as e:
            logger.error(f"Error: {e}")
            sys.exit(1)

    def classify_text(self, args):
        """Handle text classification command"""
        try:
            from src.text_classifier import text_classifier

            result = text_classifier.classify(
                args.text, args.labels, multi_label=args.multi_label
            )
            print("\n=== Text Classification ===")
            for label, score in zip(result["labels"], result["scores"]):
                bar = "#" * int(score * 40)
                print(f"  {label:20s} {score:.4f} {bar}")
            print()
        except Exception as e:
            logger.error(f"Error: {e}")
            sys.exit(1)

    def chat(self, args):
        """Interactive chat with conversation memory"""
        try:
            from src.conversation_memory import conversation_memory

            session_id = conversation_memory.create_session(
                system_prompt=args.system_prompt
            )
            print(f"\n=== AAIS Chat (session: {session_id[:8]}...) ===")
            print("Type 'quit' or 'exit' to end the conversation.\n")

            while True:
                try:
                    user_input = input("You: ").strip()
                except (EOFError, KeyboardInterrupt):
                    print("\nGoodbye!")
                    break

                if user_input.lower() in ("quit", "exit", "q"):
                    print("Goodbye!")
                    break

                if not user_input:
                    continue

                session = conversation_memory.get_session(session_id)
                session.add_turn("user", user_input)
                prompt = session.build_prompt()

                response = self.ai.generate_text(
                    prompt,
                    max_length=args.max_length,
                    temperature=args.temperature,
                )
                session.add_turn("assistant", response)

                print(f"\nAI: {response}\n")

        except Exception as e:
            logger.error(f"Error: {e}")
            sys.exit(1)

    def process_video(self, args):
        """Handle video processing command"""
        try:
            from src.video_processor import video_processor

            if not Path(args.video).exists():
                print(f"Error: Video file not found: {args.video}")
                sys.exit(1)

            info = video_processor.get_video_info(args.video)
            print("\n=== Video Info ===")
            print(json.dumps(info, indent=2))

            if args.analyze:
                print("\nExtracting and analyzing frames...")
                frames = video_processor.extract_frames(
                    args.video, num_frames=args.num_frames
                )
                analyzed = video_processor.analyze_frames(frames, self.ai)
                summary = video_processor.generate_summary(analyzed, self.ai)
                print("\n=== Video Summary ===")
                print(summary)
            print()
        except Exception as e:
            logger.error(f"Error: {e}")
            sys.exit(1)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="AAIS - Uncensored Multi-Modal AI System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate text
  python -m src.cli text --prompt "Write a story about..."

  # Interactive chat with memory
  python -m src.cli chat

  # Analyze image
  python -m src.cli image-analyze --image path/to/image.jpg

  # Generate image
  python -m src.cli image-generate --prompt "A beautiful sunset"

  # Multi-modal query
  python -m src.cli multimodal --prompt "Describe this" --image path/to/image.jpg

  # Transcribe audio
  python -m src.cli transcribe --audio path/to/audio.wav

  # Text-to-speech
  python -m src.cli speak --text "Hello world" --output hello.wav

  # Sentiment analysis
  python -m src.cli sentiment --text "I love this product!"

  # Text classification
  python -m src.cli classify --text "The stock market crashed" --labels finance politics sports

  # Video analysis
  python -m src.cli video --video path/to/video.mp4 --analyze
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Text generation
    text_parser = subparsers.add_parser("text", help="Generate text")
    text_parser.add_argument("--prompt", required=True, help="Text prompt")
    text_parser.add_argument("--max-length", type=int, default=512)
    text_parser.add_argument("--temperature", type=float, default=0.7)

    # Interactive chat
    chat_parser = subparsers.add_parser("chat", help="Interactive chat with memory")
    chat_parser.add_argument("--system-prompt", default=None, help="System prompt")
    chat_parser.add_argument("--max-length", type=int, default=512)
    chat_parser.add_argument("--temperature", type=float, default=0.7)

    # Image analysis
    img_analyze = subparsers.add_parser("image-analyze", help="Analyze image")
    img_analyze.add_argument("--image", required=True)

    # Image generation
    img_gen = subparsers.add_parser("image-generate", help="Generate image")
    img_gen.add_argument("--prompt", required=True)
    img_gen.add_argument("--steps", type=int, default=50)
    img_gen.add_argument("--output", help="Output path")

    # Multi-modal query
    mm_parser = subparsers.add_parser("multimodal", help="Multi-modal query")
    mm_parser.add_argument("--prompt", required=True)
    mm_parser.add_argument("--image", help="Optional image path")

    # Audio transcription
    transcribe_parser = subparsers.add_parser("transcribe", help="Transcribe audio")
    transcribe_parser.add_argument("--audio", required=True, help="Audio file path")
    transcribe_parser.add_argument("--language", default=None, help="Language code")
    transcribe_parser.add_argument("--segments", action="store_true", help="Show segments")

    # Text-to-speech
    speak_parser = subparsers.add_parser("speak", help="Text-to-speech")
    speak_parser.add_argument("--text", required=True, help="Text to synthesize")
    speak_parser.add_argument("--output", default=None, help="Output WAV path")

    # Sentiment analysis
    sentiment_parser = subparsers.add_parser("sentiment", help="Sentiment analysis")
    sentiment_parser.add_argument("--text", required=True)

    # Text classification
    classify_parser = subparsers.add_parser("classify", help="Text classification")
    classify_parser.add_argument("--text", required=True)
    classify_parser.add_argument("--labels", nargs="+", required=True, help="Category labels")
    classify_parser.add_argument("--multi-label", action="store_true")

    # Video processing
    video_parser = subparsers.add_parser("video", help="Video processing")
    video_parser.add_argument("--video", required=True, help="Video file path")
    video_parser.add_argument("--num-frames", type=int, default=8)
    video_parser.add_argument("--analyze", action="store_true", help="Analyze frames with AI")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    cli = AAISCLI()

    commands = {
        "text": cli.generate_text,
        "chat": cli.chat,
        "image-analyze": cli.analyze_image,
        "image-generate": cli.generate_image,
        "multimodal": cli.multimodal_query,
        "transcribe": cli.transcribe_audio,
        "speak": cli.synthesize_speech,
        "sentiment": cli.analyze_sentiment,
        "classify": cli.classify_text,
        "video": cli.process_video,
    }

    handler = commands.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
