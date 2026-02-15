import tkinter as tk
from tkinter import filedialog, messagebox
import os
import glob
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cert_manager
import crypto_utils
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

class EmployerWindow:
    def __init__(self, parent):
        self.top = tk.Toplevel(parent)
        self.top.title("Employer - Verify Certificates")
        self.top.geometry("500x300")

        # Automatically load CA certificate
        self.ca_cert = self.load_ca_automatically()
        if self.ca_cert is None:
            tk.Label(self.top, text="CA certificate not found.\nPlace ca_cert.pem in the application directory.", fg="red").pack(pady=10)
            self.verify_btn = tk.Button(self.top, text="Verify Signed PDF", state=tk.DISABLED)
        else:
            tk.Label(self.top, text="University CA loaded automatically.", fg="green").pack(pady=5)
            self.verify_btn = tk.Button(self.top, text="Verify Signed PDF", command=self.verify)
        self.verify_btn.pack(pady=5)
        tk.Button(self.top, text="Close", command=self.top.destroy).pack(pady=20)

    def load_ca_automatically(self):
        """Look for ca_cert.pem in current directory; if missing, prompt user to select and copy it."""
        ca_path = "ca_cert.pem"
        if os.path.exists(ca_path):
            try:
                with open(ca_path, 'rb') as f:
                    cert_data = f.read()
                return x509.load_pem_x509_certificate(cert_data, default_backend())
            except Exception:
                pass

        # If not found, ask user to locate it
        messagebox.showinfo(
            "CA Certificate",
            "The University CA certificate (ca_cert.pem) was not found.\n"
            "Please select it now. It will be copied to the application directory for future use."
        )
        filename = filedialog.askopenfilename(title="Select CA certificate", filetypes=[("PEM files", "*.pem")])
        if filename:
            try:
                with open(filename, 'rb') as f:
                    cert_data = f.read()
                cert = x509.load_pem_x509_certificate(cert_data, default_backend())
                # Save a copy locally
                with open(ca_path, 'wb') as f:
                    f.write(cert_data)
                return cert
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load CA certificate: {str(e)}")
        return None

    def verify(self):
        if not self.ca_cert:
            messagebox.showerror("Error", "CA certificate not loaded.")
            return

        # Select PDF and signature
        pdf_file = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not pdf_file:
            return
        sig_file = filedialog.askopenfilename(filetypes=[("Signature files", "*.sig")])
        if not sig_file:
            return

        # Directory containing registrar public certificates
        registrars_dir = "registrars"
        if not os.path.isdir(registrars_dir):
            messagebox.showerror(
                "Error",
                f"Registrars directory '{registrars_dir}' not found.\n"
                "Please create it and place all registrar public certificates (*.pem, *.crt) inside."
            )
            return

        # Gather all candidate certificate files
        cert_files = glob.glob(os.path.join(registrars_dir, "*.pem")) + glob.glob(os.path.join(registrars_dir, "*.crt"))
        if not cert_files:
            messagebox.showerror(
                "Error",
                f"No certificate files found in '{registrars_dir}'.\n"
                "Please add registrar public certificates (exported from their .p12 files)."
            )
            return

        ca_public_key = self.ca_cert.public_key()
        verified = False
        last_error = ""

        for cert_file in cert_files:
            try:
                with open(cert_file, 'rb') as f:
                    cert_data = f.read()
                cert = x509.load_pem_x509_certificate(cert_data, default_backend())

                # 1. Verify that the certificate is signed by our CA
                try:
                    ca_public_key.verify(
                        cert.signature,
                        cert.tbs_certificate_bytes,
                        padding.PKCS1v15(),
                        cert.signature_hash_algorithm,
                    )
                except Exception:
                    continue  # Not signed by this CA – skip

                # 2. Check revocation list
                if cert_manager.is_revoked(hex(cert.serial_number)[2:]):
                    continue  # Revoked – skip

                # 3. Verify the PDF signature using this registrar's public key
                public_key = cert.public_key()
                if crypto_utils.verify_signature(pdf_file, sig_file, public_key):
                    verified = True
                    messagebox.showinfo(
                        "Success",
                        f"Signature is VALID.\nVerified using certificate: {os.path.basename(cert_file)}"
                    )
                    break
            except Exception as e:
                last_error = str(e)
                continue

        if not verified:
            messagebox.showerror(
                "Failure",
                f"Signature could not be verified with any known registrar certificate.\n"
                f"Last error: {last_error}"
            )
