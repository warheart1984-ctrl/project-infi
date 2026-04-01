"""Video processing: frame extraction, analysis, and summarization"""

import os
import tempfile
from pathlib import Path
from src.logger import get_logger

logger = get_logger(__name__)


class VideoProcessor:
    """Extract frames, analyze content, and generate summaries from video"""

    def __init__(self):
        self._cv2 = None

    def _get_cv2(self):
        """Lazy-load OpenCV"""
        if self._cv2 is None:
            try:
                import cv2
                self._cv2 = cv2
            except ImportError:
                raise ImportError(
                    "opencv-python is required. Install with: pip install opencv-python"
                )
        return self._cv2

    def get_video_info(self, video_path: str) -> dict:
        """Get basic video metadata"""
        cv2 = self._get_cv2()
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = frame_count / fps if fps > 0 else 0

            return {
                "fps": round(fps, 2),
                "frame_count": frame_count,
                "width": width,
                "height": height,
                "duration_seconds": round(duration, 2),
                "resolution": f"{width}x{height}",
            }
        finally:
            cap.release()

    def extract_frames(
        self,
        video_path: str,
        num_frames: int = 10,
        output_dir: str = None,
    ) -> list:
        """Extract evenly-spaced frames from a video

        Args:
            video_path: Path to video file
            num_frames: Number of frames to extract
            output_dir: Directory to save frames (uses temp dir if None)

        Returns:
            List of dicts with 'path', 'timestamp', and 'frame_index'
        """
        cv2 = self._get_cv2()
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="aais_frames_")
        os.makedirs(output_dir, exist_ok=True)

        try:
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            interval = max(1, total_frames // num_frames)

            extracted = []
            for i in range(num_frames):
                frame_idx = i * interval
                if frame_idx >= total_frames:
                    break

                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if not ret:
                    continue

                frame_path = os.path.join(output_dir, f"frame_{i:04d}.jpg")
                cv2.imwrite(frame_path, frame)

                extracted.append({
                    "path": frame_path,
                    "frame_index": frame_idx,
                    "timestamp": round(frame_idx / fps, 2) if fps > 0 else 0,
                })

            logger.info(f"Extracted {len(extracted)} frames from {video_path}")
            return extracted
        finally:
            cap.release()

    def extract_key_frames(self, video_path: str, threshold: float = 30.0) -> list:
        """Extract key frames based on scene change detection

        Uses absolute difference between consecutive frames to detect scene changes.

        Args:
            video_path: Path to video file
            threshold: Scene change sensitivity (lower = more frames)

        Returns:
            List of dicts with 'path', 'timestamp', 'frame_index', 'change_score'
        """
        cv2 = self._get_cv2()
        import numpy as np

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        output_dir = tempfile.mkdtemp(prefix="aais_keyframes_")

        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            key_frames = []
            prev_frame = None
            frame_idx = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray_small = cv2.resize(gray, (160, 120))

                if prev_frame is not None:
                    diff = np.mean(np.abs(
                        gray_small.astype(float) - prev_frame.astype(float)
                    ))
                    if diff > threshold:
                        frame_path = os.path.join(
                            output_dir, f"keyframe_{len(key_frames):04d}.jpg"
                        )
                        cv2.imwrite(frame_path, frame)
                        key_frames.append({
                            "path": frame_path,
                            "frame_index": frame_idx,
                            "timestamp": round(frame_idx / fps, 2) if fps > 0 else 0,
                            "change_score": round(diff, 2),
                        })
                else:
                    # Always capture first frame
                    frame_path = os.path.join(output_dir, "keyframe_0000.jpg")
                    cv2.imwrite(frame_path, frame)
                    key_frames.append({
                        "path": frame_path,
                        "frame_index": 0,
                        "timestamp": 0,
                        "change_score": 0,
                    })

                prev_frame = gray_small
                frame_idx += 1

            logger.info(f"Extracted {len(key_frames)} key frames")
            return key_frames
        finally:
            cap.release()

    def analyze_frames(self, frames: list, ai_model) -> list:
        """Analyze extracted frames using the AI vision model

        Args:
            frames: List of frame dicts from extract_frames/extract_key_frames
            ai_model: MultiModalAI instance for image analysis

        Returns:
            List of frame dicts enriched with 'analysis'
        """
        from PIL import Image

        results = []
        for frame_info in frames:
            try:
                image = Image.open(frame_info["path"]).convert("RGB")
                analysis = ai_model.analyze_image(image)
                frame_info["analysis"] = analysis
            except Exception as e:
                logger.error(f"Error analyzing frame {frame_info['path']}: {e}")
                frame_info["analysis"] = {"error": str(e)}
            results.append(frame_info)

        return results

    def generate_summary(self, analyzed_frames: list, ai_model) -> str:
        """Generate a text summary of the video from analyzed frames

        Args:
            analyzed_frames: Frames with 'analysis' from analyze_frames()
            ai_model: MultiModalAI instance for text generation

        Returns:
            Summary string
        """
        descriptions = []
        for f in analyzed_frames:
            analysis = f.get("analysis", {})
            desc = analysis.get("description", "")
            ts = f.get("timestamp", 0)
            if desc:
                descriptions.append(f"[{ts}s] {desc}")

        if not descriptions:
            return "No visual content could be analyzed from the video."

        prompt = (
            "Based on the following frame-by-frame descriptions of a video, "
            "write a concise summary of what happens in the video:\n\n"
            + "\n".join(descriptions)
            + "\n\nVideo summary:"
        )

        summary = ai_model.generate_text(prompt, max_length=300, temperature=0.5)
        return summary


video_processor = VideoProcessor()
