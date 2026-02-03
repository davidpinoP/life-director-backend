"""
Memory Service
User history and context persistence.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.db import crud


class MemoryService:
    """
    Manages user memory and context.
    Provides relevant history for decision making.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """
        Get complete user context for plan generation.
        """
        
        # Get onboarding data
        onboarding = await crud.get_user_onboarding(self.db, user_id)
        
        # Get recent plans
        recent_plans = await crud.get_recent_plans(self.db, user_id, days=7)
        
        # Get feedback history
        feedback_history = await crud.get_user_feedback_history(self.db, user_id, limit=30)
        
        # Calculate statistics
        stats = self._calculate_stats(recent_plans, feedback_history)
        
        return {
            "onboarding": self._serialize_onboarding(onboarding) if onboarding else None,
            "recent_plans": [self._serialize_plan(p) for p in recent_plans],
            "feedback_history": [self._serialize_feedback(f) for f in feedback_history],
            "stats": stats,
        }
    
    async def get_yesterday_completion(self, user_id: str) -> Optional[float]:
        """
        Get yesterday's plan completion rate.
        """
        
        plans = await crud.get_recent_plans(self.db, user_id, days=2)
        
        if not plans:
            return None
        
        # Find yesterday's plan
        yesterday = datetime.now().date() - timedelta(days=1)
        
        for plan in plans:
            if plan.date == yesterday:
                # Get feedback for this plan
                feedback_list = await crud.get_user_feedback_history(
                    self.db, user_id, limit=10
                )
                
                for fb in feedback_list:
                    if fb.plan_id == plan.id:
                        return fb.completion_rate
        
        return None
    
    def _calculate_stats(
        self,
        plans: List[Any],
        feedback: List[Any]
    ) -> Dict[str, Any]:
        """
        Calculate aggregate statistics.
        """
        
        if not feedback:
            return {
                "average_completion": 0.0,
                "total_plans": len(plans),
                "days_active": 0,
                "blocker_frequency": 0.0,
            }
        
        completion_rates = [f.completion_rate for f in feedback if f.completion_rate is not None]
        avg_completion = sum(completion_rates) / len(completion_rates) if completion_rates else 0.0
        
        blockers = sum(1 for f in feedback if f.had_blockers)
        blocker_frequency = blockers / len(feedback) if feedback else 0.0
        
        return {
            "average_completion": avg_completion,
            "total_plans": len(plans),
            "days_active": len(set(p.date for p in plans)),
            "blocker_frequency": blocker_frequency,
        }
    
    def _serialize_onboarding(self, onboarding: Any) -> Dict[str, Any]:
        """Serialize onboarding data."""
        return {
            "primary_goal": onboarding.primary_goal,
            "current_activities": onboarding.current_activities or [],
            "hours_work": onboarding.hours_work,
            "hours_sleep": onboarding.hours_sleep,
            "main_obstacle": onboarding.main_obstacle,
            "peak_energy_time": onboarding.peak_energy_time,
        }
    
    def _serialize_plan(self, plan: Any) -> Dict[str, Any]:
        """Serialize daily plan."""
        return {
            "id": plan.id,
            "date": str(plan.date),
            "no_hoy": plan.no_hoy,
            "si_hoy": plan.si_hoy,
            "horarios": plan.horarios,
            "regla_clave": plan.regla_clave,
        }
    
    def _serialize_feedback(self, feedback: Any) -> Dict[str, Any]:
        """Serialize feedback."""
        return {
            "plan_id": feedback.plan_id,
            "completion_rate": feedback.completion_rate,
            "had_blockers": feedback.had_blockers,
            "blocker_type": feedback.blocker_type,
            "energy_at_start": feedback.energy_at_start,
            "energy_at_end": feedback.energy_at_end,
            "sleep_hours": feedback.sleep_hours,
        }


async def get_memory_service(db: AsyncSession) -> MemoryService:
    """Factory function."""
    return MemoryService(db)
