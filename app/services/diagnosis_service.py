"""
Diagnosis Service
Rule-based analysis. No LLM.
Detects bottlenecks, dispersion, sleep debt, energy leaks, incoherence.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from app.core.constants import (
    SLEEP_DEBT_THRESHOLD_HOURS,
    DISPERSION_THRESHOLD,
    ENERGY_LEAK_THRESHOLD,
    WEIGHT_BOTTLENECK,
    WEIGHT_DISPERSION,
    WEIGHT_SLEEP_DEBT,
    WEIGHT_ENERGY_LEAK,
    WEIGHT_INCOHERENCE,
)
from app.utils.scoring import (
    calculate_bottleneck_score,
    calculate_dispersion_score,
    calculate_sleep_debt,
    calculate_energy_leak,
    calculate_incoherence,
)


@dataclass
class DiagnosisResult:
    """Complete diagnosis result."""
    
    # Scores (0.0 to 1.0, higher = worse)
    bottleneck_score: float
    dispersion_score: float
    sleep_debt_score: float
    energy_leak_score: float
    incoherence_score: float
    
    # Overall
    overall_score: float
    
    # Details
    primary_bottleneck: str
    bottleneck_details: str
    
    is_dispersed: bool
    active_goals_count: int
    
    sleep_debt_hours: float
    
    energy_leak_percentage: float
    energy_leak_sources: List[str]
    
    is_incoherent: bool
    incoherence_details: Optional[str]
    
    # Action
    priority_action: str


class DiagnosisService:
    """
    Analyzes user data to detect problems.
    Pure rule-based scoring. No LLM.
    """
    
    @classmethod
    def diagnose(cls, onboarding_data: Dict[str, Any]) -> DiagnosisResult:
        """
        Run complete diagnosis on user data.
        Returns scores and identified problems.
        """
        
        # Extract data
        activities = onboarding_data.get("current_activities", [])
        primary_goal = onboarding_data.get("primary_goal", "")
        hours_sleep = onboarding_data.get("hours_sleep", 7.0)
        hours_work = onboarding_data.get("hours_work", 8.0)
        main_obstacle = onboarding_data.get("main_obstacle", "")
        peak_energy = onboarding_data.get("peak_energy_time", "morning")
        
        # Calculate individual scores
        bottleneck_result = cls._analyze_bottleneck(
            main_obstacle, activities, hours_work
        )
        
        dispersion_result = cls._analyze_dispersion(activities)
        
        sleep_result = cls._analyze_sleep(hours_sleep)
        
        energy_leak_result = cls._analyze_energy_leaks(
            activities, primary_goal
        )
        
        incoherence_result = cls._analyze_incoherence(
            activities, primary_goal
        )
        
        # Calculate overall score
        overall = (
            bottleneck_result["score"] * WEIGHT_BOTTLENECK +
            dispersion_result["score"] * WEIGHT_DISPERSION +
            sleep_result["score"] * WEIGHT_SLEEP_DEBT +
            energy_leak_result["score"] * WEIGHT_ENERGY_LEAK +
            incoherence_result["score"] * WEIGHT_INCOHERENCE
        )
        
        # Determine priority action
        priority_action = cls._determine_priority_action(
            bottleneck_result,
            dispersion_result,
            sleep_result,
            energy_leak_result,
            incoherence_result
        )
        
        return DiagnosisResult(
            bottleneck_score=bottleneck_result["score"],
            dispersion_score=dispersion_result["score"],
            sleep_debt_score=sleep_result["score"],
            energy_leak_score=energy_leak_result["score"],
            incoherence_score=incoherence_result["score"],
            overall_score=overall,
            primary_bottleneck=bottleneck_result["primary"],
            bottleneck_details=bottleneck_result["details"],
            is_dispersed=dispersion_result["is_dispersed"],
            active_goals_count=dispersion_result["count"],
            sleep_debt_hours=sleep_result["debt_hours"],
            energy_leak_percentage=energy_leak_result["percentage"],
            energy_leak_sources=energy_leak_result["sources"],
            is_incoherent=incoherence_result["is_incoherent"],
            incoherence_details=incoherence_result["details"],
            priority_action=priority_action
        )
    
    @classmethod
    def _analyze_bottleneck(
        cls,
        main_obstacle: str,
        activities: List[Dict],
        hours_work: float
    ) -> Dict[str, Any]:
        """
        Identify primary bottleneck.
        """
        score = calculate_bottleneck_score(main_obstacle, activities, hours_work)
        
        # Determine bottleneck type
        if hours_work > 10:
            primary = "overwork"
            details = "Exceso de horas de trabajo impide progreso real"
        elif len(activities) > 7:
            primary = "fragmentation"
            details = "Demasiadas actividades fragmentan la atención"
        elif main_obstacle:
            primary = "declared_obstacle"
            details = main_obstacle
        else:
            primary = "unclear"
            details = "Cuello de botella no identificado claramente"
        
        return {
            "score": score,
            "primary": primary,
            "details": details
        }
    
    @classmethod
    def _analyze_dispersion(cls, activities: List[Dict]) -> Dict[str, Any]:
        """
        Detect goal/activity dispersion.
        """
        count = len(activities)
        score = calculate_dispersion_score(count)
        is_dispersed = count > DISPERSION_THRESHOLD
        
        return {
            "score": score,
            "is_dispersed": is_dispersed,
            "count": count
        }
    
    @classmethod
    def _analyze_sleep(cls, hours_sleep: float) -> Dict[str, Any]:
        """
        Calculate sleep debt.
        """
        optimal = 7.5
        debt = max(0, optimal - hours_sleep)
        score = calculate_sleep_debt(hours_sleep)
        
        return {
            "score": score,
            "debt_hours": debt,
            "has_debt": debt > SLEEP_DEBT_THRESHOLD_HOURS
        }
    
    @classmethod
    def _analyze_energy_leaks(
        cls,
        activities: List[Dict],
        primary_goal: str
    ) -> Dict[str, Any]:
        """
        Identify activities consuming energy without contributing to goal.
        """
        total_hours = sum(a.get("hours_per_week", 0) for a in activities)
        
        if total_hours == 0:
            return {
                "score": 0.0,
                "percentage": 0.0,
                "sources": []
            }
        
        # Find non-aligned activities
        leak_sources = []
        leak_hours = 0
        
        for activity in activities:
            if not activity.get("aligned_with_goal", False):
                name = activity.get("name", "unknown")
                hours = activity.get("hours_per_week", 0)
                if hours > 2:  # Only count significant time investments
                    leak_sources.append(name)
                    leak_hours += hours
        
        percentage = leak_hours / total_hours if total_hours > 0 else 0
        score = calculate_energy_leak(percentage)
        
        return {
            "score": score,
            "percentage": percentage,
            "sources": leak_sources
        }
    
    @classmethod
    def _analyze_incoherence(
        cls,
        activities: List[Dict],
        primary_goal: str
    ) -> Dict[str, Any]:
        """
        Detect misalignment between goal and actual activities.
        """
        if not activities:
            return {
                "score": 0.5,
                "is_incoherent": True,
                "details": "No hay actividades definidas"
            }
        
        # Count aligned vs non-aligned
        aligned = sum(1 for a in activities if a.get("aligned_with_goal", False))
        total = len(activities)
        
        alignment_ratio = aligned / total if total > 0 else 0
        
        is_incoherent = alignment_ratio < 0.3
        score = calculate_incoherence(alignment_ratio)
        
        details = None
        if is_incoherent:
            details = f"Solo {aligned} de {total} actividades alineadas con objetivo"
        
        return {
            "score": score,
            "is_incoherent": is_incoherent,
            "details": details
        }
    
    @classmethod
    def _determine_priority_action(
        cls,
        bottleneck: Dict,
        dispersion: Dict,
        sleep: Dict,
        energy_leak: Dict,
        incoherence: Dict
    ) -> str:
        """
        Determine the single most important action.
        Returns a direct order, not a suggestion.
        """
        
        # Find highest score
        scores = [
            (bottleneck["score"], "bottleneck"),
            (dispersion["score"], "dispersion"),
            (sleep["score"], "sleep"),
            (energy_leak["score"], "energy_leak"),
            (incoherence["score"], "incoherence"),
        ]
        
        highest = max(scores, key=lambda x: x[0])
        
        # Determine action text based on bottleneck type
        if bottleneck["primary"] == "declared_obstacle":
            bottleneck_action = f"Elimina bloqueo: {bottleneck['details']}"
        elif bottleneck["primary"] == "overwork":
            bottleneck_action = "Reduce jornada laboral (límite 10h)"
        elif bottleneck["primary"] == "fragmentation":
            bottleneck_action = "Elimina 2 actividades hoy"
        else:
            bottleneck_action = "Identifica tu bloqueo principal"

        actions = {
            "bottleneck": bottleneck_action,
            "dispersion": f"Reduce actividades a {DISPERSION_THRESHOLD} máximo",
            "sleep": "Aumenta horas de sueño esta semana",
            "energy_leak": f"Elimina: {', '.join(energy_leak['sources'][:2]) if energy_leak['sources'] else 'actividades sin impacto'}",
            "incoherence": "Alinea actividades con objetivo principal",
        }
        
        return actions.get(highest[1], "Define un objetivo claro")


def run_diagnosis(onboarding_data: Dict[str, Any]) -> DiagnosisResult:
    """Convenience function to run diagnosis."""
    return DiagnosisService.diagnose(onboarding_data)
