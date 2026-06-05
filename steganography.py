"""
Image Steganography Tool
Hides secret text messages inside image files using LSB (Least Significant Bit) technique.

Author: Chaitanya Bikkina
B.Tech CS (Cyber Security) — Malla Reddy University

Fixes vs original:
  - Proper UTF-8 encoding (original had overflow bug for non-ASCII / emoji)
  - Uses image.load() instead of deprecated getdata()
  - Threading keeps UI responsive during encode/decode
  - Image preview with size & capacity info on Decode tab
  - Live character counter with capacity warning on Encode tab
  - Copy-to-clipboard button on decoded result
"""

import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import os
import threading


# ══════════════════════════════════════════════
#  COLOUR PALETTE  (matches presentation theme)
# ══════════════════════════════════════════════
BG_DARK    = "#0b0f1e"
BG_CARD    = "#111827"
BG_INPUT   = "#0d1117"
BORDER     = "#1e2d40"
TEAL       = "#00d4aa"
TEAL_DIM   = "#00a884"
TEAL_DARK  = "#004d3e"
PURPLE     = "#7c6bff"
TEXT_MAIN  = "#e2e8f0"
TEXT_MUTED = "#4a6070"
TEXT_LABEL = "#8fa8be"
SUCCESS    = "#00d4aa"
ERROR_RED  = "#ff5f5f"


# ══════════════════════════════════════════════
#  CORE STEGANOGRAPHY LOGIC  (LSB technique)
# ══════════════════════════════════════════════
DELIMITER = b"$$END$$"   # byte-level sentinel


def _image_pixels(image_path: str):
    """Return (pixels list, width, height) — uses image.load() (not deprecated getdata)."""
    image = Image.open(image_path).convert("RGB")
    w, h  = image.size
    px    = image.load()
    flat  = [px[x, y] for y in range(h) for x in range(w)]
    return flat, w, h


def image_capacity(image_path: str) -> int:
    """Max bytes storable = (pixels × 3) // 8 minus delimiter length."""
    image = Image.open(image_path).convert("RGB")
    w, h  = image.size
    return (w * h * 3) // 8 - len(DELIMITER)


def encode_message(image_path: str, message: str, output_path: str) -> int:
    """Embed *message* (UTF-8) into image via LSB. Saves lossless PNG."""
    msg_bytes   = message.encode("utf-8")
    payload     = msg_bytes + DELIMITER
    max_bytes   = image_capacity(image_path)

    if len(msg_bytes) > max_bytes:
        raise ValueError(
            f"Message too long!\n"
            f"  Message size : {len(msg_bytes):,} bytes\n"
            f"  Image capacity: {max_bytes:,} bytes"
        )

    # Convert payload to a flat bit-string
    bits = "".join(format(b, "08b") for b in payload)

    pixels, w, h = _image_pixels(image_path)
    bit_index    = 0
    new_pixels   = []

    for (r, g, b) in pixels:
        ch = [r, g, b]
        for i in range(3):
            if bit_index < len(bits):
                ch[i]      = (ch[i] & ~1) | int(bits[bit_index])
                bit_index += 1
        new_pixels.append(tuple(ch))

    out = Image.new("RGB", (w, h))
    out.putdata(new_pixels)
    out.save(output_path, "PNG")
    return len(msg_bytes)


def decode_message(image_path: str) -> str:
    """Extract hidden UTF-8 text from a steganographic image."""
    pixels, _, _ = _image_pixels(image_path)

    bits = "".join(str(ch & 1) for (r, g, b) in pixels for ch in (r, g, b))

    raw = bytearray()
    for i in range(0, len(bits), 8):
        byte = bits[i: i + 8]
        if len(byte) < 8:
            break
        raw.append(int(byte, 2))
        if raw[-len(DELIMITER):] == DELIMITER:
            payload = bytes(raw[: -len(DELIMITER)])
            try:
                return payload.decode("utf-8")
            except UnicodeDecodeError:
                raise ValueError("Hidden data found but could not be decoded as UTF-8 text.")

    raise ValueError(
        "No hidden message found in this image.\n"
        "Make sure you selected the correct encoded PNG file."
    )


