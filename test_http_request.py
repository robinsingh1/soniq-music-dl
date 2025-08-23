#!/usr/bin/env python3
"""
Test processing endpoint with HTTP request like Cloud Run
"""
import requests
import json
import tempfile
import shutil
import os
import http.server
import socketserver
from threading import Thread
import time

def start_file_server():
    """Start local file server for test video"""
    # Copy test video to web directory
    web_dir = tempfile.mkdtemp()
    test_video_src = "/Users/rajvindersingh/Projects/karooke/test_30sec_video.mp4"
    test_video_dst = os.path.join(web_dir, "test_video.mp4")
    
    if not os.path.exists(test_video_src):
        print(f"❌ Test video not found: {test_video_src}")
        return None, None
    
    shutil.copy2(test_video_src, test_video_dst)
    
    # Start HTTP server
    original_dir = os.getcwd()
    os.chdir(web_dir)
    
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            pass
    
    httpd = socketserver.TCPServer(("", 8001), QuietHandler)
    
    def serve():
        httpd.serve_forever()
    
    server_thread = Thread(target=serve, daemon=True)
    server_thread.start()
    
    print(f"🌐 File server started: http://localhost:8001/test_video.mp4")
    time.sleep(1)
    
    return f"http://localhost:8001/test_video.mp4", httpd

def test_processing_request():
    """Test the processing endpoint with HTTP request"""
    
    # Start file server
    video_url, file_server = start_file_server()
    if not video_url:
        return False
    
    try:
        # Test processing request
        payload = {
            "video_url": video_url,
            "vocal_levels": [0.0, 0.25],
            "test_duration": 15
        }
        
        print("🎯 Testing processing endpoint...")
        print(f"   Video URL: {video_url}")
        print(f"   Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            "http://localhost:8080/process",
            json=payload,
            timeout=300,  # 5 minutes
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"\n🔍 Response:")
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   Body: {json.dumps(result, indent=2)}")
            
            if result.get('success'):
                print(f"\n✅ Processing successful!")
                print(f"   Job ID: {result.get('job_id')}")
                videos = result.get('videos', [])
                print(f"   Videos generated: {len(videos)}")
                
                # Show where files would be uploaded
                for video in videos:
                    print(f"     - {video['vocal_level']}% vocal: {video['filename']}")
                    if 'url' in video:
                        print(f"       GCS URL: {video['url']}")
                    else:
                        print(f"       Local file (GCS upload failed)")
                
                return True
            else:
                print(f"❌ Processing failed: {result}")
                return False
        else:
            print(f"❌ HTTP error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False
    finally:
        if file_server:
            file_server.shutdown()
            print("🛑 File server stopped")

if __name__ == "__main__":
    print("🧪 Testing HTTP processing request (Cloud Run simulation)")
    print("="*60)
    
    success = test_processing_request()
    
    if success:
        print("\n✅ HTTP processing test PASSED!")
    else:
        print("\n❌ HTTP processing test FAILED!")
    
    exit(0 if success else 1)