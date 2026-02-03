"""
Elimination Engine
Reduces options. Removes non-essential activities.
"""

from typing import List, Dict, Any


class EliminationEngine:
    """
    Decides what to eliminate.
    Core principle: Less is more.
    """
    
    # Categories that are often unnecessary
    ELIMINATION_CANDIDATES = [
        "redes sociales",
        "social media",
        "netflix",
        "streaming",
        "videojuegos",
        "gaming",
        "reuniones",
        "meetings",
        "noticias",
        "news",
        "email",
        "correo",
    ]
    
    # Never eliminate these
    PROTECTED_ACTIVITIES = [
        "sueño",
        "sleep",
        "dormir",
        "comer",
        "eat",
        "ejercicio",
        "exercise",
        "trabajo principal",
        "main work",
    ]
    
    @classmethod
    def evaluate_for_elimination(
        cls,
        activities: List[Dict[str, Any]],
        primary_goal: str
    ) -> List[Dict[str, Any]]:
        """
        Evaluate each activity for potential elimination.
        Returns list with elimination_score added.
        """
        
        evaluated = []
        
        for activity in activities:
            name = activity.get("name", "").lower()
            hours = activity.get("hours_per_week", 0)
            aligned = activity.get("aligned_with_goal", False)
            priority = activity.get("priority", 5)
            
            # Calculate elimination score (higher = should eliminate)
            score = cls._calculate_elimination_score(
                name, hours, aligned, priority
            )
            
            evaluated.append({
                **activity,
                "elimination_score": score,
                "should_eliminate": score > 0.6
            })
        
        # Sort by elimination score (highest first)
        evaluated.sort(key=lambda x: x["elimination_score"], reverse=True)
        
        return evaluated
    
    @classmethod
    def _calculate_elimination_score(
        cls,
        name: str,
        hours: float,
        aligned: bool,
        priority: int
    ) -> float:
        """
        Calculate how likely an activity should be eliminated.
        Score 0.0 to 1.0.
        """
        
        score = 0.0
        
        # Check if protected
        for protected in cls.PROTECTED_ACTIVITIES:
            if protected in name:
                return 0.0  # Never eliminate
        
        # Check if common elimination candidate
        for candidate in cls.ELIMINATION_CANDIDATES:
            if candidate in name:
                score += 0.4
                break
        
        # Not aligned with goal
        if not aligned:
            score += 0.3
        
        # Low priority
        if priority < 5:
            score += 0.2
        
        # High time investment without alignment
        if hours > 5 and not aligned:
            score += 0.2
        
        return min(1.0, score)
    
    @classmethod
    def get_elimination_list(
        cls,
        activities: List[Dict[str, Any]],
        primary_goal: str,
        max_items: int = 5
    ) -> List[str]:
        """
        Get list of activities to eliminate.
        Returns just the names.
        """
        
        evaluated = cls.evaluate_for_elimination(activities, primary_goal)
        
        to_eliminate = [
            a["name"] for a in evaluated 
            if a.get("should_eliminate", False)
        ]
        
        return to_eliminate[:max_items]
    
    @classmethod
    def reduce_to_essentials(
        cls,
        items: List[str],
        max_count: int = 3
    ) -> List[str]:
        """
        Reduce any list to essential items only.
        Keeps first N items (assumes already prioritized).
        """
        return items[:max_count]


def eliminate(
    activities: List[Dict[str, Any]], 
    goal: str
) -> List[str]:
    """Convenience function."""
    return EliminationEngine.get_elimination_list(activities, goal)
