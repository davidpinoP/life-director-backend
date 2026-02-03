"""
Decision Engine
LLM-powered decision making.
Strict output format. No conversation. Just orders.
"""

from typing import Dict, Any, List, Tuple, Optional

from app.services.llm_client import get_llm_client, LLMResponseError
from app.services.diagnosis_service import DiagnosisResult
from app.core.authority import apply_authority
from app.core.constants import REQUIRED_PLAN_KEYS, MAX_SI_HOY_ITEMS, MAX_NO_HOY_ITEMS
from app.utils.time import get_current_hour, format_time


class DecisionEngine:
    """
    Generates daily plans using LLM.
    - Enforces strict output format
    - Applies authority filter
    - Regenerates on invalid response
    """
    
    def __init__(self):
        self.llm = get_llm_client()
        self.system_prompt = self._load_prompt("director_base.txt")
        self.order_prompt = self._load_prompt("daily_order.txt")
    
    def _load_prompt(self, filename: str) -> str:
        """Load prompt from file."""
        import os
        prompt_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "prompts"
        )
        filepath = os.path.join(prompt_dir, filename)
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            # Return embedded fallback
            return self._get_fallback_prompt(filename)
    
    def _get_fallback_prompt(self, filename: str) -> str:
        """Fallback prompts if files not found."""
        
        if filename == "director_base.txt":
            return """Eres un sistema de decisión. No conversas. No motivas. No explicas.
Emites órdenes directas y cortas.
Respondes SOLO en JSON con este formato exacto:
{
  "no_hoy": ["item1", "item2"],
  "si_hoy": ["item1", "item2"],
  "horarios": {"HH:MM": "actividad"},
  "regla_clave": "Una frase corta imperativa"
}
Sin emojis. Sin explicaciones. Solo el JSON."""

        elif filename == "daily_order.txt":
            return """Genera el plan del día.
CONTEXTO:
{context}

DIAGNÓSTICO:
{diagnosis}

RESPONDE SOLO CON EL JSON. NADA MÁS."""

        return ""
    
    async def generate_daily_plan(
        self,
        diagnosis: DiagnosisResult,
        context: Dict[str, Any],
        user_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Generate daily plan based on diagnosis.
        Returns filtered, validated plan.
        """
        
        # Build context string
        context_str = self._build_context(context, user_history)
        diagnosis_str = self._build_diagnosis_summary(diagnosis)
        
        # Format prompt
        user_prompt = self.order_prompt.format(
            context=context_str,
            diagnosis=diagnosis_str
        )
        
        # Generate with validation
        result = await self.llm.generate_with_retry(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            validate_fn=self._validate_plan_format
        )
        
        # Apply authority filter
        plan = apply_authority(result["data"])
        
        # Enforce limits
        plan = self._enforce_limits(plan)
        
        return {
            "plan": plan,
            "tokens_used": result["tokens"]
        }
    
    def _build_context(
        self,
        context: Dict[str, Any],
        history: Optional[List[Dict]] = None
    ) -> str:
        """Build context string for prompt."""
        
        parts = []
        
        if context.get("available_hours"):
            parts.append(f"Horas disponibles: {context['available_hours']}")
        
        if context.get("energy_level"):
            parts.append(f"Nivel energía: {context['energy_level']}/10")
        
        if context.get("existing_commitments"):
            parts.append(f"Compromisos: {', '.join(context['existing_commitments'])}")
        
        if context.get("yesterday_completion"):
            pct = int(context["yesterday_completion"] * 100)
            parts.append(f"Cumplimiento ayer: {pct}%")
        
        current_hour = get_current_hour()
        parts.append(f"Hora actual: {format_time(current_hour)}")
        
        if history:
            # Add recent pattern summary
            avg_completion = sum(h.get("completion_rate", 0) for h in history) / len(history)
            parts.append(f"Media cumplimiento reciente: {int(avg_completion * 100)}%")
        
        return "\n".join(parts) if parts else "Sin contexto adicional"
    
    def _build_diagnosis_summary(self, diagnosis: DiagnosisResult) -> str:
        """Build diagnosis summary for prompt."""
        
        lines = []
        
        lines.append(f"Cuello de botella: {diagnosis.primary_bottleneck}")
        
        if diagnosis.is_dispersed:
            lines.append(f"Dispersión: {diagnosis.active_goals_count} actividades activas")
        
        if diagnosis.sleep_debt_hours > 0:
            lines.append(f"Deuda de sueño: {diagnosis.sleep_debt_hours}h")
        
        if diagnosis.energy_leak_percentage > 0.1:
            pct = int(diagnosis.energy_leak_percentage * 100)
            lines.append(f"Fuga de energía: {pct}%")
        
        if diagnosis.is_incoherent:
            lines.append("Incoherencia objetivo/acciones detectada")
        
        lines.append(f"Acción prioritaria: {diagnosis.priority_action}")
        
        return "\n".join(lines)
    
    def _validate_plan_format(self, data: Dict) -> Tuple[bool, Optional[str]]:
        """
        Validate plan has required format.
        Returns (is_valid, error_message).
        """
        
        if not isinstance(data, dict):
            return False, "Response is not a dictionary"
        
        # Check required keys
        for key in REQUIRED_PLAN_KEYS:
            if key not in data:
                return False, f"Missing required key: {key}"
        
        # Validate types
        if not isinstance(data["no_hoy"], list):
            return False, "no_hoy must be a list"
        
        if not isinstance(data["si_hoy"], list):
            return False, "si_hoy must be a list"
        
        if not isinstance(data["horarios"], dict):
            return False, "horarios must be a dictionary"
        
        if not isinstance(data["regla_clave"], str):
            return False, "regla_clave must be a string"
        
        # Validate content
        if len(data["si_hoy"]) == 0:
            return False, "si_hoy cannot be empty"
        
        if not data["regla_clave"].strip():
            return False, "regla_clave cannot be empty"
        
        return True, None
    
    def _enforce_limits(self, plan: Dict) -> Dict:
        """Enforce item count limits."""
        
        if len(plan.get("no_hoy", [])) > MAX_NO_HOY_ITEMS:
            plan["no_hoy"] = plan["no_hoy"][:MAX_NO_HOY_ITEMS]
        
        if len(plan.get("si_hoy", [])) > MAX_SI_HOY_ITEMS:
            plan["si_hoy"] = plan["si_hoy"][:MAX_SI_HOY_ITEMS]
        
        return plan


# Singleton
_engine: Optional[DecisionEngine] = None


def get_decision_engine() -> DecisionEngine:
    """Get or create decision engine instance."""
    global _engine
    if _engine is None:
        _engine = DecisionEngine()
    return _engine


async def generate_plan(
    diagnosis: DiagnosisResult,
    context: Dict[str, Any],
    history: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """Convenience function to generate plan."""
    engine = get_decision_engine()
    return await engine.generate_daily_plan(diagnosis, context, history)
