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
from gui import theme as T


class EmployerWindow:
    def __init__(self, parent):
        self.top = tk.Toplevel(parent)
        self.top.title("Employer Verifier")
        self.top.geometry("580x520")
        self.top.resizable(False, False)
        self.top.configure(bg=T.BG_BASE)

        self.ca_cert = None
        self._build()
        self._load_ca()

    # ─────────────────────────────────────────────────────────────────
    def _build(self):
        top = self.top

        # Header
        hdr = tk.Frame(top, bg=T.BG_DEEP)
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=T.BLUE_MID, height=3).pack(fill="x")
        inner_hdr = tk.Frame(hdr, bg=T.BG_DEEP)
        inner_hdr.pack(fill="x", padx=24, pady=16)
        tk.Label(inner_hdr, text="🏢  Employer Verifier",
                 font=T.FONT_TITLE, fg=T.BLUE_LIGHT, bg=T.BG_DEEP).pack(side="left")
        T.GoldButton(inner_hdr, text="✕ Close", command=self.top.destroy,
                     width=90, height=30, style="ghost").pack(side="right")

        T.Divider(top).pack(fill="x")

        body = tk.Frame(top, bg=T.BG_BASE)
        body.pack(fill="both", expand=True, padx=28, pady=20)

        # ── CA Status card ────────────────────────────────────────────
        tk.Label(body, text="CERTIFICATE AUTHORITY",
                 font=T.FONT_SMALL, fg=T.TEXT_SECONDARY, bg=T.BG_BASE).pack(anchor="w", pady=(0, 6))

        ca_card = T.SectionCard(body)
        ca_card.pack(fill="x", pady=(0, 20))
        ca_inner = tk.Frame(ca_card, bg=T.BG_CARD)
        ca_inner.pack(fill="x", padx=16, pady=14)

        left = tk.Frame(ca_inner, bg=T.BG_CARD)
        left.pack(side="left", fill="x", expand=True)
        tk.Label(left, text="University CA Certificate",
                 font=T.FONT_HEADING, fg=T.TEXT_PRIMARY, bg=T.BG_CARD).pack(anchor="w")

        self.ca_status = T.StatusLabel(left, bg=T.BG_CARD)
        self.ca_status.pack(anchor="w")

        T.GoldButton(ca_inner, text="Reload CA",
                     command=self._load_ca,
                     width=110, height=34, style="secondary").pack(side="right")

        # ── Verify action ─────────────────────────────────────────────
        tk.Label(body, text="VERIFICATION",
                 font=T.FONT_SMALL, fg=T.TEXT_SECONDARY, bg=T.BG_BASE).pack(anchor="w", pady=(0, 6))

        verify_card = T.SectionCard(body)
        verify_card.pack(fill="x")
        v_inner = tk.Frame(verify_card, bg=T.BG_CARD)
        v_inner.pack(fill="x", padx=16, pady=14)

        txt = tk.Frame(v_inner, bg=T.BG_CARD)
        txt.pack(side="left", fill="x", expand=True)
        tk.Label(txt, text="Verify Signed PDF",
                 font=T.FONT_HEADING, fg=T.TEXT_PRIMARY, bg=T.BG_CARD).pack(anchor="w")
        tk.Label(txt, text="Select a PDF and its .sig file to authenticate",
                 font=T.FONT_SMALL, fg=T.TEXT_SECONDARY, bg=T.BG_CARD).pack(anchor="w")

        self.verify_btn = T.GoldButton(v_inner, text="Verify →",
                                       command=self.verify,
                                       width=100, height=34, style="primary")
        self.verify_btn.pack(side="right")

        # ── Result panel ──────────────────────────────────────────────
        tk.Label(body, text="RESULT",
                 font=T.FONT_SMALL, fg=T.TEXT_SECONDARY, bg=T.BG_BASE).pack(anchor="w", pady=(20, 6))

        result_card = T.SectionCard(body)
        result_card.pack(fill="x")
        r_inner = tk.Frame(result_card, bg=T.BG_CARD)
        r_inner.pack(fill="both", padx=16, pady=14)

        self.result_icon = tk.Label(r_inner, text="—",
                                    font=(T.FONT_DISPLAY[0], 28),
                                    fg=T.TEXT_DISABLED, bg=T.BG_CARD)
        self.result_icon.pack()
        self.result_text = tk.Label(r_inner, text="No verification run yet.",
                                    font=T.FONT_BODY, fg=T.TEXT_DISABLED, bg=T.BG_CARD)
        self.result_text.pack(pady=(4, 0))
        self.result_detail = tk.Label(r_inner, text="",
                                      font=T.FONT_SMALL, fg=T.TEXT_SECONDARY, bg=T.BG_CARD,
                                      wraplength=460)
        self.result_detail.pack()

    # ─────────────────────────────────────────────────────────────────
    def _load_ca(self):
        ca_path = "ca_cert.pem"
        if os.path.exists(ca_path):
            try:
                with open(ca_path, "rb") as f:
                    self.ca_cert = x509.load_pem_x509_certificate(f.read(), default_backend())
                self.ca_status.set_state("ok", "ca_cert.pem loaded")
                return
            except Exception:
                pass

        messagebox.showinfo(
            "CA Certificate Required",
            "The University CA certificate (ca_cert.pem) was not found.\n"
            "Please select it now."
        )
        filename = filedialog.askopenfilename(
            title="Select CA Certificate",
            filetypes=[("PEM files", "*.pem")])
        if filename:
            try:
                with open(filename, "rb") as f:
                    cert_data = f.read()
                self.ca_cert = x509.load_pem_x509_certificate(cert_data, default_backend())
                with open(ca_path, "wb") as f:
                    f.write(cert_data)
                self.ca_status.set_state("ok", "CA loaded & saved")
            except Exception as e:
                self.ca_status.set_state("error", "Failed to load CA")
                messagebox.showerror("Error", f"Could not load CA:\n{e}")
        else:
            self.ca_status.set_state("error", "CA not loaded")

    # ─────────────────────────────────────────────────────────────────
    def verify(self):
        if not self.ca_cert:
            messagebox.showerror("CA Missing", "Please load the CA certificate first.")
            return

        pdf_file = filedialog.askopenfilename(
            title="Select PDF Document",
            filetypes=[("PDF files", "*.pdf")])
        if not pdf_file:
            return

        sig_file = filedialog.askopenfilename(
            title="Select Signature File",
            filetypes=[("Signature files", "*.sig")])
        if not sig_file:
            return

        registrars_dir = "registrars"
        if not os.path.isdir(registrars_dir):
            messagebox.showerror("Directory Missing",
                f"Registrars directory '{registrars_dir}' not found.\n"
                "Create it and place registrar public certificates (.pem/.crt) inside.")
            return

        cert_files = (glob.glob(os.path.join(registrars_dir, "*.pem"))
                    + glob.glob(os.path.join(registrars_dir, "*.crt")))
        if not cert_files:
            messagebox.showerror("No Certificates",
                f"No registrar certificates found in '{registrars_dir}'.")
            return

        ca_public_key = self.ca_cert.public_key()
        verified = False
        last_error = ""
        matched_cert = ""

        for cert_file in cert_files:
            try:
                with open(cert_file, "rb") as f:
                    cert = x509.load_pem_x509_certificate(f.read(), default_backend())
                try:
                    ca_public_key.verify(
                        cert.signature,
                        cert.tbs_certificate_bytes,
                        padding.PKCS1v15(),
                        cert.signature_hash_algorithm,
                    )
                except Exception:
                    continue
                if cert_manager.is_revoked(hex(cert.serial_number)[2:]):
                    continue
                try:
                    valid = crypto_utils.verify_signature(
                        pdf_file, sig_file, cert.public_key(), timestamp=True)
                except ValueError as e:
                    last_error = str(e)
                    continue
                if valid:
                    verified = True
                    matched_cert = os.path.basename(cert_file)
                    break
            except Exception as e:
                last_error = str(e)

        if verified:
            self.result_icon.configure(text="✓", fg=T.SUCCESS)
            self.result_text.configure(
                text="Signature is VALID", fg=T.SUCCESS,
                font=T.FONT_TITLE)
            self.result_detail.configure(
                text=f"Verified using registrar certificate: {matched_cert}",
                fg=T.TEXT_SECONDARY)
        else:
            self.result_icon.configure(text="✗", fg=T.ERROR)
            self.result_text.configure(
                text="Signature could NOT be verified", fg=T.ERROR,
                font=T.FONT_TITLE)
            self.result_detail.configure(
                text=f"No matching registrar certificate found.\nLast error: {last_error}",
                fg=T.TEXT_SECONDARY)
