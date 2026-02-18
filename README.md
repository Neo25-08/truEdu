# truEdu – University Certificate Verification Tool

truEdu is a GUI-based Python application that uses Public Key Infrastructure (PKI) to allow universities to issue digitally signed certificates and employers to verify them. It also provides hybrid encryption for confidential file exchange.

## Features
- **Registrar mode**: Generate RSA keys, issue X.509 certificates signed by a university CA, sign PDF diplomas (with timestamp), export public certificates, and revoke certificates.
- **Employer mode**: Verify signed PDFs using the university’s CA certificate and a folder of registrar public certificates. Timestamp freshness is checked to prevent replay attacks.
- **Encryption mode**: Hybrid encryption (AES-256-GCM + RSA-OAEP) for confidential file sharing.
- **Secure key storage**: All private keys are stored in password-protected PKCS#12 files; the CA private key is encrypted with a password.
- **Revocation**: Simple CRL via JSON file.

## Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/truEdu.git
   cd truEdu
