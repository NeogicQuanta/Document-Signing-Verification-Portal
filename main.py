import hashlib
import json
import base64
from pathlib import Path
from datetime import datetime
import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.exceptions import InvalidSignature

# All generated files are kept in this folder.
OUTPUT = Path("output")
OUTPUT.mkdir(exist_ok=True)

PRIVATE_KEY_FILE = OUTPUT / "private_key.pem"
PUBLIC_KEY_FILE = OUTPUT / "public_key.pem"


def create_keys():
    """Create an RSA key pair once, then reuse it."""
    if not PRIVATE_KEY_FILE.exists():
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )

        PRIVATE_KEY_FILE.write_bytes(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
        )

        PUBLIC_KEY_FILE.write_bytes(
            private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        )

        print("\nRSA keys generated successfully.")

    private_key = serialization.load_pem_private_key(
        PRIVATE_KEY_FILE.read_bytes(),
        password=None
    )
    public_key = serialization.load_pem_public_key(
        PUBLIC_KEY_FILE.read_bytes()
    )
    return private_key, public_key


def calculate_hash(file_path):
    """Calculate the SHA-256 hash of a file."""
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        for data in iter(lambda: file.read(4096), b""):
            sha256.update(data)

    return sha256.hexdigest()


def generate_pdf(name, course, certificate_id):
    """Create the certificate PDF and QR code."""
    pdf_path = OUTPUT / f"{certificate_id}.pdf"
    qr_path = OUTPUT / f"{certificate_id}_qr.png"

    # QR contains the certificate ID for this local demonstration.
    qr = qrcode.make(f"Certificate ID: {certificate_id}")
    qr.save(qr_path)

    pdf = canvas.Canvas(str(pdf_path), pagesize=A4)
    width, height = A4

    pdf.setTitle("Digital Certificate")
    pdf.setFont("Helvetica-Bold", 24)
    pdf.drawCentredString(width / 2, height - 120, "CERTIFICATE")

    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(width / 2, height - 180, "This certificate is awarded to")

    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawCentredString(width / 2, height - 225, name)

    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(width / 2, height - 275, f"For completing: {course}")

    pdf.setFont("Helvetica", 10)
    pdf.drawCentredString(width / 2, height - 330, f"Certificate ID: {certificate_id}")
    pdf.drawCentredString(width / 2, height - 350,
                          f"Issue date: {datetime.now().strftime('%d-%m-%Y')}")

    pdf.drawImage(str(qr_path), width / 2 - 45, height - 500, 90, 90)
    pdf.setFont("Helvetica", 9)
    pdf.drawCentredString(width / 2, height - 520, "Scan the QR code to identify this certificate")

    pdf.save()
    qr_path.unlink(missing_ok=True)
    return pdf_path


def generate_certificate():
    print("\n--- GENERATE CERTIFICATE ---")
    name = input("Enter recipient name: ").strip()
    course = input("Enter course/certificate title: ").strip()

    if not name or not course:
        print("Name and course cannot be empty.")
        return

    certificate_id = "CSL-G48-" + datetime.now().strftime("%Y%m%d%H%M%S")
    private_key, _ = create_keys()

    pdf_path = generate_pdf(name, course, certificate_id)

    # Important: hash only after the PDF is completely generated.
    file_hash = calculate_hash(pdf_path)

    signature = private_key.sign(
        bytes.fromhex(file_hash),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )

    record = {
        "certificate_id": certificate_id,
        "file_name": pdf_path.name,
        "sha256_hash": file_hash,
        "digital_signature": base64.b64encode(signature).decode("utf-8")
    }

    record_path = OUTPUT / f"{certificate_id}.json"
    record_path.write_text(json.dumps(record, indent=4))

    print("\nCertificate generated successfully!")
    print("PDF:", pdf_path)
    print("Record:", record_path)
    print("SHA-256:", file_hash)
    print("Digital signature saved in the JSON record.")
    print("Keep the PDF and its JSON record together for verification.")


def verify_certificate():
    print("\n--- VERIFY CERTIFICATE ---")
    pdf_name = input("Enter PDF file path (e.g. output/CSL-G48-....pdf): ").strip()
    record_name = input("Enter matching JSON record path: ").strip()

    pdf_path = Path(pdf_name)
    record_path = Path(record_name)

    if not pdf_path.is_file() or not record_path.is_file():
        print("PDF or JSON record not found.")
        return

    try:
        record = json.loads(record_path.read_text())
        public_key = serialization.load_pem_public_key(
            PUBLIC_KEY_FILE.read_bytes()
        )

        actual_hash = calculate_hash(pdf_path)
        saved_hash = record["sha256_hash"]

        if actual_hash != saved_hash:
            print("\nTAMPERING DETECTED!")
            print("The PDF hash does not match the original hash.")
            print("Original hash:", saved_hash)
            print("Current hash: ", actual_hash)
            return

        signature = base64.b64decode(record["digital_signature"])

        public_key.verify(
            signature,
            bytes.fromhex(saved_hash),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        print("\nCERTIFICATE IS AUTHENTIC!")
        print("SHA-256 hash matches.")
        print("RSA digital signature is valid.")

    except InvalidSignature:
        print("\nVERIFICATION FAILED: Digital signature is invalid.")
    except (KeyError, ValueError, json.JSONDecodeError):
        print("\nInvalid or damaged verification record.")
    except Exception as error:
        print("\nVerification error:", error)


def main():
    create_keys()

    while True:
        print("\n===================================")
        print(" DOCUMENT SIGNING & VERIFICATION")
        print("===================================")
        print("1. Generate Digital Certificate")
        print("2. Verify Certificate")
        print("3. Exit")

        choice = input("\nEnter your choice: ").strip()

        if choice == "1":
            generate_certificate()
        elif choice == "2":
            verify_certificate()
        elif choice == "3":
            print("Thank you!")
            break
        else:
            print("Invalid choice. Please enter 1, 2 or 3.")


if __name__ == "__main__":
    main()
