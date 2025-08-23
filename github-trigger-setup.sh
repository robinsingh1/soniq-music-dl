#!/bin/bash
# GitHub Cloud Build Trigger Setup Script
# Run this after completing GitHub OAuth authorization

echo "🚀 Setting up GitHub Cloud Build Trigger"
echo "========================================"

# Check if connection exists and is authorized
echo "🔍 Checking GitHub connection status..."
gcloud alpha builds connections describe github-connection --region=us-central1

# Create repository connection
echo "📂 Creating repository connection..."
gcloud alpha builds repositories create soniq-music-dl-repo \
  --connection=github-connection \
  --remote-uri=https://github.com/robinsingh1/soniq-music-dl.git \
  --region=us-central1

# Create trigger for processing service
echo "🔧 Creating processing service trigger..."
gcloud builds triggers create manual \
  --name="soniq-processing-github-trigger" \
  --repo="https://github.com/robinsingh1/soniq-music-dl" \
  --repo-type="GITHUB" \
  --branch-pattern="^main$" \
  --build-config="cloudbuild-processing.yaml" \
  --description="Auto-deploy processing service on main branch push"

# Alternative trigger creation with webhook
echo "🪝 Creating webhook-based trigger..."
gcloud builds triggers create webhook \
  --name="soniq-processing-webhook" \
  --inline-config="cloudbuild-processing.yaml" \
  --secret="projects/soundbyte-e419d/secrets/github-webhook/versions/latest" \
  --description="Processing service webhook trigger"

# List all triggers to verify
echo "✅ Listing all triggers..."
gcloud builds triggers list --format="table(name,triggerTemplate.repoName,filename)"

echo ""
echo "🎉 Setup complete!"
echo "💡 To test the trigger:"
echo "   1. Make any change to the repository"
echo "   2. Push to main branch: git push origin main"
echo "   3. Check Cloud Build history: gcloud builds list"
echo "   4. Monitor deployment: gcloud run services describe soniq-processor --region=us-central1"