import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cert_manager
import crypto_utils
from cryptography.hazmat.primitives import serialization

class RegistrarWindow:
    def __init__(self, parent):
        self.top = tk.Toplevel(parent)
        self.top.title("Registrar - Issue Certificates")
        self.top.geometry("600x450")

        # Variables
        self.identity_file = None
        self.password = None
        self.private_key = None
        self.cert = None

        # Widgets
        tk.Label(self.top, text="Registrar Dashboard", font=("Arial", 14)).pack(pady=10)

        # Load identity frame
        frame_id = tk.Frame(self.top)
        frame_id.pack(pady=5)
        tk.Label(frame_id, text="Registrar Identity (PKCS#12):").pack(side=tk.LEFT)
        self.lbl_id = tk.Label(frame_id, text="Not loaded", fg="red")
        self.lbl_id.pack(side=tk.LEFT, padx=5)
        tk.Button(frame_id, text="Load Identity", command=self.load_identity).pack(side=tk.LEFT)

        # Issue new registrar certificate (if CA)
        tk.Button(self.top, text="Issue New Registrar Certificate", command=self.issue_registrar).pack(pady=5)

        # Sign PDF - store reference directly
        self.sign_btn = tk.Button(self.top, text="Sign Student Certificate (PDF)", command=self.sign_pdf, state=tk.DISABLED)
        self.sign_btn.pack(pady=5)

        # Export public certificate (enabled after identity loaded)
        self.export_btn = tk.Button(self.top, text="Export Public Certificate", command=self.export_public_cert, state=tk.DISABLED)
        self.export_btn.pack(pady=5)

        # Revoke a certificate
        tk.Button(self.top, text="Revoke a Certificate", command=self.revoke_cert).pack(pady=5)

        # Close button
        tk.Button(self.top, text="Close", command=self.top.destroy).pack(pady=20)

    def load_identity(self):
        filename = filedialog.askopenfilename(filetypes=[("PKCS#12 files", "*.p12")])
        if not filename:
            return
        password = simpledialog.askstring("Password", "Enter PKCS#12 password:", show='*')
        if password is None:
            return
        try:
            self.private_key, self.cert = cert_manager.load_registrar_identity(filename, password)
            self.identity_file = filename
            self.lbl_id.config(text=f"Loaded: {os.path.basename(filename)}", fg="green")
            self.sign_btn.config(state=tk.NORMAL)
            self.export_btn.config(state=tk.NORMAL)
            messagebox.showinfo("Success", "Identity loaded successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load identity: {str(e)}")

    def issue_registrar(self):
        if not os.path.exists(cert_manager.CA_KEY_FILE):
            messagebox.showerror("Error", "CA key not found. Only the system that created the CA can issue registrar certificates.")
            return
        name = simpledialog.askstring("Registrar Name", "Enter registrar's common name (e.g., 'Registrar Office'):")
        if not name:
            return
        password = simpledialog.askstring("Password", "Enter password to protect new PKCS#12 file:", show='*')
        if not password:
            return
        filename = filedialog.asksaveasfilename(defaultextension=".p12", filetypes=[("PKCS#12 files", "*.p12")])
        if not filename:
            return
        try:
            cert = cert_manager.issue_registrar_cert(name, filename, password)
            messagebox.showinfo("Success", f"Registrar certificate issued and saved to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to issue certificate: {str(e)}")

    def sign_pdf(self):
        if not self.private_key:
            messagebox.showerror("Error", "No identity loaded.")
            return
        pdf_file = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not pdf_file:
            return
        # Suggest signature file name
        sig_file = pdf_file + ".sig"
        sig_file = filedialog.asksaveasfilename(initialfile=os.path.basename(sig_file), defaultextension=".sig", filetypes=[("Signature files", "*.sig")])
        if not sig_file:
            return
        try:
            crypto_utils.sign_file(pdf_file, self.private_key, sig_file)
            messagebox.showinfo("Success", f"PDF signed successfully. Signature saved to {sig_file}")
        except Exception as e:
            messagebox.showerror("Error", f"Signing failed: {str(e)}")

    def export_public_cert(self):
        """Export the public certificate (PEM) from the loaded identity."""
        if not self.cert:
            messagebox.showerror("Error", "No identity loaded.")
            return
        filename = filedialog.asksaveasfilename(
            title="Save Public Certificate",
            defaultextension=".pem",
            filetypes=[("PEM files", "*.pem"), ("All files", "*.*")]
        )
        if not filename:
            return
        try:
            # Serialize the certificate to PEM
            pem_data = self.cert.public_bytes(encoding=serialization.Encoding.PEM)
            with open(filename, 'wb') as f:
                f.write(pem_data)
            messagebox.showinfo("Success", f"Public certificate exported to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {str(e)}")

    def revoke_cert(self):
        serial = simpledialog.askstring("Revoke Certificate", "Enter certificate serial number (in hex):")
        if not serial:
            return
        try:
            int(serial, 16)
            cert_manager.revoke_certificate(serial)
            messagebox.showinfo("Success", f"Certificate {serial} revoked.")
        except ValueError:
            messagebox.showerror("Error", "Invalid serial number format. Must be hexadecimal.")
