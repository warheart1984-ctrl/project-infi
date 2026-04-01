"""Audio processing utilities"""

import librosa
import numpy as np
from src.logger import get_logger

logger = get_logger(__name__)

class AudioProcessor:
    """Audio processing and analysis"""
    
    @staticmethod
    def extract_features(audio_path):
        """Extract audio features"""
        try:
            logger.info(f"Extracting features from {audio_path}")
            y, sr = librosa.load(audio_path)
            
            features = {
                "duration": librosa.get_duration(y=y, sr=sr),
                "sample_rate": sr,
                "mfcc_mean": librosa.feature.mfcc(y=y, sr=sr).mean(axis=1).tolist(),
                "spectral_centroid": float(librosa.feature.spectral_centroid(y=y, sr=sr).mean()),
                "zero_crossing_rate": float(librosa.feature.zero_crossing_rate(y).mean()),
            }
            return features
        except Exception as e:
            logger.error(f"Error: {e}")
            raise
    
    @staticmethod
    def detect_silence(audio_path, threshold=0.01):
        """Detect silent segments"""
        try:
            logger.info(f"Detecting silence in {audio_path}")
            y, sr = librosa.load(audio_path)
            S = librosa.feature.melspectrogram(y=y, sr=sr)
            S_db = librosa.power_to_db(S, ref=np.max)
            silent_frames = np.where(np.mean(S_db, axis=0) < -40)[0]
            silent_times = librosa.frames_to_time(silent_frames, sr=sr)
            return silent_times.tolist()
        except Exception as e:
            logger.error(f"Error: {e}")
            raise
