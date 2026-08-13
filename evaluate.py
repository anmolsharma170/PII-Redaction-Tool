# pyrefly: ignore [missing-import]
import re
import spacy
from redactor import redact_text_content
from anonymizer import pii_map

# Define a representative sample prospectus text (similar to 1-2 pages of snippets)
EVAL_TEXT = """RED HERRING PROSPECTUS DRAFT - CONFIDENTIAL
Dated: August 13, 2026

This prospectus is prepared for the public offering of Acme Corp. The company's lead promoter is Jane Doe, who can be contacted at jane.doe@acmecorp.com or at +1 (555) 019-2834. The registered office is located at 100 Enterprise Way, Silicon Valley, California.

Key Personnel and Contacts:
1. Amit Sharma (Director) - amit.sharma@acmecorp.com, Phone: +91 98765 43210.
2. Priya Patel (CFO) - priya.patel@acmecorp.com.
3. John Smith (Independent Director) - john.smith@external-audit.com, SSN: 987-65-4321.

Financial transactions and auditing are handled through corporate credit card ending in 4111-2222-3333-4444. 
The servers hosting our prospectus information are located at IP address 192.168.1.1 and backup servers at 10.0.0.254.

Compliance and Legal:
As per Section 32 of the Companies Act, 2013, and SEBI regulations, all filings must be completed by November 30, 2026. The committee met on July 15, 2026, to approve these terms. 

For any inquiries, please contact our support department at support@acmecorp.com.
"""

# Ground Truth definition of PII elements present in the text:
# Format: (pii_value, pii_type)
GROUND_TRUTH = [
    # Dates
    ("August 13, 2026", "DATE"),
    ("November 30, 2026", "DATE"),
    ("July 15, 2026", "DATE"),
    # Organizations
    ("Acme Corp", "ORG"),
    # Persons
    ("Jane Doe", "PERSON"),
    ("Amit Sharma", "PERSON"),
    ("Priya Patel", "PERSON"),
    ("John Smith", "PERSON"),
    # Emails
    ("jane.doe@acmecorp.com", "EMAIL"),
    ("amit.sharma@acmecorp.com", "EMAIL"),
    ("priya.patel@acmecorp.com", "EMAIL"),
    ("john.smith@external-audit.com", "EMAIL"),
    ("support@acmecorp.com", "EMAIL"),
    # Phones
    ("+1 (555) 019-2834", "PHONE"),
    ("+91 98765 43210", "PHONE"),
    # Locations / Addresses
    ("100 Enterprise Way", "LOC"),
    ("Silicon Valley", "LOC"),
    ("California", "GPE"),
    # SSN
    ("987-65-4321", "SSN"),
    # Credit Card
    ("4111-2222-3333-4444", "CARD"),
    # IP Addresses
    ("192.168.1.1", "IP"),
    ("10.0.0.254", "IP")
]

def run_evaluation():
    print("Running Redactor on Evaluation Text...")
    redacted_text = redact_text_content(EVAL_TEXT)
    
    print("\n--- ORIGINAL TEXT ---")
    print(EVAL_TEXT)
    
    print("\n--- REDACTED TEXT ---")
    print(redacted_text)
    
    # Analyze the replacements using the global pii_map
    print("\n--- REPLACEMENT MAP GENERATED ---")
    for original, replacement in pii_map.items():
        print(f"'{original}' -> '{replacement}'")

    # Let's count TP, FP, FN
    # A True Positive (TP) is a ground truth PII element that was replaced.
    # A False Negative (FN) is a ground truth PII element that was NOT replaced.
    tp_list = []
    fn_list = []
    
    for val, ptype in GROUND_TRUTH:
        if val in pii_map:
            tp_list.append((val, ptype))
        else:
            fn_list.append((val, ptype))

    # A False Positive (FP) is a replacement that was made, but the original text is NOT in GROUND_TRUTH.
    # Note: We must exclude any substrings of other Ground Truth elements to avoid counting double replacements or parts of text.
    fp_list = []
    ground_truth_values = {gt[0] for gt in GROUND_TRUTH}
    
    for original in pii_map.keys():
        # Check if the original key itself is in ground truth
        if original not in ground_truth_values:
            # Also check if it's a subpart or just a random entity caught (e.g. "SEBI", "Companies Act, 2013", etc.)
            fp_list.append(original)

    # Let's count them
    tp = len(tp_list)
    fn = len(fn_list)
    fp = len(fp_list)

    print(f"\n--- EVALUATION METRICS BUCKETS ---")
    print(f"True Positives (TP) [{tp}]:")
    for item in tp_list:
        print(f"  - {item[0]} ({item[1]})")
        
    print(f"\nFalse Negatives (FN) [{fn}]:")
    for item in fn_list:
        print(f"  - {item[0]} ({item[1]})")
        
    print(f"\nFalse Positives (FP) [{fp}]:")
    for item in fp_list:
        print(f"  - {item}")

    # Calculate metrics
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    print(f"\n--- PERFORMANCE METRICS ---")
    print(f"Precision: {precision:.4f} ({precision * 100:.2f}%)")
    print(f"Recall:    {recall:.4f} ({recall * 100:.2f}%)")
    print(f"F1-Score:  {f1:.4f} ({f1 * 100:.2f}%)")

if __name__ == "__main__":
    run_evaluation()
