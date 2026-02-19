"""
truEdu Design System — Premium Dark Luxury Theme
A complete UI toolkit built on pure tkinter.
"""

import tkinter as tk
from tkinter import ttk
import platform

# ── Color Palette ─────────────────────────────────────────────────────────────
BG_DEEP      = "#0B0C10"   # deepest background
BG_BASE      = "#111318"   # main window background
BG_CARD      = "#191C24"   # card / panel background
BG_ELEMENT   = "#1F2330"   # input fields, secondary panels
BG_HOVER     = "#262B3A"   # hover state

BORDER_DIM   = "#252836"   # subtle dividers
BORDER_GLOW  = "#3A4060"   # active/focus borders

GOLD_LIGHT   = "#F5D07A"   # headlines, logo
GOLD_MID     = "#D4A853"   # primary accent
GOLD_DARK    = "#A07830"   # pressed / dark gold

BLUE_LIGHT   = "#82CFFF"   # secondary actions
BLUE_MID     = "#4A9ECC"   # secondary accent
BLUE_DARK    = "#2A6A99"   # pressed / dark blue

TEXT_PRIMARY  = "#E8EAF0"   # main body text
TEXT_SECONDARY= "#8A90A8"   # muted / label text
TEXT_DISABLED = "#4A5070"   # disabled state

SUCCESS      = "#3DCB7A"
WARNING      = "#F5A623"
ERROR        = "#E8455A"

# ── Typography ────────────────────────────────────────────────────────────────
_plat = platform.system()
if _plat == "Darwin":
    FONT_DISPLAY = ("SF Pro Display", 22, "bold")
    FONT_TITLE   = ("SF Pro Display", 15, "bold")
    FONT_HEADING = ("SF Pro Text",    12, "bold")
    FONT_BODY    = ("SF Pro Text",    11)
    FONT_SMALL   = ("SF Pro Text",     9)
    FONT_MONO    = ("SF Mono",         10)
elif _plat == "Windows":
    FONT_DISPLAY = ("Segoe UI",  22, "bold")
    FONT_TITLE   = ("Segoe UI",  15, "bold")
    FONT_HEADING = ("Segoe UI",  11, "bold")
    FONT_BODY    = ("Segoe UI",  10)
    FONT_SMALL   = ("Segoe UI",   8)
    FONT_MONO    = ("Consolas",  10)
else:
    FONT_DISPLAY = ("DejaVu Sans", 20, "bold")
    FONT_TITLE   = ("DejaVu Sans", 14, "bold")
    FONT_HEADING = ("DejaVu Sans", 11, "bold")
    FONT_BODY    = ("DejaVu Sans", 10)
    FONT_SMALL   = ("DejaVu Sans",  8)
    FONT_MONO    = ("DejaVu Sans Mono", 9)


# ── TTK Style Bootstrap ───────────────────────────────────────────────────────
def apply_theme(root: tk.Tk):
    """Apply the global dark-luxury ttk theme to the root window."""
    root.configure(bg=BG_BASE)
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure(".",
        background=BG_BASE,
        foreground=TEXT_PRIMARY,
        fieldbackground=BG_ELEMENT,
        bordercolor=BORDER_DIM,
        darkcolor=BG_DEEP,
        lightcolor=BG_CARD,
        troughcolor=BG_DEEP,
        selectbackground=GOLD_DARK,
        selectforeground=TEXT_PRIMARY,
        font=FONT_BODY,
        relief="flat",
    )
    style.configure("TFrame",       background=BG_BASE)
    style.configure("Card.TFrame",  background=BG_CARD)
    style.configure("TLabel",       background=BG_BASE,  foreground=TEXT_PRIMARY,  font=FONT_BODY)
    style.configure("Muted.TLabel", background=BG_CARD,  foreground=TEXT_SECONDARY, font=FONT_SMALL)
    style.configure("Title.TLabel", background=BG_BASE,  foreground=GOLD_LIGHT,    font=FONT_TITLE)
    style.configure("TScrollbar",   background=BG_ELEMENT, arrowcolor=TEXT_SECONDARY, bordercolor=BG_BASE, troughcolor=BG_BASE)
    style.configure("TSeparator",   background=BORDER_DIM)
    style.map("TScrollbar", background=[("active", BG_HOVER)])


