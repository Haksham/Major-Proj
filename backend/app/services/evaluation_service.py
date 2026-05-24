"""
SALF Record Evaluation Manager (REM)
Primary: Claude LLM agent for research quality and novelty assessment.
Fallback: Sentence-BERT cosine similarity (used when API key is absent or call fails).
"""
import json
import hashlib
import logging
import numpy as np
from typing import Dict, Any, List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# ─── SBERT availability (fallback only) ────────────────────────────────────────

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity as sk_cosine
    SBERT_AVAILABLE = True
except ImportError:
    SBERT_AVAILABLE = False

# ─── Anthropic availability ─────────────────────────────────────────────────────

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


# ─── Shared benchmark metadata (weights used by both paths) ────────────────────

BENCHMARK_ATTRIBUTES = [
    ("methodology_rigor",        4.0),
    ("research_design",          3.5),
    ("data_collection",          3.0),
    ("data_analysis",            3.5),
    ("reproducibility",          3.0),
    ("validation",               3.0),
    ("sample_size",              2.5),
    ("control_variables",        2.5),
    ("literature_review",        3.5),
    ("theoretical_framework",    3.5),
    ("research_gap",             4.0),
    ("hypothesis",               3.0),
    ("citations",                2.5),
    ("state_of_art",             3.0),
    ("findings_clarity",         3.5),
    ("statistical_significance", 3.0),
    ("practical_application",    4.0),
    ("societal_impact",          3.5),
    ("innovation",               4.5),
    ("contribution",             4.0),
    ("scalability",              2.5),
    ("future_work",              2.0),
    ("conclusion_strength",      3.0),
    ("clarity",                  3.0),
    ("structure",                2.5),
    ("abstract_quality",         3.0),
    ("ethical_consideration",    2.5),
    ("acknowledgment_limitations", 2.5),
    ("interdisciplinary",        2.0),
    ("technical_depth",          3.0),
    ("domain_relevance",         3.5),
    ("benchmark_comparison",     3.0),
    ("tool_development",         2.5),
    ("dataset_contribution",     2.5),
    ("algorithm_novelty",        3.5),
    ("evaluation_metrics",       2.5),
]

_TOTAL_WEIGHT = sum(w for _, w in BENCHMARK_ATTRIBUTES)

_EVAL_PROMPT_TEMPLATE = """\
You are an expert academic research evaluator for a university faculty ledger system.

Evaluate the following research contribution and return ONLY valid JSON — no prose, no markdown fences.

Title: {title}
Category: {category}
Abstract:
{abstract}

Score each of the 36 benchmark attributes on a 0-100 scale, then derive overall quality and novelty.

Return this exact JSON shape:
{{
  "quality_score": <weighted average of all attribute scores, 0-100>,
  "novelty_percentage": <how original/novel this work is compared to typical research, 0-100>,
  "benchmark_scores": {{
    "methodology_rigor": <0-100>,
    "research_design": <0-100>,
    "data_collection": <0-100>,
    "data_analysis": <0-100>,
    "reproducibility": <0-100>,
    "validation": <0-100>,
    "sample_size": <0-100>,
    "control_variables": <0-100>,
    "literature_review": <0-100>,
    "theoretical_framework": <0-100>,
    "research_gap": <0-100>,
    "hypothesis": <0-100>,
    "citations": <0-100>,
    "state_of_art": <0-100>,
    "findings_clarity": <0-100>,
    "statistical_significance": <0-100>,
    "practical_application": <0-100>,
    "societal_impact": <0-100>,
    "innovation": <0-100>,
    "contribution": <0-100>,
    "scalability": <0-100>,
    "future_work": <0-100>,
    "conclusion_strength": <0-100>,
    "clarity": <0-100>,
    "structure": <0-100>,
    "abstract_quality": <0-100>,
    "ethical_consideration": <0-100>,
    "acknowledgment_limitations": <0-100>,
    "interdisciplinary": <0-100>,
    "technical_depth": <0-100>,
    "domain_relevance": <0-100>,
    "benchmark_comparison": <0-100>,
    "tool_development": <0-100>,
    "dataset_contribution": <0-100>,
    "algorithm_novelty": <0-100>,
    "evaluation_metrics": <0-100>
  }},
  "summary": "<2-3 sentence evaluation>",
  "strengths": ["<strength>", "<strength>"],
  "concerns": ["<concern>"]
}}

Scoring guidelines:
- quality_score: weighted average using attribute weights (innovation=4.5, research_gap=4.0, practical_application=4.0, contribution=4.0 are highest)
- novelty_percentage: base on genuine originality — cite evidence from the abstract
- Be strict: a generic abstract with no concrete method scores 30-50; a clear novel contribution with results scores 70-90
"""


