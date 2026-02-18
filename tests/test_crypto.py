import os
import tempfile
import pytest
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
import crypto_utils
import cert_manager

def test_key_generation():
    private_key = crypto_utils.generate_rsa_keypair()
    assert private_key is not None

def test_sign_verify_with_timestamp():
    private_key = crypto_utils.generate_rsa_keypair()
    public_key = private_key.public_key()

    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"Hello, world!")
        file_path = f.name
    sig_path = file_path + ".sig"

    crypto_utils.sign_file(file_path, private_key, sig_path, timestamp=True)
    assert crypto_utils.verify_signature(file_path, sig_path, public_key, timestamp=True)

    # Tamper with file
    with open(file_path, 'ab') as f:
        f.write(b"tamper")
    assert not crypto_utils.verify_signature(file_path, sig_path, public_key, timestamp=True)

    os.unlink(file_path)
    os.unlink(sig_path)

def test_encryption_decryption():
    # Generate recipient key pair
    recipient_priv = crypto_utils.generate_rsa_keypair()
    recipient_pub = recipient_priv.public_key()

    # Save recipient's public cert (simulate)
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    import datetime
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "NP"),
        x509.NameAttribute(NameOID.COMMON_NAME, "Test Recipient"),
    ])
    cert = x509.CertificateBuilder().subject_name(subject).issuer_name(issuer).public_key(recipient_pub).serial_number(x509.random_serial_number()).not_valid_before(datetime.datetime.utcnow()).not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=1)).sign(recipient_priv, hashes.SHA256(), default_backend())
    cert_path = tempfile.NamedTemporaryFile(suffix='.pem', delete=False).name
    with open(cert_path, 'wb') as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    # Encrypt a file
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"Secret data")
        plain_path = f.name
    enc_path = plain_path + ".enc"
    crypto_utils.encrypt_file_hybrid(cert_path, plain_path, enc_path)

    # Decrypt
    dec_path = plain_path + ".dec"
    crypto_utils.decrypt_file_hybrid(recipient_priv, enc_path, dec_path)

    with open(dec_path, 'rb') as f:
        decrypted = f.read()
    assert decrypted == b"Secret data"

    os.unlink(plain_path)
    os.unlink(enc_path)
    os.unlink(dec_path)
    os.unlink(cert_path)
