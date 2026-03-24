
# Multilingual Document-to-Speech System

A robust, AI-powered Flask API designed to bridge the gap between visual documents and auditory accessibility. This system converts images and complex PDFs into high-fidelity speech across multiple languages, including English, Hindi, Gujarati, and Odia.

By utilizing a hybrid pipeline of **OCR (Optical Character Recognition)** and **Neural TTS (Text-to-Speech)**, the application ensures that even scanned, non-searchable documents become accessible to everyone.

---



## Key Features

* **Hybrid OCR Engine**: Uses **EasyOCR** (neural-based) for English and Hindi, and **Tesseract OCR** for specialized scripts like Gujarati and Odia.
* **Intelligent PDF Processing**:
  * **Direct Extraction**: First, it pulls the native text layer from digital PDFs for 100% accuracy.
  * **OCR Fallback**: If a page is a scan or an image, the system automatically rasterizes it and runs OCR.
* **Multi-Engine Speech (TTS)**:
  * **Edge TTS**: High-fidelity cloud-based neural voices for English, Hindi, and Gujarati.
  * **Meta MMS**: Uses Facebook’s Massively Multilingual Speech models for Odia, ensuring support for low-resource languages.
* **Smart Text Chunking**: An algorithm that splits long text at sentence boundaries (using `।`, `.`, `!`, or `?`) to prevent memory crashes and ensure smooth audio flow.
* **Lazy Loading**: Heavy AI models are only loaded into RAM when a specific language request triggers them, keeping the initial footprint light.

---



## Tech Stack & System Requirements

### Software Frameworks

| Component                  | Technology                                                       |
| :------------------------- | :--------------------------------------------------------------- |
| **Backend**          | Python 3.10+, Flask, Flask-CORS                                  |
| **OCR Engines**      | EasyOCR (Neural), Tesseract OCR                                  |
| **PDF Handling**     | `pypdf` (Native), `pdf2image` (Rasterization)                |
| **Speech (TTS)**     | `edge-tts` (Microsoft Neural), `transformers` (Meta MMS-TTS) |
| **Audio Processing** | NumPy, PyTorch, SoundFile                                        |

### External System Dependencies

To ensure the OCR and PDF conversion functions correctly, the following must be installed on your operating system:

1. **Tesseract OCR**: Required for Gujarati and Odia extraction.
   * *Linux*: `sudo apt install tesseract-ocr`
   * *Mac*: `brew install tesseract`
2. **Poppler (poppler-utils)**: Required to convert PDF pages into images for OCR.
   * *Linux*: `sudo apt install poppler-utils`
   * *Mac*: `brew install poppler`
   * *Windows*: Download binaries and add the `bin` folder to your System PATH.

---



## Installation & Running the App

### 1. Setup Your Python Environment

Clone the repository and install the necessary Python packages. Using a virtual environment is highly recommended.

```bash
# Clone the repository
git clone [https://github.com/your-username/multilingual-tts.git](https://github.com/your-username/multilingual-tts.git)
cd multilingual-tts

# Create a virtual environment (optional)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (using the exact versions in requirements.txt)
pip install -r requirements.txt
```


### 2. Start the Flask Server

Run the application using Python. By default, the server will listen on port **5000**.

```bash
python app.py
```


### 3. Verify the Service

Once the server is running, you can access the frontend at `http://127.0.0.1:5000` or interact directly with the API endpoints.

---



## API Documentation

The primary interaction with the system happens through the `/process` endpoint.

### Process Document

**Endpoint:** `POST /process`
**Content-Type:** `multipart/form-data`

| Parameter      | Type    | Required | Description                                                                          |
| :------------- | :------ | :------- | :----------------------------------------------------------------------------------- |
| `image`      | File    | Yes      | The Image (PNG, JPG, WEBP, BMP, TIFF) or PDF file.                                   |
| `language`   | String  | Yes      | Language code:`en` (English), `hi` (Hindi), `gu` (Gujarati), or `od` (Odia). |
| `start_page` | Integer | No       | The page number to start processing (PDF only). Default: 1.                          |
| `end_page`   | Integer | No       | The page number to stop processing (PDF only).                                       |

### Example Response (JSON)

```json
{
  "text": "The extracted text content from the document...",
  "audio_url": "/audio/550e8400-e29b-41d4-a716-446655440000.mp3",
  "total_pages": 5,
  "pages_processed": "1–5"
}
```


### Serve Audio

**Endpoint:** `GET /audio/<filename>`

Used to retrieve the generated audio file for playback or download.

---



## Future Scope & Conclusion

### Future Enhancements

* **Expanded Language Support**: Adding more regional Indian languages such as Bengali, Tamil, and Telugu using specialized MMS or Tesseract models.
* **Document Layout Analysis**: Implementing advanced pre-processing to handle complex layouts like tables, multi-column articles, and embedded charts.
* **Mobile-First UI**: Developing a dedicated mobile application or a responsive React/Vue.js frontend for on-the-go document scanning.
* **Cloud Scaling**: Containerizing the application using **Docker** to deploy on AWS or Google Cloud for better performance and scalability.

### Conclusion

This project successfully demonstrates a hybrid AI pipeline that bridges the gap between static documents and auditory accessibility. By intelligently switching between OCR and TTS engines based on the language and document type, it provides a seamless experience for converting visual information into natural, spoken words.