class RecordEvaluationManager:
    """
    LLM-first evaluation. Falls back to SBERT heuristics if Claude is unavailable.
    """

    def __init__(self):
        self._sbert_model = None
        self._attr_embeddings = None

    # ─── Claude path ────────────────────────────────────────────────────────────

    def _call_claude(self, abstract: str, title: str = "", category: str = "") -> Optional[Dict[str, Any]]:
        if not ANTHROPIC_AVAILABLE or not settings.ANTHROPIC_API_KEY:
            return None

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        prompt = _EVAL_PROMPT_TEMPLATE.format(
            title=title or "Untitled",
            category=category or "General",
            abstract=abstract,
        )

        try:
            message = client.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = message.content[0].text.strip()
            # Strip accidental markdown fences
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            result = json.loads(raw)

            # Validate required keys
            if "quality_score" not in result or "novelty_percentage" not in result:
                logger.warning("Claude response missing required keys")
                return None

            result["evaluation_version"] = f"claude-{settings.CLAUDE_MODEL}"
            return result

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.warning(f"Claude response parse error: {e}")
            return None
        except Exception as e:
            logger.warning(f"Claude API error: {e}")
            return None

    # ─── SBERT fallback ─────────────────────────────────────────────────────────

    def _load_sbert(self):
        if self._sbert_model is None:
            if not SBERT_AVAILABLE:
                raise ImportError("sentence-transformers is not installed")
            self._sbert_model = SentenceTransformer(settings.SBERT_MODEL)
            attr_texts = [name.replace("_", " ") for name, _ in BENCHMARK_ATTRIBUTES]
            self._attr_embeddings = self._sbert_model.encode(attr_texts)

    def _sbert_evaluate(self, abstract: str) -> Dict[str, Any]:
        self._load_sbert()
        emb = self._sbert_model.encode([abstract])[0]

        benchmark_scores: Dict[str, Any] = {}
        weighted_sum = 0.0

        for i, (name, weight) in enumerate(BENCHMARK_ATTRIBUTES):
            sim = float(sk_cosine([emb], [self._attr_embeddings[i]])[0][0])
            score = max(0.0, min(100.0, (sim + 1) * 50))
            benchmark_scores[name] = {"score": round(score, 2), "weight": weight}
            weighted_sum += score * weight

        quality_score = weighted_sum / _TOTAL_WEIGHT

        # Novelty heuristic
        innovation_kws = ["novel", "new", "first", "innovative", "breakthrough",
                          "pioneering", "cutting-edge", "unique", "original"]
        kw_count = sum(1 for kw in innovation_kws if kw in abstract.lower())
        novelty = min(100.0, kw_count * 8 + min(40.0, float(np.var(emb)) * 100)
                      + min(20.0, max(0.0, (len(abstract) - 100) / 50)))

        return {
            "quality_score": round(quality_score, 2),
            "novelty_percentage": round(novelty, 2),
            "benchmark_scores": benchmark_scores,
            "evaluation_version": "sbert-fallback",
        }

    # ─── Public API ─────────────────────────────────────────────────────────────

    def evaluate_abstract(
        self,
        abstract: str,
        title: str = "",
        category: str = "",
    ) -> Dict[str, Any]:
        if len(abstract) < settings.MIN_ABSTRACT_LENGTH:
            return {
                "quality_score": 0,
                "novelty_percentage": 0,
                "benchmark_scores": {},
                "error": f"Abstract too short (minimum {settings.MIN_ABSTRACT_LENGTH} characters)",
            }

        # Try Claude first
        result = self._call_claude(abstract, title, category)
        if result:
            logger.info("Evaluation completed via Claude LLM")
            return result

        # Fallback to SBERT
        logger.info("Claude unavailable — falling back to SBERT evaluation")
        try:
            return self._sbert_evaluate(abstract)
        except Exception as e:
            logger.error(f"SBERT fallback also failed: {e}")
            return {
                "quality_score": 0,
                "novelty_percentage": 0,
                "benchmark_scores": {},
                "error": str(e),
            }

    def calculate_final_credits(
        self,
        base_points: float,
        quality_score: float,
        novelty_percentage: float,
    ) -> float:
        """FinalCredits = BasePoints × (1 + quality/100) × (1 + novelty/200)"""
        return round(base_points * (1 + quality_score / 100) * (1 + novelty_percentage / 200), 2)


# ─── Mock for tests / CI without any ML deps ───────────────────────────────────

class MockRecordEvaluationManager(RecordEvaluationManager):
    def evaluate_abstract(self, abstract: str, title: str = "", category: str = "") -> Dict[str, Any]:
        if len(abstract) < settings.MIN_ABSTRACT_LENGTH:
            return {"quality_score": 0, "novelty_percentage": 0, "benchmark_scores": {},
                    "error": f"Abstract too short (minimum {settings.MIN_ABSTRACT_LENGTH} characters)"}
        h = int(hashlib.md5(abstract.encode()).hexdigest()[:8], 16)
        quality = 50 + (h % 40)
        novelty = 20 + (int(hashlib.md5(f"n{abstract}".encode()).hexdigest()[:8], 16) % 60)
        scores = {name: round(40 + (int(hashlib.md5(f"{abstract}{name}".encode()).hexdigest()[:8], 16) % 50), 2)
                  for name, _ in BENCHMARK_ATTRIBUTES}
        return {
            "quality_score": round(quality, 2),
            "novelty_percentage": round(novelty, 2),
            "benchmark_scores": scores,
            "evaluation_version": "mock",
        }


def get_rem_service() -> RecordEvaluationManager:
    if ANTHROPIC_AVAILABLE and settings.ANTHROPIC_API_KEY:
        logger.info("REM: using Claude LLM agent")
        return RecordEvaluationManager()
    if SBERT_AVAILABLE:
        logger.info("REM: using SBERT fallback (no ANTHROPIC_API_KEY)")
        return RecordEvaluationManager()
    logger.warning("REM: using mock evaluator (no ML deps)")
    return MockRecordEvaluationManager()


rem_service = get_rem_service()
