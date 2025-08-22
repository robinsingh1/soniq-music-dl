# Soniq Music DL - AI Karaoke Creator

🎵 **AI-powered karaoke video creator** using Docker Spleeter for ML-based vocal separation and OpenAI Whisper for transcription.

## Features

- 🤖 **Docker Spleeter integration** - True ML-based vocal/instrumental separation
- 🗣️ **OpenAI Whisper transcription** - Accurate speech-to-text with word-level timing
- 📝 **Synchronized subtitles** - Word highlighting with professional typography
- 🎚️ **Multiple vocal levels** - 0%, 5%, 10%, 15%, 25%, 50%, 75%
- 🌐 **Bilingual support** - Original language + transliteration
- ☁️ **Cloud deployment** - Google Cloud Run ready

## Local Usage

### Prerequisites

- Python 3.9+
- Docker
- FFmpeg
- OpenAI API key

### Installation

```bash
pip install -r requirements.txt
```

### Environment Variables

```bash
export OPENAI_API_KEY="your-openai-api-key"
```

### Create Karaoke Videos

```bash
# Multiple vocal levels (0%, 5%, 10%, 15%, 25%, 50%, 75%)
python create_multi_vocal_karaoke.py

# Low vocal levels (5%, 10%, 15%) 
python create_low_vocal_karaoke.py

# Download & process YouTube videos
python download_and_create_karaoke.py
```

## Cloud Deployment

### Deploy to Google Cloud Run

1. **Set up Google Cloud Project**
```bash
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com cloudbuild.googleapis.com storage.googleapis.com
```

2. **Create Storage Bucket**
```bash
gsutil mb gs://soniq-karaoke-videos
```

3. **Deploy with Cloud Build**
```bash
gcloud builds submit --config=cloudbuild.yaml
```

### API Usage

**Health Check**
```bash
curl https://soniq-karaoke-HASH-uc.a.run.app/health
```

**Process Video**
```bash
curl -X POST https://soniq-karaoke-HASH-uc.a.run.app/process \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "vocal_levels": [0.0, 0.25, 0.5]
  }'
```

**Response:**
```json
{
  "job_id": "uuid",
  "title": "Video Title",
  "videos": [
    {
      "vocal_level": 0,
      "url": "https://storage.googleapis.com/bucket/file.mp4",
      "filename": "karaoke_0_vocal.mp4"
    }
  ]
}
```

## Architecture

```
YouTube URL → yt-dlp → Docker Spleeter → OpenAI Whisper → FFmpeg → Cloud Storage
                ↓              ↓             ↓           ↓
            Video File    Vocal/Instrumental  Subtitles   Karaoke Video
```

## Video Pipeline

1. **Download** - Extract video from YouTube URL
2. **Separate** - Use Docker Spleeter for ML-based audio separation  
3. **Transcribe** - OpenAI Whisper for word-level timestamps
4. **Subtitle** - Create synchronized ASS subtitles with highlighting
5. **Mix** - Combine vocals/instrumentals at specified levels
6. **Render** - Generate final karaoke video with FFmpeg
7. **Upload** - Store in Google Cloud Storage

## Technologies

- **Python Spleeter** - ML audio separation (replaced Docker-in-Docker)
- **OpenAI Whisper** - Speech transcription
- **yt-dlp** - YouTube video downloading
- **FFmpeg** - Video/audio processing
- **Flask** - Web API framework
- **Google Cloud Run** - Serverless deployment
- **Google Cloud Storage** - Video storage

## GitHub Auto-Deploy
✅ Trigger "soniqpush" active - pushes to main branch automatically deploy to Cloud Run!

## Examples

Created karaoke videos with various vocal levels:
- `punjaban_karaoke_0_vocal.mp4` - Pure instrumental
- `punjaban_karaoke_25_vocal.mp4` - Light vocal guide
- `punjaban_karaoke_50_vocal.mp4` - Balanced mix
- `punjaban_karaoke_75_vocal.mp4` - Strong vocal guide

Perfect for different karaoke preferences and skill levels!

## License

MIT License - See LICENSE file for details.# GitHub Auto-Deployment Test Fri 22 Aug 2025 15:28:44 EDT
# GitHub trigger test - Fri 22 Aug 2025 15:38:10 EDT
