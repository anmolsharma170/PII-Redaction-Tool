# pyrefly: ignore [missing-import]
import re
import spacy
from anonymizer import get_fake_replacement

# Load spaCy's English model
nlp = spacy.load("en_core_web_sm")

def redact_text_content(text: str) -> str:
    """
    Redacts PII from text in two phases:
    1. Regex for structured patterns (emails, phone numbers, IPs, SSNs, credit cards).
    2. spaCy NER for unstructured contextual entities (names, organizations, locations, dates).
    """
    if not text or not text.strip():
        return text

    # --- Phase 1: Regex Redaction ---
    # We use non-capturing groups (?:...) to ensure we get the full matches.
    regex_rules = {
        "EMAIL": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        "PHONE": r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        "IP": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
        "SSN": r'\b\d{3}-\d{2}-\d{4}\b',
        "CARD": r'\b(?:\d[ -]*?){13,16}\b'
    }

    for p_type, pattern in regex_rules.items():
        # Use finditer to get full matches, avoiding issues with capturing groups
        matches = set(m.group(0) for m in re.finditer(pattern, text))
        for match_str in matches:
            if match_str:
                fake_val = get_fake_replacement(match_str, p_type)
                text = text.replace(match_str, fake_val)

    # --- Phase 2: spaCy NER Redaction ---
    doc = nlp(text)
    # Iterate backwards so string replacement indices don't shift
    for ent in reversed(doc.ents):
        if ent.label_ in ["PERSON", "ORG", "GPE", "LOC", "DATE"]:
            original_str = ent.text
            fake_val = get_fake_replacement(original_str, ent.label_)
            start, end = ent.start_char, ent.end_char
            text = text[:start] + fake_val + text[end:]

    return text

if __name__ == "__main__":
    # Sample text containing structured and unstructured PII
    sample_text = (
        "Hello, my name is John Doe and I work at Google. "
        "You can contact me at john.doe@example.com or call +1 (555) 123-4567. "
        "I live at 1600 Amphitheatre Parkway, Mountain View, CA. "
        "My SSN is 123-45-6789 and I was born on January 1, 1990."
    )
    
    print("Original Text:")
    print(sample_text)
    print("\nRedacted Text:")
    redacted = redact_text_content(sample_text)
    print(redacted)
