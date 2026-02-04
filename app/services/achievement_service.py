"""
Achievement Service
Handles generation and progress tracking for monthly milestones.
"""

import os
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.llm_client import get_llm_client
from app.db import crud
from app.models.achievement import Achievement


class AchievementService:
    """
    Manages user achievements/milestones.
    - Generates 6-month roadmap using LLM.
    - Calculates progress based on daily completion rates.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = get_llm_client()
        self.prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts",
            "achievement_generator.txt"
        )

    async def generate_user_roadmap(self, user_id: str, primary_goal: str) -> List[Achievement]:
        """
        Generate a 6-month roadmap for a new user.
        """
        # Load prompt
        try:
            with open(self.prompt_path, "r", encoding="utf-8") as f:
                prompt_template = f.read()
        except FileNotFoundError:
            # Fallback simple prompt
            prompt_template = "Generate a 6-month roadmap for goal: {primary_goal}. JSON format: {{'achievements': [{{'month': 1, 'title': '...', 'description': '...'}}]}}"

        system_prompt = "You are a strategic life coach. Output ONLY JSON."
        user_prompt = prompt_template.replace("{primary_goal}", primary_goal)

        # Call LLM
        result = await self.llm.generate_with_retry(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            validate_fn=self._validate_roadmap_format
        )

        achievements_data = result["data"]["achievements"]
        
        # Store in DB
        return await crud.create_achievements_batch(self.db, user_id, achievements_data)

    async def update_active_achievement_progress(self, user_id: str, daily_completion_rate: float):
        """
        Update the progress of the currently active achievement.
        Each day contributes (1/30)th of the progress multiplied by completion rate.
        Assuming a 30-day month.
        """
        active_achievement = await crud.get_active_achievement(self.db, user_id)
        
        if not active_achievement:
            return None
            
        # Progress calculation:
        # If user completes 100% of tasks, they get +3.33% progress (for 30 days)
        # We cap progress at 100.
        DAILY_WEIGHT = 100.0 / 30.0 
        added_progress = daily_completion_rate * DAILY_WEIGHT
        
        new_progress = active_achievement.progress + added_progress
        
        return await crud.update_achievement_progress(
            self.db, 
            active_achievement.id, 
            new_progress
        )

    def _validate_roadmap_format(self, data: Dict) -> tuple[bool, Optional[str]]:
        """Validate LLM output format."""
        if not isinstance(data, dict) or "achievements" not in data:
            return False, "Missing 'achievements' key"
        
        items = data["achievements"]
        if not isinstance(items, list) or len(items) != 6:
            return False, f"Expected 6 achievements, got {len(items) if isinstance(items, list) else 'none'}"
            
        for item in items:
            if not all(k in item for k in ("month", "title", "description")):
                return False, f"Missing keys in item: {item}"
        
        return True, None
