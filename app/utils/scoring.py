"""
Scoring Utilities
Calculation functions for diagnosis.
"""

from typing import List, Dict, Any

from app.core.constants import (
    SLEEP_DEBT_THRESHOLD_HOURS,
    DISPERSION_THRESHOLD,
    ENERGY_LEAK_THRESHOLD,
)


def calculate_bottleneck_score(
    main_obstacle: str,
    activities: List[Dict],
    hours_work: float
) -> float:
    """
    Calculate bottleneck severity score.
    Returns 0.0 to 1.0 (higher = worse).
    """
    score = 0.0
    
    # Has declared obstacle
    if main_obstacle and len(main_obstacle) > 10:
        score += 0.3
    
    # Too many activities
    if len(activities) > 10:
        score += 0.3
    elif len(activities) > 7:
        score += 0.2
    
    # Overwork
    if hours_work > 12:
        score += 0.4
    elif hours_work > 10:
        score += 0.2
    elif hours_work > 8:
        score += 0.1
    
    return min(1.0, score)


def calculate_dispersion_score(activity_count: int) -> float:
    """
    Calculate dispersion score based on activity count.
    Returns 0.0 to 1.0 (higher = more dispersed).
    """
    if activity_count <= 3:
        return 0.0
    elif activity_count <= DISPERSION_THRESHOLD:
        # Linear scale from 0 to 0.5
        return (activity_count - 3) / (DISPERSION_THRESHOLD - 3) * 0.5
    elif activity_count <= 10:
        # Scale from 0.5 to 0.8
        return 0.5 + (activity_count - DISPERSION_THRESHOLD) / (10 - DISPERSION_THRESHOLD) * 0.3
    else:
        # Maximum dispersion
        return min(1.0, 0.8 + (activity_count - 10) * 0.02)


def calculate_sleep_debt(hours_sleep: float) -> float:
    """
    Calculate sleep debt score.
    Based on optimal 7.5 hours.
    Returns 0.0 to 1.0 (higher = more debt).
    """
    optimal = 7.5
    
    if hours_sleep >= optimal:
        return 0.0
    
    debt = optimal - hours_sleep
    
    if debt <= 1:
        return debt * 0.2
    elif debt <= SLEEP_DEBT_THRESHOLD_HOURS:
        return 0.2 + (debt - 1) * 0.3
    else:
        # Severe debt
        return min(1.0, 0.5 + (debt - SLEEP_DEBT_THRESHOLD_HOURS) * 0.2)


def calculate_energy_leak(leak_percentage: float) -> float:
    """
    Calculate energy leak score.
    Percentage is 0.0 to 1.0.
    Returns 0.0 to 1.0.
    """
    if leak_percentage <= 0.1:
        return 0.0
    elif leak_percentage <= ENERGY_LEAK_THRESHOLD:
        # Linear from 0 to 0.5
        return (leak_percentage - 0.1) / (ENERGY_LEAK_THRESHOLD - 0.1) * 0.5
    elif leak_percentage <= 0.5:
        return 0.5 + (leak_percentage - ENERGY_LEAK_THRESHOLD) / 0.2 * 0.3
    else:
        # High leak
        return min(1.0, 0.8 + (leak_percentage - 0.5) * 0.4)


def calculate_incoherence(alignment_ratio: float) -> float:
    """
    Calculate incoherence score.
    Alignment ratio is 0.0 to 1.0 (higher = more aligned).
    Returns 0.0 to 1.0 (higher = more incoherent).
    """
    # Inverse relationship
    if alignment_ratio >= 0.7:
        return 0.0
    elif alignment_ratio >= 0.5:
        return (0.7 - alignment_ratio) / 0.2 * 0.3
    elif alignment_ratio >= 0.3:
        return 0.3 + (0.5 - alignment_ratio) / 0.2 * 0.3
    else:
        return min(1.0, 0.6 + (0.3 - alignment_ratio) * 1.3)


def calculate_overall_score(scores: Dict[str, float], weights: Dict[str, float]) -> float:
    """
    Calculate weighted overall score.
    """
    total = 0.0
    weight_sum = 0.0
    
    for key, score in scores.items():
        weight = weights.get(key, 0.2)
        total += score * weight
        weight_sum += weight
    
    if weight_sum == 0:
        return 0.0
    
    return total / weight_sum


def normalize_score(value: float, min_val: float, max_val: float) -> float:
    """
    Normalize a value to 0.0-1.0 range.
    """
    if max_val == min_val:
        return 0.5
    
    normalized = (value - min_val) / (max_val - min_val)
    return max(0.0, min(1.0, normalized))
