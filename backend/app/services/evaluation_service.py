"""
SALF Record Evaluation Manager (REM)
AI-driven evaluation using Sentence-BERT for research quality and novelty assessment
"""
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import hashlib
import json

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    SBERT_AVAILABLE = True
except ImportError:
    SBERT_AVAILABLE = False

from app.core.config import settings


@dataclass
class BenchmarkAttribute:
    """Represents one of the 36 benchmark attributes for evaluation."""
    name: str
    weight: float
    keywords: List[str]
    description: str


class RecordEvaluationManager:
    """
    AI-powered Record Evaluation Manager using Sentence-BERT.
    Evaluates research abstracts against 36 benchmark attributes.
    """
    
    # The 36 benchmark attributes for academic evaluation
    BENCHMARK_ATTRIBUTES = [
        # Methodology (8 attributes)
        BenchmarkAttribute("methodology_rigor", 4.0, 
            ["methodology", "rigorous", "systematic", "controlled", "experimental"],
            "Rigor and soundness of research methodology"),
        BenchmarkAttribute("research_design", 3.5,
            ["design", "framework", "structure", "approach", "protocol"],
            "Quality of research design and framework"),
        BenchmarkAttribute("data_collection", 3.0,
            ["data collection", "sampling", "survey", "measurement", "instrumentation"],
            "Data collection methods and quality"),
        BenchmarkAttribute("data_analysis", 3.5,
            ["analysis", "statistical", "quantitative", "qualitative", "modeling"],
            "Quality and depth of data analysis"),
        BenchmarkAttribute("reproducibility", 3.0,
            ["reproducible", "replicable", "transparent", "documented", "repeatable"],
            "Reproducibility of research"),
        BenchmarkAttribute("validation", 3.0,
            ["validation", "verification", "testing", "evaluation", "assessment"],
            "Validation procedures used"),
        BenchmarkAttribute("sample_size", 2.5,
            ["sample size", "participants", "subjects", "population", "n="],
            "Adequacy of sample size"),
        BenchmarkAttribute("control_variables", 2.5,
            ["control", "confounding", "variables", "bias", "adjustment"],
            "Control of confounding variables"),
        
        # Literature & Theory (6 attributes)
        BenchmarkAttribute("literature_review", 3.5,
            ["literature", "review", "previous", "existing", "prior work"],
            "Comprehensiveness of literature review"),
        BenchmarkAttribute("theoretical_framework", 3.5,
            ["theory", "theoretical", "framework", "model", "conceptual"],
            "Strength of theoretical foundation"),
        BenchmarkAttribute("research_gap", 4.0,
            ["gap", "limitation", "unexplored", "novel", "contribution"],
            "Identification and addressing of research gaps"),
        BenchmarkAttribute("hypothesis", 3.0,
            ["hypothesis", "proposition", "assumption", "conjecture", "prediction"],
            "Clarity of research hypothesis"),
        BenchmarkAttribute("citations", 2.5,
            ["cite", "reference", "source", "bibliography", "literature"],
            "Quality and relevance of citations"),
        BenchmarkAttribute("state_of_art", 3.0,
            ["state-of-the-art", "cutting-edge", "recent", "latest", "advances"],
            "Awareness of current state of the art"),
        
        # Results & Impact (8 attributes)
        BenchmarkAttribute("findings_clarity", 3.5,
            ["findings", "results", "outcomes", "discoveries", "observations"],
            "Clarity of research findings"),
        BenchmarkAttribute("statistical_significance", 3.0,
            ["significant", "p-value", "confidence", "correlation", "regression"],
            "Statistical significance of results"),
        BenchmarkAttribute("practical_application", 4.0,
            ["application", "practical", "implementation", "industry", "real-world"],
            "Practical applicability of research"),
        BenchmarkAttribute("societal_impact", 3.5,
            ["impact", "society", "community", "benefit", "welfare"],
            "Societal impact and relevance"),
        BenchmarkAttribute("innovation", 4.5,
            ["innovative", "novel", "new", "breakthrough", "pioneering"],
            "Innovation and originality"),
        BenchmarkAttribute("contribution", 4.0,
            ["contribution", "advance", "progress", "improvement", "enhancement"],
            "Contribution to the field"),
        BenchmarkAttribute("scalability", 2.5,
            ["scalable", "generalize", "extend", "adapt", "transfer"],
            "Scalability and generalizability"),
        BenchmarkAttribute("future_work", 2.0,
            ["future", "direction", "extension", "further", "ongoing"],
            "Identification of future research directions"),
        
        # Quality & Presentation (8 attributes)
        BenchmarkAttribute("conclusion_strength", 3.0,
            ["conclusion", "summary", "implication", "inference", "insight"],
            "Strength and clarity of conclusions"),
        BenchmarkAttribute("clarity", 3.0,
            ["clear", "concise", "readable", "understandable", "well-written"],
            "Overall clarity of presentation"),
        BenchmarkAttribute("structure", 2.5,
            ["structure", "organized", "logical", "coherent", "flow"],
            "Organization and structure"),
        BenchmarkAttribute("abstract_quality", 3.0,
            ["abstract", "summary", "overview", "key points", "highlights"],
            "Quality of abstract"),
        BenchmarkAttribute("ethical_consideration", 2.5,
            ["ethics", "ethical", "consent", "privacy", "integrity"],
            "Ethical considerations"),
        BenchmarkAttribute("acknowledgment_limitations", 2.5,
            ["limitation", "constraint", "weakness", "caveat", "boundary"],
            "Acknowledgment of limitations"),
        BenchmarkAttribute("interdisciplinary", 2.0,
            ["interdisciplinary", "cross-domain", "multidisciplinary", "transdisciplinary"],
            "Interdisciplinary approach"),
        BenchmarkAttribute("technical_depth", 3.0,
            ["technical", "detailed", "in-depth", "comprehensive", "thorough"],
            "Technical depth of work"),
        
        # Domain Specific (6 attributes)
        BenchmarkAttribute("domain_relevance", 3.5,
            ["relevant", "pertinent", "applicable", "domain", "field"],
            "Relevance to specific domain"),
        BenchmarkAttribute("benchmark_comparison", 3.0,
            ["benchmark", "baseline", "comparison", "state-of-art", "competing"],
            "Comparison with benchmarks"),
        BenchmarkAttribute("tool_development", 2.5,
            ["tool", "software", "framework", "library", "platform"],
            "Development of tools or frameworks"),
        BenchmarkAttribute("dataset_contribution", 2.5,
            ["dataset", "corpus", "collection", "repository", "database"],
            "Contribution of datasets"),
        BenchmarkAttribute("algorithm_novelty", 3.5,
            ["algorithm", "method", "technique", "procedure", "approach"],
            "Novelty of algorithms or methods"),
        BenchmarkAttribute("evaluation_metrics", 2.5,
            ["metric", "measure", "criterion", "indicator", "assessment"],
            "Use of appropriate evaluation metrics"),
    ]
    
    def __init__(self):
        self.model = None
        self._attribute_embeddings = None
        self._reference_corpus_embeddings = None
        
    def _load_model(self):
        """Lazy load the Sentence-BERT model."""
        if self.model is None:
            if not SBERT_AVAILABLE:
                raise ImportError("sentence-transformers is not installed")
            self.model = SentenceTransformer(settings.SBERT_MODEL)
            self._compute_attribute_embeddings()
    
    def _compute_attribute_embeddings(self):
        """Pre-compute embeddings for benchmark attributes."""
        attribute_texts = [
            f"{attr.name}: {attr.description}. Keywords: {', '.join(attr.keywords)}"
            for attr in self.BENCHMARK_ATTRIBUTES
        ]
        self._attribute_embeddings = self.model.encode(attribute_texts)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text for quick matching."""
        text_lower = text.lower()
        found_keywords = []
        for attr in self.BENCHMARK_ATTRIBUTES:
            for keyword in attr.keywords:
                if keyword.lower() in text_lower:
                    found_keywords.append(keyword)
        return list(set(found_keywords))
    
    def evaluate_abstract(self, abstract: str) -> Dict[str, Any]:
        """
        Evaluate a research abstract against 36 benchmark attributes.
        
        Args:
            abstract: The research abstract text
            
        Returns:
            Dictionary containing quality score, novelty percentage, and detailed scores
        """
        self._load_model()
        
        # Validate abstract length
        if len(abstract) < settings.MIN_ABSTRACT_LENGTH:
            return {
                "quality_score": 0,
                "novelty_percentage": 0,
                "benchmark_scores": {},
                "error": f"Abstract too short (minimum {settings.MIN_ABSTRACT_LENGTH} characters)"
            }
        
        # Encode the abstract
        abstract_embedding = self.model.encode([abstract])[0]
        
        # Calculate similarity with each benchmark attribute
        benchmark_scores = {}
        weighted_sum = 0
        total_weight = 0
        
        for i, attr in enumerate(self.BENCHMARK_ATTRIBUTES):
            # Cosine similarity with attribute embedding
            similarity = cosine_similarity(
                [abstract_embedding], 
                [self._attribute_embeddings[i]]
            )[0][0]
            
            # Normalize to 0-100 scale
            score = max(0, min(100, (similarity + 1) * 50))
            
            # Apply keyword bonus
            keyword_matches = sum(1 for kw in attr.keywords if kw.lower() in abstract.lower())
            keyword_bonus = min(10, keyword_matches * 2)
            score = min(100, score + keyword_bonus)
            
            benchmark_scores[attr.name] = {
                "score": round(score, 2),
                "weight": attr.weight,
                "weighted_score": round(score * attr.weight, 2)
            }
            
            weighted_sum += score * attr.weight
            total_weight += attr.weight
        
        # Calculate overall quality score
        quality_score = weighted_sum / total_weight if total_weight > 0 else 0
        
        # Calculate novelty percentage
        novelty_percentage = self._calculate_novelty(abstract, abstract_embedding)
        
        return {
            "quality_score": round(quality_score, 2),
            "novelty_percentage": round(novelty_percentage, 2),
            "benchmark_scores": benchmark_scores,
            "keywords_found": self._extract_keywords(abstract),
            "abstract_length": len(abstract),
            "evaluation_version": "1.0"
        }
    
    def _calculate_novelty(self, abstract: str, embedding: np.ndarray) -> float:
        """
        Calculate novelty percentage based on semantic distance from reference corpus.
        Higher distance from existing works = higher novelty.
        """
        # For now, use a heuristic based on innovation-related keywords
        innovation_keywords = [
            "novel", "new", "first", "innovative", "breakthrough", "unprecedented",
            "pioneering", "cutting-edge", "state-of-the-art", "advanced", "unique",
            "original", "creative", "revolutionary", "transformative"
        ]
        
        text_lower = abstract.lower()
        keyword_count = sum(1 for kw in innovation_keywords if kw in text_lower)
        
        # Base novelty from innovation keywords (up to 40%)
        keyword_novelty = min(40, keyword_count * 8)
        
        # Semantic variance component (up to 40%)
        # Higher embedding magnitude variance indicates more unique content
        embedding_variance = np.var(embedding)
        semantic_novelty = min(40, embedding_variance * 100)
        
        # Abstract length bonus (up to 20%) - longer abstracts may contain more detail
        length_bonus = min(20, (len(abstract) - 100) / 50)
        
        novelty = keyword_novelty + semantic_novelty + max(0, length_bonus)
        
        return min(100, max(0, novelty))
    
    def batch_evaluate(self, abstracts: List[str]) -> List[Dict[str, Any]]:
        """Evaluate multiple abstracts efficiently."""
        self._load_model()
        
        results = []
        # Batch encode all abstracts
        embeddings = self.model.encode(abstracts)
        
        for abstract, embedding in zip(abstracts, embeddings):
            if len(abstract) < settings.MIN_ABSTRACT_LENGTH:
                results.append({
                    "quality_score": 0,
                    "novelty_percentage": 0,
                    "error": "Abstract too short"
                })
                continue
            
            # Calculate scores using pre-computed embedding
            benchmark_scores = {}
            weighted_sum = 0
            total_weight = 0
            
            for i, attr in enumerate(self.BENCHMARK_ATTRIBUTES):
                similarity = cosine_similarity(
                    [embedding], 
                    [self._attribute_embeddings[i]]
                )[0][0]
                
                score = max(0, min(100, (similarity + 1) * 50))
                keyword_matches = sum(1 for kw in attr.keywords if kw.lower() in abstract.lower())
                keyword_bonus = min(10, keyword_matches * 2)
                score = min(100, score + keyword_bonus)
                
                benchmark_scores[attr.name] = round(score, 2)
                weighted_sum += score * attr.weight
                total_weight += attr.weight
            
            quality_score = weighted_sum / total_weight if total_weight > 0 else 0
            novelty_percentage = self._calculate_novelty(abstract, embedding)
            
            results.append({
                "quality_score": round(quality_score, 2),
                "novelty_percentage": round(novelty_percentage, 2),
                "benchmark_scores": benchmark_scores
            })
        
        return results
    
    def calculate_final_credits(
        self,
        base_points: int,
        quality_score: float,
        novelty_percentage: float
    ) -> float:
        """
        Calculate final credits using the formula:
        FinalCredits = BasePoints × (1 + QualityScore/100) × (1 + NoveltyMultiplier)
        
        Where NoveltyMultiplier = NoveltyPercentage / 200 (up to 50% bonus)
        """
        quality_multiplier = 1 + (quality_score / 100)
        novelty_multiplier = 1 + (novelty_percentage / 200)
        
        final_credits = base_points * quality_multiplier * novelty_multiplier
        
        return round(final_credits, 2)


class MockRecordEvaluationManager(RecordEvaluationManager):
    """Mock REM for development/testing without ML dependencies."""
    
    def __init__(self):
        super().__init__()
        self._mock_mode = True
    
    def _load_model(self):
        """No-op for mock mode."""
        pass
    
    def evaluate_abstract(self, abstract: str) -> Dict[str, Any]:
        """Generate mock evaluation scores."""
        if len(abstract) < settings.MIN_ABSTRACT_LENGTH:
            return {
                "quality_score": 0,
                "novelty_percentage": 0,
                "benchmark_scores": {},
                "error": f"Abstract too short (minimum {settings.MIN_ABSTRACT_LENGTH} characters)"
            }
        
        # Generate deterministic scores based on abstract content
        hash_int = int(hashlib.md5(abstract.encode()).hexdigest()[:8], 16)
        base_score = 50 + (hash_int % 40)  # Score between 50-90
        
        benchmark_scores = {}
        for attr in self.BENCHMARK_ATTRIBUTES:
            # Vary score based on attribute name hash
            attr_hash = int(hashlib.md5(f"{abstract}{attr.name}".encode()).hexdigest()[:8], 16)
            score = 40 + (attr_hash % 50)  # Score between 40-90
            benchmark_scores[attr.name] = {
                "score": round(score, 2),
                "weight": attr.weight,
                "weighted_score": round(score * attr.weight, 2)
            }
        
        novelty_hash = int(hashlib.md5(f"novelty{abstract}".encode()).hexdigest()[:8], 16)
        novelty = 20 + (novelty_hash % 60)  # Novelty between 20-80
        
        return {
            "quality_score": round(base_score, 2),
            "novelty_percentage": round(novelty, 2),
            "benchmark_scores": benchmark_scores,
            "keywords_found": self._extract_keywords(abstract) if abstract else [],
            "abstract_length": len(abstract),
            "evaluation_version": "1.0-mock"
        }


def get_rem_service() -> RecordEvaluationManager:
    """Factory function to get appropriate REM service."""
    if SBERT_AVAILABLE:
        try:
            rem = RecordEvaluationManager()
            return rem
        except Exception:
            pass
    
    return MockRecordEvaluationManager()


# Singleton instance
rem_service = get_rem_service()
