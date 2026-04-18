"""
SALF Fraud Detection Gatekeeper
ML-based anomaly detection for identifying fraudulent academic credit requests
"""
import hashlib
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.feature_extraction.text import TfidfVectorizer
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from app.core.config import settings


class FraudDetectionGatekeeper:
    """
    ML-based gatekeeper for detecting fraudulent or anomalous academic credit requests.
    
    Detection capabilities:
    1. Duplicate submission detection
    2. AI-generated content detection
    3. Anomalous submission patterns
    4. Plagiarism indicators
    5. Metadata inconsistencies
    """
    
    # Common AI-generated text patterns
    AI_PATTERNS = [
        r"as an ai",
        r"as a language model",
        r"i don't have personal",
        r"i cannot provide",
        r"it's important to note",
        r"in conclusion,?\s+(?:overall|this|we)",
        r"(?:first|second|third|finally),?\s+(?:we|it|this)",
    ]
    
    # Suspicious word density patterns
    SUSPICIOUS_DENSITY_WORDS = [
        "novel", "innovative", "unprecedented", "revolutionary",
        "breakthrough", "state-of-the-art", "cutting-edge", "pioneering"
    ]
    
    def __init__(self):
        self._isolation_forest = None
        self._tfidf_vectorizer = None
        self._submission_history: Dict[str, List[datetime]] = defaultdict(list)
        self._content_hashes: Dict[str, str] = {}
        self._is_model_trained = False
    
    def _initialize_models(self):
        """Initialize ML models for fraud detection."""
        if not SKLEARN_AVAILABLE:
            return
        
        # Initialize Isolation Forest for anomaly detection
        self._isolation_forest = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )
        
        # Initialize TF-IDF vectorizer for text analysis
        self._tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
    
    def detect_fraud(
        self,
        faculty_address: str,
        category: str,
        title: str,
        abstract: str,
        metadata: Dict[str, Any],
        ipfs_hash: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a submission for potential fraud.
        
        Returns:
            Dictionary containing:
            - fraud_probability: float (0-1)
            - is_flagged: bool
            - flag_reasons: list of detected issues
            - recommendations: suggested actions
        """
        flag_reasons = []
        risk_scores = []
        
        # 1. Check for duplicate submissions
        duplicate_result = self._check_duplicates(abstract, ipfs_hash, faculty_address)
        if duplicate_result["is_duplicate"]:
            flag_reasons.append(f"Duplicate detected: {duplicate_result['reason']}")
            risk_scores.append(1.0)
        
        # 2. Check for AI-generated content
        ai_result = self._detect_ai_content(abstract)
        if ai_result["is_ai_generated"]:
            flag_reasons.append(f"AI-generated content suspected: {ai_result['reason']}")
            risk_scores.append(ai_result["confidence"])
        
        # 3. Check submission pattern anomalies
        pattern_result = self._check_submission_patterns(faculty_address)
        if pattern_result["is_anomalous"]:
            flag_reasons.append(f"Anomalous submission pattern: {pattern_result['reason']}")
            risk_scores.append(pattern_result["anomaly_score"])
        
        # 4. Check metadata consistency
        metadata_result = self._check_metadata_consistency(category, metadata)
        if not metadata_result["is_consistent"]:
            flag_reasons.extend([f"Metadata issue: {r}" for r in metadata_result["issues"]])
            risk_scores.append(0.5)
        
        # 5. Check text quality indicators
        quality_result = self._check_text_quality(title, abstract)
        if quality_result["has_issues"]:
            flag_reasons.extend(quality_result["issues"])
            risk_scores.append(quality_result["risk_score"])
        
        # 6. Check for suspicious word density
        density_result = self._check_suspicious_density(abstract)
        if density_result["is_suspicious"]:
            flag_reasons.append(f"Suspicious keyword density: {density_result['reason']}")
            risk_scores.append(0.4)
        
        # Calculate overall fraud probability
        if risk_scores:
            fraud_probability = min(1.0, sum(risk_scores) / len(risk_scores) + 0.1 * len(risk_scores))
        else:
            fraud_probability = 0.0
        
        # Determine if should be flagged
        is_flagged = fraud_probability >= settings.FRAUD_DETECTION_THRESHOLD
        
        # Record this submission
        self._record_submission(faculty_address, abstract)
        
        return {
            "fraud_probability": round(fraud_probability, 4),
            "is_flagged": is_flagged,
            "flag_reasons": flag_reasons,
            "risk_scores": {
                "duplicate": duplicate_result.get("score", 0),
                "ai_content": ai_result.get("confidence", 0),
                "pattern_anomaly": pattern_result.get("anomaly_score", 0),
                "metadata": 0.5 if not metadata_result["is_consistent"] else 0,
                "text_quality": quality_result.get("risk_score", 0),
                "keyword_density": 0.4 if density_result["is_suspicious"] else 0
            },
            "recommendations": self._get_recommendations(flag_reasons, fraud_probability),
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
    
    def _check_duplicates(
        self,
        abstract: str,
        ipfs_hash: Optional[str],
        faculty_address: str
    ) -> Dict[str, Any]:
        """Check for duplicate submissions."""
        # Hash the abstract content
        content_hash = hashlib.sha256(abstract.lower().strip().encode()).hexdigest()
        
        # Check if this content hash exists
        if content_hash in self._content_hashes:
            return {
                "is_duplicate": True,
                "reason": "Exact content match found",
                "score": 1.0
            }
        
        # Check IPFS hash duplicates
        if ipfs_hash and ipfs_hash in self._content_hashes.values():
            return {
                "is_duplicate": True,
                "reason": "Document hash already submitted",
                "score": 1.0
            }
        
        return {"is_duplicate": False, "score": 0}
    
    def _detect_ai_content(self, text: str) -> Dict[str, Any]:
        """Detect AI-generated content patterns."""
        text_lower = text.lower()
        detected_patterns = []
        
        for pattern in self.AI_PATTERNS:
            if re.search(pattern, text_lower):
                detected_patterns.append(pattern)
        
        if detected_patterns:
            confidence = min(0.9, 0.3 * len(detected_patterns))
            return {
                "is_ai_generated": True,
                "reason": f"Detected {len(detected_patterns)} AI-typical patterns",
                "confidence": confidence,
                "patterns": detected_patterns
            }
        
        # Check for unnaturally perfect structure
        sentences = text.split('.')
        if len(sentences) > 5:
            lengths = [len(s.split()) for s in sentences if s.strip()]
            if lengths:
                variance = np.var(lengths)
                if variance < 5:  # Very uniform sentence lengths
                    return {
                        "is_ai_generated": True,
                        "reason": "Unnaturally uniform sentence structure",
                        "confidence": 0.4
                    }
        
        return {"is_ai_generated": False, "confidence": 0}
    
    def _check_submission_patterns(self, faculty_address: str) -> Dict[str, Any]:
        """Check for anomalous submission patterns."""
        history = self._submission_history.get(faculty_address, [])
        
        if not history:
            return {"is_anomalous": False, "anomaly_score": 0}
        
        now = datetime.utcnow()
        
        # Check submissions in last hour
        last_hour = [s for s in history if now - s < timedelta(hours=1)]
        if len(last_hour) >= 5:
            return {
                "is_anomalous": True,
                "reason": f"{len(last_hour)} submissions in the last hour (threshold: 5)",
                "anomaly_score": 0.6
            }
        
        # Check submissions in last day
        last_day = [s for s in history if now - s < timedelta(days=1)]
        if len(last_day) >= 20:
            return {
                "is_anomalous": True,
                "reason": f"{len(last_day)} submissions in the last 24 hours (threshold: 20)",
                "anomaly_score": 0.7
            }
        
        # Check for burst patterns (multiple submissions within minutes)
        if len(last_hour) >= 3:
            sorted_times = sorted(last_hour)
            min_gap = min(
                (sorted_times[i+1] - sorted_times[i]).total_seconds()
                for i in range(len(sorted_times) - 1)
            )
            if min_gap < 60:  # Less than 1 minute between submissions
                return {
                    "is_anomalous": True,
                    "reason": "Rapid-fire submission pattern detected",
                    "anomaly_score": 0.5
                }
        
        return {"is_anomalous": False, "anomaly_score": 0}
    
    def _check_metadata_consistency(
        self,
        category: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check for metadata consistency issues."""
        issues = []
        
        # Check ISBN/ISSN format
        isbn = metadata.get("isbn", "")
        issn = metadata.get("issn", "")
        
        if isbn and not self._validate_isbn(isbn):
            issues.append("Invalid ISBN format")
        
        if issn and not self._validate_issn(issn):
            issues.append("Invalid ISSN format")
        
        # Check DOI format
        doi = metadata.get("doi", "")
        if doi and not re.match(r'^10\.\d{4,}/[^\s]+$', doi):
            issues.append("Invalid DOI format")
        
        # Check publication date
        pub_date = metadata.get("publication_date")
        if pub_date:
            try:
                if isinstance(pub_date, str):
                    pub_date = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                if pub_date > datetime.utcnow():
                    issues.append("Publication date is in the future")
            except Exception:
                issues.append("Invalid publication date format")
        
        # Category-specific checks
        if "journal" in category.lower() and not issn:
            issues.append("Journal article missing ISSN")
        
        if "book" in category.lower() and not isbn:
            issues.append("Book contribution missing ISBN")
        
        return {
            "is_consistent": len(issues) == 0,
            "issues": issues
        }
    
    def _check_text_quality(self, title: str, abstract: str) -> Dict[str, Any]:
        """Check for text quality issues."""
        issues = []
        risk_score = 0
        
        # Check title quality
        if len(title) < 10:
            issues.append("Title too short")
            risk_score += 0.1
        
        if title.isupper():
            issues.append("Title is all uppercase")
            risk_score += 0.05
        
        if not any(c.isalpha() for c in title):
            issues.append("Title contains no letters")
            risk_score += 0.3
        
        # Check abstract quality
        word_count = len(abstract.split())
        
        if word_count < 50:
            issues.append("Abstract too short (less than 50 words)")
            risk_score += 0.2
        
        # Check for excessive repetition
        words = abstract.lower().split()
        if words:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.3:
                issues.append("High word repetition detected")
                risk_score += 0.3
        
        # Check for gibberish (consonant clusters)
        gibberish_pattern = r'[bcdfghjklmnpqrstvwxz]{5,}'
        if re.search(gibberish_pattern, abstract.lower()):
            issues.append("Potential gibberish detected")
            risk_score += 0.4
        
        return {
            "has_issues": len(issues) > 0,
            "issues": issues,
            "risk_score": min(1.0, risk_score)
        }
    
    def _check_suspicious_density(self, text: str) -> Dict[str, Any]:
        """Check for suspicious keyword density."""
        text_lower = text.lower()
        word_count = len(text_lower.split())
        
        if word_count == 0:
            return {"is_suspicious": False}
        
        suspicious_count = sum(
            text_lower.count(word) for word in self.SUSPICIOUS_DENSITY_WORDS
        )
        
        density = suspicious_count / word_count
        
        # More than 3% suspicious word density
        if density > 0.03:
            return {
                "is_suspicious": True,
                "reason": f"Suspicious word density: {density:.1%}",
                "density": density
            }
        
        return {"is_suspicious": False}
    
    def _validate_isbn(self, isbn: str) -> bool:
        """Validate ISBN-10 or ISBN-13 format."""
        isbn = isbn.replace("-", "").replace(" ", "")
        
        if len(isbn) == 10:
            # ISBN-10 validation
            if not isbn[:-1].isdigit() or isbn[-1] not in "0123456789Xx":
                return False
            total = sum((10-i) * int(d) for i, d in enumerate(isbn[:-1]))
            check = isbn[-1].upper()
            check_digit = 11 - (total % 11)
            return (check == 'X' and check_digit == 10) or (check.isdigit() and int(check) == check_digit % 11)
        
        elif len(isbn) == 13:
            # ISBN-13 validation
            if not isbn.isdigit():
                return False
            total = sum((1 if i % 2 == 0 else 3) * int(d) for i, d in enumerate(isbn[:-1]))
            check_digit = (10 - (total % 10)) % 10
            return int(isbn[-1]) == check_digit
        
        return False
    
    def _validate_issn(self, issn: str) -> bool:
        """Validate ISSN format."""
        issn = issn.replace("-", "").replace(" ", "")
        
        if len(issn) != 8:
            return False
        
        if not issn[:-1].isdigit() or issn[-1] not in "0123456789Xx":
            return False
        
        # Checksum validation
        total = sum((8-i) * int(d) for i, d in enumerate(issn[:-1]))
        check = issn[-1].upper()
        check_digit = 11 - (total % 11)
        
        return (check == 'X' and check_digit == 10) or (check.isdigit() and int(check) == check_digit % 11)
    
    def _record_submission(self, faculty_address: str, abstract: str):
        """Record a submission for pattern analysis."""
        self._submission_history[faculty_address].append(datetime.utcnow())
        
        # Store content hash
        content_hash = hashlib.sha256(abstract.lower().strip().encode()).hexdigest()
        self._content_hashes[content_hash] = faculty_address
        
        # Clean old entries (older than 7 days)
        cutoff = datetime.utcnow() - timedelta(days=7)
        for address in self._submission_history:
            self._submission_history[address] = [
                s for s in self._submission_history[address] if s > cutoff
            ]
    
    def _get_recommendations(
        self,
        flag_reasons: List[str],
        fraud_probability: float
    ) -> List[str]:
        """Generate recommendations based on detected issues."""
        recommendations = []
        
        if fraud_probability >= 0.9:
            recommendations.append("BLOCK: High fraud probability - require manual review")
        elif fraud_probability >= 0.7:
            recommendations.append("FLAG: Elevated risk - route to HoD for verification")
        elif fraud_probability >= 0.5:
            recommendations.append("REVIEW: Moderate risk - additional documentation recommended")
        
        if any("duplicate" in r.lower() for r in flag_reasons):
            recommendations.append("Verify this is not a resubmission of existing work")
        
        if any("ai" in r.lower() for r in flag_reasons):
            recommendations.append("Request original manuscript or raw data")
        
        if any("pattern" in r.lower() for r in flag_reasons):
            recommendations.append("Review faculty submission history")
        
        if any("metadata" in r.lower() for r in flag_reasons):
            recommendations.append("Verify publication details with original source")
        
        return recommendations if recommendations else ["Process normally"]
    
    def get_faculty_risk_profile(self, faculty_address: str) -> Dict[str, Any]:
        """Get risk profile for a faculty member based on history."""
        history = self._submission_history.get(faculty_address, [])
        
        if not history:
            return {
                "risk_level": "unknown",
                "total_submissions": 0,
                "recent_submissions": 0,
                "flags_count": 0
            }
        
        now = datetime.utcnow()
        recent = [s for s in history if now - s < timedelta(days=30)]
        
        # Simple risk assessment
        if len(recent) > 50:
            risk_level = "high"
        elif len(recent) > 20:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "risk_level": risk_level,
            "total_submissions": len(history),
            "recent_submissions": len(recent),
            "average_interval_days": self._calculate_average_interval(history)
        }
    
    def _calculate_average_interval(self, timestamps: List[datetime]) -> float:
        """Calculate average interval between submissions in days."""
        if len(timestamps) < 2:
            return 0
        
        sorted_ts = sorted(timestamps)
        intervals = [
            (sorted_ts[i+1] - sorted_ts[i]).total_seconds() / 86400
            for i in range(len(sorted_ts) - 1)
        ]
        return round(sum(intervals) / len(intervals), 2)


# Singleton instance
fraud_gatekeeper = FraudDetectionGatekeeper()
