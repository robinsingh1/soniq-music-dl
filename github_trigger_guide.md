# GitHub Cloud Build Trigger Setup

## Current Status
✅ **GitHub connection created**: `github-connection` in `us-central1`  
⚠️ **Authorization required**: Connection is in `PENDING_USER_OAUTH` state

## Complete Setup Steps

### 1. Authorize GitHub Connection
Visit this link to authorize Cloud Build to access your GitHub account:
```
https://accounts.google.com/AccountChooser?continue=https%3A%2F%2Fconsole.cloud.google.com%2Fm%2Fgcb%2Fgithub%2Flocations%2Fus-central1%2Foauth_v2%3Fconnection_name%3Dprojects%252F894603036612%252Flocations%252Fus-central1%252Fconnections%252Fgithub-connection
```

### 2. Complete Repository Setup
After authorization, run:
```bash
# Create repository connection
gcloud alpha builds repositories create soniq-music-dl-repo \
  --connection=github-connection \
  --remote-uri=https://github.com/robinsingh1/soniq-music-dl.git \
  --region=us-central1

# Create the trigger
gcloud builds triggers create github \
  --name="soniq-processing-auto-deploy" \
  --repo-name="soniq-music-dl" \
  --repo-owner="robinsingh1" \
  --branch-pattern="^main$" \
  --build-config="cloudbuild-processing.yaml" \
  --description="Auto-deploy processing service on main branch push"
```

### 3. Test the Setup
```bash
# Make a test change and push
echo "# Test automatic deployment" >> README.md
git add README.md  
git commit -m "test: trigger Cloud Build deployment"
git push origin main
```

## Alternative: Manual Console Setup

1. Go to [Cloud Build Triggers](https://console.cloud.google.com/cloud-build/triggers)
2. Click **CREATE TRIGGER**
3. Select **GitHub** as source
4. Connect `robinsingh1/soniq-music-dl` repository
5. Configure trigger with `cloudbuild-processing.yaml`

## What Happens on Push

When code is pushed to main branch:
1. **Cloud Build** automatically starts
2. **Processing service** rebuilt with separated audio preservation
3. **Separated files** saved to `gs://soniq-karaoke-videos/separated_audio/`
4. **Request metadata** saved to `gs://soniq-karaoke-videos/requests/`
5. **Cloud Run** service updated automatically