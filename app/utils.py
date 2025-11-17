"""Utility functions for text processing and cleanup."""
import re
from typing import Any


def clean_text(text: Any) -> str:
    """Clean text by removing UTF-8 artifacts and non-printable characters.
    
    Args:
        text: Input text to clean (can be any type)
        
    Returns:
        Cleaned text string
    """
    if not isinstance(text, str):
        return text
    
    # Remove non-UTF-8 and replace common artifacts
    text = text.encode('utf-8', errors='replace').decode('utf-8')
    
    # Replace common smart quote artifacts
    replacements = {
        'ΓÇÖ': "'",
        'ΓÇ£': '"',
        'ΓÇ¥': '"',
        'ΓÇæ': '-',
        '├óΓé¼ΓÇ¥': '—',
        '├óΓé¼╦£': "'",
        'Γé¼': '€'
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Remove any remaining non-printable chars (keep standard ASCII + common punctuation)
    text = re.sub(r'[^\x20-\x7E\u2018\u2019\u201C\u201D\u20AC\u2014]', '', text)
    
    return text
