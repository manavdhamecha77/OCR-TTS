let selectedLang = 'en';
let selectedFile = null;

// ── Language ──
function selectLang(code) {
  selectedLang = code;
  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.classList.toggle('selected', btn.dataset.lang === code);
  });
}

// ── File Handling ──
const fileInput = document.getElementById('fileInput');
const dropzone  = document.getElementById('dropzone');

fileInput.addEventListener('change', e => {
  if (e.target.files.length > 0) handleFile(e.target.files[0]);
});

dropzone.addEventListener('dragover', e => {
  e.preventDefault();
  dropzone.classList.add('dragover');
});
dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
dropzone.addEventListener('drop', e => {
  e.preventDefault();
  dropzone.classList.remove('dragover');
  if (e.dataTransfer.files.length > 0) handleFile(e.dataTransfer.files[0]);
});

function handleFile(file) {
  selectedFile = file;
  document.getElementById('previewName').textContent = file.name;
  document.getElementById('previewSize').textContent = formatBytes(file.size);
  document.getElementById('preview').classList.add('visible');
  dropzone.style.display = 'none';
  hideError();
  document.getElementById('processBtn').disabled = false;
}

function removeFile() {
  selectedFile = null;
  fileInput.value = '';
  document.getElementById('preview').classList.remove('visible');
  dropzone.style.display = '';
  document.getElementById('processBtn').disabled = true;
}

function formatBytes(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1048576).toFixed(1) + ' MB';
}

// ── Error ──
function showError(msg) {
  const box = document.getElementById('errorBox');
  document.getElementById('errorMsg').textContent = msg;
  box.classList.add('visible');
}

function hideError() {
  document.getElementById('errorBox').classList.remove('visible');
}

// ── Loader ──
let loaderInterval = null;

function startLoader() {
  const steps = ['Running OCR…', 'Generating audio…', 'Almost done…'];
  let i = 0;
  document.getElementById('loaderMsg').textContent = steps[0];
  document.getElementById('loader').classList.add('visible');
  loaderInterval = setInterval(() => {
    i = (i + 1) % steps.length;
    document.getElementById('loaderMsg').textContent = steps[i];
  }, 3000);
}

function stopLoader() {
  clearInterval(loaderInterval);
  document.getElementById('loader').classList.remove('visible');
}

// ── Process ──
async function processFile() {
  if (!selectedFile) return;
  hideError();

  const btn = document.getElementById('processBtn');
  btn.disabled = true;
  document.getElementById('results').classList.remove('visible');
  startLoader();

  const formData = new FormData();
  formData.append('image', selectedFile);
  formData.append('language', selectedLang);

  try {
    const res  = await fetch('/process', { method: 'POST', body: formData });
    const data = await res.json();

    if (!res.ok) throw new Error(data.error || `Error ${res.status}`);

    stopLoader();
    showResults(data.text, data.audio_url);
  } catch (err) {
    stopLoader();
    showError(err.message);
    btn.disabled = false;
  }
}

function showResults(text, audioUrl) {
  document.getElementById('ocrText').textContent = text;

  const player = document.getElementById('audioPlayer');
  player.src = audioUrl;
  player.load();

  const dl = document.getElementById('downloadLink');
  dl.href = audioUrl;
  dl.download = `audio-${selectedLang}`;

  document.getElementById('results').classList.add('visible');
  document.getElementById('results').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ── Copy ──
async function copyText() {
  const text = document.getElementById('ocrText').textContent;
  try {
    await navigator.clipboard.writeText(text);
    const btn = document.getElementById('copyBtn');
    btn.textContent = 'Copied!';
    setTimeout(() => btn.textContent = 'Copy', 2000);
  } catch {
    showError('Copy failed — please select text manually.');
  }
}

// ── Reset ──
function resetAll() {
  removeFile();
  document.getElementById('results').classList.remove('visible');
  hideError();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}