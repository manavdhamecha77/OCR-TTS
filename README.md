
# Audio Pipeline

A simple end-to-end pipeline to convert image-based documents into spoken audio using OCR and text-to-speech (TTS). Supports English, Hindi, Gujarati, and Odia.

This project runs as a Flask web app with a clean browser UI.

---

## Pipeline Overview

```
Document / Image
       |
       v
OCR (EasyOCR or Tesseract)
       |
       v
TTS (Edge TTS or Sarvam AI)
       |
       v
Audio Output (MP3)
```

### Steps Explained

- **OCR** — Extracts text from uploaded images.

  - **EasyOCR** is used for English and Hindi.
  - **Tesseract** is used for Gujarati (`guj`) and Odia (`ori`).
- **Text-to-Speech (TTS)** — Converts extracted text into natural-sounding speech.

  - **Edge TTS** (Microsoft) is used for English, Hindi, and Gujarati.
  - **Sarvam AI Bulbul v3** is used for Odia, since Edge TTS has no Odia voice.

---

## Supported Languages

| Language | Script     | OCR Engine | TTS Engine            |
| -------- | ---------- | ---------- | --------------------- |
| English  | Latin      | EasyOCR    | Edge TTS              |
| Hindi    | Devanagari | EasyOCR    | Edge TTS              |
| Gujarati | Gujarati   | Tesseract  | Edge TTS              |
| Odia     | Odia       | Tesseract  | Sarvam AI (Bulbul v3) |

---

## Getting Started

### 1. Install Dependencies

```bash
pip install flask flask-cors easyocr edge-tts pytesseract pillow requests
```

Install Tesseract with Gujarati and Odia language packs:

```bash
# Ubuntu / Debian
sudo apt install tesseract-ocr tesseract-ocr-guj tesseract-ocr-ori
```

### 2. Set Up Sarvam AI API Key (required for Odia)

Get a free API key at https://dashboard.sarvam.ai, then export it:

```bash
export SARVAM_API_KEY="your_key_here"
```

### 3. Run the App

```bash
python app.py
```

Open http://localhost:5000 in your browser.

---

## Web UI Features

- Language selector (English, Hindi, Gujarati, Odia)
- Drag-and-drop image upload with preview
- Live processing status indicator
- Extracted text display with copy button
- In-browser audio playback
- MP3 download

---

## Project Structure

```
.
├── app.py              # Flask backend — OCR + TTS pipeline
└── templates/
    └── index.html      # Frontend UI
```

---

## Environment Variables

| Variable           | Description                      | Required       |
| ------------------ | -------------------------------- | -------------- |
| `SARVAM_API_KEY` | API key for Sarvam AI (Odia TTS) | Yes (for Odia) |

---

## Supported Image Formats

PNG, JPG, JPEG, WEBP, BMP, TIFF
