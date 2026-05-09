from pydantic import BaseModel
from typing import List
import time
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class GatekeeperResult(BaseModel):
    is_authentic: bool
    duplicate_score: float
    is_duplicate: bool
    ai_probability: float
    is_ai_generated: bool
    anomaly_score: float
    is_anomalous: bool

class GatekeeperService:
    """
    Minimal implementation of Gatekeeper Services mentioned in project report.
    Includes Duplicate Detector, AI Text Detector, and Anomaly Detector.
    """
    def __init__(self, model: SentenceTransformer):
        self.model = model
        self.submission_history = {} # Mock in-memory database for rate limiting

    def check_duplicate(self, text: str, corpus: List[str], threshold: float = 0.92) -> tuple[float, bool]:
        """Duplicate Detector: Uses SBERT cosine similarity"""
        if not corpus:
            return 0.0, False
        text_emb = self.model.encode([text])
        corpus_emb = self.model.encode(corpus)
        sims = cosine_similarity(text_emb, corpus_emb)[0]
        max_sim = float(np.max(sims)) if len(sims) > 0 else 0.0
        return max_sim, max_sim >= threshold

    def check_ai_text(self, text: str, threshold: float = 0.70) -> tuple[float, bool]:
        """AI Text Detector: Minimal mock heuristics in place of GPT-2 perplexity"""
        word_count = len(text.split())
        if word_count < 10:
            return 0.0, False
        
        # Simple heuristic for minimal implementation
        # A real implementation would use GPT-2 perplexity and burstiness here
        probability = 0.8 if "Furthermore" in text and "Moreover" in text else 0.1
        return probability, probability >= threshold

    def check_anomaly(self, faculty_id: str) -> tuple[float, bool]:
        """Anomaly Detector: Minimal rate limit and burst check"""
        now = time.time()
        if faculty_id not in self.submission_history:
            self.submission_history[faculty_id] = []
        
        history = self.submission_history[faculty_id]
        # Keep only last 24h
        history = [t for t in history if now - t < 86400]
        
        score = 0.0
        if len(history) >= 10:
            score = 0.9  # Rate limit exceeded
        elif len(history) > 0 and now - history[-1] < 60:
            score = 0.8  # Burst detection
            
        history.append(now)
        self.submission_history[faculty_id] = history
        
        return score, score >= 0.5

    def evaluate(self, text: str, corpus: List[str], faculty_id: str = "unknown") -> GatekeeperResult:
        """Runs the full gatekeeper pipeline"""
        dup_score, is_dup = self.check_duplicate(text, corpus)
        ai_score, is_ai = self.check_ai_text(text)
        anom_score, is_anom = self.check_anomaly(faculty_id)
        
        is_authentic = not (is_dup or is_ai or is_anom)
        
        return GatekeeperResult(
            is_authentic=is_authentic,
            duplicate_score=dup_score,
            is_duplicate=is_dup,
            ai_probability=ai_score,
            is_ai_generated=is_ai,
            anomaly_score=anom_score,
            is_anomalous=is_anom
        )
