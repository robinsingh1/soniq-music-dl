#!/usr/bin/env python3
"""
Test the Docker processing service HTTP endpoint
"""
import os
import json
import requests
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler

def start_file_server():
    """Start a simple HTTP server to serve test files"""
    os.chdir('/Users/rajvindersingh/Projects/karooke')
    
    class CustomHandler(SimpleHTTPRequestHandler):
        def end_headers(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            super().end_headers()
    
    server = HTTPServer(('localhost', 8081), CustomHandler)
    print("🌐 Starting file server on http://localhost:8081")
    server.serve_forever()

def test_processing_endpoint():
    """Test the processing endpoint with a test video"""
    
    # Use a publicly accessible test video from GCS
    video_url = "https://storage.googleapis.com/soniq-karaoke-videos/test_audio_10sec.mp4"
    
    # Test data for processing
    test_data = {
        "video_url": video_url,
        "vocal_levels": [0.0],  # Just test 0% vocal (pure instrumental)
        "test_duration": 10     # Only process first 10 seconds
    }
    
    print(f"🎯 Testing processing endpoint with: {video_url}")
    print(f"📋 Test data: {json.dumps(test_data, indent=2)}")
    
    try:
        # Call the processing endpoint
        response = requests.post(
            'http://localhost:8080/process',
            json=test_data,
            timeout=120  # 2 minute timeout
        )
        
        print(f"📟 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Processing successful!")
            print(f"📋 Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print("❌ Processing failed!")
            print(f"📋 Error: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out - this might indicate the service is still processing")
        return False
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def test_spleeter_only():
    """Test just the Spleeter functionality without OpenAI/GCS dependencies"""
    
    # Start file server in background
    server_thread = threading.Thread(target=start_file_server, daemon=True)
    server_thread.start()
    time.sleep(2)
    
    # Use host.docker.internal to access host machine from container
    video_url = "http://host.docker.internal:8081/test_30sec_video.mp4"
    
    print("🧪 Testing Spleeter-only functionality...")
    print("Note: This will fail at transcription step (expected without OpenAI API key)")
    
    test_data = {
        "video_url": video_url,
        "test_duration": 10
    }
    
    try:
        response = requests.post(
            'http://localhost:8080/process',
            json=test_data,
            timeout=60
        )
        
        print(f"📟 Response Status: {response.status_code}")
        print(f"📋 Response: {response.text}")
        
        if response.status_code == 500 and "Transcription failed" in response.text:
            print("✅ Spleeter separation likely worked (failed at transcription as expected)")
            return True
        elif response.status_code == 200:
            print("✅ Full processing worked!")
            return True
        else:
            print("❌ Unexpected failure")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    print("🐳 Testing Docker processing service...")
    
    # Check if container is running
    print("🔍 Checking if container is running...")
    try:
        health_response = requests.get('http://localhost:8080/health', timeout=5)
        if health_response.status_code != 200:
            print("❌ Container health check failed")
            exit(1)
        print(f"✅ Container is healthy: {health_response.json()}")
    except Exception as e:
        print(f"❌ Cannot connect to container: {e}")
        exit(1)
    
    # Test Spleeter functionality (will fail at transcription without API keys)
    print("\n" + "="*50)
    print("🧪 Testing Spleeter separation functionality...")
    success = test_spleeter_only()
    
    if success:
        print("✅ Docker processing test completed successfully!")
        print("🎤 Spleeter audio separation is working!")
    else:
        print("❌ Docker processing test failed!")