import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog
import os
import sys
from PIL import Image, ImageTk

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gui.registrar_window import RegistrarWindow
from gui.employer_window import EmployerWindow
from gui.encryption_window import EncryptionWindow
import cert_manager
from gui import theme as T


class MainApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("truEdu — Certificate Verification System")
        self.root.geometry("520x640")
        self.root.resizable(False, False)
        self.root.configure(bg=T.BG_BASE)
        T.apply_theme(root)

        self._check_ca()
        self._build_ui()

    # -----------------------------
    # Certificate Authority Check
    # -----------------------------
    def _check_ca(self):
        if not os.path.exists(cert_manager.CA_CERT_FILE):
            if messagebox.askyesno(
                "Certificate Authority Missing",
                "No Certificate Authority found.\nCreate a new one now?"
            ):
                password = simpledialog.askstring(
                    "Protect CA Key",
                    "Enter a password to protect the CA private key:",
                    show="*",
                )
                if password:
                    cert_manager.create_self_signed_ca(password)
                    messagebox.showinfo("Success", "Certificate Authority created.")
                else:
                    messagebox.showerror("Cancelled", "CA creation cancelled.")
                    self.root.quit()
            else:
                messagebox.showerror("Error", "A CA is required to run truEdu.")
                self.root.quit()

    # -----------------------------
    # UI Construction
    # -----------------------------
    def _build_ui(self):
        root = self.root

        # Hero Section
        hero = tk.Frame(root, bg=T.BG_DEEP, height=220)
        hero.pack(fill="x")
        hero.pack_propagate(False)

        tk.Frame(hero, bg=T.GOLD_MID, height=3).pack(fill="x")

        # Load Logo
        self._load_logo(hero)

        tk.Label(
            hero,
            text="truEdu",
            font=T.FONT_DISPLAY,
            fg=T.GOLD_LIGHT,
            bg=T.BG_DEEP
        ).pack()

        tk.Label(
            hero,
            text="Certificate Verification System",
            font=T.FONT_SMALL,
            fg=T.TEXT_SECONDARY,
            bg=T.BG_DEEP
        ).pack(pady=(4, 0))

        T.Divider(root).pack(fill="x")

        # Center Content
        centre = tk.Frame(root, bg=T.BG_BASE)
        centre.pack(fill="both", expand=True, padx=44, pady=28)

        tk.Label(
            centre,
            text="Select a Module",
            font=T.FONT_HEADING,
            fg=T.TEXT_SECONDARY,
            bg=T.BG_BASE
        ).pack(anchor="w", pady=(0, 14))

        modules = [
            ("🎓  Registrar Portal",  "Issue & manage student certificates",  self.open_registrar,  "primary"),
            ("🏢  Employer Verifier", "Verify authenticity of signed docs",    self.open_employer,   "secondary"),
            ("🔐  Hybrid Encryption", "AES-256 + RSA file encryption",         self.open_encryption, "ghost"),
        ]

        for title, subtitle, cmd, style in modules:
            self._module_row(centre, title, subtitle, cmd, style)

        # Footer
        footer = tk.Frame(root, bg=T.BG_DEEP)
        footer.pack(fill="x", side="bottom")

        T.Divider(footer).pack(fill="x")

        bot = tk.Frame(footer, bg=T.BG_DEEP)
        bot.pack(fill="x", padx=24, pady=12)

        tk.Label(
            bot,
            text="© 2024 truEdu  ·  Cryptographic Certificate System",
            font=T.FONT_SMALL,
            fg=T.TEXT_DISABLED,
            bg=T.BG_DEEP
        ).pack(side="left")

        T.GoldButton(
            bot,
            text="Quit",
            command=root.quit,
            width=80,
            height=30,
            style="danger"
        ).pack(side="right")

    # -----------------------------
    # Logo Loader
    # -----------------------------        
    def _load_logo(self, parent):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(base_dir, "assets", "logo.png")

        if not os.path.exists(logo_path):
            tk.Label(
                parent,
                text=f"[Logo Missing]\n{logo_path}",
                fg="red",
                bg=T.BG_DEEP
            ).pack(pady=(20, 6))
            return

        img = Image.open(logo_path)
        img = img.resize((90, 90), Image.LANCZOS)

        self.logo_img = ImageTk.PhotoImage(img)

        tk.Label(
            parent,
            image=self.logo_img,
            bg=T.BG_DEEP
        ).pack(pady=(20, 6))


    # -----------------------------
    # Module Row Builder
    # -----------------------------
    def _module_row(self, parent, title, subtitle, command, btn_style):
        card = T.SectionCard(parent)
        card.pack(fill="x", pady=7)

        inner = tk.Frame(card, bg=T.BG_CARD)
        inner.pack(fill="x", padx=16, pady=14)

        txt = tk.Frame(inner, bg=T.BG_CARD)
        txt.pack(side="left", fill="x", expand=True)

        tk.Label(
            txt,
            text=title,
            font=T.FONT_HEADING,
            fg=T.TEXT_PRIMARY,
            bg=T.BG_CARD,
            anchor="w"
        ).pack(fill="x")

        tk.Label(
            txt,
            text=subtitle,
            font=T.FONT_SMALL,
            fg=T.TEXT_SECONDARY,
            bg=T.BG_CARD,
            anchor="w"
        ).pack(fill="x")

        T.GoldButton(
            inner,
            text="Open →",
            command=command,
            width=100,
            height=34,
            style=btn_style
        ).pack(side="right")

    # -----------------------------
    # Window Openers
    # -----------------------------
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
