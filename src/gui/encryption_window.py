import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import crypto_utils
import cert_manager

class EncryptionWindow:
    def __init__(self, parent):
        self.top = tk.Toplevel(parent)
        self.top.title("Encryption/Decryption")
        self.top.geometry("500x300")

        tk.Label(self.top, text="Hybrid Encryption (AES-256 + RSA)", font=("Arial", 12)).pack(pady=10)

        # Encrypt section
        tk.Label(self.top, text="Encrypt a file:", font=("Arial", 10, "bold")).pack(anchor='w', padx=20)
        tk.Button(self.top, text="Encrypt File", command=self.encrypt_file).pack(pady=5)

        # Decrypt section
        tk.Label(self.top, text="Decrypt a file:", font=("Arial", 10, "bold")).pack(anchor='w', padx=20, pady=(10,0))
        tk.Button(self.top, text="Decrypt File", command=self.decrypt_file).pack(pady=5)

        tk.Button(self.top, text="Close", command=self.top.destroy).pack(pady=20)

    def encrypt_file(self):
        # Select recipient's certificate
        cert_file = filedialog.askopenfilename(
            title="Select Recipient's Certificate (PEM)",
            filetypes=[("PEM files", "*.pem"), ("All files", "*.*")]
        )
        if not cert_file:
            return
        # Select input file
        input_file = filedialog.askopenfilename(title="Select file to encrypt")
        if not input_file:
            return
        # Select output file
        output_file = filedialog.asksaveasfilename(defaultextension=".enc", filetypes=[("Encrypted files", "*.enc")])
        if not output_file:
            return
        try:
            crypto_utils.encrypt_file_hybrid(cert_file, input_file, output_file)
            messagebox.showinfo("Success", f"File encrypted successfully:\n{output_file}")
        except Exception as e:
            messagebox.showerror("Error", f"Encryption failed: {str(e)}")

    def decrypt_file(self):
        # Need private key (PKCS#12) of recipient
        p12_file = filedialog.askopenfilename(
            title="Select Your PKCS#12 Identity",
            filetypes=[("PKCS#12 files", "*.p12")]
        )
        if not p12_file:
            return
        password = simpledialog.askstring("Password", "Enter PKCS#12 password:", show='*')
        if password is None:
            return
        try:
            private_key, _ = cert_manager.load_registrar_identity(p12_file, password)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load identity: {str(e)}")
            return
        # Select encrypted file
        enc_file = filedialog.askopenfilename(filetypes=[("Encrypted files", "*.enc")])
        if not enc_file:
            return
        # Select output file
        output_file = filedialog.asksaveasfilename(defaultextension=".dec", filetypes=[("All files", "*.*")])
        if not output_file:
            return
        try:
            crypto_utils.decrypt_file_hybrid(private_key, enc_file, output_file)
            messagebox.showinfo("Success", f"File decrypted successfully:\n{output_file}")
        except Exception as e:
            messagebox.showerror("Error", f"Decryption failed: {str(e)}")
