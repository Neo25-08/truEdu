import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cert_manager
import crypto_utils
from cryptography import x509
from cryptography.hazmat.backends import default_backend

class EmployerWindow:
    def __init__(self, parent):
        self.top = tk.Toplevel(parent)
        self.top.title("Employer - Verify Certificates")
        self.top.geometry("500x300")

        tk.Label(self.top, text="Employer Verification", font=("Arial", 14)).pack(pady=10)

        # Load CA certificate
        tk.Button(self.top, text="Load University CA Certificate", command=self.load_ca).pack(pady=5)
        self.ca_label = tk.Label(self.top, text="CA not loaded", fg="red")
        self.ca_label.pack()

        # Select PDF and signature
        tk.Button(self.top, text="Verify Signed PDF", command=self.verify, state=tk.DISABLED)
        self.verify_btn = self.top.children['!button']  # again, referencing

        # Close
        tk.Button(self.top, text="Close", command=self.top.destroy).pack(pady=20)

        self.ca_cert = None

    def load_ca(self):
        filename = filedialog.askopenfilename(filetypes=[("PEM files", "*.pem")])
        if not filename:
            return
        try:
            with open(filename, 'rb') as f:
                cert_data = f.read()
            self.ca_cert = x509.load_pem_x509_certificate(cert_data, default_backend())
            self.ca_label.config(text=f"CA loaded: {os.path.basename(filename)}", fg="green")
            self.verify_btn.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load CA certificate: {str(e)}")

    def verify(self):
        if not self.ca_cert:
            messagebox.showerror("Error", "No CA certificate loaded.")
            return

        pdf_file = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not pdf_file:
            return
        sig_file = filedialog.askopenfilename(filetypes=[("Signature files", "*.sig")])
        if not sig_file:
            return

        # We need the signer's public key. In a real system, we would extract it from the certificate that signed the PDF.
        # For simplicity, we assume the signer's certificate is provided separately, or we can ask the user to select it.
        # We'll ask the user to select the registrar's certificate (PEM or PKCS#12 with cert only).
        cert_file = filedialog.askopenfilename(title="Select Registrar's Certificate (PEM or PKCS#12)", filetypes=[("Certificate files", "*.pem *.crt *.p12")])
        if not cert_file:
            return
        try:
            if cert_file.endswith('.p12'):
                # Need password to extract cert
                password = simpledialog.askstring("Password", "Enter PKCS#12 password:", show='*')
                if password is None:
                    return
                _, cert = cert_manager.load_registrar_identity(cert_file, password)
            else:
                with open(cert_file, 'rb') as f:
                    cert_data = f.read()
                cert = x509.load_pem_x509_certificate(cert_data, default_backend())

            # Verify certificate is signed by our CA
            ca_public_key = self.ca_cert.public_key()
            try:
                ca_public_key.verify(
                    cert.signature,
                    cert.tbs_certificate_bytes,
                    padding.PKCS1v15(),
                    cert.signature_hash_algorithm,
                )
            except Exception:
                messagebox.showerror("Error", "Registrar certificate is not signed by this CA.")
                return

            # Check revocation
            if cert_manager.is_revoked(hex(cert.serial_number)[2:]):  # remove '0x'
                messagebox.showerror("Error", "This registrar's certificate has been revoked.")
                return

            # Now verify the PDF signature
            public_key = cert.public_key()
            valid = crypto_utils.verify_signature(pdf_file, sig_file, public_key)
            if valid:
                messagebox.showinfo("Success", "Signature is VALID. The document is authentic.")
            else:
                messagebox.showerror("Failure", "Signature is INVALID. The document may have been tampered.")
        except Exception as e:
            messagebox.showerror("Error", f"Verification failed: {str(e)}")
