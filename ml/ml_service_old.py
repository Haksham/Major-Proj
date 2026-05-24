"""
ML Service for SALF - Sentence-BERT based evaluation
Provides NLP evaluation capabilities for academic contributions
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os
from typing import List, Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="SALF ML Service",
    description="NLP Evaluation Service for Academic Contributions",
    version="1.0.0"
)

# Load model
MODEL_NAME = os.getenv("MODEL_NAME", "all-MiniLM-L6-v2")
model = None

@app.on_event("startup")
async def load_model():
    """Load Sentence-BERT model on startup"""
    global model
    logger.info(f"Loading model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    logger.info("Model loaded successfully")

# Benchmark attributes for academic evaluation
BENCHMARK_ATTRIBUTES = {
    # Research Quality (40% weight)
    "research_quality": [
        "novel research contribution",
        "original methodology",
        "significant findings",
        "rigorous analysis",
        "well-designed experiments",
        "reproducible results",
        "clear hypothesis",
        "systematic approach",
    ],
    # Academic Impact (25% weight)
    "academic_impact": [
        "high citation potential",
        "field advancement",
        "interdisciplinary relevance",
        "practical applications",
        "theoretical contribution",
        "policy implications",
    ],
    # Writing Quality (20% weight)
    "writing_quality": [
        "clear and concise writing",
        "well-structured presentation",
        "logical flow of arguments",
        "comprehensive literature review",
        "proper academic style",
    ],
    # Innovation (15% weight)
    "innovation": [
        "novel approach",
        "creative solution",
        "breakthrough discovery",
        "paradigm shift",
        "innovative methodology",
    ],
}

CATEGORY_WEIGHTS = {
    "research_quality": 0.40,
    "academic_impact": 0.25,
    "writing_quality": 0.20,
    "innovation": 0.15,
}

# Pre-compute benchmark embeddings
benchmark_embeddings = {}

@app.on_event("startup")
async def compute_benchmark_embeddings():
    """Pre-compute embeddings for benchmark attributes"""
    global benchmark_embeddings
    for category, attributes in BENCHMARK_ATTRIBUTES.items():
        benchmark_embeddings[category] = model.encode(attributes)
    logger.info("Benchmark embeddings computed")


class EvaluationRequest(BaseModel):
    """Request model for evaluation"""
    abstract: str
    title: Optional[str] = None
    keywords: Optional[List[str]] = None
    contribution_category: Optional[int] = None


class EvaluationResponse(BaseModel):
    """Response model for evaluation"""
    quality_score: float
    novelty_score: float
    category_scores: Dict[str, float]
    top_matching_attributes: List[Dict[str, float]]
    confidence: float


class SimilarityRequest(BaseModel):
    """Request model for similarity check"""
    text: str
    corpus: List[str]
    threshold: Optional[float] = 0.8


class SimilarityResponse(BaseModel):
    """Response model for similarity check"""
    is_duplicate: bool
    max_similarity: float
    similar_indices: List[int]


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model": MODEL_NAME,
        "model_loaded": model is not None
    }


@app.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_contribution(request: EvaluationRequest):
    """
    Evaluate academic contribution against benchmark attributes
    Returns quality score, novelty score, and detailed breakdown
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    # Combine title and abstract for evaluation
    text = request.abstract
    if request.title:
        text = f"{request.title}. {text}"
    if request.keywords:
        text += f" Keywords: {', '.join(request.keywords)}"
    
    # Generate embedding for the contribution
    contribution_embedding = model.encode([text])[0]
    
    # Calculate scores for each category
    category_scores = {}
    all_similarities = []
    top_attributes = []
    
    for category, embeddings in benchmark_embeddings.items():
        similarities = cosine_similarity([contribution_embedding], embeddings)[0]
        category_scores[category] = float(np.mean(similarities) * 100)
        
        # Track top matching attributes
        for idx, sim in enumerate(similarities):
            all_similarities.append(sim)
            top_attributes.append({
                "attribute": BENCHMARK_ATTRIBUTES[category][idx],
                "category": category,
                "similarity": float(sim)
            })
    
    # Sort and get top matching attributes
    top_attributes = sorted(top_attributes, key=lambda x: x["similarity"], reverse=True)[:10]
    
    # Calculate weighted quality score
    quality_score = sum(
        category_scores[cat] * weight
        for cat, weight in CATEGORY_WEIGHTS.items()
    )
    
    # Calculate novelty score (inverse of average similarity to common patterns)
    # Higher novelty = lower similarity to typical patterns
    avg_similarity = np.mean(all_similarities)
    novelty_score = (1 - avg_similarity) * 100 * 1.5  # Scale factor
    novelty_score = min(100, max(0, novelty_score))  # Clamp to 0-100
    
    # Calculate confidence based on text length and quality
    word_count = len(text.split())
    confidence = min(1.0, word_count / 200)  # Higher confidence for longer texts
    
    return EvaluationResponse(
        quality_score=round(quality_score, 2),
        novelty_score=round(novelty_score, 2),
        category_scores={k: round(v, 2) for k, v in category_scores.items()},
        top_matching_attributes=top_attributes,
        confidence=round(confidence, 2)
    )


@app.post("/similarity", response_model=SimilarityResponse)
async def check_similarity(request: SimilarityRequest):
    """
    Check text similarity against a corpus for duplicate detection
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    if not request.corpus:
        return SimilarityResponse(
            is_duplicate=False,
            max_similarity=0.0,
            similar_indices=[]
        )
    
    # Generate embeddings
    text_embedding = model.encode([request.text])
    corpus_embeddings = model.encode(request.corpus)
    
    # Calculate similarities
    similarities = cosine_similarity(text_embedding, corpus_embeddings)[0]
    
    # Find similar items
    similar_indices = [
        int(idx) for idx, sim in enumerate(similarities)
        if sim >= request.threshold
    ]
    
    max_similarity = float(np.max(similarities)) if len(similarities) > 0 else 0.0
    
    return SimilarityResponse(
        is_duplicate=max_similarity >= request.threshold,
        max_similarity=round(max_similarity, 4),
        similar_indices=similar_indices
    )


@app.post("/embed")
async def generate_embedding(text: str):
    """
    Generate embedding for given text
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    embedding = model.encode([text])[0]
    return {
        "embedding": embedding.tolist(),
        "dimension": len(embedding)
    }


@app.get("/benchmarks")
async def get_benchmarks():
    """
    Get list of benchmark attributes used for evaluation
    """
    return {
        "attributes": BENCHMARK_ATTRIBUTES,
        "weights": CATEGORY_WEIGHTS,
        "total_attributes": sum(len(attrs) for attrs in BENCHMARK_ATTRIBUTES.values())
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
