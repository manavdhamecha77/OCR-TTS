import os
import uuid
import asyncio
import base64
import tempfile

import requests
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import easyocr
import edge_tts
import pytesseract
from PIL import Image

app = Flask(__name__)
CORS(app)

# --- Config ---
UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "bmp", "tiff"}

# Get your free API key at: https://dashboard.sarvam.ai
SARVAM_API_KEY = os.environ.get("SARVAM_API_KEY", "")

LANGUAGE_CONFIG = {
    "en": {
        "name": "English",
        "ocr_engine": "easyocr",
        "easyocr_langs": ["en"],
        "tts_engine": "edge",
        "tts_voice": "en-IN-NeerjaNeural",
    },
    "hi": {
        "name": "Hindi",
        "ocr_engine": "easyocr",
        "easyocr_langs": ["hi"],
        "tts_engine": "edge",
        "tts_voice": "hi-IN-SwaraNeural",
    },
    "gu": {
        "name": "Gujarati",
        "ocr_engine": "tesseract",
        "tesseract_lang": "guj",
        "tts_engine": "edge",
        "tts_voice": "gu-IN-DhwaniNeural",
    },
    "od": {
        "name": "Odia",
        "ocr_engine": "tesseract",
        "tesseract_lang": "ori",
        "tts_engine": "sarvam",          # <-- Sarvam AI for Odia
        "sarvam_lang": "od-IN",
        "sarvam_speaker": "priya",     # female; alternatives: "abhilash" (male)
    },
}

# Cache EasyOCR readers so we don't reload them every request
_easyocr_readers = {}


def get_easyocr_reader(langs: list):
    key = tuple(sorted(langs))
    if key not in _easyocr_readers:
        _easyocr_readers[key] = easyocr.Reader(list(langs), gpu=False)
    return _easyocr_readers[key]


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def run_ocr(image_path: str, lang_code: str) -> str:
    config = LANGUAGE_CONFIG[lang_code]
    if config["ocr_engine"] == "easyocr":
        reader = get_easyocr_reader(config["easyocr_langs"])
        result = reader.readtext(image_path)
        return " ".join([r[1] for r in result])
    elif config["ocr_engine"] == "tesseract":
        image = Image.open(image_path)
        return pytesseract.image_to_string(image, lang=config["tesseract_lang"])


async def run_tts_edge(text: str, voice: str, output_path: str):
    communicate = edge_tts.Communicate(text, voice=voice)
    await communicate.save(output_path)


def run_tts_sarvam(text: str, lang_code: str, output_path: str):
    """
    Call Sarvam AI Bulbul v3 REST API and save audio to output_path.
    API docs: https://docs.sarvam.ai/api-reference-docs/api-guides-tutorials/text-to-speech/rest-api
    """
    if not SARVAM_API_KEY:
        raise ValueError(
            "SARVAM_API_KEY is not set. Get a free key at https://dashboard.sarvam.ai"
        )

    config = LANGUAGE_CONFIG[lang_code]
    payload = {
        "text": text,
        "target_language_code": config["sarvam_lang"],
        "speaker": config["sarvam_speaker"],
        "model": "bulbul:v3",
        "enable_preprocessing": True,
    }
    headers = {
        "api-subscription-key": SARVAM_API_KEY,
        "Content-Type": "application/json",
    }

    response = requests.post(
        "https://api.sarvam.ai/text-to-speech",
        json=payload,
        headers=headers,
        timeout=30,
    )

    if not response.ok:
        raise RuntimeError(
            f"Sarvam TTS API error {response.status_code}: {response.text}"
        )

    data = response.json()
    # Sarvam returns base64-encoded audio in the "audios" list
    audio_b64 = data["audios"][0]
    audio_bytes = base64.b64decode(audio_b64)

    with open(output_path, "wb") as f:
        f.write(audio_bytes)


def run_tts(text: str, lang_code: str, output_path: str):
    """Dispatch to the right TTS engine based on language config."""
    config = LANGUAGE_CONFIG[lang_code]
    engine = config["tts_engine"]

    if engine == "edge":
        asyncio.run(run_tts_edge(text, config["tts_voice"], output_path))
    elif engine == "sarvam":
        run_tts_sarvam(text, lang_code, output_path)
    else:
        raise ValueError(f"Unknown TTS engine: {engine}")


# --- Routes ---

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/process", methods=["POST"])
def process():
    if "image" not in request.files:
        return jsonify({"error": "No image file provided."}), 400

    file = request.files["image"]
    lang_code = request.form.get("language", "en")

    if lang_code not in LANGUAGE_CONFIG:
        return jsonify({"error": f"Unsupported language: {lang_code}"}), 400

    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported file type. Use PNG, JPG, JPEG, WEBP, BMP or TIFF."}), 400

    ext = file.filename.rsplit(".", 1)[1].lower()
    img_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}.{ext}")
    file.save(img_path)

    try:
        # Step 1: OCR
        extracted_text = run_ocr(img_path, lang_code)
        if not extracted_text.strip():
            return jsonify({"error": "No text could be extracted from the image."}), 422

        # Step 2: TTS
        audio_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}.mp3")
        run_tts(extracted_text.strip(), lang_code, audio_path)

        return jsonify({
            "text": extracted_text.strip(),
            "audio_url": f"/audio/{os.path.basename(audio_path)}"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if os.path.exists(img_path):
            os.remove(img_path)


@app.route("/audio/<filename>")
def serve_audio(filename):
    audio_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(audio_path):
        return jsonify({"error": "Audio file not found."}), 404
    return send_file(audio_path, mimetype="audio/mpeg", as_attachment=False)


if __name__ == "__main__":
    app.run(debug=True, port=5000)