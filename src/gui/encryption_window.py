import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import crypto_utils
import cert_manager
from gui import theme as T


class EncryptionWindow:
    def __init__(self, parent):
        self.top = tk.Toplevel(parent)
        self.top.title("Hybrid Encryption")
        self.top.geometry("580x520")
        self.top.resizable(False, False)
        self.top.configure(bg=T.BG_BASE)
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
        tk.Label(inner_hdr, text="🔐  Hybrid Encryption",
                 font=T.FONT_TITLE, fg=T.GOLD_LIGHT, bg=T.BG_DEEP).pack(side="left")
        T.GoldButton(inner_hdr, text="✕ Close", command=self.top.destroy,
                     width=90, height=30, style="ghost").pack(side="right")

        T.Divider(top).pack(fill="x")

        body = tk.Frame(top, bg=T.BG_BASE)
        body.pack(fill="both", expand=True, padx=28, pady=20)

        # Algo badge
        badge_frame = tk.Frame(body, bg=T.BG_ELEMENT,
                               highlightbackground=T.BORDER_DIM,
                               highlightthickness=1)
        badge_frame.pack(fill="x", pady=(0, 20))
        badge_inner = tk.Frame(badge_frame, bg=T.BG_ELEMENT)
        badge_inner.pack(fill="x", padx=16, pady=12)

        tk.Label(badge_inner, text="Algorithm",
                 font=T.FONT_SMALL, fg=T.TEXT_SECONDARY, bg=T.BG_ELEMENT).pack(anchor="w")
        alg_row = tk.Frame(badge_inner, bg=T.BG_ELEMENT)
        alg_row.pack(fill="x", pady=(4, 0))
        for alg, color in [("AES-256-CBC", T.GOLD_MID), ("+", T.TEXT_SECONDARY), ("RSA-OAEP", T.BLUE_LIGHT)]:
            tk.Label(alg_row, text=alg, font=T.FONT_HEADING,
                     fg=color, bg=T.BG_ELEMENT).pack(side="left", padx=4)

        # ── Encrypt card ──────────────────────────────────────────────
        tk.Label(body, text="ENCRYPT",
                 font=T.FONT_SMALL, fg=T.TEXT_SECONDARY, bg=T.BG_BASE).pack(anchor="w", pady=(0, 6))

        enc_card = T.SectionCard(body)
        enc_card.pack(fill="x", pady=(0, 16))
        enc_inner = tk.Frame(enc_card, bg=T.BG_CARD)
        enc_inner.pack(fill="x", padx=16, pady=14)

        enc_txt = tk.Frame(enc_inner, bg=T.BG_CARD)
        enc_txt.pack(side="left", fill="x", expand=True)
        tk.Label(enc_txt, text="Encrypt a File",
                 font=T.FONT_HEADING, fg=T.TEXT_PRIMARY, bg=T.BG_CARD).pack(anchor="w")
        tk.Label(enc_txt, text="Requires recipient's public certificate (.pem)",
                 font=T.FONT_SMALL, fg=T.TEXT_SECONDARY, bg=T.BG_CARD).pack(anchor="w")

        T.GoldButton(enc_inner, text="Encrypt →", command=self.encrypt_file,
                     width=110, height=34, style="primary").pack(side="right")

        # ── Decrypt card ──────────────────────────────────────────────
        tk.Label(body, text="DECRYPT",
                 font=T.FONT_SMALL, fg=T.TEXT_SECONDARY, bg=T.BG_BASE).pack(anchor="w", pady=(0, 6))

        dec_card = T.SectionCard(body)
        dec_card.pack(fill="x")
        dec_inner = tk.Frame(dec_card, bg=T.BG_CARD)
        dec_inner.pack(fill="x", padx=16, pady=14)

        dec_txt = tk.Frame(dec_inner, bg=T.BG_CARD)
        dec_txt.pack(side="left", fill="x", expand=True)
        tk.Label(dec_txt, text="Decrypt a File",
                 font=T.FONT_HEADING, fg=T.TEXT_PRIMARY, bg=T.BG_CARD).pack(anchor="w")
        tk.Label(dec_txt, text="Requires your PKCS#12 identity file (.p12)",
                 font=T.FONT_SMALL, fg=T.TEXT_SECONDARY, bg=T.BG_CARD).pack(anchor="w")

        T.GoldButton(dec_inner, text="Decrypt →", command=self.decrypt_file,
                     width=110, height=34, style="secondary").pack(side="right")

        # ── Activity log ──────────────────────────────────────────────
        tk.Label(body, text="ACTIVITY LOG",
                 font=T.FONT_SMALL, fg=T.TEXT_SECONDARY, bg=T.BG_BASE).pack(anchor="w", pady=(20, 6))

        log_frame, self.log = T.make_scrolled_text(body, height=5)
        log_frame.pack(fill="x")
        self.log.configure(state="disabled")
        self._log("Ready. Select an operation above to begin.")

    # ─────────────────────────────────────────────────────────────────
    def _log(self, message: str, color=None):
        self.log.configure(state="normal")
        tag = f"col_{id(message)}"
        self.log.insert("end", f"› {message}\n", tag)
        self.log.tag_configure(tag, foreground=color or T.TEXT_SECONDARY)
        self.log.see("end")
        self.log.configure(state="disabled")

    # ─────────────────────────────────────────────────────────────────
    def encrypt_file(self):
        cert_file = filedialog.askopenfilename(
            title="Select Recipient's Certificate (.pem)",
            filetypes=[("PEM files", "*.pem"), ("All files", "*.*")])
        if not cert_file:
            return

        input_file = filedialog.askopenfilename(title="Select File to Encrypt")
        if not input_file:
            return

        output_file = filedialog.asksaveasfilename(
            title="Save Encrypted File",
            defaultextension=".enc",
            filetypes=[("Encrypted files", "*.enc")])
        if not output_file:
            return

        try:
            crypto_utils.encrypt_file_hybrid(cert_file, input_file, output_file)
            self._log(f"Encrypted: {os.path.basename(input_file)} → {os.path.basename(output_file)}", T.SUCCESS)
            messagebox.showinfo("Encrypted", f"File encrypted successfully:\n{output_file}")
        except Exception as e:
            self._log(f"Encryption failed: {e}", T.ERROR)
            messagebox.showerror("Encryption Failed", f"{e}")

    def decrypt_file(self):
        p12_file = filedialog.askopenfilename(
            title="Select Your PKCS#12 Identity",
            filetypes=[("PKCS#12 files", "*.p12")])
        if not p12_file:
            return

        password = simpledialog.askstring("Password", "Enter PKCS#12 password:", show="*")
        if password is None:
            return

        try:
            private_key, _ = cert_manager.load_registrar_identity(p12_file, password)
        except Exception as e:
            self._log(f"Identity load failed: {e}", T.ERROR)
            messagebox.showerror("Error", f"Could not load identity:\n{e}")
            return

        enc_file = filedialog.askopenfilename(
            title="Select Encrypted File",
            filetypes=[("Encrypted files", "*.enc")])
        if not enc_file:
            return

        output_file = filedialog.asksaveasfilename(
            title="Save Decrypted File",
            filetypes=[("All files", "*.*")])
        if not output_file:
            return

        try:
            crypto_utils.decrypt_file_hybrid(private_key, enc_file, output_file)
            self._log(f"Decrypted: {os.path.basename(enc_file)} → {os.path.basename(output_file)}", T.SUCCESS)
            messagebox.showinfo("Decrypted", f"File decrypted successfully:\n{output_file}")
        except Exception as e:
            self._log(f"Decryption failed: {e}", T.ERROR)
            messagebox.showerror("Decryption Failed", f"{e}")
