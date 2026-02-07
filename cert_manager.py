import datetime
import json
import os
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import crypto_utils

CA_CERT_FILE = "ca_cert.pem"
CA_KEY_FILE = "ca_key.pem"
CRL_FILE = "crl.json"

def create_self_signed_ca():
    """Create a self-signed CA certificate and private key."""
    private_key = crypto_utils.generate_rsa_keypair()
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "NP"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Bagmati"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Kathmandu"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "truEdu University"),
        x509.NameAttribute(NameOID.COMMON_NAME, "truEdu CA"),
    ])
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(days=3650)  # 10 years
    ).add_extension(
        x509.BasicConstraints(ca=True, path_length=None), critical=True
    ).sign(private_key, hashes.SHA256(), default_backend())

    # Save CA key and cert
    with open(CA_KEY_FILE, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    with open(CA_CERT_FILE, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    return private_key, cert

def load_ca_cert():
    """Load the CA certificate from file."""
    with open(CA_CERT_FILE, "rb") as f:
        cert_data = f.read()
    return x509.load_pem_x509_certificate(cert_data, default_backend())

def load_ca_key():
    """Load the CA private key from file."""
    with open(CA_KEY_FILE, "rb") as f:
        key_data = f.read()
    return serialization.load_pem_private_key(key_data, password=None, backend=default_backend())

def issue_registrar_cert(common_name, output_p12, password):
    """Issue a certificate for a registrar signed by the CA."""
    # Generate registrar key pair
    registrar_key = crypto_utils.generate_rsa_keypair()

    # Load CA key and cert
    ca_key = load_ca_key()
    ca_cert = load_ca_cert()

    # Build registrar certificate
    subject = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "NP"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "truEdu University"),
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
    ])
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        ca_cert.subject
    ).public_key(
        registrar_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(days=365)
    ).add_extension(
        x509.BasicConstraints(ca=False, path_length=None), critical=True
    ).sign(ca_key, hashes.SHA256(), default_backend())

    # Save as PKCS#12
    crypto_utils.save_private_key_pkcs12(registrar_key, cert, password, output_p12)

    # Return the cert (for display)
    return cert

def load_registrar_identity(p12_file, password):
    """Load registrar private key and certificate from PKCS#12."""
    return crypto_utils.load_private_key_pkcs12(p12_file, password)

# CRL functions
def init_crl():
    if not os.path.exists(CRL_FILE):
        with open(CRL_FILE, 'w') as f:
            json.dump([], f)

def revoke_certificate(serial_number):
    """Add a certificate serial number to the CRL."""
    init_crl()
    with open(CRL_FILE, 'r') as f:
        crl = json.load(f)
    if serial_number not in crl:
        crl.append(serial_number)
        with open(CRL_FILE, 'w') as f:
            json.dump(crl, f)

def is_revoked(serial_number):
    """Check if a certificate serial number is revoked."""
    init_crl()
    with open(CRL_FILE, 'r') as f:
        crl = json.load(f)
    return serial_number in crl
