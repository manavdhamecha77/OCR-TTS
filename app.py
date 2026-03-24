import os
import uuid
import asyncio
import tempfile

from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import easyocr
import edge_tts
import pytesseract
from PIL import Image
from pdf2image import convert_from_path  # pip install pdf2image
from pypdf import PdfReader              # pip install pypdf

app = Flask(__name__)
CORS(app)

# --- Config ---
UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "bmp", "tiff", "pdf"}

# Max pages processed per request — no hard engine limit, just time/RAM safety
PDF_MAX_PAGES = 20

# Parler TTS chunk size (characters).
# Parler handles long text fine but chunking keeps memory predictable.
PARLER_TTS_CHUNK = 500

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
        "tts_engine": "mms",
        "mms_model_id": "facebook/mms-tts-ory",
    },
}

# ---------------------------------------------------------------------------
# Lazy-loaded caches — nothing heavy is loaded until the first request needs it
# ---------------------------------------------------------------------------
_easyocr_readers: dict = {}
_mms_models: dict = {}  # keyed by model_id


# ---------------------------------------------------------------------------
# General helpers
# ---------------------------------------------------------------------------

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def is_pdf(filename: str) -> bool:
    return filename.rsplit(".", 1)[1].lower() == "pdf"


def chunk_text(text: str, max_chars: int) -> list:
    """
    Split text into chunks of at most max_chars, preferring sentence
    boundaries (। . ! ?) or whitespace as break points.
    """
    if len(text) <= max_chars:
        return [text]

    chunks = []
    while text:
        if len(text) <= max_chars:
            chunks.append(text)
            break
        cut = max_chars
        for sep in ("। ", ". ", "! ", "? ", "\n"):
            pos = text.rfind(sep, 0, max_chars)
            if pos != -1:
                cut = pos + len(sep)
                break
        else:
            pos = text.rfind(" ", 0, max_chars)
            if pos != -1:
                cut = pos + 1
        chunks.append(text[:cut].strip())
        text = text[cut:].strip()
    return [c for c in chunks if c]


# ---------------------------------------------------------------------------
# EasyOCR reader cache
# ---------------------------------------------------------------------------

def get_easyocr_reader(langs: list):
    key = tuple(sorted(langs))
    if key not in _easyocr_readers:
        _easyocr_readers[key] = easyocr.Reader(list(langs), gpu=False)
    return _easyocr_readers[key]


# ---------------------------------------------------------------------------
# OCR
# ---------------------------------------------------------------------------

def run_ocr(image_path: str, lang_code: str) -> str:
    """Run OCR on a single image file."""
    config = LANGUAGE_CONFIG[lang_code]
    if config["ocr_engine"] == "easyocr":
        reader = get_easyocr_reader(config["easyocr_langs"])
        result = reader.readtext(image_path)
        return " ".join([r[1] for r in result])
    elif config["ocr_engine"] == "tesseract":
        image = Image.open(image_path)
        return pytesseract.image_to_string(image, lang=config["tesseract_lang"])
    return ""


def extract_text_from_pdf(pdf_path: str, lang_code: str,
                           start_page: int = 1,
                           end_page=None):
    """
    Extract text from a PDF with two strategies per page:
      1. Native text layer (fast, for digital PDFs)
      2. Rasterise + OCR fallback (for scanned / image-only pages)

    Returns: (extracted_text: str, total_pages: int)
    """
    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)

    start_page = max(1, start_page)
    if end_page is None or end_page > total_pages:
        end_page = total_pages
    if end_page - start_page + 1 > PDF_MAX_PAGES:
        end_page = start_page + PDF_MAX_PAGES - 1

    pages_text = []
    raster_images = None  # lazily rasterised only when a page needs OCR

    for page_idx in range(start_page - 1, end_page):  # pypdf is 0-indexed
        page = reader.pages[page_idx]
        native_text = (page.extract_text() or "").strip()

        if native_text:
            pages_text.append(native_text)
            continue

        # OCR fallback — rasterise if not done yet
        if raster_images is None:
            raster_images = convert_from_path(
                pdf_path,
                dpi=150,
                first_page=start_page,
                last_page=end_page,
            )

        img = raster_images[page_idx - (start_page - 1)]
        tmp_img = os.path.join(UPLOAD_FOLDER, f"pdf_page_{uuid.uuid4()}.png")
        img.save(tmp_img, "PNG")
        try:
            ocr_text = run_ocr(tmp_img, lang_code).strip()
            if ocr_text:
                pages_text.append(ocr_text)
        finally:
            if os.path.exists(tmp_img):
                os.remove(tmp_img)

    return "\n\n".join(pages_text), total_pages


# ---------------------------------------------------------------------------
# TTS — Edge TTS  (en / hi / gu)
# ---------------------------------------------------------------------------

