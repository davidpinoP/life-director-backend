"""
Report Service
Handles LLM generation for Daily Reports and Post-Mortems.
"""

import os
import json
from typing import Dict, Any, Optional

from app.services.llm_client import get_llm_client

class ReportService:
    """
    Service for generating Director responses to user reports.
    """
    
    def __init__(self):
        self.llm = get_llm_client()
        self.prompts_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts"
        )
        
    def _load_prompt(self, filename: str) -> str:
        path = os.path.join(self.prompts_dir, filename)
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    async def analyze_daily_report(self, report_content: str, primary_goal: str) -> str:
        """
        Analyze daily report and return decision.
        Returns the decision string directly.
        """
        prompt_template = self._load_prompt("report_daily.txt")
        
        user_prompt = prompt_template.replace("{report_content}", report_content)\
                                     .replace("{primary_goal}", primary_goal)
        
        system_prompt = "You are the Life Director. DECIDE. JSON output."
        
        result = await self.llm.generate_with_retry(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            validate_fn=self._validate_daily_decision
        )
        
        return result["data"]["decision"]

    async def analyze_post_mortem(
        self, 
        content_good: str, 
        content_bad: str, 
        content_delusion: str, 
        primary_goal: str
    ) -> Dict[str, str]:
        """
        Analyze post-mortem and return structured response.
        Returns dict with keys: adjustments, cuts, rules.
        """
        prompt_template = self._load_prompt("report_post_mortem.txt")
        
        user_prompt = prompt_template.replace("{content_good}", content_good)\
                                     .replace("{content_bad}", content_bad)\
                                     .replace("{content_delusion}", content_delusion)\
                                     .replace("{primary_goal}", primary_goal)
        
        system_prompt = "You are the Life Director. Post-Mortem Analysis. JSON output."
        
        result = await self.llm.generate_with_retry(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            validate_fn=self._validate_post_mortem
        )
        
        return result["data"]

    def _validate_daily_decision(self, data: Dict) -> tuple[bool, Optional[str]]:
        if not isinstance(data, dict) or "decision" not in data:
            return False, "Missing 'decision' key"
        return True, None

    def _validate_post_mortem(self, data: Dict) -> tuple[bool, Optional[str]]:
        required = ["adjustments", "cuts", "rules"]
        if not all(k in data for k in required):
            return False, f"Missing keys. Required: {required}"
        return True, None
