# 📄 Audio Pipeline

A simple end-to-end pipeline to convert Hindi and Gujarati documents into spoken audio using OCR, optional LLM-based text cleanup, and text-to-speech (TTS).

This project is designed to run easily in Google Colab without complex setup or dependency issues.

---

## 🔄 Pipeline Overview

The workflow follows a simple modular pipeline:

```
Document / Image
↓
EasyOCR (Text Extraction)
↓
Indic TTS / Edge TTS
↓
Audio Output (MP3)
```

### ✅ Steps Explained

- **EasyOCR**  
  Extracts text from Hindi and Gujarati documents or images.

- **Text-to-Speech (TTS)**  
  Converts corrected text into natural-sounding speech audio.


