import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cert_manager
import crypto_utils
from cryptography.hazmat.primitives import serialization
from gui import theme as T


class RegistrarWindow:
    def __init__(self, parent):
        self.top = tk.Toplevel(parent)
        self.top.title("Registrar Portal")
        self.top.geometry("640x620")
        self.top.resizable(False, False)
        self.top.configure(bg=T.BG_BASE)

        self.identity_file = None
        self.private_key   = None
        self.cert          = None

        self._build()

    # ─────────────────────────────────────────────────────────────────
    def _build(self):
        top = self.top

        # Header
        hdr = tk.Frame(top, bg=T.BG_DEEP)
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=T.GOLD_MID, height=3).pack(fill="x")
        inner_hdr = tk.Frame(hdr, bg=T.BG_DEEP)
        inner_hdr.pack(fill="x", padx=24, pady=16)
        tk.Label(inner_hdr, text="🎓  Registrar Portal",
                 font=T.FONT_TITLE, fg=T.GOLD_LIGHT, bg=T.BG_DEEP).pack(side="left")
        T.GoldButton(inner_hdr, text="✕ Close", command=self.top.destroy,
                     width=90, height=30, style="ghost").pack(side="right")

        T.Divider(top).pack(fill="x")

        # Scrollable body
        body = tk.Frame(top, bg=T.BG_BASE)
        body.pack(fill="both", expand=True, padx=28, pady=20)

        # ── Identity card ─────────────────────────────────────────────
        self._section(body, "🔑  Identity")

        id_card = T.SectionCard(body)
        id_card.pack(fill="x", pady=(0, 16))
        id_inner = tk.Frame(id_card, bg=T.BG_CARD)
        id_inner.pack(fill="x", padx=16, pady=14)

        left = tk.Frame(id_inner, bg=T.BG_CARD)
        left.pack(side="left", fill="x", expand=True)
        tk.Label(left, text="PKCS#12 Identity File",
                 font=T.FONT_HEADING, fg=T.TEXT_PRIMARY, bg=T.BG_CARD).pack(anchor="w")
        self.lbl_id = tk.Label(left, text="No identity loaded",
                               font=T.FONT_SMALL, fg=T.TEXT_DISABLED, bg=T.BG_CARD)
        self.lbl_id.pack(anchor="w")

        T.GoldButton(id_inner, text="Load .p12",
                     command=self.load_identity,
                     width=110, height=34, style="primary").pack(side="right")

        # ── Actions ───────────────────────────────────────────────────
        self._section(body, "⚙  Actions")

        actions = [
            ("Issue New Registrar Certificate",
             "Create a new registrar cert signed by the CA",
             self.issue_registrar, "secondary", None),
            ("Sign Student Certificate (PDF)",
             "Digitally sign a PDF document",
             self.sign_pdf, "primary", "sign"),
            ("Export Public Certificate",
             "Save your .pem public cert for distribution",
             self.export_public_cert, "ghost", "export"),
            ("Show Certificate Details",
             "View serial number and validity of loaded cert",
             self.show_details, "ghost", "details"),
            ("Revoke a Certificate",
             "Add a certificate to the revocation list",
             self.revoke_cert, "danger", None),
        ]

        self._btns = {}
        for title, sub, cmd, style, key in actions:
            btn = self._action_row(body, title, sub, cmd, style)
            if key:
                self._btns[key] = btn

        self._update_sign_state()

    # ─────────────────────────────────────────────────────────────────
    def _section(self, parent, title):
        tk.Label(parent, text=title, font=T.FONT_SMALL,
                 fg=T.TEXT_SECONDARY, bg=T.BG_BASE).pack(anchor="w", pady=(8, 4))

    def _action_row(self, parent, title, subtitle, command, style):
        card = T.SectionCard(parent)
        card.pack(fill="x", pady=5)
        inner = tk.Frame(card, bg=T.BG_CARD)
        inner.pack(fill="x", padx=16, pady=12)

        txt = tk.Frame(inner, bg=T.BG_CARD)
        txt.pack(side="left", fill="x", expand=True)
        tk.Label(txt, text=title, font=T.FONT_HEADING,
                 fg=T.TEXT_PRIMARY, bg=T.BG_CARD, anchor="w").pack(fill="x")
        tk.Label(txt, text=subtitle, font=T.FONT_SMALL,
                 fg=T.TEXT_SECONDARY, bg=T.BG_CARD, anchor="w").pack(fill="x")

        btn = T.GoldButton(inner, text="Run →", command=command,
                           width=90, height=34, style=style)
        btn.pack(side="right")
        return btn

    # ─────────────────────────────────────────────────────────────────
    def _update_sign_state(self):
        loaded = self.private_key is not None
        color = T.GOLD_MID if loaded else T.TEXT_DISABLED
        text  = f"Loaded: {os.path.basename(self.identity_file)}" if loaded \
                else "No identity loaded"
        self.lbl_id.configure(text=text, fg=color)

        # Enable/disable buttons that require loaded identity
        for key in ["sign", "export", "details"]:
            if key in self._btns:
                # Set the button's state directly via config (assuming GoldButton has config)
                self._btns[key].config(state=tk.NORMAL if loaded else tk.DISABLED)

    # ─────────────────────────────────────────────────────────────────
    def load_identity(self):
        filename = filedialog.askopenfilename(
            title="Select PKCS#12 Identity",
            filetypes=[("PKCS#12 files", "*.p12")])
        if not filename:
            return
        password = simpledialog.askstring(
            "Identity Password", "Enter PKCS#12 password:", show="*")
        if password is None:
            return
        try:
            self.private_key, self.cert = cert_manager.load_registrar_identity(
                filename, password)
            self.identity_file = filename
            self._update_sign_state()
            messagebox.showinfo("Identity Loaded",
                                "Identity loaded successfully.\n"
                                "You may now sign, export, and view details.")
        except Exception as e:
            messagebox.showerror("Load Failed", f"Could not load identity:\n{e}")

    def issue_registrar(self):
        if not os.path.exists(cert_manager.CA_KEY_FILE):
            messagebox.showerror("CA Key Missing",
                "The CA private key was not found.\n"
                "Only the system that created the CA can issue registrar certificates.")
            return
        ca_password = simpledialog.askstring(
            "CA Password", "Enter CA private key password:", show="*")
        if not ca_password:
            return
        name = simpledialog.askstring(
            "Registrar Name", "Enter the registrar's common name\n(e.g. 'Registrar Office'):")
        if not name:
            return
        password = simpledialog.askstring(
            "Protect Key", "Enter password to protect the new PKCS#12 file:", show="*")
        if not password:
            return
        filename = filedialog.asksaveasfilename(
            title="Save PKCS#12 File",
            defaultextension=".p12",
            filetypes=[("PKCS#12 files", "*.p12")])
        if not filename:
            return
        try:
            cert = cert_manager.issue_registrar_cert(name, filename, password, ca_password)
            serial_hex = hex(cert.serial_number)[2:].upper()
            messagebox.showinfo("Certificate Issued",
                                f"Registrar certificate issued and saved to:\n{filename}\n\n"
                                f"Serial number (for revocation): {serial_hex}")
        except Exception as e:
            messagebox.showerror("Issuance Failed", f"Could not issue certificate:\n{e}")

    def sign_pdf(self):
        if not self.private_key:
            messagebox.showerror("No Identity", "Please load an identity first.")
            return
        pdf_file = filedialog.askopenfilename(
            title="Select PDF to Sign",
            filetypes=[("PDF files", "*.pdf")])
        if not pdf_file:
            return
        sig_file = filedialog.asksaveasfilename(
            title="Save Signature File",
            defaultextension=".sig",
            filetypes=[("Signature files", "*.sig")])
        if not sig_file:
            return
        try:
            crypto_utils.sign_file(pdf_file, self.private_key, sig_file, timestamp=True)
            messagebox.showinfo("Signed", f"PDF signed successfully.\nSignature saved to:\n{sig_file}")
        except Exception as e:
            messagebox.showerror("Signing Failed", f"Could not sign PDF:\n{e}")

    def export_public_cert(self):
        if not self.cert:
            messagebox.showerror("No Identity", "Please load an identity first.")
            return
        filename = filedialog.asksaveasfilename(
            title="Export Public Certificate",
            defaultextension=".pem",
            filetypes=[("PEM files", "*.pem")])
        if not filename:
            return
        try:
            pem_data = self.cert.public_bytes(encoding=serialization.Encoding.PEM)
            with open(filename, "wb") as f:
                f.write(pem_data)
            messagebox.showinfo("Exported", f"Public certificate exported to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not export certificate:\n{e}")

    def show_details(self):
        """Display details of the loaded certificate."""
        if not self.cert:
            messagebox.showerror("No Identity", "Please load an identity first.")
            return
        try:
            subject = self.cert.subject
            issuer = self.cert.issuer
            serial = hex(self.cert.serial_number)[2:].upper()
            # Use UTC methods to avoid deprecation warnings
            not_before = self.cert.not_valid_before_utc
            not_after = self.cert.not_valid_after_utc

            details = (
                f"Subject: {subject.rfc4514_string()}\n"
                f"Issuer: {issuer.rfc4514_string()}\n"
                f"Serial Number: {serial}\n"
                f"Valid From: {not_before}\n"
                f"Valid To: {not_after}"
            )
            messagebox.showinfo("Certificate Details", details)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read certificate details:\n{e}")

    def revoke_cert(self):
        serial = simpledialog.askstring(
            "Revoke Certificate",
            "Enter certificate serial number (hexadecimal):")
        if not serial:
            return
        # Remove any '0x' prefix if present
        if serial.startswith('0x') or serial.startswith('0X'):
            serial = serial[2:]
        try:
            int(serial, 16)
            cert_manager.revoke_certificate(serial)
            messagebox.showinfo("Revoked", f"Certificate {serial} has been revoked.")
        except ValueError:
            messagebox.showerror("Invalid Input",
                                 "Serial number must be in hexadecimal format.")