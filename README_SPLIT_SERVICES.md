# Split Karaoke Services Architecture

This project is now split into two independent microservices:

## 🚀 Services Overview

### 1. Download Service
- **Purpose**: Downloads YouTube videos and stores them in Google Cloud Storage
- **Endpoint**: `/download`
- **Input**: YouTube URL
- **Output**: Downloadable video URL in GCS

### 2. Processing Service  
- **Purpose**: Takes downloaded video URL and creates karaoke versions
- **Endpoint**: `/process`
- **Input**: Video URL from storage + vocal levels
- **Output**: Multiple karaoke videos with different vocal levels

## 🏗️ Architecture Benefits

- **Scalability**: Each service can scale independently
- **Reliability**: If one service fails, the other continues working
- **Cost Optimization**: Processing service uses more resources only when needed
- **Flexibility**: Can process any video URL, not just from downloads

## 📁 File Structure

```
├── download_service.py          # Download service Flask app
├── processing_service.py        # Processing service Flask app
├── Dockerfile.download          # Download service container
├── Dockerfile.processing        # Processing service container
├── cloudbuild-download.yaml     # Download service deployment
├── cloudbuild-processing.yaml   # Processing service deployment
├── workflow_client.py           # Example client usage
└── requirements.txt             # Shared dependencies
```

## 🚀 Deployment

### Deploy Download Service
```bash
gcloud builds submit --config=cloudbuild-download.yaml
```

### Deploy Processing Service
```bash
gcloud builds submit --config=cloudbuild-processing.yaml
```

## 📡 API Usage

### 1. Download Video
```bash
curl -X POST https://soniq-downloader-PROJECT.us-central1.run.app/download \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=VIDEO_ID"}'
```

**Response:**
```json
{
  "success": true,
  "job_id": "abc123",
  "title": "Song Title",
  "duration": 231,
  "download_url": "https://storage.googleapis.com/bucket/downloads/video.mp4",
  "filename": "video.mp4"
}
```

### 2. Process Video
```bash
curl -X POST https://soniq-processor-PROJECT.us-central1.run.app/process \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://storage.googleapis.com/bucket/downloads/video.mp4",
    "vocal_levels": [0.0, 0.25, 0.5]
  }'
```

**Response:**
```json
{
  "success": true,
  "job_id": "def456",
  "videos": [
    {
      "vocal_level": 0,
      "url": "https://storage.googleapis.com/bucket/karaoke/karaoke_0vocal.mp4",
      "filename": "karaoke_0vocal.mp4"
    },
    {
      "vocal_level": 25,
      "url": "https://storage.googleapis.com/bucket/karaoke/karaoke_25vocal.mp4", 
      "filename": "karaoke_25vocal.mp4"
    }
  ]
}
```

## 🔄 Workflow Example

```python
# Step 1: Download video
download_response = requests.post(f"{DOWNLOAD_SERVICE}/download", 
                                json={'url': youtube_url})
video_url = download_response.json()['download_url']

# Step 2: Process video  
process_response = requests.post(f"{PROCESSING_SERVICE}/process",
                               json={
                                   'video_url': video_url,
                                   'vocal_levels': [0.0, 0.25, 0.5]
                               })
karaoke_videos = process_response.json()['videos']
```

## 🏥 Health Checks

Both services provide health endpoints:
- `GET /health` - Returns service status

## 🔧 Configuration

### Environment Variables

**Download Service:**
- `BUCKET_NAME` - Google Cloud Storage bucket name
- `PORT` - Service port (default: 8080)

**Processing Service:**
- `OPENAI_API_KEY` - OpenAI API key for Whisper transcription  
- `BUCKET_NAME` - Google Cloud Storage bucket name
- `PORT` - Service port (default: 8080)

## 🔒 Security

- Services are publicly accessible but can be restricted
- No sensitive data in source code
- Environment variables for secrets
- Public GCS bucket for video sharing

## 💰 Cost Optimization

- **Download Service**: Lightweight, minimal resources
- **Processing Service**: Higher resources, Docker Spleeter ML processing
- **Auto-scaling**: Both services scale to zero when not in use
- **Storage**: Pay only for video storage used

## 🚀 Future Enhancements

- Add authentication/API keys
- Implement job queuing for processing
- Add video processing status tracking
- Support batch processing
- Add webhook notifications
- Implement video expiration/cleanup