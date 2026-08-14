# Evaluation Strategy and Metrics Report

This document outlines the evaluation strategy, dataset, metrics, and performance analysis of the PII Redaction Tool.

---

## 1. Evaluation Strategy Overview

To ensure the PII Redaction Tool successfully anonymizes sensitive data while preserving the structure and readability of Word documents (`.docx`), a standardized evaluation framework has been implemented. 

The evaluation strategy assesses:
1. **Anonymization Success (Recall):** Ensuring that sensitive PII elements (Names, Emails, Phone numbers, Addresses, SSNs, Credit Cards, IP addresses, Dates) are completely redacted and replaced with fake equivalents.
2. **Context Preservation (Precision):** Minimizing "over-redaction" (False Positives) where standard legal terms, headings, or non-PII terms are incorrectly anonymized.
3. **Consistency:** Guaranteeing that identical original PII elements map to the identical fake values throughout the document.

---

## 2. Evaluation Dataset & Ground Truth

The tool's performance is measured using a representative sample prospectus text (`EVAL_TEXT` in `evaluate.py`) containing **22 hand-annotated Ground Truth PII instances**:

| Entity Type | Ground Truth Value | Category |
| :--- | :--- | :--- |
| **DATE** | August 13, 2026 | Date |
| **DATE** | November 30, 2026 | Date |
| **DATE** | July 15, 2026 | Date |
| **ORG** | Acme Corp | Organization |
| **PERSON** | Jane Doe | Person / Name |
| **PERSON** | Amit Sharma | Person / Name |
| **PERSON** | Priya Patel | Person / Name |
| **PERSON** | John Smith | Person / Name |
| **EMAIL** | jane.doe@acmecorp.com | Email |
| **EMAIL** | amit.sharma@acmecorp.com | Email |
| **EMAIL** | priya.patel@acmecorp.com | Email |
| **EMAIL** | john.smith@external-audit.com | Email |
| **EMAIL** | support@acmecorp.com | Email |
| **PHONE** | +1 (555) 019-2834 | Phone Number |
| **PHONE** | +91 98765 43210 | Phone Number |
| **LOC** | 100 Enterprise Way | Address / Location |
| **LOC** | Silicon Valley | Address / Location |
| **GPE** | California | Geopolitical Entity |
| **SSN** | 987-65-4321 | Social Security Number |
| **CARD** | 4111-2222-3333-4444 | Credit Card Number |
| **IP** | 192.168.1.1 | IP Address |
| **IP** | 10.0.0.254 | IP Address |

---

## 3. Evaluation Metrics

We classify the outputs of the redaction system into three categories:

*   **True Positives (TP):** Ground truth PII elements that were successfully matched and redacted.
*   **False Negatives (FN):** Ground truth PII elements that were missed by the redaction system (remained in the final text).
*   **False Positives (FP):** Text sequences replaced by the tool that were not actually PII (or did not match the specific ground truth boundary).

From these buckets, standard Information Retrieval metrics are calculated:

$$\text{Precision} = \frac{TP}{TP + FP}$$
$$\text{Recall} = \frac{TP}{TP + FN}$$
$$F_1\text{-score} = 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$$

---

## 4. Current Test Performance

Running the evaluation script (`evaluate.py`) yields the following performance metrics:

*   **Precision:** **95.24%** (20 / 21 replacements)
*   **Recall:** **90.91%** (20 / 22 ground truths matched)
*   **F1-Score:** **93.02%**

### Performance Breakdown

#### True Positives (TP) [20]
All structured PII (emails, phones, credit cards, SSNs, IPs), names, dates, and geopolitical entities were successfully identified and redacted:
1. `August 13, 2026` (DATE) -> Redacted to Fake Date
2. `November 30, 2026` (DATE) -> Redacted to Fake Date
3. `July 15, 2026` (DATE) -> Redacted to Fake Date
4. `Acme Corp` (ORG) -> Redacted to Fake Company Name
5. `Jane Doe` (PERSON) -> Redacted to Fake Name
6. `Amit Sharma` (PERSON) -> Redacted to Fake Name
7. `Priya Patel` (PERSON) -> Redacted to Fake Name
8. `John Smith` (PERSON) -> Redacted to Fake Name
9. `jane.doe@acmecorp.com` (EMAIL) -> Redacted to Fake Email
10. `amit.sharma@acmecorp.com` (EMAIL) -> Redacted to Fake Email
11. `priya.patel@acmecorp.com` (EMAIL) -> Redacted to Fake Email
12. `john.smith@external-audit.com` (EMAIL) -> Redacted to Fake Email
13. `support@acmecorp.com` (EMAIL) -> Redacted to Fake Email
14. `+1 (555) 019-2834` (PHONE) -> Redacted to Fake Phone
15. `+91 98765 43210` (PHONE) -> Redacted to Fake Phone
16. `California` (GPE) -> Redacted to Fake Address/State
17. `987-65-4321` (SSN) -> Redacted to Fake SSN
18. `4111-2222-3333-4444` (CARD) -> Redacted to Fake Credit Card
19. `192.168.1.1` (IP) -> Redacted to Fake IP
20. `10.0.0.254` (IP) -> Redacted to Fake IP

#### False Negatives (FN) [2]
*   `100 Enterprise Way` (LOC)
*   `Silicon Valley` (LOC)

#### False Positives (FP) [1]
*   `100 Enterprise Way, Silicon Valley`

### Analysis of the Address Match Discrepancy
The 2 False Negatives and 1 False Positive are a direct result of a **custom address regex boundary merge**.
The custom address regex pattern matched `100 Enterprise Way, Silicon Valley` as a **single continuous block** rather than two separate elements. 

- In practice, this is the **preferred formatting output** for document redaction, as redacting the full address block in one go is safer and prevents leaving leaking context (like commas or connecting words).
- However, since the ground truth listed them as separate values (`100 Enterprise Way` and `Silicon Valley`), the strict matching logic penalized the tool with 2 FNs and 1 FP.

---

## 5. Technical Approach & Design Trade-offs

The redaction engine utilizes a hybrid processing pipeline:
1. **Deterministic Regex:** Matches structured patterns (Emails, Phones, IPs, SSNs, Credit Cards) with near 100% accuracy.
2. **Contextual NLP (spaCy `en_core_web_sm`):** Handles names, organizations, and dates that require grammatical context.
3. **Custom Phrase Matching & Fallbacks:** Uses custom capitalization patterns for Indian/international names and address structures.
4. **Consistency Mapping:** Keeps an in-memory dictionary backed by the Python `Faker` library, replacing identical PII values with the exact same fake entity (e.g., all occurrences of `Jane Doe` are consistently replaced by the same fake name throughout the docx).

### Key Limitations & Mitigation Strategies
*   **Legal/Heading Over-redaction:** Generic terms (e.g. `SEBI`, `CFO`, `Companies Act`) can be misclassified as `ORG` or `PERSON`. To mitigate this, a comprehensive `NON_PII_BLACKLIST` is maintained in `redactor.py` to filter out corporate legal jargon.
*   **In-Memory Scope:** Mappings are reset per execution. For enterprise-grade scaling (consistent redaction across files over time), these mappings should be saved to an external database.
