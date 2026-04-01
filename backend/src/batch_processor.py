"""Batch processing for multiple inputs

Optimized with configurable concurrency, timeout handling,
and ordered result collection.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from src.logger import get_logger
from src.performance import timed
import os

logger = get_logger(__name__)

DEFAULT_MAX_WORKERS = int(os.getenv("BATCH_MAX_WORKERS", "4"))
DEFAULT_TIMEOUT = int(os.getenv("BATCH_TIMEOUT", "120"))


class BatchProcessor:
    """Process multiple items in parallel with timeout and ordering"""

    def __init__(self, max_workers=None, timeout=None):
        self.max_workers = max_workers or DEFAULT_MAX_WORKERS
        self.timeout = timeout or DEFAULT_TIMEOUT

    @timed
    def process_texts(self, prompts, process_func, **kwargs):
        """Process multiple text prompts in parallel, preserving order"""
        try:
            logger.info(f"Batch processing {len(prompts)} prompts (workers={self.max_workers})")
            results = [None] * len(prompts)

            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_idx = {
                    executor.submit(process_func, prompt, **kwargs): i
                    for i, prompt in enumerate(prompts)
                }

                for future in as_completed(future_to_idx, timeout=self.timeout):
                    idx = future_to_idx[future]
                    try:
                        results[idx] = future.result()
                    except Exception as e:
                        logger.error(f"Batch item {idx} failed: {e}")
                        results[idx] = {"error": str(e)}

            return results

        except TimeoutError:
            logger.error(f"Batch processing timed out after {self.timeout}s")
            return [{"error": "timeout"} if r is None else r for r in results]
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
            raise

    @timed
    def process_items(self, items, process_func, **kwargs):
        """Generic batch processor for any item type, preserving order"""
        try:
            logger.info(f"Batch processing {len(items)} items")
            results = [None] * len(items)

            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_idx = {
                    executor.submit(process_func, item, **kwargs): i
                    for i, item in enumerate(items)
                }

                for future in as_completed(future_to_idx, timeout=self.timeout):
                    idx = future_to_idx[future]
                    try:
                        results[idx] = future.result()
                    except Exception as e:
                        logger.error(f"Batch item {idx} failed: {e}")
                        results[idx] = {"error": str(e)}

            return results

        except TimeoutError:
            logger.error(f"Batch processing timed out after {self.timeout}s")
            return [{"error": "timeout"} if r is None else r for r in results]
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
            raise
