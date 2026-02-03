"""
Tests for Diagnosis Service
"""

import pytest
from app.services.diagnosis_service import DiagnosisService, run_diagnosis


class TestDiagnosisService:
    """Tests for rule-based diagnosis."""
    
    def test_diagnosis_basic(self):
        """Test basic diagnosis with minimal data."""
        
        data = {
            "primary_goal": "Lanzar producto",
            "current_activities": [
                {"name": "Trabajo", "hours_per_week": 40, "aligned_with_goal": True, "priority": 9},
            ],
            "hours_work": 8,
            "hours_sleep": 7,
            "main_obstacle": None,
        }
        
        result = run_diagnosis(data)
        
        assert result.overall_score >= 0
        assert result.overall_score <= 1
        assert result.primary_bottleneck is not None
        assert result.priority_action is not None
    
    def test_diagnosis_overwork(self):
        """Test diagnosis detects overwork."""
        
        data = {
            "primary_goal": "Lanzar producto",
            "current_activities": [
                {"name": "Trabajo", "hours_per_week": 60, "aligned_with_goal": True, "priority": 9},
            ],
            "hours_work": 12,
            "hours_sleep": 5,
            "main_obstacle": "No tengo tiempo",
        }
        
        result = run_diagnosis(data)
        
        assert result.bottleneck_score > 0.3
        assert result.sleep_debt_hours > 0
    
    def test_diagnosis_dispersion(self):
        """Test diagnosis detects dispersion."""
        
        activities = [
            {"name": f"Activity {i}", "hours_per_week": 5, "aligned_with_goal": False, "priority": 5}
            for i in range(10)
        ]
        
        data = {
            "primary_goal": "Lanzar producto",
            "current_activities": activities,
            "hours_work": 8,
            "hours_sleep": 7,
            "main_obstacle": None,
        }
        
        result = run_diagnosis(data)
        
        assert result.is_dispersed is True
        assert result.dispersion_score > 0.5
    
    def test_diagnosis_sleep_debt(self):
        """Test sleep debt calculation."""
        
        data = {
            "primary_goal": "Lanzar producto",
            "current_activities": [],
            "hours_work": 8,
            "hours_sleep": 5,
            "main_obstacle": None,
        }
        
        result = run_diagnosis(data)
        
        assert result.sleep_debt_hours >= 2.5
        assert result.sleep_debt_score > 0.3
    
    def test_diagnosis_energy_leak(self):
        """Test energy leak detection."""
        
        data = {
            "primary_goal": "Lanzar producto",
            "current_activities": [
                {"name": "Trabajo", "hours_per_week": 40, "aligned_with_goal": True, "priority": 9},
                {"name": "Netflix", "hours_per_week": 20, "aligned_with_goal": False, "priority": 2},
                {"name": "Redes sociales", "hours_per_week": 15, "aligned_with_goal": False, "priority": 1},
            ],
            "hours_work": 8,
            "hours_sleep": 7,
            "main_obstacle": None,
        }
        
        result = run_diagnosis(data)
        
        assert result.energy_leak_percentage > 0.3
        assert len(result.energy_leak_sources) >= 2
    
    def test_diagnosis_incoherence(self):
        """Test incoherence detection."""
        
        data = {
            "primary_goal": "Perder peso",
            "current_activities": [
                {"name": "Trabajo", "hours_per_week": 50, "aligned_with_goal": False, "priority": 9},
                {"name": "Netflix", "hours_per_week": 20, "aligned_with_goal": False, "priority": 5},
                {"name": "Gaming", "hours_per_week": 10, "aligned_with_goal": False, "priority": 5},
            ],
            "hours_work": 10,
            "hours_sleep": 6,
            "main_obstacle": "No tengo motivación",
        }
        
        result = run_diagnosis(data)
        
        assert result.is_incoherent is True
        assert result.incoherence_score > 0.5
    
    def test_priority_action_generated(self):
        """Test priority action is always generated."""
        
        test_cases = [
            {"hours_work": 12, "hours_sleep": 5},
            {"hours_work": 8, "hours_sleep": 7},
            {"hours_work": 6, "hours_sleep": 8},
        ]
        
        for case in test_cases:
            data = {
                "primary_goal": "Test goal",
                "current_activities": [],
                **case,
                "main_obstacle": None,
            }
            
            result = run_diagnosis(data)
            
            assert result.priority_action is not None
            assert len(result.priority_action) > 0
