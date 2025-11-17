from typing import List

def format_policies_for_prompt(policies: List[dict]) -> str:
    return "\n".join([
        f"{p['id']}: {p['description']} Forbidden: {p.get('forbidden_phrases', [])} Preferred: {p.get('preferred_pattern', '')} Verification: {p.get('requires_verification', False)}"
        for p in policies
    ])

def detect_forbidden_phrases(text: str, policies: List[dict]) -> List[str]:
    found = []
    for p in policies:
        for phrase in p.get('forbidden_phrases', []):
            if phrase and phrase.lower() in text.lower():
                found.append(phrase)
    return found
