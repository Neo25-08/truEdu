import os
import tempfile
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
import crypto_utils
import cert_manager

def test_key_generation():
    private_key = crypto_utils.generate_rsa_keypair()
    assert isinstance(private_key, rsa.RSAPrivateKey)

def test_sign_verify():
    private_key = crypto_utils.generate_rsa_keypair()
    public_key = private_key.public_key()

    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"Hello, world!")
        file_path = f.name
    sig_path = file_path + ".sig"

    crypto_utils.sign_file(file_path, private_key, sig_path)
    assert crypto_utils.verify_signature(file_path, sig_path, public_key)

    # Tamper with file
    with open(file_path, 'ab') as f:
        f.write(b"tamper")
    assert not crypto_utils.verify_signature(file_path, sig_path, public_key)

    os.unlink(file_path)
    os.unlink(sig_path)

def test_ca_creation():
    if os.path.exists(cert_manager.CA_CERT_FILE):
        os.remove(cert_manager.CA_CERT_FILE)
        os.remove(cert_manager.CA_KEY_FILE)
    priv, cert = cert_manager.create_self_signed_ca()
    assert os.path.exists(cert_manager.CA_CERT_FILE)
    assert os.path.exists(cert_manager.CA_KEY_FILE)

def test_issue_registrar():
    # Ensure CA exists
    if not os.path.exists(cert_manager.CA_CERT_FILE):
        cert_manager.create_self_signed_ca()

    with tempfile.NamedTemporaryFile(suffix='.p12', delete=False) as f:
        p12_path = f.name
    password = "test123"
    cert_manager.issue_registrar_cert("Test Registrar", p12_path, password)
    assert os.path.exists(p12_path)

    # Load it back
    priv, cert = cert_manager.load_registrar_identity(p12_path, password)
    assert priv is not None
    assert cert is not None
    os.unlink(p12_path)

def test_revocation():
    cert_manager.init_crl()
    serial = "123ABC"
    cert_manager.revoke_certificate(serial)
    assert cert_manager.is_revoked(serial)
    assert not cert_manager.is_revoked("456DEF")
