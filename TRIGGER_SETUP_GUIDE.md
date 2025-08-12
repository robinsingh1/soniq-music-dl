# Cloud Build Trigger Setup Guide

## Status: GitHub App Connection Required

The automated setup scripts show that **GitHub repository connection must be done through the web console first**. Here's why and how to set it up:

## Why Manual Setup is Required

1. **GitHub App Authorization**: Google Cloud Build needs permission to access your GitHub repository
2. **Secret Manager**: GitHub webhooks require secrets that must be managed securely
3. **OAuth Flow**: The initial connection requires an interactive OAuth flow

## Option 1: Manual Setup (Recommended)

### Step 1: Connect GitHub Repository
1. Go to [Cloud Build Triggers Console](https://console.cloud.google.com/cloud-build/triggers?project=soundbyte-e419d)
2. Click **"CREATE TRIGGER"**
3. Click **"Connect new repository"**
4. Select **"GitHub (Cloud Build GitHub App)"**
5. Click **"CONTINUE"** 
6. **Authenticate with GitHub** and authorize Google Cloud Build
7. Select repository: **`robinsingh1/soniq-music-dl`**
8. Click **"CONNECT"**

### Step 2: Create the Trigger
1. **Name**: `soniq-processing-auto-deploy`
2. **Event**: `Push to a branch`
3. **Branch**: `^main$` (regex for main branch)
4. **Configuration Type**: `Cloud Build configuration file`
5. **Cloud Build configuration file location**: `cloudbuild.yaml`
6. Click **"CREATE"**

## Option 2: Webhook Trigger (Alternative)

If GitHub App setup fails, you can use a webhook:

1. **Create webhook secret**:
   ```bash
   echo -n "your-secret-key" | gcloud secrets create github-webhook-secret --data-file=-
   ```

2. **Create webhook trigger**:
   ```bash
   gcloud builds triggers create webhook \
     --name="soniq-webhook-deploy" \
     --inline-config="cloudbuild.yaml" \
     --secret="projects/soundbyte-e419d/secrets/github-webhook-secret/versions/latest"
   ```

3. **Add webhook to GitHub**:
   - Go to repository → Settings → Webhooks
   - Add the webhook URL from Cloud Build
   - Set content type: `application/json`
   - Select events: `push`

## Option 3: Manual Deployment

Continue with manual deployment until trigger is set up:

```bash
# Deploy when needed
gcloud builds submit --config=cloudbuild.yaml

# Or use the quick test script
python test_async_processing.py
```

## Verification

Once set up, test the trigger:

1. **Make a small change** to any file
2. **Push to main branch**: `git push origin main`
3. **Check Cloud Build**: [Build History](https://console.cloud.google.com/cloud-build/builds?project=soundbyte-e419d)
4. **Verify deployment**: Check Cloud Run service is updated

## Current Service Status

- **Processing Service**: `https://soniq-processor-scqr2wnnya-uc.a.run.app` ✅ Healthy
- **Download Service**: `https://soniq-downloader-scqr2wnnya-uc.a.run.app` ✅ Active
- **GitHub Repository**: `https://github.com/robinsingh1/soniq-music-dl` ✅ Updated
- **Build Configuration**: `cloudbuild.yaml` ✅ Ready
- **Async Test**: `test_async_processing.py` ✅ Available

## Next Steps After Trigger Setup

1. **Test with GCS video**: Run `python test_async_processing.py`
2. **Process trending videos**: Run `python upload_and_process_via_gsutil.py`
3. **Monitor deployments**: Watch Cloud Build for automatic builds
4. **Scale if needed**: Adjust Cloud Run concurrency and memory

The trigger setup requires the one-time GitHub App authorization, but once connected, all future pushes to main will automatically deploy both services.