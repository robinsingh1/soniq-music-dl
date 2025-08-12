# GitHub Cloud Build Trigger Setup

## Automated Deployment Setup

To set up automatic deployment from GitHub pushes, follow these steps:

### 1. Connect GitHub to Cloud Build (One-time setup)

1. Go to the [Cloud Build GitHub App page](https://github.com/apps/google-cloud-build)
2. Click "Configure" and select your GitHub account
3. Grant access to the `soniq-music-dl` repository
4. This connects GitHub to Google Cloud Build

### 2. Create Build Trigger

1. Go to [Google Cloud Console - Cloud Build Triggers](https://console.cloud.google.com/cloud-build/triggers)
2. Click "CREATE TRIGGER"
3. Configure the trigger:
   - **Name**: `soniq-processing-auto-deploy`
   - **Event**: Push to a branch
   - **Source**: Select the connected `robinsingh1/soniq-music-dl` repository
   - **Branch**: `^main$` (regex pattern for main branch)
   - **Configuration**: Cloud Build configuration file
   - **Cloud Build configuration file location**: `cloudbuild.yaml`
   
### 3. Test the Setup

1. Make any small change to the code
2. Push to main branch: `git push origin main`
3. Check Cloud Build history to see automatic deployment
4. Verify the service is updated

### Current Configuration

- **Repository**: https://github.com/robinsingh1/soniq-music-dl
- **Build Configuration**: `cloudbuild.yaml`
- **Services Deployed**: 
  - Processing Service: `soniq-processor-894603036612.us-central1.run.app`
  - Download Service: `soniq-downloader-894603036612.us-central1.run.app`

### Manual Deployment (Alternative)

If automatic triggers aren't working, you can manually deploy:

```bash
# Deploy processing service
gcloud builds submit --config=cloudbuild.yaml

# Or deploy download service  
gcloud builds submit --config=cloudbuild-download.yaml
```

### Build Status

The current build includes:
- Python Spleeter instead of Docker-in-Docker
- 30-second test mode support
- Compatible dependency versions for Cloud Run
- Trending music video batch processing capabilities

## GitHub Integration Benefits

1. **Automatic Deployment**: Push to main triggers deployment
2. **Build History**: Track all deployments in Cloud Build
3. **Rollback Capability**: Easy to revert to previous versions
4. **Status Checks**: See build status in GitHub PRs
5. **Continuous Integration**: Automated testing and deployment