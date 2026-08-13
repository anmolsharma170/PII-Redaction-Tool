# PII Redaction Script

This tool is designed to scan and redact Personally Identifiable Information (PII) from Word documents (`.docx`), ensuring data privacy while maintaining consistent mappings for recurring entities.

## Technical Approach
This tool uses a hybrid approach combining Regular Expressions (Regex) and spaCy's Named Entity Recognition (`en_core_web_sm`).
- **Regex** handles deterministic, structured formats (Emails, Phone Numbers, SSNs, Credit Cards, IP Addresses).
- **spaCy** handles dynamic, contextual entities (Names, Organizations, Addresses, Dates).
- **Replacement consistency** is maintained using an in-memory mapping dictionary (`pii_map` in `anonymizer.py`) backed by `Faker` so that identical original PII elements are replaced with identical fake values throughout the document.

---

## Installation & Setup

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/anmolsharma170/PII-Redaction-Tool.git
   cd PII-Redaction-Tool
   ```

2. **Create and Activate a Virtual Environment:**
   ```bash
   python -m venv venv
   # On Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download the spaCy Language Model:**
   ```bash
   python -m spacy download en_core_web_sm
   ```

---

## Usage

### 1. Redacting a .docx Document
To run the redaction pipeline on a document:
```python
from processor import process_prospectus_docx

process_prospectus_docx("input_path.docx", "output_path.docx")
```

Or run the test suite directly to check the local pipeline functionality:
```bash
python processor.py
```

### 2. Running Evaluation
To check the precision, recall, and F1-score metrics on a sample prospectus snippet:
```bash
python evaluate.py
```

---

## Trade-offs & Limitations
1. **False Positives in Legal Headings:** Generic legal terms and headings (e.g., "Red Herring Prospectus", "Companies Act", "CFO", "SSN") are sometimes misclassified by spaCy as `ORG` or `PERSON` entities and replaced.
2. **Address Detection:** Complex, multi-line postal addresses lack rigid syntax and may be partially captured or missed across line breaks.
3. **In-Memory Mapping Scope:** The consistent mapping dictionary runs in-memory and is reset per execution. For persistent consistency across multiple run sessions, a database backend is recommended.
