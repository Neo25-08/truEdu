import os
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import pkcs12

def generate_rsa_keypair(key_size=2048):
    """Generate an RSA private key."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
        backend=default_backend()
    )
    return private_key

def save_private_key_pkcs12(private_key, cert, password, filename):
    """
    Save private key and associated certificate as a PKCS#12 file.
    cert can be None if you only want to store the key (but for PKCS#12 we need a cert).
    We'll use this later with a certificate.
    """
    if cert is None:
        # If no certificate, we cannot create PKCS#12; fallback to PEM encryption
        # For simplicity, we'll handle separately. We'll assume cert is always provided.
        raise ValueError("Certificate required for PKCS#12")
    # Convert private_key to bytes for PKCS12 serialization
    pkcs12_data = pkcs12.serialize_key_and_certificates(
        name=b"truEdu Identity",
        key=private_key,
        cert=cert,
        cas=None,  # no additional CA certs
        encryption_algorithm=serialization.BestAvailableEncryption(password.encode('utf-8'))
    )
    with open(filename, 'wb') as f:
        f.write(pkcs12_data)

def load_private_key_pkcs12(filename, password):
    """Load private key and certificate from PKCS#12 file."""
    with open(filename, 'rb') as f:
        p12_data = f.read()
    private_key, cert, additional_certs = pkcs12.load_key_and_certificates(
        p12_data,
        password.encode('utf-8'),
        backend=default_backend()
    )
    return private_key, cert

def sign_file(file_path, private_key: RSAPrivateKey, signature_path):
    """Sign a file and save the signature."""
    with open(file_path, 'rb') as f:
        data = f.read()
    signature = private_key.sign(
        data,
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    with open(signature_path, 'wb') as f:
        f.write(signature)

def verify_signature(file_path, signature_path, public_key: RSAPublicKey):
    """Verify a file's signature."""
    with open(file_path, 'rb') as f:
        data = f.read()
    with open(signature_path, 'rb') as f:
        signature = f.read()
    try:
        public_key.verify(
            signature,
            data,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False