# ── Canvas Helpers ────────────────────────────────────────────────────────────
def _round_rect(canvas: tk.Canvas, x1, y1, x2, y2, r=12, **kw):
    """Draw a rounded rectangle on a canvas."""
    pts = [
        x1+r, y1,  x2-r, y1,   x2, y1,   x2, y1+r,
        x2,   y2-r, x2,  y2,   x2-r, y2, x1+r, y2,
        x1,   y2,  x1,   y2-r, x1,  y2-r, x1, y1+r,
        x1,   y1,  x1+r, y1,
    ]
    return canvas.create_polygon(pts, smooth=True, **kw)


# ── Custom Widgets ────────────────────────────────────────────────────────────

class GoldButton(tk.Canvas):
    """A canvas-based rounded button with solid colours and hover/press states."""

    def __init__(self, parent, text="", command=None, width=200, height=42,
                 style="primary", **kw):
        kw.setdefault("highlightthickness", 0)
        kw.setdefault("bd", 0)
        super().__init__(parent, width=width, height=height,
                         bg=parent.cget("bg"), **kw)

        self._text    = text
        self._command = command
        self._width   = width
        self._height  = height
        self._style   = style
        self._hover   = False
        self._pressed = False

        # (normal, hover, pressed, text_color)
        self._colors = {
            "primary":   (GOLD_MID,    GOLD_LIGHT,  GOLD_DARK,   BG_DEEP),
            "secondary": (BLUE_MID,    BLUE_LIGHT,  BLUE_DARK,   BG_DEEP),
            "ghost":     (BG_ELEMENT,  BG_HOVER,    BG_DEEP,     GOLD_MID),
            "danger":    (ERROR,       "#F06070",   "#B03040",   BG_DEEP),
        }[style]

        self._draw()
        self.bind("<Enter>",           self._on_enter)
        self.bind("<Leave>",           self._on_leave)
        self.bind("<ButtonPress-1>",   self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _draw(self):
        self.delete("all")
        w, h = self._width, self._height
        normal, hover_c, pressed_c, text_color = self._colors

        if self._pressed:
            fill = pressed_c
        elif self._hover:
            fill = hover_c
        else:
            fill = normal

        # Solid rounded rectangle — no shadow, no shine
        _round_rect(self, 0, 0, w, h, r=10, fill=fill, outline="")

        # Text colour: ghost button uses gold text; others use the defined text_color
        if self._style == "ghost":
            tc = GOLD_LIGHT if self._hover else GOLD_MID
        else:
            tc = text_color

        self.create_text(w // 2, h // 2, text=self._text,
                         fill=tc, font=FONT_HEADING, anchor="center")

    def _on_enter(self, e):
        self._hover = True;   self._draw()

    def _on_leave(self, e):
        self._hover = False;  self._draw()

    def _on_press(self, e):
        self._pressed = True; self._draw()

    def _on_release(self, e):
        self._pressed = False; self._draw()
        if self._command:
            self._command()

    def configure_state(self, state):
        if state == "disabled":
            self._command = None
            self._colors = (TEXT_DISABLED, TEXT_DISABLED, TEXT_DISABLED, BG_BASE)
        self._draw()


class IconBadge(tk.Canvas):
    """A small circular badge for status indicators."""
    def __init__(self, parent, color=SUCCESS, size=10, **kw):
        kw.setdefault("highlightthickness", 0)
        kw.setdefault("bd", 0)
        bg = parent.cget("bg")
        super().__init__(parent, width=size, height=size, bg=bg, **kw)
        self.create_oval(1, 1, size-1, size-1, fill=color, outline="")


class SectionCard(tk.Frame):
    """A card-style container with rounded border and subtle background."""
    def __init__(self, parent, **kw):
        kw.setdefault("bg", BG_CARD)
        kw.setdefault("relief", "flat")
        kw.setdefault("bd", 0)
        super().__init__(parent, **kw)
        self.configure(highlightbackground=BORDER_DIM,
                        highlightthickness=1,
                        highlightcolor=BORDER_GLOW)


class StatusLabel(tk.Label):
    """A dynamic status label that changes color based on state."""
    def __init__(self, parent, **kw):
        kw.setdefault("font", FONT_SMALL)
        kw.setdefault("bg", parent.cget("bg"))
        super().__init__(parent, **kw)
        self.set_state("idle")

    def set_state(self, state: str, text: str = ""):
        colors = {
            "idle":    (TEXT_DISABLED, "● Idle"),
            "ok":      (SUCCESS,       f"✓ {text}" if text else "✓ Ready"),
            "error":   (ERROR,         f"✗ {text}" if text else "✗ Error"),
            "warning": (WARNING,       f"⚠ {text}" if text else "⚠ Warning"),
            "loading": (BLUE_LIGHT,    f"◌ {text}" if text else "◌ Loading…"),
        }
        color, label = colors.get(state, colors["idle"])
        self.configure(fg=color, text=label)


class StyledEntry(tk.Entry):
    """A styled dark-themed entry widget."""
    def __init__(self, parent, placeholder="", **kw):
        kw.setdefault("bg", BG_ELEMENT)
        kw.setdefault("fg", TEXT_PRIMARY)
        kw.setdefault("insertbackground", GOLD_MID)
        kw.setdefault("relief", "flat")
        kw.setdefault("font", FONT_BODY)
        kw.setdefault("bd", 0)
        super().__init__(parent, **kw)
        self._placeholder = placeholder
        self._ph_color    = TEXT_DISABLED
        self._showing_ph  = False
        self.configure(highlightbackground=BORDER_DIM,
                       highlightthickness=1,
                       highlightcolor=GOLD_MID)
        if placeholder:
            self._show_placeholder()
        self.bind("<FocusIn>",  self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)

    def _show_placeholder(self):
        self.insert(0, self._placeholder)
        self.configure(fg=self._ph_color)
        self._showing_ph = True

    def _on_focus_in(self, e):
        if self._showing_ph:
            self.delete(0, "end")
            self.configure(fg=TEXT_PRIMARY)
            self._showing_ph = False

    def _on_focus_out(self, e):
        if not self.get() and self._placeholder:
            self._show_placeholder()

    def get_value(self):
        return "" if self._showing_ph else self.get()


class Divider(tk.Frame):
    """A thin horizontal divider."""
    def __init__(self, parent, **kw):
        kw.setdefault("bg", BORDER_DIM)
        kw.setdefault("height", 1)
        super().__init__(parent, **kw)


def make_scrolled_text(parent, height=8, **kw):
    """Create a dark-styled scrollable Text widget."""
    frame = tk.Frame(parent, bg=BG_ELEMENT,
                     highlightbackground=BORDER_DIM,
                     highlightthickness=1)
    sb = tk.Scrollbar(frame, bg=BG_ELEMENT, troughcolor=BG_DEEP,
                      activebackground=BG_HOVER, relief="flat", bd=0, width=10)
    txt = tk.Text(frame, bg=BG_ELEMENT, fg=TEXT_PRIMARY,
                  insertbackground=GOLD_MID, relief="flat", bd=0,
                  font=FONT_MONO, height=height, wrap="word",
                  yscrollcommand=sb.set, selectbackground=GOLD_DARK,
                  **kw)
    sb.config(command=txt.yview)
    txt.pack(side="left", fill="both", expand=True, padx=6, pady=4)
    sb.pack(side="right", fill="y")
    return frame, txt


def label(parent, text, style="body", **kw):
    """Convenience: make a styled label."""
    configs = {
        "display": dict(font=FONT_DISPLAY, fg=GOLD_LIGHT,     bg=parent.cget("bg")),
        "title":   dict(font=FONT_TITLE,   fg=GOLD_LIGHT,     bg=parent.cget("bg")),
        "heading": dict(font=FONT_HEADING, fg=TEXT_PRIMARY,   bg=parent.cget("bg")),
        "body":    dict(font=FONT_BODY,    fg=TEXT_PRIMARY,   bg=parent.cget("bg")),
        "muted":   dict(font=FONT_SMALL,   fg=TEXT_SECONDARY, bg=parent.cget("bg")),
        "gold":    dict(font=FONT_HEADING, fg=GOLD_MID,       bg=parent.cget("bg")),
        "mono":    dict(font=FONT_MONO,    fg=TEXT_PRIMARY,   bg=parent.cget("bg")),
    }
    cfg = configs.get(style, configs["body"])
    cfg.update(kw)
    return tk.Label(parent, text=text, **cfg)