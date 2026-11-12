# AI Misinformation Detection and Evidence Verification

A web application for detecting misinformation and extracting evidence using local AI models via Ollama.

## Features

- **Text Analysis**: Analyze text for potential misinformation using local LLM
- **Evidence Extraction**: Extract factual statements, sources, statistics, and arguments from text
- **URL Checking**: Verify URL credibility and check for security flags
- **Local AI**: Uses Ollama for privacy-focused, offline AI processing
- **Modern UI**: Clean, responsive web interface

## Prerequisites

1. **Python 3.8+** installed
2. **Ollama** installed and running with a model (e.g., llama2, mistral)

### Installing Ollama

1. Download Ollama from [https://ollama.ai](https://ollama.ai)
2. Install it on your system
3. Pull a model (e.g., llama2):
   ```bash
   ollama pull llama2
   ```
4. Start Ollama (it usually starts automatically after installation)
   ```bash
   ollama serve
   ```

## Setup

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Ensure Ollama is running:
   ```bash
   ollama serve
   ```

3. Start the FastAPI server:
   ```bash
   python app.py
   ```

4. Open your browser and navigate to:
   ```
   http://localhost:8000
   ```

## Usage

### Analyze Text
1. Navigate to the "Analyze Text" tab
2. Paste or type the text you want to analyze
3. Click "Analyze Text"
4. View the verdict, confidence score, and identified claims

### Extract Evidence
1. Navigate to the "Extract Evidence" tab
2. Paste or type the text you want to analyze
3. Click "Extract Evidence"
4. View extracted factual statements, sources, statistics, and arguments

### Check URL
1. Navigate to the "Check URL" tab
2. Enter the URL you want to verify
3. Click "Check URL"
4. View accessibility status, credibility score, and security flags

## Configuration

You can modify the following settings in `app.py`:

- `OLLAMA_BASE_URL`: Default is `http://localhost:11434`
- `MODEL_NAME`: Default is `llama2` (can be changed to mistral, phi, etc.)

## API Endpoints

- `GET /` - Serve the frontend interface
- `GET /health` - Health check and Ollama status
- `POST /api/analyze` - Analyze text for misinformation
- `POST /api/extract-evidence` - Extract evidence from text
- `POST /api/check-url` - Check URL credibility

## Troubleshooting

### Ollama Not Running
If you see "Ollama Not Running" in the status bar:
1. Make sure Ollama is installed
2. Start Ollama: `ollama serve`
3. Check if a model is installed: `ollama list`
4. If no model, pull one: `ollama pull llama2`

### Slow Response Times
Local LLMs can be slower than cloud APIs. Consider:
- Using a smaller model (e.g., phi instead of llama2)
- Ensuring you have sufficient RAM and CPU
- Running on a machine with a GPU if available

### Port Already in Use
If port 8000 is already in use, modify the port in `app.py`:
```python
uvicorn.run(app, host="0.0.0.0", port=8001)  # Change to 8001 or another port
```

## License

MIT License
