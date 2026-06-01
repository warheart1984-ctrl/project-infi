"""Sentiment analysis and text classification

Optimized with inference caching and batch processing.
"""

from src.logger import get_logger
from src.performance import inference_cache, timed

logger = get_logger(__name__)


class TextClassifier:
    """Sentiment analysis and multi-label text classification"""

    def __init__(self):
        self._sentiment_pipeline = None
        self._zero_shot_pipeline = None

    def _get_sentiment_pipeline(self):
        """Lazy-load sentiment analysis pipeline"""
        if self._sentiment_pipeline is None:
            from transformers import pipeline as hf_pipeline
            import torch

            logger.info("Loading sentiment analysis model...")
            device = 0 if torch.cuda.is_available() else -1
            self._sentiment_pipeline = hf_pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                device=device,
            )
            logger.info("Sentiment model loaded")
        return self._sentiment_pipeline

    def _get_zero_shot_pipeline(self):
        """Lazy-load zero-shot classification pipeline"""
        if self._zero_shot_pipeline is None:
            from transformers import pipeline as hf_pipeline
            import torch

            logger.info("Loading zero-shot classification model...")
            device = 0 if torch.cuda.is_available() else -1
            self._zero_shot_pipeline = hf_pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=device,
            )
            logger.info("Zero-shot classification model loaded")
        return self._zero_shot_pipeline

    @timed
    def analyze_sentiment(self, text: str) -> dict:
        """Analyze sentiment with caching"""
        cached = inference_cache.get("sentiment", text=text[:512])
        if cached is not None:
            logger.info("Sentiment cache hit")
            return cached

        logger.info(f"Analyzing sentiment: {text[:60]}...")
        pipe = self._get_sentiment_pipeline()
        result = pipe(text[:512])[0]
        output = {
            "label": result["label"],
            "score": round(result["score"], 4),
        }

        inference_cache.set("sentiment", output, ttl=3600, text=text[:512])
        return output

    @timed
    def analyze_sentiment_batch(self, texts: list) -> list:
        """Analyze sentiment for multiple texts with batched inference"""
        pipe = self._get_sentiment_pipeline()
        truncated = [t[:512] for t in texts]

        # Check cache for each
        results = []
        uncached_indices = []
        uncached_texts = []

        for i, t in enumerate(truncated):
            cached = inference_cache.get("sentiment", text=t)
            if cached is not None:
                results.append((i, cached))
            else:
                uncached_indices.append(i)
                uncached_texts.append(t)

        # Batch-process uncached texts
        if uncached_texts:
            batch_results = pipe(uncached_texts, batch_size=min(32, len(uncached_texts)))
            for idx, r in zip(uncached_indices, batch_results):
                output = {"label": r["label"], "score": round(r["score"], 4)}
                inference_cache.set("sentiment", output, ttl=3600, text=truncated[idx])
                results.append((idx, output))

        results.sort(key=lambda x: x[0])
        return [r[1] for r in results]

    @timed
    def classify(
        self,
        text: str,
        candidate_labels: list,
        multi_label: bool = False,
    ) -> dict:
        """Classify text with caching"""
        cache_key_labels = ",".join(sorted(candidate_labels))
        cached = inference_cache.get(
            "classify",
            text=text[:1024],
            labels=cache_key_labels,
            multi_label=multi_label,
        )
        if cached is not None:
            logger.info("Classification cache hit")
            return cached

        logger.info(f"Classifying text into {len(candidate_labels)} categories")
        pipe = self._get_zero_shot_pipeline()
        result = pipe(text[:1024], candidate_labels, multi_label=multi_label)
        output = {
            "labels": result["labels"],
            "scores": [round(s, 4) for s in result["scores"]],
            "top_label": result["labels"][0],
            "top_score": round(result["scores"][0], 4),
        }

        inference_cache.set(
            "classify",
            output,
            ttl=3600,
            text=text[:1024],
            labels=cache_key_labels,
            multi_label=multi_label,
        )
        return output

    @timed
    def classify_batch(
        self,
        texts: list,
        candidate_labels: list,
        multi_label: bool = False,
    ) -> list:
        """Classify multiple texts"""
        pipe = self._get_zero_shot_pipeline()
        results = pipe(
            [t[:1024] for t in texts],
            candidate_labels,
            multi_label=multi_label,
            batch_size=min(16, len(texts)),
        )
        if not isinstance(results, list):
            results = [results]
        return [
            {
                "labels": r["labels"],
                "scores": [round(s, 4) for s in r["scores"]],
                "top_label": r["labels"][0],
                "top_score": round(r["scores"][0], 4),
            }
            for r in results
        ]


text_classifier = TextClassifier()
