"""
System Constants
Thresholds, limits, and patterns.
"""

# Diagnosis thresholds
SLEEP_DEBT_THRESHOLD_HOURS: float = 2.0
DISPERSION_THRESHOLD: int = 5  # More than 5 active goals = dispersion
ENERGY_LEAK_THRESHOLD: float = 0.3  # 30% energy on non-priority items

# Scoring weights
WEIGHT_BOTTLENECK: float = 0.25
WEIGHT_DISPERSION: float = 0.20
WEIGHT_SLEEP_DEBT: float = 0.20
WEIGHT_ENERGY_LEAK: float = 0.15
WEIGHT_INCOHERENCE: float = 0.20

# Plan limits
MAX_SI_HOY_ITEMS: int = 3
MAX_NO_HOY_ITEMS: int = 5
MAX_RULE_LENGTH: int = 80

# Time blocks
MORNING_START: int = 6
MORNING_END: int = 12
AFTERNOON_START: int = 12
AFTERNOON_END: int = 18
EVENING_START: int = 18
EVENING_END: int = 22
NIGHT_START: int = 22
NIGHT_END: int = 6

# LLM retry
MAX_LLM_RETRIES: int = 3
LLM_RETRY_DELAY_SECONDS: float = 1.0

# Validation patterns
VALID_TIME_FORMAT: str = r"^\d{1,2}:\d{2}$"
VALID_DURATION_FORMAT: str = r"^\d+\s*(min|h|hora|horas|minutos)$"

# Response format
REQUIRED_PLAN_KEYS: list = ["no_hoy", "si_hoy", "horarios", "regla_clave"]
