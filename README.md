# ASR Service with Speaker Diarization

This project is an automatic speech recognition service based on Whisper, with added speaker diarization functionality.

![App screenshot](doc/doc.PNG)

## 1. Project Structure

```
ASRService/
├── app/                    # Application code
│   ├── main.py            # FastAPI application entry point
│   ├── asr_service.py     # Core ASR functionality
│   ├── auth.py            # Authentication module
│   ├── config.py          # Configuration settings
│   ├── logger.py          # Logging configuration
│   ├── metrics.py         # Prometheus metrics
│   ├── s3.py              # S3 storage integration
│   ├── cli.py             # Command-line interface
│   ├── mcp_server.py      # MCP server for LLM integration
│   ├── static/            # Static files (CSS, JS)
│   └── templates/         # HTML templates
├── docker/                 # Docker configuration
│   ├── Dockerfile         # Docker image definition
│   ├── docker-compose.yml # Docker Compose configuration
│   └── start.sh           # Quick start script
├── doc/                   # Documentation
│   ├── doc.PNG           # Application screenshot
│   └── CHANGELOG.md      # Version history
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## 2. Features

- Speech-to-text (ASR)
- Multi-language support
- Speaker diarization
- RESTful API interface
- Web frontend for easy use
- Logging and auditing
- Prometheus monitoring metrics
- Command-line interface (CLI) for local transcription
- MCP server for LLM workflow integration

## 3. Installation

```bash
pip install -r requirements.txt
```

## 4. Starting the Service

### 4.1 Method 1: Using Docker (Recommended)

#### Prerequisites
- Docker installed
- Docker Compose installed

#### Quick Start

```bash
# Navigate to the docker directory
cd docker

# Run the startup script (Linux/Mac)
./start.sh

# Or manually start with docker-compose
docker-compose up -d
```

#### Docker Commands

```bash
# Build and start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down

# Rebuild the image
docker-compose build --no-cache
```

### 4.2 Method 2: Manual Installation

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 5. Usage

### 5.1 Web Interface

After starting the service, visit `http://localhost:8000` in your browser to access the web interface. The interface has two main sections:

1. **Token Generation**: Click the "Generate New Token" button to obtain an API token for authentication.
2. **Audio Transcription**: Upload WAV or MP3 audio files and download the transcription results as JSON.

### 5.2 API Endpoints

#### Get Access Token

```bash
curl -X POST http://localhost:8000/auth/token
```

#### Transcribe Audio

```bash
# Upload audio file
curl -X POST http://localhost:8000/transcribe \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@audio.wav" \
  -F "language=en"

# Or provide audio URL
curl -X POST http://localhost:8000/transcribe \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "audio_url=http://example.com/audio.wav" \
  -F "language=en"
```

### 5.3 Command-Line Interface (CLI)

The ASR Service includes a command-line interface for local audio transcription:

```bash
# Basic usage - transcribe audio file
python -m app.cli /path/to/audio.wav

# Specify language
python -m app.cli /path/to/audio.wav --language en

# Specify output format (json or text)
python -m app.cli /path/to/audio.wav --format text

# Save output to file
python -m app.cli /path/to/audio.wav --output transcription.json

# Specify chunk length (in seconds)
python -m app.cli /path/to/audio.wav --chunk-length 60
```

CLI options:
- `--language`, `-l`: Language code for transcription (default: fr)
- `--chunk-length`, `-c`: Chunk length in seconds (default: 30)
- `--output`, `-o`: Output file path. If not specified, prints to stdout.
- `--format`, `-f`: Output format (json or text)

### 5.4 MCP Server

The ASR Service includes an MCP (Model Context Protocol) server for integration with LLM workflows.

#### Running the MCP Server

```bash
python -m app.mcp_server
```

The MCP server exposes three tools:

1. **transcribe_audio**: Transcribe an audio file
   - Parameters:
     - `audio_path` (required): Path to the audio file (.wav or .mp3)
     - `language` (optional): Language code for transcription (default: fr)
     - `chunk_length` (optional): Chunk length in seconds (default: 30)
     - `output_format` (optional): Output format ('json' or 'text')

2. **transcribe_audio_from_url**: Download and transcribe an audio file from URL
   - Parameters:
     - `audio_url` (required): URL to the audio file (.wav or .mp3)
     - `language` (optional): Language code for transcription (default: fr)
     - `chunk_length` (optional): Chunk length in seconds (default: 30)
     - `output_format` (optional): Output format ('json' or 'text')

3. **transcribe_and_save**: Transcribe an audio file and save the result to a file
   - Parameters:
     - `audio_path` (required): Path to the audio file (.wav or .mp3)
     - `output_path` (required): Path where the transcription result will be saved
     - `language` (optional): Language code for transcription (default: fr)
     - `chunk_length` (optional): Chunk length in seconds (default: 30)
     - `output_format` (optional): Output format ('json' or 'text')

#### MCP Server Configuration

To use the MCP server with an MCP client (e.g., Claude Desktop, Cursor), add it to your MCP configuration:

```json
{
  "mcpServers": {
    "asr-service": {
      "command": "python",
      "args": ["-m", "app.mcp_server"]
    }
  }
}
```

The server uses stdio transport by default, which is compatible with most MCP clients.

## 6. Response Format

```json
{
  "language": "en",
  "segments": [
    {
      "start": 0.0,
      "end": 5.58,
      "text": "Hello, world.",
      "speaker": "SPEAKER0"
    },
    {
      "start": 5.58,
      "end": 10.25,
      "text": "The weather is nice today.",
      "speaker": "SPEAKER1"
    }
  ]
}
```

## 7. Environment Variables

### 7.1 Docker Environment Variables

When using Docker, you can customize the service by setting environment variables in the `docker-compose.yml` file:

```yaml
environment:
  - WHISPER_MODEL_PATH=openai/whisper-large-v3
  - DIARIZATION_MODEL_PATH=pyannote/speaker-diarization-3.1
  - LOG_LEVEL=INFO
  - API_TOKENS=your_token_here,another_token
```

### 7.2 Available Variables

- `WHISPER_MODEL_PATH`: Whisper model path (default: openai/whisper-large-v3)
- `DIARIZATION_MODEL_PATH`: Speaker diarization model path (default: pyannote/speaker-diarization-3.1)
- `LOG_LEVEL`: Log level (default: INFO)
- `API_TOKENS`: Allowed API tokens list (comma separated)

## 8. Speaker Diarization

This project integrates the PyAnnote.audio library to implement speaker diarization functionality. When processing audio, the system automatically detects different speakers and assigns corresponding speaker labels to each transcription segment.

## 9. Development

The project follows a modular structure with clear separation of concerns:

- **app/main.py**: FastAPI application setup and routing
- **app/asr_service.py**: Core ASR and speaker diarization logic
- **app/auth.py**: Token-based authentication system
- **app/config.py**: Configuration management
- **app/logger.py**: Logging configuration
- **app/metrics.py**: Prometheus metrics collection
- **app/s3.py**: Optional S3 storage integration
- **app/cli.py**: Command-line interface
- **app/mcp_server.py**: MCP server for LLM integration