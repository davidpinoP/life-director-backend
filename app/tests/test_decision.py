"""
Tests for Decision Engine
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.decision_engine import DecisionEngine, get_decision_engine
from app.services.diagnosis_service import DiagnosisResult
from app.core.authority import AuthorityFilter


class TestDecisionEngine:
    """Tests for decision engine."""
    
    def test_validate_plan_format_valid(self):
        """Test validation of valid plan format."""
        
        engine = DecisionEngine()
        
        valid_plan = {
            "no_hoy": ["Redes sociales", "Netflix"],
            "si_hoy": ["Trabajo profundo", "Ejercicio"],
            "horarios": {"07:00": "Despertar", "22:30": "Cama"},
            "regla_clave": "Hoy no entrenas"
        }
        
        is_valid, error = engine._validate_plan_format(valid_plan)
        
        assert is_valid is True
        assert error is None
    
    def test_validate_plan_format_missing_key(self):
        """Test validation fails on missing key."""
        
        engine = DecisionEngine()
        
        invalid_plan = {
            "no_hoy": [],
            "si_hoy": ["Trabajo"],
            # Missing horarios and regla_clave
        }
        
        is_valid, error = engine._validate_plan_format(invalid_plan)
        
        assert is_valid is False
        assert "Missing required key" in error
    
    def test_validate_plan_format_empty_si_hoy(self):
        """Test validation fails on empty si_hoy."""
        
        engine = DecisionEngine()
        
        invalid_plan = {
            "no_hoy": ["Netflix"],
            "si_hoy": [],  # Empty
            "horarios": {"07:00": "Despertar"},
            "regla_clave": "Test"
        }
        
        is_valid, error = engine._validate_plan_format(invalid_plan)
        
        assert is_valid is False
        assert "si_hoy cannot be empty" in error
    
    def test_enforce_limits(self):
        """Test limits are enforced."""
        
        engine = DecisionEngine()
        
        plan = {
            "no_hoy": ["1", "2", "3", "4", "5", "6", "7"],  # Over limit
            "si_hoy": ["1", "2", "3", "4", "5"],  # Over limit
            "horarios": {},
            "regla_clave": "Test"
        }
        
        result = engine._enforce_limits(plan)
        
        assert len(result["no_hoy"]) <= 5
        assert len(result["si_hoy"]) <= 3


class TestAuthorityFilter:
    """Tests for authority filter."""
    
    def test_filter_text_removes_soft_words(self):
        """Test soft words are removed."""
        
        text = "Tal vez podrías considerar descansar un poco"
        result = AuthorityFilter.filter_text(text)
        
        assert "tal vez" not in result.lower()
        assert "podrías" not in result.lower()
        assert "considerar" not in result.lower()
    
    def test_filter_text_removes_emotional_language(self):
        """Test emotional language is removed."""
        
        text = "Te entiendo, es normal sentirse así. Tú puedes lograrlo."
        result = AuthorityFilter.filter_text(text)
        
        assert "te entiendo" not in result.lower()
        assert "es normal" not in result.lower()
        assert "tú puedes" not in result.lower()
    
    def test_filter_list(self):
        """Test list filtering."""
        
        items = [
            "Tal vez deberías descansar",
            "Trabaja 90 minutos",
            "Podrías considerar ejercitarte",
        ]
        
        result = AuthorityFilter.filter_list(items)
        
        assert len(result) == 3
        for item in result:
            assert "tal vez" not in item.lower()
            assert "podrías" not in item.lower()
    
    def test_filter_daily_plan(self):
        """Test daily plan filtering."""
        
        plan = {
            "no_hoy": ["Tal vez las redes sociales", "Netflix si quieres"],
            "si_hoy": ["Podrías trabajar", "Intenta ejercitarte"],
            "horarios": {"07:00": "Tal vez despertar"},
            "regla_clave": "Te sugiero que descanses"
        }
        
        result = AuthorityFilter.filter_daily_plan(plan)
        
        assert "tal vez" not in str(result).lower()
        assert "podrías" not in str(result).lower()
        assert "te sugiero" not in str(result).lower()
    
    def test_shorten(self):
        """Test text shortening."""
        
        long_text = "Esta es una frase muy larga que debería ser acortada. Tiene más de cien caracteres para probar la función de acortar."
        
        result = AuthorityFilter.shorten(long_text, max_length=50)
        
        assert len(result) <= 51  # +1 for potential period
    
    def test_clean_text(self):
        """Test text cleanup."""
        
        messy_text = "  Multiple   spaces   and  weird    punctuation.."
        
        result = AuthorityFilter._clean_text(messy_text)
        
        assert "   " not in result  # No triple spaces
        assert ".." not in result  # No double periods


class TestIntegration:
    """Integration tests."""
    
    def test_diagnosis_to_context(self):
        """Test diagnosis result can be used for context building."""
        
        diagnosis = DiagnosisResult(
            bottleneck_score=0.5,
            dispersion_score=0.3,
            sleep_debt_score=0.4,
            energy_leak_score=0.2,
            incoherence_score=0.1,
            overall_score=0.3,
            primary_bottleneck="overwork",
            bottleneck_details="Exceso de trabajo",
            is_dispersed=False,
            active_goals_count=3,
            sleep_debt_hours=2.0,
            energy_leak_percentage=0.15,
            energy_leak_sources=["Netflix"],
            is_incoherent=False,
            incoherence_details=None,
            priority_action="Reduce horas de trabajo"
        )
        
        engine = DecisionEngine()
        summary = engine._build_diagnosis_summary(diagnosis)
        
        assert "overwork" in summary
        assert "Reduce horas" in summary
