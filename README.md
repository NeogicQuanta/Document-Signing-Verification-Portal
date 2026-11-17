# CSL-G48: Simple Document Signing & Tamper Verification System

A beginner-friendly, menu-driven Python mini project for Cyber Security Lab Experiment 8.

## What it does
1. Generates a sample PDF certificate.
2. Calculates its SHA-256 hash.
3. Signs the hash using an RSA private key (RSA-PSS).
4. Saves the signature and hash in a small JSON record.
5. Creates a QR code containing the certificate ID.
6. Verifies the PDF by checking its hash and digital signature.
7. Detects modifications to the PDF.

## Requirements
- Python 3.9 or newer
- Internet connection only for installing packages

## Installation
Open terminal in this project folder:

```bash
python -m venv venv
# Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

pip install -r requirements.txt
python main.py
```

## How to demonstrate
1. Select option 1 and enter dummy name/course details.
2. Open the `output` folder. It contains the PDF and matching JSON record.
3. Select option 2 and enter both paths, for example:
   - `output/CSL-G48-YYYYMMDDHHMMSS.pdf`
   - `output/CSL-G48-YYYYMMDDHHMMSS.json`
4. Expected result: `CERTIFICATE IS AUTHENTIC!`
5. Make a copy of the PDF and modify it (for example, open and resave it in a PDF editor).
6. Verify the modified copy against the original JSON record.
7. Expected result: `TAMPERING DETECTED!`

## Important notes
- Keep `private_key.pem`, `public_key.pem`, the PDF and JSON record in the `output` folder.
- The JSON record is the reference record for the certificate. Do not edit it during the tampering test.
- The QR code identifies the certificate; this simple version does not open an online verification page.
- This is a lab demonstration, not a production certificate authority.
- Use dummy data only. Protect the private key.
