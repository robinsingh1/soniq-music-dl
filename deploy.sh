#!/bin/bash
# Deployment script for Soniq Music DL to Google Cloud Run

echo "🚀 DEPLOYING SONIQ MUSIC DL TO CLOUD RUN"
echo "========================================"

# Set variables
PROJECT_ID="your-project-id"  # Replace with actual project ID
SERVICE_NAME="soniq-karaoke"
REGION="us-central1"
BUCKET_NAME="soniq-karaoke-videos"

echo "📋 Configuration:"
echo "  Project: $PROJECT_ID"
echo "  Service: $SERVICE_NAME"
echo "  Region: $REGION"
echo "  Bucket: $BUCKET_NAME"
echo ""

# Check if gcloud is authenticated
echo "🔐 Checking authentication..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1 > /dev/null 2>&1; then
    echo "❌ Please run: gcloud auth login"
    echo "   Then run this script again"
    exit 1
fi

# Set project
echo "🏗️  Setting project..."
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔌 Enabling required APIs..."
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    storage.googleapis.com \
    containerregistry.googleapis.com

# Create storage bucket if it doesn't exist
echo "🪣 Creating storage bucket..."
gsutil mb gs://$BUCKET_NAME 2>/dev/null || echo "  Bucket already exists"

# Make bucket publicly readable
gsutil iam ch allUsers:objectViewer gs://$BUCKET_NAME

# Build and deploy using Cloud Build
echo "🏗️  Building and deploying with Cloud Build..."
gcloud builds submit --config=cloudbuild.yaml

# Get the service URL
echo "🌐 Getting service URL..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo "========================================"
echo "🌍 Service URL: $SERVICE_URL"
echo ""
echo "🧪 Test endpoints:"
echo "  Health: $SERVICE_URL/health"
echo "  Process: $SERVICE_URL/process"
echo ""
echo "📖 Example API call:"
echo "curl -X POST $SERVICE_URL/process \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"url\": \"https://www.youtube.com/watch?v=VIDEO_ID\", \"vocal_levels\": [0.0, 0.25]}'"
echo ""
echo "🎵 Your karaoke service is ready!"