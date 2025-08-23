#!/usr/bin/env python3
"""
Comprehensive test for Docker processing service
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
        
        def log_message(self, format, *args):
            print(f"📁 File server: {format%args}")
    
    server = HTTPServer(('localhost', 8081), CustomHandler)
    print("🌐 Starting file server on http://localhost:8081")
    server.serve_forever()

def test_comprehensive_processing():
    """Test the complete processing pipeline"""
    
    # Start file server in background
    server_thread = threading.Thread(target=start_file_server, daemon=True)
    server_thread.start()
    time.sleep(2)
    
    # Use host.docker.internal to access host machine from container
    video_url = "http://host.docker.internal:8081/test_30sec_video.mp4"
    
    print("🎯 Testing comprehensive processing pipeline...")
    print(f"📹 Video URL: {video_url}")
    
    # Test data for processing
    test_data = {
        "video_url": video_url,
        "vocal_levels": [0.0, 0.25],  # Test multiple levels
        "test_duration": 15  # Process first 15 seconds
    }
    
    print(f"📋 Test data: {json.dumps(test_data, indent=2)}")
    
    try:
        print("📡 Sending request to processing endpoint...")
        start_time = time.time()
        
        response = requests.post(
            'http://localhost:8080/process',
            json=test_data,
            timeout=180  # 3 minute timeout for processing
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"⏱️ Processing took {processing_time:.2f} seconds")
        print(f"📟 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Processing completed successfully!")
            print(f"📋 Response:")
            print(json.dumps(result, indent=2))
            
            # Analyze the response
            if result.get('success'):
                print("\n📊 Analysis:")
                print(f"   Job ID: {result.get('job_id')}")
                print(f"   Message: {result.get('message')}")
                print(f"   Separated Audio Files: {len(result.get('separated_audio', []))}")
                print(f"   Metadata URL: {result.get('metadata_url', 'None')}")
                print(f"   Note: {result.get('note', 'None')}")
                
                if result.get('separated_audio'):
                    print("   🎵 Separated Audio:")
                    for audio in result['separated_audio']:
                        print(f"      - {audio.get('type')}: {audio.get('url', 'No URL')}")
                
                return True
            else:
                print("❌ Processing returned success=false")
                return False
        else:
            print("❌ Processing failed!")
            print(f"📋 Error: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out - processing took too long")
        return False
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Comprehensive Docker Processing Test")
    print("=" * 50)
    
    # Check if container is running
    print("🔍 Checking if container is healthy...")
    try:
        health_response = requests.get('http://localhost:8080/health', timeout=5)
        if health_response.status_code != 200:
            print("❌ Container health check failed")
            exit(1)
        print(f"✅ Container is healthy: {health_response.json()}")
    except Exception as e:
        print(f"❌ Cannot connect to container: {e}")
        exit(1)
    
    # Run comprehensive test
    print("\n" + "="*50)
    success = test_comprehensive_processing()
    
    print("\n" + "="*50)
    if success:
        print("✅ Comprehensive processing test PASSED!")
        print("🎤 Audio separation pipeline is working correctly")
    else:
        print("❌ Comprehensive processing test FAILED!")