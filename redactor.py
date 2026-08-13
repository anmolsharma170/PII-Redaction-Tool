# pyrefly: ignore [missing-import]
import re
# pyrefly: ignore [missing-import]
import spacy
from anonymizer import get_fake_replacement

# Load spaCy's English model
nlp = spacy.load("en_core_web_sm")

# Blacklist of common non-PII terms that spaCy NER or regex commonly misidentifies
NON_PII_BLACKLIST = {
    "red herring", "prospectus", "red herring prospectus", "companies act", "companies act, 1956",
    "companies act, 2013", "sebi", "sebi regulations", "sebi icdr regulations", "brlm", "brlms",
    "bse", "nse", "roc", "pan", "din", "cfo", "ceo", "cs", "ip", "ssn", "alternate investment fund",
    "book building process", "mutual funds", "equity shares", "equity share", "key personnel",
    "key personnel and contacts", "the company", "our company", "board of directors", "board",
    "directors", "promoters", "promoter group", "promoter trusts", "demographic details", "client id",
    "rtas", "scsbs", "upi", "asba", "fema", "gst", "ebitda", "cagr", "roe", "roce", "audit committee",
    "statutory auditors", "bonus issue", "mufg", "icici securities", "nuvama", "kirtane & pandit",
    "trilegal", "hdfc bank", "sbi", "axis bank", "axis", "citi", "citibank", "indusind", "idbi",
    "state bank of india", "bajaj finance", "federal bank", "care ratings", "care report", "mca portal",
    "independent director", "executive director", "managing director", "joint managing director",
    "whole-time director", "company secretary", "compliance officer", "promoter selling shareholder",
    "promoter selling shareholders", "selling shareholders", "public offering", "fresh issue",
    "offer for sale", "total offer size", "securities", "exchange board", "exchange board of india",
    "securities and exchange board of india", "securities and exchange board", "securities contracts",
    "securities contracts (regulation) rules", "eligible", "eligibility", "share reservation",
    "qualified institutional buyers", "non-institutional investors", "retail individual investors",
    "retail portion", "anchor investor", "anchor investors", "mutual fund portion", "net qib portion"
}

# Words that should not start a name
INVALID_NAME_STARTERS = {
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
    "January", "February", "March", "April", "May", "June", "July", "August", "September",
    "October", "November", "December", "Dated", "This", "The", "Key", "Our", "As", "For", "In",
    "We", "He", "She", "They", "It", "A", "An", "Please", "Section", "Table", "Name", "Type"
}

def clean_entity_text(text: str) -> str:
    """Helper to strip trailing/leading punctuation and whitespace for clean mapping."""
    return text.strip(".,;:()\"' ")

def is_blacklisted(text: str) -> bool:
    """Checks if a term is in the blacklist (case-insensitive)."""
    normalized = text.lower().strip(".,;:()\"' ")
    if normalized in NON_PII_BLACKLIST:
        return True
    # If the text is an acronym (all caps) and short, check if it's in blacklist
    if text.isupper() and len(text) <= 5 and normalized in NON_PII_BLACKLIST:
        return True
    return False

def redact_text_content(text: str) -> str:
    """
    Redacts PII from text using a multi-phase entity extraction approach.
    All candidate PII elements are gathered from the original text, filtered,
    sorted by length (descending) to prevent substring replacement conflicts,
    and then replaced with consistent fake values.
    """
    if not text or not text.strip():
        return text

    # Set of unique (original_string, category) to redact
    pii_candidates = set()

    # --- Phase 1: Structured Regex Patterns ---
    regex_rules = {
        "EMAIL": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        # Matches standard US numbers and international/Indian format like +91 98765 43210
        "PHONE": r'(?:\+?\d{1,4}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\b\d{5}[-.\s]?\d{5}\b)',
        "IP": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
        "SSN": r'\b\d{3}-\d{2}-\d{4}\b',
        "CARD": r'\b(?:\d[ -]*?){13,16}\b'
    }

    for p_type, pattern in regex_rules.items():
        for m in re.finditer(pattern, text):
            match_str = m.group(0)
            cleaned = clean_entity_text(match_str)
            if cleaned and not is_blacklisted(cleaned):
                pii_candidates.add((match_str, p_type))

    # --- Phase 2: Custom Address Regex ---
    # Safe flat regex pattern matching numbers, street indicator keywords, and locations
    address_pattern = r'\b\d+[\w\s,\-\/]{2,30}?\b(?:Way|Road|Street|Avenue|Lane|Drive|Parkway|Business Centre|Village|Farms|Centre|Tower|Office)[\w\s,.\-\/]{2,60}?\b(?:Pune|Mumbai|Maharashtra|Bhopal|India|Bengaluru|Delhi|California|Silicon Valley)\b'
    for m in re.finditer(address_pattern, text):
        match_str = m.group(0)
        cleaned = clean_entity_text(match_str)
        if cleaned and not is_blacklisted(cleaned):
            pii_candidates.add((match_str, "LOC"))

    # --- Phase 3: spaCy NER ---
    doc = nlp(text)
    for ent in doc.ents:
        ent_text = ent.text
        cleaned_ent = clean_entity_text(ent_text)

        if not cleaned_ent or is_blacklisted(cleaned_ent):
            continue

        # Skip single 4-digit years tagged as DATE (e.g. 2013, 2025)
        if ent.label_ == "DATE" and cleaned_ent.isdigit() and len(cleaned_ent) == 4:
            continue

        if ent.label_ in ["PERSON", "ORG", "GPE", "LOC", "DATE"]:
            pii_candidates.add((ent_text, ent.label_))

    # --- Phase 4: Fallback Name Patterns (Capitalized & ALL CAPS names missed by NER) ---
    # 4.1 Capitalized Name fallback (e.g. Amit Sharma)
    name_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}\b'
    for m in re.finditer(name_pattern, text):
        match_str = m.group(0)
        cleaned = clean_entity_text(match_str)
        if cleaned and not is_blacklisted(cleaned):
            first_word = cleaned.split()[0]
            if first_word not in INVALID_NAME_STARTERS:
                pii_candidates.add((match_str, "PERSON"))

    # 4.2 ALL CAPS Name fallback (e.g. KUSHAL SUBBAYYA HEGDE)
    caps_name_pattern = r'\b[A-Z]{3,}\s+[A-Z]{3,}(?:\s+[A-Z]{3,})?\b'
    for m in re.finditer(caps_name_pattern, text):
        match_str = m.group(0)
        cleaned = clean_entity_text(match_str)
        if cleaned and not is_blacklisted(cleaned):
            first_word = cleaned.split()[0]
            if first_word not in INVALID_NAME_STARTERS and first_word.lower() not in NON_PII_BLACKLIST:
                pii_candidates.add((match_str, "PERSON"))

    # --- Phase 5: Apply Replacements ---
    # Sort candidates by length in descending order to avoid substring corruption
    sorted_candidates = sorted(list(pii_candidates), key=lambda x: len(x[0]), reverse=True)

    for original_str, category in sorted_candidates:
        # Check if the exact candidate string is still present in the text
        # (This prevents double replacement of substrings that were already replaced)
        if original_str in text:
            cleaned_str = clean_entity_text(original_str)
            fake_val = get_fake_replacement(cleaned_str, category)
            # Safely replace all occurrences in the text
            text = text.replace(original_str, fake_val)

    return text

if __name__ == "__main__":
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
