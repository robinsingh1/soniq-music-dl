# Deploy Split Microservices to Cloud Run

✅ **Code pushed to GitHub successfully!**

## 🚀 Deployment Commands

### 1. Install Google Cloud SDK (if not installed)
```bash
# macOS
brew install --cask google-cloud-sdk

# Or download from: https://cloud.google.com/sdk/docs/install
```

### 2. Authenticate and Set Project
```bash
gcloud auth login
gcloud config set project soundbyte  # Your project ID
```

### 3. Enable Required APIs
```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  storage.googleapis.com \
  containerregistry.googleapis.com
```

### 4. Deploy Download Service
```bash
gcloud builds submit --config=cloudbuild-download.yaml
```

Expected output:
```
✅ soniq-downloader deployed to: 
   https://soniq-downloader-894603036612.us-central1.run.app
```

### 5. Deploy Processing Service
```bash
gcloud builds submit --config=cloudbuild-processing.yaml
```

### 6. Update OpenAI API Key
```bash
gcloud run services update soniq-processor \
  --set-env-vars OPENAI_API_KEY=your-working-api-key \
  --region us-central1
```

## 🧪 Test Deployed Services

### Test Download Service
```bash
curl -X POST https://soniq-downloader-PROJECT.us-central1.run.app/download \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=V9PVRfjEBTI"}'
```

### Test Processing Service
```bash
# Use video URL from download response
curl -X POST https://soniq-processor-PROJECT.us-central1.run.app/process \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://storage.googleapis.com/bucket/downloads/video.mp4",
    "vocal_levels": [0.0, 0.5]
  }'
```

## 📊 Service URLs

After deployment, you'll get these endpoints:

- **Download Service**: `https://soniq-downloader-PROJECT.us-central1.run.app`
- **Processing Service**: `https://soniq-processor-PROJECT.us-central1.run.app`

## 🔧 Configuration

### Download Service
- Memory: 2GB
- CPU: 1 vCPU  
- Timeout: 15 minutes
- Scaling: 0-100 instances

### Processing Service  
- Memory: 4GB
- CPU: 2 vCPU
- Timeout: 30 minutes
- Docker: Spleeter ML processing
- Scaling: 0-10 instances

## 💰 Estimated Costs

- **Download**: ~$0.01 per video
- **Processing**: ~$0.05-0.10 per karaoke video
- **Storage**: ~$0.02/GB/month
- **Cold starts**: ~30 seconds initial delay

## 🎯 What's Been Accomplished

✅ **Split into microservices** - Independent scaling and deployment  
✅ **Docker Spleeter** - Professional ML vocal separation  
✅ **Cloud Run ready** - Serverless, auto-scaling deployment  
✅ **Complete workflow** - Download → Process → Multiple karaoke videos  
✅ **Cost optimized** - Pay only for actual usage  
✅ **GitHub integration** - Version controlled and documented  

## 🔄 Workflow Example

```python
import requests

# Step 1: Download
download_resp = requests.post(DOWNLOAD_URL + "/download", 
                            json={"url": "https://youtube.com/watch?v=..."})
video_url = download_resp.json()["download_url"]

# Step 2: Process  
process_resp = requests.post(PROCESSING_URL + "/process",
                           json={"video_url": video_url, 
                                "vocal_levels": [0.0, 0.25, 0.5]})
karaoke_videos = process_resp.json()["videos"]
```

Ready to deploy when you have gcloud CLI installed! 🚀