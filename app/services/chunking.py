import re
from typing import List

def fixed_length_chunking(text: str, chunk_size: int = 500) -> List[str]:
    words = text.split()
    chunks = [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
    return chunks

def paragraph_chunking(text: str) -> List[str]:
    # Split by paragraph or new lines
    paragraphs = re.split(r'\n\s*\n', text)
    return [p.strip() for p in paragraphs if p.strip()]
