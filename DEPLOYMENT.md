# Cloud Run Deployment Guide

## Prerequisites

1. **Google Cloud Project with Billing Enabled**
   - Create a new project or use existing one
   - Enable billing in Google Cloud Console
   - Note your PROJECT_ID

2. **Local Setup**
   ```bash
   # Install Google Cloud SDK
   brew install --cask google-cloud-sdk
   
   # Authenticate
   gcloud auth login
   
   # Set project
   gcloud config set project YOUR_PROJECT_ID
   ```

## Quick Deploy

1. **Enable Required APIs**
   ```bash
   gcloud services enable \
     run.googleapis.com \
     cloudbuild.googleapis.com \
     storage.googleapis.com \
     containerregistry.googleapis.com
   ```

2. **Create Storage Bucket**
   ```bash
   gsutil mb gs://soniq-karaoke-videos
   gsutil iam ch allUsers:objectViewer gs://soniq-karaoke-videos
   ```

3. **Deploy with Cloud Build**
   ```bash
   gcloud builds submit --config=cloudbuild.yaml
   ```

4. **Set Environment Variables** (after deployment)
   ```bash
   gcloud run services update soniq-karaoke \
     --set-env-vars OPENAI_API_KEY=your-api-key-here \
     --region us-central1
   ```

## Alternative: Manual Deploy

1. **Build Docker Image**
   ```bash
   docker build -t gcr.io/YOUR_PROJECT_ID/soniq-karaoke:latest .
   docker push gcr.io/YOUR_PROJECT_ID/soniq-karaoke:latest
   ```

2. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy soniq-karaoke \
     --image gcr.io/YOUR_PROJECT_ID/soniq-karaoke:latest \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --memory 4Gi \
     --cpu 2 \
     --timeout 1800 \
     --set-env-vars BUCKET_NAME=soniq-karaoke-videos,OPENAI_API_KEY=your-api-key
   ```

## API Usage

Once deployed, your service will be available at:
`https://soniq-karaoke-HASH-uc.a.run.app`

### Health Check
```bash
curl https://your-service-url/health
```

### Process Video
```bash
curl -X POST https://your-service-url/process \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "vocal_levels": [0.0, 0.25, 0.5]
  }'
```

### Response Format
```json
{
  "job_id": "uuid-string",
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

## Configuration

### Environment Variables
- `OPENAI_API_KEY` - Required for transcription
- `BUCKET_NAME` - Google Cloud Storage bucket for videos
- `PORT` - Server port (default: 8080)

### Resource Limits
- **Memory**: 4GB (recommended for video processing)
- **CPU**: 2 vCPU (for faster processing)
- **Timeout**: 30 minutes (for long videos)

## Troubleshooting

### Billing Issues
```
ERROR: Billing account not found
```
**Solution**: Enable billing in Google Cloud Console

### Docker Issues
```
ERROR: Docker not found
```
**Solution**: The service uses Docker-in-Docker for Spleeter. Cloud Run handles this automatically.

### Memory Issues
```
ERROR: Out of memory
```
**Solution**: Increase memory to 8GB for very long videos:
```bash
gcloud run services update soniq-karaoke --memory 8Gi --region us-central1
```

### Timeout Issues
```
ERROR: Request timeout
```
**Solution**: Increase timeout for longer videos:
```bash
gcloud run services update soniq-karaoke --timeout 3600 --region us-central1
```

## Cost Optimization

- **Cold Starts**: ~30 seconds (includes Docker Spleeter initialization)
- **Processing**: ~2-5 minutes for 3-minute video
- **Storage**: $0.020/GB/month for output videos
- **Compute**: Pay per request, scales to zero

## Security

- API is public by default (change with `--no-allow-unauthenticated`)
- Videos are stored in public GCS bucket
- No authentication required for processing
- Logs contain video titles and processing info

## Monitoring

View logs and metrics in Google Cloud Console:
- **Logs**: Cloud Run > Service > Logs
- **Metrics**: Cloud Run > Service > Metrics
- **Traces**: Cloud Trace (if enabled)