async def _run_tts_edge_async(text: str, voice: str, output_path: str):
    communicate = edge_tts.Communicate(text, voice=voice)
    await communicate.save(output_path)


def run_tts_edge(text: str, voice: str, output_path: str):
    asyncio.run(_run_tts_edge_async(text, voice, output_path))


# ---------------------------------------------------------------------------
# TTS — Facebook MMS-TTS  (Odia)
# ---------------------------------------------------------------------------

def get_mms_model(model_id: str):
    """Lazy-load a MMS-TTS model once and cache it by model_id."""
    if model_id not in _mms_models:
        from transformers import VitsModel, AutoTokenizer
        import torch
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        model = VitsModel.from_pretrained(model_id, torch_dtype=torch.float32)
        model.eval()
        _mms_models[model_id] = (model, tokenizer)
    return _mms_models[model_id]


def run_tts_mms(text: str, model_id: str, output_path: str):
    """
    Synthesise text with Facebook MMS-TTS and save as WAV.
    Chunks long text and concatenates audio so there is no length limit.
    Output path should end in .wav.
    """
    import torch
    import numpy as np
    import soundfile as sf

    model, tokenizer = get_mms_model(model_id)
    chunks = chunk_text(text, PARLER_TTS_CHUNK)
    all_audio = []

    for chunk in chunks:
        inputs = tokenizer(chunk, return_tensors="pt")
        with torch.no_grad():
            waveform = model(**inputs).waveform[0].cpu().numpy()
        all_audio.append(waveform)

    combined = np.concatenate(all_audio)
    sf.write(output_path, combined, model.config.sampling_rate)


# ---------------------------------------------------------------------------
# TTS dispatcher
# ---------------------------------------------------------------------------

def run_tts(text: str, lang_code: str, output_path: str) -> str:
    """
    Dispatch to the correct TTS engine.
    Returns the actual saved file path (extension may differ for WAV output).
    """
    config = LANGUAGE_CONFIG[lang_code]
    engine = config["tts_engine"]

    if engine == "edge":
        run_tts_edge(text, config["tts_voice"], output_path)
        return output_path

    elif engine == "mms":
        wav_path = output_path.replace(".mp3", ".wav")
        run_tts_mms(text, config["mms_model_id"], wav_path)
        return wav_path

    else:
        raise ValueError(f"Unknown TTS engine: {engine}")
# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/process", methods=["POST"])
def process():
    if "image" not in request.files:
        return jsonify({"error": "No file provided."}), 400

    file = request.files["image"]
    lang_code = request.form.get("language", "en")

    # Optional page range — only used for PDF uploads
    try:
        start_page = int(request.form.get("start_page", 1))
        end_page_raw = request.form.get("end_page", None)
        end_page = int(end_page_raw) if end_page_raw else None
    except ValueError:
        return jsonify({"error": "start_page and end_page must be integers."}), 400

    if lang_code not in LANGUAGE_CONFIG:
        return jsonify({"error": f"Unsupported language: {lang_code}"}), 400

    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    if not allowed_file(file.filename):
        return jsonify({
            "error": "Unsupported file type. Accepted: PNG, JPG, JPEG, WEBP, BMP, TIFF, PDF."
        }), 400

    ext = file.filename.rsplit(".", 1)[1].lower()
    file_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}.{ext}")
    file.save(file_path)

    total_pages = None

    try:
        # --- Step 1: extract text ---
        if is_pdf(file.filename):
            extracted_text, total_pages = extract_text_from_pdf(
                file_path, lang_code, start_page, end_page
            )
        else:
            extracted_text = run_ocr(file_path, lang_code)

        if not extracted_text.strip():
            return jsonify({"error": "No text could be extracted from the file."}), 422

        # --- Step 2: TTS ---
        audio_stem = os.path.join(UPLOAD_FOLDER, str(uuid.uuid4()))
        audio_path = run_tts(extracted_text.strip(), lang_code, audio_stem + ".mp3")

        response_data = {
            "text": extracted_text.strip(),
            "audio_url": f"/audio/{os.path.basename(audio_path)}",
        }
        if total_pages is not None:
            actual_end = min(end_page or total_pages, total_pages)
            response_data["total_pages"] = total_pages
            response_data["pages_processed"] = f"{start_page}–{actual_end}"

        return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@app.route("/audio/<filename>")
def serve_audio(filename):
    audio_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(audio_path):
        return jsonify({"error": "Audio file not found."}), 404
    mimetype = "audio/wav" if filename.endswith(".wav") else "audio/mpeg"
    return send_file(audio_path, mimetype=mimetype, as_attachment=False)


if __name__ == "__main__":
    app.run(debug=True, port=5000)