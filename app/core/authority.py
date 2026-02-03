"""
Authority Filter - Core Language Processing
Converts soft language to direct orders.
No suggestions. No explanations. Commands only.
"""

import re
from typing import List, Dict, Any


class AuthorityFilter:
    """
    Transforms LLM output into authoritative language.
    - Shortens phrases
    - Removes soft words
    - Converts suggestions to commands
    """
    
    # Words to eliminate completely
    ELIMINATE_WORDS: List[str] = [
        "tal vez",
        "quizás",
        "podrías",
        "considera",
        "intenta",
        "prueba",
        "te sugiero",
        "te recomiendo",
        "sería bueno",
        "sería ideal",
        "podría ser",
        "me parece",
        "creo que",
        "pienso que",
        "en mi opinión",
        "personalmente",
        "si quieres",
        "si te apetece",
        "cuando puedas",
        "un poco",
        "algo de",
        "bastante",
        "más o menos",
        "aproximadamente",
        "idealmente",
        "preferiblemente",
    ]
    
    # Soft phrases to replace with direct commands
    REPLACEMENTS: Dict[str, str] = {
        "podrías hacer": "haz",
        "deberías": "haz",
        "te aconsejo": "",
        "mi sugerencia es": "",
        "lo mejor sería": "",
        "sería conveniente": "",
        "te invito a": "",
        "piensa en": "",
        "reflexiona sobre": "",
        "no olvides que": "",
        "recuerda que": "",
        "ten en cuenta que": "",
        "es importante que": "",
        "procura": "",
        "trata de": "",
        "intenta": "",
        "considera": "",
    }
    
    # Filler phrases to remove
    FILLERS: List[str] = [
        "como ya sabes",
        "como mencioné",
        "dicho esto",
        "sin embargo",
        "no obstante",
        "por otro lado",
        "en cualquier caso",
        "de todas formas",
        "en definitiva",
        "básicamente",
        "fundamentalmente",
        "esencialmente",
    ]
    
    # Emotional/therapeutic language to eliminate
    EMOTIONAL_LANGUAGE: List[str] = [
        "te entiendo",
        "es normal",
        "no te preocupes",
        "tranquilo",
        "no pasa nada",
        "es comprensible",
        "puedo imaginar",
        "me imagino",
        "sé que es difícil",
        "ánimo",
        "tú puedes",
        "confío en ti",
        "lo vas a lograr",
        "éxito",
        "suerte",
    ]
    
    @classmethod
    def filter_text(cls, text: str) -> str:
        """
        Apply all filters to convert text to authoritative language.
        """
        if not text:
            return text
            
        result = text
        
        # Remove emotional language
        for phrase in cls.EMOTIONAL_LANGUAGE:
            result = re.sub(
                rf'\b{re.escape(phrase)}\b[.,!?]*\s*',
                '',
                result,
                flags=re.IGNORECASE
            )
        
        # Apply replacements
        for soft, direct in cls.REPLACEMENTS.items():
            result = re.sub(
                rf'\b{re.escape(soft)}\b',
                direct,
                result,
                flags=re.IGNORECASE
            )
        
        # Remove soft words
        for word in cls.ELIMINATE_WORDS:
            result = re.sub(
                rf'\b{re.escape(word)}\b\s*',
                '',
                result,
                flags=re.IGNORECASE
            )
        
        # Remove fillers
        for filler in cls.FILLERS:
            result = re.sub(
                rf'\b{re.escape(filler)}\b[.,]*\s*',
                '',
                result,
                flags=re.IGNORECASE
            )
        
        # Clean up
        result = cls._clean_text(result)
        
        return result
    
    @classmethod
    def filter_list(cls, items: List[str]) -> List[str]:
        """Filter a list of strings."""
        return [cls.filter_text(item) for item in items if item.strip()]
    
    @classmethod
    def filter_daily_plan(cls, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter a complete daily plan response.
        Ensures all text fields are authoritative.
        """
        filtered = {}
        
        if "no_hoy" in plan:
            filtered["no_hoy"] = cls.filter_list(plan["no_hoy"])
            
        if "si_hoy" in plan:
            filtered["si_hoy"] = cls.filter_list(plan["si_hoy"])
            
        if "horarios" in plan:
            filtered["horarios"] = {
                k: cls.filter_text(v) 
                for k, v in plan["horarios"].items()
            }
            
        if "regla_clave" in plan:
            filtered["regla_clave"] = cls.filter_text(plan["regla_clave"])
        
        return filtered
    
    @classmethod
    def _clean_text(cls, text: str) -> str:
        """
        Clean up text after filtering.
        - Remove double spaces
        - Remove empty parentheses
        - Fix punctuation
        - Trim
        """
        # Multiple spaces to single
        result = re.sub(r'\s+', ' ', text)
        
        # Remove empty parentheses/brackets
        result = re.sub(r'\(\s*\)', '', result)
        result = re.sub(r'\[\s*\]', '', result)
        
        # Fix double punctuation
        result = re.sub(r'([.,!?])\s*\1+', r'\1', result)
        
        # Remove leading punctuation
        result = re.sub(r'^\s*[.,]\s*', '', result)
        
        # Fix spacing around punctuation
        result = re.sub(r'\s+([.,!?])', r'\1', result)
        
        return result.strip()
    
    @classmethod
    def shorten(cls, text: str, max_length: int = 100) -> str:
        """
        Shorten text to maximum length.
        Cuts at sentence boundary if possible.
        """
        if not text or len(text) <= max_length:
            return text
            
        # Try to cut at sentence end
        truncated = text[:max_length]
        last_period = truncated.rfind('.')
        
        if last_period > max_length * 0.5:
            return truncated[:last_period + 1]
        
        # Cut at word boundary
        last_space = truncated.rfind(' ')
        if last_space > 0:
            return truncated[:last_space] + '.'
            
        return truncated + '.'


# Convenience function
def apply_authority(data: Any) -> Any:
    """
    Apply authority filter to any data structure.
    """
    if isinstance(data, str):
        return AuthorityFilter.filter_text(data)
    elif isinstance(data, list):
        return AuthorityFilter.filter_list(data)
    elif isinstance(data, dict):
        return AuthorityFilter.filter_daily_plan(data)
    return data
