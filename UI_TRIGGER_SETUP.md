# GitHub Trigger Setup via Google Cloud Console UI

## Step 1: Access Cloud Build Triggers

1. **Open Google Cloud Console**: https://console.cloud.google.com
2. **Select your project**: `soundbyte-e419d`
3. **Navigate to Cloud Build**: 
   - Use the search bar and type "Cloud Build"
   - Or go to: https://console.cloud.google.com/cloud-build/triggers
4. **Click "Triggers"** in the left sidebar

## Step 2: Create New Trigger

1. **Click "CREATE TRIGGER"** button
2. **Give it a name**: `soniq-processing-auto-deploy`
3. **Description**: `Auto-deploy processing service on GitHub push`
4. **Event**: Select "Push to a branch"

## Step 3: Connect GitHub Repository

1. **Source**: Click "CONNECT NEW REPOSITORY"
2. **Select source**: Choose "GitHub (Cloud Build GitHub App)"
3. **Authenticate**: Sign in to your GitHub account if prompted
4. **Select repository**: 
   - **GitHub account**: `robinsingh1`
   - **Repository**: `soniq-music-dl`
5. **Click "CONNECT"**

## Step 4: Configure Trigger Settings

### **Source:**
- **Repository**: `robinsingh1/soniq-music-dl` (should auto-populate)
- **Branch**: `^main$` (regex pattern for main branch)

### **Configuration:**
- **Type**: Select "Cloud Build configuration file (yaml or json)"
- **Location**: `cloudbuild-processing.yaml`

### **Advanced (Optional):**
- **Substitution variables**: 
  - `_SERVICE_NAME`: `soniq-processor`
  - `_REGION`: `us-central1`

## Step 5: Create and Test

1. **Click "CREATE"** to save the trigger
2. **Test the trigger**:
   - Go back to your terminal
   - Make a small change: `echo "UI trigger test" >> README.md`
   - Commit and push: 
     ```bash
     git add README.md
     git commit -m "test: UI trigger setup"
     git push origin main
     ```

## Step 6: Verify Deployment

1. **Check build status**: Go to "Cloud Build > History"
2. **Monitor deployment**: Go to "Cloud Run > soniq-processor"
3. **Verify new features**: Test the `/health` endpoint

## Alternative: Quick Link

Direct link to create trigger:
https://console.cloud.google.com/cloud-build/triggers/add

## Screenshots Guide

If you see these screens:

### 1. **Repository Connection Screen**
- Choose "GitHub (Cloud Build GitHub App)"
- NOT "GitHub (via Cloud Build GitHub App)" if both options appear

### 2. **GitHub Authorization**
- Click "Authorize Google Cloud Build"
- Grant permissions to the repository

### 3. **Repository Selection**
- Select `robinsingh1/soniq-music-dl`
- This should be visible after authorization

### 4. **Configuration File**
- Select "Cloud Build configuration file"
- Enter: `cloudbuild-processing.yaml`

## Expected Result

✅ **When working correctly:**
- Trigger appears in triggers list
- Shows "GitHub" as source
- Status shows "Enabled"
- Any push to main branch will trigger automatic deployment

## Troubleshooting

**If repository not visible:**
1. Make sure you're signed in to the correct GitHub account
2. Check repository is public or you have access
3. Try refreshing the page

**If trigger fails:**
1. Check Cloud Build history for error messages
2. Verify `cloudbuild-processing.yaml` exists in repository root
3. Check Cloud Build service account permissions