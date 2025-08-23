#!/usr/bin/env python3
"""
Simple test script to run processing service directly
"""
import os
import json
import requests
import tempfile
from flask import Flask
from processing_service import app

def test_processing_service():
    """Test the processing service directly"""
    
    # Start the Flask app in test mode
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        
        # Test health endpoint
        print("🩺 Testing health endpoint...")
        response = client.get('/health')
        print(f"Health status: {response.status_code}")
        print(f"Health response: {response.json}")
        
        # Test processing endpoint with a small video file
        print("🎯 Testing processing endpoint...")
        
        # Use test video file
        test_video_url = "file:///Users/rajvindersingh/Projects/karooke/test_30sec_video.mp4"
        
        payload = {
            "video_url": test_video_url,
            "vocal_levels": [0.0],  # Just test one level
            "test_duration": 5  # Only process 5 seconds
        }
        
        response = client.post('/process', 
                             data=json.dumps(payload),
                             content_type='application/json')
        
        print(f"Processing status: {response.status_code}")
        if response.status_code == 200:
            result = response.json
            print(f"✅ Processing successful!")
            print(f"Job ID: {result.get('job_id')}")
            print(f"Videos: {result.get('videos')}")
        else:
            print(f"❌ Processing failed: {response.data}")
        
        return response.status_code == 200

if __name__ == "__main__":
    # Update ffmpeg path for local testing
    import processing_service
    processing_service.FFMPEG_PATH = '/opt/homebrew/bin/ffmpeg'
    
    print("🧪 Testing processing service locally...")
    success = test_processing_service()
    
    if success:
        print("✅ Processing service works locally!")
    else:
        print("❌ Processing service test failed!")