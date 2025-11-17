"""Policy utilities for formatting and detection."""
from typing import List, Dict, Any

def format_policies_for_prompt(policies: List[Dict[str, Any]]) -> str:
    """Format policies into a string for LLM prompt.
    
    Args:
        policies: List of policy dictionaries
        
    Returns:
        Formatted policy string
    """
    if not policies:
        return "No policies specified."
    return "\n".join([
        f"{p['id']}: {p['description']} Forbidden: {p.get('forbidden_phrases', [])} Preferred: {p.get('preferred_pattern', '')} Verification: {p.get('requires_verification', False)}"
        for p in policies
    ])

def detect_forbidden_phrases(text: str, policies: List[Dict[str, Any]]) -> List[str]:
    """Detect forbidden phrases in text based on policies.
    
    Args:
        text: Text to check
        policies: List of policy dictionaries
        
    Returns:
        List of detected forbidden phrases
    """
    if not text or not policies:
        return []
    found = []
    text_lower = text.lower()
    for p in policies:
        for phrase in p.get('forbidden_phrases', []):
            if phrase and phrase.lower() in text_lower:
                found.append(phrase)
    return found
