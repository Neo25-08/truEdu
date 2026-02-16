import os
import time
import struct
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography import x509

def generate_rsa_keypair(key_size=2048):
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
        backend=default_backend()
    )
    return private_key

def save_private_key_pkcs12(private_key, cert, password, filename):
    if cert is None:
        raise ValueError("Certificate required for PKCS#12")
    pkcs12_data = pkcs12.serialize_key_and_certificates(
        name=b"truEdu Identity",
        key=private_key,
        cert=cert,
        cas=None,
        encryption_algorithm=serialization.BestAvailableEncryption(password.encode('utf-8'))
    )
    with open(filename, 'wb') as f:
        f.write(pkcs12_data)

def load_private_key_pkcs12(filename, password):
    with open(filename, 'rb') as f:
        p12_data = f.read()
    private_key, cert, additional_certs = pkcs12.load_key_and_certificates(
        p12_data,
        password.encode('utf-8'),
        backend=default_backend()
    )
    return private_key, cert

def sign_file(file_path, private_key: RSAPrivateKey, signature_path, timestamp=True):
    """Sign a file. If timestamp=True, include an 8-byte timestamp."""
    with open(file_path, 'rb') as f:
        data = f.read()
    if timestamp:
        ts = int(time.time()).to_bytes(8, 'big')
        signed_data = ts + data
    else:
        ts = b''
        signed_data = data
    signature = private_key.sign(
        signed_data,
        asym_padding.PKCS1v15(),
        hashes.SHA256()
    )
    with open(signature_path, 'wb') as f:
        f.write(ts + signature)

def verify_signature(file_path, signature_path, public_key: RSAPublicKey, allowed_time_window=3600, timestamp=True):
    """Verify signature. If timestamp=True, expect timestamp and check freshness."""
    with open(file_path, 'rb') as f:
        data = f.read()
    with open(signature_path, 'rb') as f:
        sig_data = f.read()
    if timestamp:
        if len(sig_data) < 8:
            return False
        ts = int.from_bytes(sig_data[:8], 'big')
        signature = sig_data[8:]
        now = int(time.time())
        if now - ts > allowed_time_window:
            raise ValueError("Signature timestamp is too old (possible replay attack)")
        signed_data = ts.to_bytes(8, 'big') + data
    else:
        signature = sig_data
        signed_data = data
    try:
        public_key.verify(
            signature,
            signed_data,
            asym_padding.PKCS1v15(),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False

# Hybrid encryption
def encrypt_file_hybrid(recipient_cert_path, input_path, output_path):
    """Encrypt a file using AES-256-GCM + RSA-OAEP."""
    # Load recipient's public key from certificate
    with open(recipient_cert_path, 'rb') as f:
        cert_data = f.read()
    cert = x509.load_pem_x509_certificate(cert_data, default_backend())
    public_key = cert.public_key()

    # Generate random AES-256 key and nonce
    aes_key = os.urandom(32)
    nonce = os.urandom(12)

    # Encrypt file with AES-GCM
    cipher = Cipher(algorithms.AES(aes_key), modes.GCM(nonce), backend=default_backend())
    encryptor = cipher.encryptor()
    with open(input_path, 'rb') as f_in:
        plaintext = f_in.read()
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()
    tag = encryptor.tag

    # Encrypt AES key with RSA-OAEP
    encrypted_key = public_key.encrypt(
        aes_key,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # Write output: [encrypted_key_len(4B)][encrypted_key][nonce(12B)][tag(16B)][ciphertext]
    with open(output_path, 'wb') as f_out:
        f_out.write(struct.pack('>I', len(encrypted_key)))
        f_out.write(encrypted_key)
        f_out.write(nonce)
        f_out.write(tag)
        f_out.write(ciphertext)

def decrypt_file_hybrid(private_key, input_path, output_path):
    """Decrypt a file encrypted with hybrid encryption."""
    with open(input_path, 'rb') as f_in:
        encrypted_key_len = struct.unpack('>I', f_in.read(4))[0]
        encrypted_key = f_in.read(encrypted_key_len)
        nonce = f_in.read(12)
        tag = f_in.read(16)
        ciphertext = f_in.read()

    # Decrypt AES key with RSA-OAEP
    aes_key = private_key.decrypt(
        encrypted_key,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    # Decrypt ciphertext
    cipher = Cipher(algorithms.AES(aes_key), modes.GCM(nonce, tag), backend=default_backend())
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()

    with open(output_path, 'wb') as f_out:
        f_out.write(plaintext)
