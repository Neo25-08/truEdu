import tkinter as tk
from tkinter import messagebox
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from gui.registrar_window import RegistrarWindow
from gui.employer_window import EmployerWindow
from gui.encryption_window import EncryptionWindow
import cert_manager

class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("truEdu - Certificate Verification System")
        self.root.geometry("400x300")

        if not os.path.exists(cert_manager.CA_CERT_FILE):
            if messagebox.askyesno("CA Missing", "No Certificate Authority found. Create a new one now?"):
                password = tk.simpledialog.askstring("CA Password", "Enter password to protect CA private key:", show='*')
                if password:
                    cert_manager.create_self_signed_ca(password)
                    messagebox.showinfo("Success", "CA created successfully.")
                else:
                    messagebox.showerror("Error", "CA creation cancelled.")
                    self.root.quit()
            else:
                messagebox.showerror("Error", "CA required to run. Exiting.")
                self.root.quit()

        tk.Label(root, text="Welcome to truEdu", font=("Arial", 16)).pack(pady=20)

        tk.Button(root, text="Registrar (Issue Certificates)", command=self.open_registrar, width=30).pack(pady=5)
        tk.Button(root, text="Employer (Verify Certificates)", command=self.open_employer, width=30).pack(pady=5)
        tk.Button(root, text="Encryption (Hybrid)", command=self.open_encryption, width=30).pack(pady=5)
        tk.Button(root, text="Exit", command=root.quit).pack(pady=20)

    def open_registrar(self):
        RegistrarWindow(self.root)

    def open_employer(self):
        EmployerWindow(self.root)

    def open_encryption(self):
        EncryptionWindow(self.root)

if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()
