#!/bin/bash
# Create GitHub trigger using REST API

echo "🚀 Creating GitHub Cloud Build Trigger via REST API"
echo "=================================================="

# Get access token
ACCESS_TOKEN=$(gcloud auth print-access-token)
PROJECT_ID="soundbyte-e419d"

# Create trigger JSON payload
cat > trigger_payload.json << EOF
{
  "name": "soniq-processing-auto-deploy",
  "description": "Auto-deploy processing service on main branch push",
  "github": {
    "owner": "robinsingh1",
    "name": "soniq-music-dl",
    "push": {
      "branch": "^main$"
    }
  },
  "filename": "cloudbuild.yaml",
  "disabled": false
}
EOF

echo "📋 Trigger payload created:"
cat trigger_payload.json
echo ""

# Make the REST API call
echo "📡 Calling Cloud Build API..."
curl -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d @trigger_payload.json \
  "https://cloudbuild.googleapis.com/v1/projects/$PROJECT_ID/triggers"

echo ""
echo "✅ API call completed"

# Clean up
rm trigger_payload.json

echo ""
echo "🔍 Checking if trigger was created..."
gcloud builds triggers list