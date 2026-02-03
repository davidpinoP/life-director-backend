"""
Anti-Block Engine
Detects blocking patterns and breaks them.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class BlockerType(str, Enum):
    """Types of blockers."""
    ENERGY = "energy"
    TIME = "time"
    EXTERNAL = "external"
    MOTIVATION = "motivation"
    DECISION_PARALYSIS = "decision_paralysis"
    PERFECTIONISM = "perfectionism"
    UNKNOWN = "unknown"


@dataclass
class BlockerAnalysis:
    """Result of blocker analysis."""
    blocker_type: BlockerType
    pattern_detected: bool
    frequency: float  # 0.0 to 1.0
    intervention: str


class AntiBlockEngine:
    """
    Detects recurring blocking patterns.
    Proposes direct interventions.
    """
    
    # Pattern detection thresholds
    PATTERN_THRESHOLD = 0.3  # 30% occurrence = pattern
    
    @classmethod
    def analyze_patterns(
        cls,
        feedback_history: List[Dict[str, Any]]
    ) -> List[BlockerAnalysis]:
        """
        Analyze feedback history for blocking patterns.
        """
        
        if not feedback_history:
            return []
        
        total = len(feedback_history)
        analyses = []
        
        # Count blockers by type
        blocker_counts: Dict[str, int] = {}
        for fb in feedback_history:
            if fb.get("had_blockers"):
                bt = fb.get("blocker_type", "unknown")
                blocker_counts[bt] = blocker_counts.get(bt, 0) + 1
        
        # Analyze each blocker type
        for blocker_type, count in blocker_counts.items():
            frequency = count / total
            pattern_detected = frequency >= cls.PATTERN_THRESHOLD
            
            intervention = cls._get_intervention(
                BlockerType(blocker_type),
                frequency
            )
            
            analyses.append(BlockerAnalysis(
                blocker_type=BlockerType(blocker_type),
                pattern_detected=pattern_detected,
                frequency=frequency,
                intervention=intervention
            ))
        
        # Sort by frequency
        analyses.sort(key=lambda x: x.frequency, reverse=True)
        
        return analyses
    
    @classmethod
    def _get_intervention(
        cls,
        blocker_type: BlockerType,
        frequency: float
    ) -> str:
        """
        Get intervention for a blocker type.
        Returns direct order, not suggestion.
        """
        
        interventions = {
            BlockerType.ENERGY: "Reduce tareas a 2 máximo cuando energía baja",
            BlockerType.TIME: "Bloquea 90 minutos sin interrupciones mañana",
            BlockerType.EXTERNAL: "Di no a la próxima solicitud externa",
            BlockerType.MOTIVATION: "Ejecuta 5 minutos sin evaluar motivación",
            BlockerType.DECISION_PARALYSIS: "Elige la primera opción viable",
            BlockerType.PERFECTIONISM: "Entrega al 80%",
            BlockerType.UNKNOWN: "Identifica el bloqueo específico",
        }
        
        base = interventions.get(blocker_type, "Identifica el bloqueo")
        
        # Intensify for high frequency
        if frequency > 0.5:
            return f"URGENTE: {base}"
        
        return base
    
    @classmethod
    def get_primary_blocker(
        cls,
        feedback_history: List[Dict[str, Any]]
    ) -> Optional[BlockerAnalysis]:
        """
        Get the most significant blocker.
        """
        analyses = cls.analyze_patterns(feedback_history)
        
        if not analyses:
            return None
        
        # Return highest frequency pattern
        for analysis in analyses:
            if analysis.pattern_detected:
                return analysis
        
        return None
    
    @classmethod
    def detect_completion_trend(
        cls,
        feedback_history: List[Dict[str, Any]],
        window: int = 7
    ) -> Dict[str, Any]:
        """
        Detect completion rate trends.
        """
        
        if not feedback_history or len(feedback_history) < 2:
            return {
                "trend": "insufficient_data",
                "current_avg": 0.0,
                "intervention": None
            }
        
        recent = feedback_history[:window]
        
        # Calculate recent average
        rates = [fb.get("completion_rate", 0) for fb in recent]
        current_avg = sum(rates) / len(rates)
        
        # Compare first half to second half
        mid = len(rates) // 2
        first_half = sum(rates[:mid]) / mid if mid > 0 else 0
        second_half = sum(rates[mid:]) / (len(rates) - mid) if (len(rates) - mid) > 0 else 0
        
        if second_half > first_half + 0.1:
            trend = "improving"
            intervention = None
        elif second_half < first_half - 0.1:
            trend = "declining"
            intervention = "Reduce carga mañana 50%"
        else:
            trend = "stable"
            intervention = None
        
        return {
            "trend": trend,
            "current_avg": current_avg,
            "intervention": intervention
        }


def analyze_blocks(history: List[Dict[str, Any]]) -> Optional[BlockerAnalysis]:
    """Convenience function."""
    return AntiBlockEngine.get_primary_blocker(history)
