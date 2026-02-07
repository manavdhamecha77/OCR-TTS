# 📄 Hindi & Gujarati Document → Audio Pipeline

A simple end-to-end pipeline to convert Hindi and Gujarati documents into spoken audio using OCR, optional LLM-based text cleanup, and text-to-speech (TTS).

This project is designed to run easily in Google Colab without complex setup or dependency issues.

---

## 🚀 Open in Google Colab

👉 [Run the notebook here](https://colab.research.google.com/drive/1vgRbUXxBQxchiIBgloc6spbQKVsccKUi)

---

## 🔄 Pipeline Overview

The workflow follows a simple modular pipeline:

```
Document / Image
↓
EasyOCR (Text Extraction)
↓
Qwen (Optional OCR Cleanup)
↓
Indic TTS / Edge TTS
↓
Audio Output (MP3)
```

### ✅ Steps Explained

- **EasyOCR**  
  Extracts text from Hindi and Gujarati documents or images.

- **Qwen (Optional)**  
  Cleans OCR output by correcting spacing, punctuation, and common OCR errors.  
  ⚠️ This step is NOT compulsory and can be skipped.

- **Text-to-Speech (TTS)**  
  Converts corrected text into natural-sounding speech audio.