# ══════════════════════════════════════════════
#  TOOLTIP HELPER
# ══════════════════════════════════════════════

class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text   = text
        self.tip    = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, _=None):
        x = self.widget.winfo_rootx() + 24
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        tk.Label(self.tip, text=self.text, font=("Consolas", 9),
                 bg="#1e2d40", fg=TEXT_LABEL, padx=8, pady=4).pack()

    def hide(self, _=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None


# ══════════════════════════════════════════════
#  MAIN APPLICATION
# ══════════════════════════════════════════════

class SteganographyApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Image Steganography Tool")
        self.root.geometry("660x620")
        self.root.minsize(620, 580)
        self.root.configure(bg=BG_DARK)

        self._encode_image_path = ""
        self._decode_image_path = ""
        self._preview_photo     = None
        self._active_btn        = None

        self._build_shell()
        self._show_encode()

    # ─── Shell (header + tabs + card) ──────────

    def _build_shell(self):
        # Header
        hdr = tk.Frame(self.root, bg=BG_DARK)
        hdr.pack(fill="x", padx=32, pady=(26, 0))

        cvs = tk.Canvas(hdr, width=44, height=44, bg=BG_DARK, highlightthickness=0)
        cvs.pack(side="left")
        cvs.create_oval(2, 2, 42, 42, fill=TEAL_DARK, outline=TEAL, width=2)
        cvs.create_text(22, 22, text="🔒", font=("Segoe UI Emoji", 16))

        blk = tk.Frame(hdr, bg=BG_DARK)
        blk.pack(side="left", padx=(12, 0))
        tk.Label(blk, text="Image Steganography Tool",
                 font=("Consolas", 18, "bold"), fg=TEAL, bg=BG_DARK).pack(anchor="w")
        tk.Label(blk, text="Hide secret messages inside images using LSB technique",
                 font=("Consolas", 9), fg=TEXT_MUTED, bg=BG_DARK).pack(anchor="w")

        tk.Frame(self.root, height=1, bg=BORDER).pack(fill="x", padx=32, pady=(14, 0))

        # Tab row
        tabs = tk.Frame(self.root, bg=BG_DARK)
        tabs.pack(pady=(16, 0))
        self.btn_encode = self._make_tab(tabs, "ENCODE", self._show_encode)
        self.btn_encode.pack(side="left", padx=(0, 6))
        self.btn_decode = self._make_tab(tabs, "DECODE", self._show_decode)
        self.btn_decode.pack(side="left")

        # Content card
        self.card = tk.Frame(self.root, bg=BG_CARD,
                             highlightthickness=1, highlightbackground=BORDER)
        self.card.pack(fill="both", expand=True, padx=32, pady=(14, 26))

    # ─── Widget factories ───────────────────────

    def _make_tab(self, parent, text, cmd):
        btn = tk.Button(parent, text=text, command=cmd,
                        font=("Consolas", 11, "bold"), width=12, pady=7,
                        bg=BG_DARK, fg=TEXT_MUTED,
                        activebackground=TEAL_DARK, activeforeground=TEAL,
                        relief="flat", bd=0, cursor="hand2")
        btn.bind("<Enter>",
                 lambda e, b=btn: b.config(fg=TEXT_MAIN) if b is not self._active_btn else None)
        btn.bind("<Leave>",
                 lambda e, b=btn: b.config(fg=TEAL if b is self._active_btn else TEXT_MUTED))
        return btn

    def _lbl(self, parent, text):
        return tk.Label(parent, text=text, font=("Consolas", 9, "bold"),
                        fg=TEXT_LABEL, bg=BG_CARD, anchor="w")

    def _entry(self, parent):
        return tk.Entry(parent, font=("Consolas", 11), bg=BG_INPUT, fg=TEXT_MAIN,
                        insertbackground=TEAL, relief="flat",
                        highlightthickness=1, highlightbackground=BORDER, highlightcolor=TEAL)

    def _textbox(self, parent, height, fg=TEXT_MAIN, state="normal"):
        t = tk.Text(parent, height=height, wrap="word",
                    font=("Consolas", 11), bg=BG_INPUT, fg=fg,
                    insertbackground=TEAL, relief="flat",
                    highlightthickness=1, highlightbackground=BORDER,
                    highlightcolor=TEAL, state=state)
        return t

    def _browse_btn(self, parent, cmd, tip=""):
        b = tk.Button(parent, text="Browse", command=cmd,
                      font=("Consolas", 9, "bold"), fg=TEXT_LABEL, bg=BORDER,
                      activebackground="#253040", activeforeground=TEXT_MAIN,
                      relief="flat", bd=0, cursor="hand2", padx=10, pady=6)
        b.bind("<Enter>", lambda e: b.config(bg="#253040"))
        b.bind("<Leave>", lambda e: b.config(bg=BORDER))
        if tip:
            Tooltip(b, tip)
        return b

    def _action_btn(self, parent, text, cmd, color=TEAL, hover=TEAL_DIM):
        b = tk.Button(parent, text=text, command=cmd,
                      font=("Consolas", 13, "bold"), bg=color, fg=BG_DARK,
                      activebackground=hover, activeforeground=BG_DARK,
                      relief="flat", bd=0, cursor="hand2", pady=11)
        b.bind("<Enter>", lambda e: b.config(bg=hover))
        b.bind("<Leave>", lambda e: b.config(bg=color))
        return b

    def _status(self, parent):
        return tk.Label(parent, text="", font=("Consolas", 9),
                        bg=BG_CARD, fg=SUCCESS, anchor="w")

    # ─── Encode tab ─────────────────────────────

    def _show_encode(self):
        self._active_btn = self.btn_encode
        self.btn_encode.config(bg=TEAL_DARK, fg=TEAL)
        self.btn_decode.config(bg=BG_DARK,   fg=TEXT_MUTED)
        self._clear_card()

        P = dict(padx=20)

        self._lbl(self.card, "Select Image:").pack(anchor="w", padx=20, pady=(18, 3))

        img_row = tk.Frame(self.card, bg=BG_CARD)
        img_row.pack(fill="x", **P)
        self._enc_img_var = tk.StringVar(value="No image selected")
        tk.Label(img_row, textvariable=self._enc_img_var,
                 font=("Consolas", 9), fg=TEXT_MUTED, bg=BG_INPUT,
                 anchor="w", padx=10, highlightthickness=1,
                 highlightbackground=BORDER).pack(side="left", fill="x", expand=True, ipady=7)
        self._browse_btn(img_row, self._browse_encode_image,
                         tip="PNG, JPG, or BMP supported").pack(side="right", padx=(6, 0))

        # Capacity hint
        self._cap_lbl = tk.Label(self.card, text="", font=("Consolas", 8),
                                 fg=TEXT_MUTED, bg=BG_CARD, anchor="w")
        self._cap_lbl.pack(anchor="w", padx=20, pady=(3, 0))

        # Message header row
        mhdr = tk.Frame(self.card, bg=BG_CARD)
        mhdr.pack(fill="x", padx=20, pady=(12, 3))
        self._lbl(mhdr, "Secret Message:").pack(side="left")
        self._char_lbl = tk.Label(mhdr, text="0 chars", font=("Consolas", 8),
                                  fg=TEXT_MUTED, bg=BG_CARD)
        self._char_lbl.pack(side="right")

        self._msg_txt = self._textbox(self.card, height=6)
        self._msg_txt.pack(fill="x", padx=20)
        self._msg_txt.bind("<KeyRelease>", self._update_char_count)

        self._lbl(self.card, "Output File Name (without extension):").pack(
            anchor="w", padx=20, pady=(12, 3))
        self._out_ent = self._entry(self.card)
        self._out_ent.pack(fill="x", padx=20, ipady=7)
        self._out_ent.insert(0, "encoded_image")

        self._enc_btn = self._action_btn(self.card, "🔒  HIDE MESSAGE", self._do_encode)
        self._enc_btn.pack(fill="x", padx=20, pady=(18, 0))

        self._enc_stat = self._status(self.card)
        self._enc_stat.pack(anchor="w", padx=20, pady=(8, 4))

    def _browse_encode_image(self):
        path = filedialog.askopenfilename(
            title="Select Source Image",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp"), ("All Files", "*.*")])
        if not path:
            return
        self._encode_image_path = path
        self._enc_img_var.set(os.path.basename(path))
        try:
            cap = image_capacity(path)
            kb  = os.path.getsize(path) // 1024
            img = Image.open(path)
            w, h = img.size
            self._cap_lbl.config(
                text=f"  {w}×{h} px  •  {kb} KB  •  Capacity: {cap:,} chars")
        except Exception:
            self._cap_lbl.config(text="")
        self._update_char_count()

    def _update_char_count(self, _=None):
        text  = self._msg_txt.get("1.0", "end-1c")
        nbytes = len(text.encode("utf-8"))
        self._char_lbl.config(text=f"{len(text):,} chars / {nbytes:,} bytes")
        if self._encode_image_path:
            try:
                cap   = image_capacity(self._encode_image_path)
                color = SUCCESS if nbytes <= cap else ERROR_RED
                self._char_lbl.config(fg=color)
                return
            except Exception:
                pass
        self._char_lbl.config(fg=TEXT_MUTED)

    def _do_encode(self):
        path    = self._encode_image_path
        message = self._msg_txt.get("1.0", "end-1c").strip()
        name    = self._out_ent.get().strip() or "encoded_image"

        if not path:
            self._set_stat(self._enc_stat, "⚠  Please select a source image.", ERROR_RED); return
        if not message:
            self._set_stat(self._enc_stat, "⚠  Please enter a secret message.", ERROR_RED); return

        save = filedialog.asksaveasfilename(
            defaultextension=".png", initialfile=name,
            filetypes=[("PNG Image", "*.png")], title="Save Encoded Image")
        if not save:
            return

        self._enc_btn.config(state="disabled", text="Encoding…")
        self._set_stat(self._enc_stat, "Processing…", TEXT_MUTED)

        def worker():
            try:
                encode_message(path, message, save)
                msg = f"✅  Message hidden!  Saved as: {os.path.basename(save)}"
                self.root.after(0, lambda: (
                    self._set_stat(self._enc_stat, msg, SUCCESS),
                    self._enc_btn.config(state="normal", text="🔒  HIDE MESSAGE")))
            except Exception as exc:
                err = str(exc)
                self.root.after(0, lambda: (
                    self._set_stat(self._enc_stat, f"✗  {err}", ERROR_RED),
                    self._enc_btn.config(state="normal", text="🔒  HIDE MESSAGE")))

        threading.Thread(target=worker, daemon=True).start()

    # ─── Decode tab ─────────────────────────────

    def _show_decode(self):
        self._active_btn = self.btn_decode
        self.btn_decode.config(bg=TEAL_DARK, fg=TEAL)
        self.btn_encode.config(bg=BG_DARK,   fg=TEXT_MUTED)
        self._clear_card()

        self._lbl(self.card, "Select Encoded Image:").pack(anchor="w", padx=20, pady=(18, 3))

        img_row = tk.Frame(self.card, bg=BG_CARD)
        img_row.pack(fill="x", padx=20)
        self._dec_img_var = tk.StringVar(value="No image selected")
        tk.Label(img_row, textvariable=self._dec_img_var,
                 font=("Consolas", 9), fg=TEXT_MUTED, bg=BG_INPUT,
                 anchor="w", padx=10, highlightthickness=1,
                 highlightbackground=BORDER).pack(side="left", fill="x", expand=True, ipady=7)
        self._browse_btn(img_row, self._browse_decode_image,
                         tip="Select a PNG with a hidden message").pack(side="right", padx=(6, 0))

        # Preview strip
        prev_row = tk.Frame(self.card, bg=BG_CARD)
        prev_row.pack(fill="x", padx=20, pady=(8, 0))
        self._prev_cvs = tk.Canvas(prev_row, width=80, height=58, bg=BG_INPUT,
                                   highlightthickness=1, highlightbackground=BORDER)
        self._prev_cvs.pack(side="left")
        self._prev_info = tk.Label(prev_row, text="Select an image\nto preview",
                                   font=("Consolas", 8), fg=TEXT_MUTED,
                                   bg=BG_CARD, justify="left", anchor="w", padx=10)
        self._prev_info.pack(side="left")

        self._dec_btn = self._action_btn(
            self.card, "🔍  REVEAL MESSAGE", self._do_decode, PURPLE, "#5e52d0")
        self._dec_btn.bind("<Enter>", lambda e: self._dec_btn.config(bg="#5e52d0"))
        self._dec_btn.bind("<Leave>", lambda e: self._dec_btn.config(bg=PURPLE))
        self._dec_btn.pack(fill="x", padx=20, pady=(16, 0))

        # Result header
        rhdr = tk.Frame(self.card, bg=BG_CARD)
        rhdr.pack(fill="x", padx=20, pady=(14, 3))
        self._lbl(rhdr, "Hidden Message:").pack(side="left")
        self._copy_btn = tk.Button(rhdr, text="Copy", command=self._copy_result,
                                   font=("Consolas", 8), fg=TEXT_MUTED, bg=BORDER,
                                   relief="flat", bd=0, cursor="hand2", padx=8, pady=3)
        self._copy_btn.pack(side="right")

        self._res_txt = self._textbox(self.card, height=7, fg=TEAL, state="disabled")
        self._res_txt.pack(fill="x", padx=20)

        self._dec_stat = self._status(self.card)
        self._dec_stat.pack(anchor="w", padx=20, pady=(6, 4))

    def _browse_decode_image(self):
        path = filedialog.askopenfilename(
            title="Select Encoded PNG", filetypes=[("PNG Image", "*.png"), ("All Files", "*.*")])
        if not path:
            return
        self._decode_image_path = path
        self._dec_img_var.set(os.path.basename(path))
        self._set_stat(self._dec_stat, "", SUCCESS)
        try:
            img = Image.open(path).convert("RGB")
            w, h = img.size
            thumb = img.copy()
            thumb.thumbnail((80, 58))
            self._preview_photo = ImageTk.PhotoImage(thumb)
            self._prev_cvs.delete("all")
            self._prev_cvs.create_image(40, 29, image=self._preview_photo)
            kb  = os.path.getsize(path) // 1024
            cap = image_capacity(path)
            self._prev_info.config(
                text=f"{w}×{h} px\n{kb} KB\nCapacity: {cap:,} chars")
        except Exception:
            pass

    def _do_decode(self):
        path = self._decode_image_path
        if not path:
            self._set_stat(self._dec_stat, "⚠  Please select an encoded image.", ERROR_RED); return

        self._dec_btn.config(state="disabled", text="Decoding…")
        self._set_stat(self._dec_stat, "Extracting hidden bits…", TEXT_MUTED)

        def worker():
            try:
                message = decode_message(path)
                def update():
                    self._res_txt.config(state="normal")
                    self._res_txt.delete("1.0", "end")
                    self._res_txt.insert("1.0", message)
                    self._res_txt.config(state="disabled")
                    self._set_stat(self._dec_stat,
                                   f"✅  Decoded — {len(message)} characters found.", SUCCESS)
                    self._dec_btn.config(state="normal", text="🔍  REVEAL MESSAGE")
                self.root.after(0, update)
            except Exception as exc:
                err = str(exc)
                self.root.after(0, lambda: (
                    self._set_stat(self._dec_stat, f"✗  {err}", ERROR_RED),
                    self._dec_btn.config(state="normal", text="🔍  REVEAL MESSAGE")))

        threading.Thread(target=worker, daemon=True).start()

    def _copy_result(self):
        self._res_txt.config(state="normal")
        text = self._res_txt.get("1.0", "end-1c")
        self._res_txt.config(state="disabled")
        if text:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self._copy_btn.config(text="Copied!", fg=SUCCESS)
            self.root.after(1800, lambda: self._copy_btn.config(text="Copy", fg=TEXT_MUTED))

    # ─── Shared helpers ──────────────────────────

    def _clear_card(self):
        for w in self.card.winfo_children():
            w.destroy()

    def _set_stat(self, label, text, color):
        label.config(text=text, fg=color)


# ══════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════

if __name__ == "__main__":
    root = tk.Tk()
    try:                          # HiDPI on Windows
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    SteganographyApp(root)
    root.mainloop()
