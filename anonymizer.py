# pyrefly: ignore [missing-import]
from faker import Faker

# Global dictionary to track original-to-fake mappings
pii_map = {}
fake = Faker()

def get_fake_replacement(original_text: str, category: str) -> str:
    """
    Returns an existing fake replacement if it exists for the original text.
    Otherwise, generates a new consistent fake replacement based on the PII category.
    """
    # Check if we have already generated a replacement for this exact text
    if original_text in pii_map:
        return pii_map[original_text]

    # Generate fake replacement based on category
    category_upper = category.upper()
    
    if category_upper == "PERSON":
        replacement = fake.name()
    elif category_upper == "EMAIL":
        replacement = fake.email()
    elif category_upper == "PHONE":
        replacement = fake.phone_number()
    elif category_upper == "ORG":
        replacement = fake.company()
    elif category_upper in ["GPE", "LOC", "ADDRESS"]:
        # Address generator often contains newlines, replace them for in-line text consistency
        replacement = fake.address().replace("\n", ", ")
    elif category_upper == "SSN":
        replacement = fake.ssn()
    elif category_upper == "CARD":
        replacement = fake.credit_card_number()
    elif category_upper == "DATE":
        replacement = fake.date()
    elif category_upper == "IP":
        replacement = fake.ipv4()
    else:
        replacement = f"[REDACTED_{category_upper}]"

    # Save to mapping to ensure consistency in future lookups
    pii_map[original_text] = replacement
    return replacement

if __name__ == "__main__":
    # Quick verification to test consistency
    print("Testing PERSON category mapping:")
    p1 = get_fake_replacement("Rashi Patil", "PERSON")
    p2 = get_fake_replacement("Rashi Patil", "PERSON")
    p3 = get_fake_replacement("Amit Sharma", "PERSON")
    
    print(f"Rashi Patil -> {p1}")
    print(f"Rashi Patil -> {p2} (Should match)")
    print(f"Amit Sharma -> {p3} (Should be different)")
    
    assert p1 == p2, "Consistency check failed!"
    assert p1 != p3, "Uniqueness check failed!"
    print("Consistency tests passed successfully!")
