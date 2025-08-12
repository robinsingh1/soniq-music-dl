#!/bin/bash
# Create webhook trigger instead of GitHub trigger

echo "🪝 Creating Webhook Cloud Build Trigger"
echo "========================================"

source ~/.zshrc

# Create webhook trigger
echo "📡 Creating webhook trigger..."
gcloud builds triggers create webhook \
  --name="soniq-webhook-deploy" \
  --inline-config="cloudbuild.yaml" \
  --description="Webhook trigger for soniq processing deployment" \
  --substitutions="_REPO_NAME=soniq-music-dl,_BRANCH_NAME=main" \
  --secret="projects/soundbyte-e419d/secrets/github-webhook-secret/versions/latest"

echo ""
echo "🔍 Checking triggers..."
gcloud builds triggers list

echo ""
echo "💡 To use this trigger:"
echo "1. Get the webhook URL from the trigger details"
echo "2. Add it as a webhook in GitHub repository settings"
echo "3. Set content type to 'application/json'"
echo "4. Select 'push' events"