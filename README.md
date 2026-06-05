# 🔒 Image Steganography Tool

A Python desktop application that hides secret text messages inside image files using the **LSB (Least Significant Bit)** steganography technique — changes are completely invisible to the human eye.

---

## What It Does

| Feature | Description |
|---|---|
| **Encode** | Hides any text message (including emoji & Unicode) inside a PNG/JPG/BMP image |
| **Decode** | Extracts the hidden message from an encoded image |
| **GUI** | Dark-themed desktop UI built with Tkinter |
| **Invisible** | Encoded images look pixel-for-pixel identical to the original |
| **Live counter** | Shows character count vs. image capacity while you type |
| **Preview** | Thumbnail + image info shown before decoding |
| **Copy button** | One-click copy of the decoded message |

---

## How It Works (LSB Technique)

Every image is made of pixels. Each pixel has R, G, B values (0–255 = 8 bits each).  
Changing only the **last bit** (LSB) shifts a colour value by 1 — completely invisible.

```
R: 200 = 11001000   →   11001001  (bit changed, colour shifts by 1)
G: 150 = 10010110   →   10010110  (no change needed)
B:  80 = 01010000   →   01010001  (bit changed)
```

The message is UTF-8 encoded to bytes, converted to bits, then written one bit per colour channel. A `$$END$$` byte sentinel marks the end so decoding knows where to stop.

---

## Fixes vs. Original Code

| Issue | Fix |
|---|---|
| **Unicode / emoji bug** — `format(ord(ch), '08b')` overflows for chars > U+00FF | Switched to `message.encode('utf-8')` — correct byte-level encoding |
| **Pillow deprecation warning** — `image.getdata()` deprecated in Pillow 10+ | Replaced with `image.load()` |
| **UI freezes on large images** | Encode/decode now run in a background thread |
| **No feedback during processing** | Button disables + status label shows progress |
| **No capacity info** | Image capacity (bytes) shown after browsing |
| **No message length feedback** | Live char/byte counter with red warning if over capacity |

---

## Getting Started

### Prerequisites
- Python 3.8+
- pip

### Installation

```bash
# 1. Clone / download the project
cd image-steganography

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
python steganography.py
```

---

## How To Use

### Hiding a Message (Encode)
1. Click the **ENCODE** tab
2. Click **Browse** → select any PNG, JPG, or BMP image
3. Type your secret message (emoji and Unicode supported)
4. Set an output file name
5. Click **🔒 HIDE MESSAGE** and choose where to save

### Revealing a Message (Decode)
1. Click the **DECODE** tab
2. Click **Browse** → select the encoded PNG
3. Click **🔍 REVEAL MESSAGE**
4. The hidden text appears in teal; click **Copy** to copy it

> ⚠️ **Always save encoded images as `.png`.**  
> JPG uses lossy compression which corrupts the hidden bits.

---

## Project Structure

```
image-steganography/
├── steganography.py     # Main application (UI + logic)
├── requirements.txt     # Python dependencies (Pillow)
└── README.md            # This file
```

---

## Technologies Used

- **Python 3** — Core language  
- **Tkinter** — Desktop GUI (built into Python, no install needed)  
- **Pillow (PIL)** — Image open / save / pixel access  
- **threading** — Non-blocking encode/decode for large images  

---

## Author

**Chaitanya Bikkina**  
B.Tech Computer Science (Cyber Security) — Malla Reddy University  
[LinkedIn](https://linkedin.com/in/chaitanya-bikkina) • [GitHub](https://github.com/chaitanyacyb)

---

## License

MIT License — open source, free to use and modify.
