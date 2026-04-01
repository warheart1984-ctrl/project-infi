"""Speech processing: transcription (STT) and text-to-speech (TTS)"""

import os
import io
import tempfile
import numpy as np
from pathlib import Path
from src.logger import get_logger

logger = get_logger(__name__)


class SpeechToText:
    """Audio transcription using OpenAI Whisper"""

    def __init__(self, model_size: str = "base"):
        """
        Args:
            model_size: Whisper model size - tiny, base, small, medium, large
        """
        self.model_size = model_size
        self._model = None

    def _load_model(self):
        """Lazy-load the Whisper model"""
        if self._model is None:
            try:
                import whisper
                logger.info(f"Loading Whisper model: {self.model_size}")
                self._model = whisper.load_model(self.model_size)
                logger.info("Whisper model loaded")
            except ImportError:
                raise ImportError(
                    "openai-whisper is required. Install with: pip install openai-whisper"
                )
        return self._model

    def transcribe(self, audio_path: str, language: str = None) -> dict:
        """Transcribe an audio file to text

        Args:
            audio_path: Path to audio file (wav, mp3, m4a, flac, etc.)
            language: Optional language code (e.g. 'en', 'es', 'fr')

        Returns:
            Dict with 'text', 'segments', and 'language'
        """
        model = self._load_model()
        logger.info(f"Transcribing: {audio_path}")

        options = {}
        if language:
            options["language"] = language

        result = model.transcribe(str(audio_path), **options)

        segments = [
            {
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"].strip(),
            }
            for seg in result.get("segments", [])
        ]

        logger.info(f"Transcription complete: {len(segments)} segments")
        return {
            "text": result["text"].strip(),
            "language": result.get("language", language),
            "segments": segments,
            "duration": segments[-1]["end"] if segments else 0,
        }

    def transcribe_bytes(self, audio_bytes: bytes, suffix: str = ".wav", language: str = None) -> dict:
        """Transcribe audio from raw bytes"""
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            return self.transcribe(tmp_path, language=language)
        finally:
            os.unlink(tmp_path)


class TextToSpeech:
    """Text-to-speech synthesis"""

    def __init__(self):
        self._synthesizer = None

    def _load_model(self):
        """Lazy-load the TTS model"""
        if self._synthesizer is None:
            try:
                from transformers import pipeline as hf_pipeline
                logger.info("Loading TTS model: microsoft/speecht5_tts")
                self._synthesizer = hf_pipeline(
                    "text-to-speech",
                    model="microsoft/speecht5_tts",
                )
                logger.info("TTS model loaded")
            except Exception as e:
                logger.error(f"Failed to load TTS model: {e}")
                raise
        return self._synthesizer

    def synthesize(self, text: str) -> dict:
        """Convert text to speech audio

        Args:
            text: Text to synthesize

        Returns:
            Dict with 'audio' (numpy array) and 'sampling_rate'
        """
        synthesizer = self._load_model()
        logger.info(f"Synthesizing speech for: {text[:60]}...")

        result = synthesizer(text)

        logger.info("Speech synthesis complete")
        return {
            "audio": result["audio"],
            "sampling_rate": result["sampling_rate"],
        }

    def synthesize_to_wav_bytes(self, text: str) -> bytes:
        """Convert text to speech and return WAV bytes"""
        import struct
        import wave

        result = self.synthesize(text)
        audio = result["audio"]
        sr = result["sampling_rate"]

        # Ensure audio is float32 numpy array, convert to int16 PCM
        if isinstance(audio, np.ndarray):
            audio_int16 = (audio * 32767).astype(np.int16)
        else:
            audio_int16 = np.array(audio, dtype=np.int16)

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(audio_int16.tobytes())

        return buf.getvalue()


# Module-level singletons (lazy-loaded)
speech_to_text = SpeechToText(model_size=os.getenv("WHISPER_MODEL_SIZE", "base"))
text_to_speech = TextToSpeech()
