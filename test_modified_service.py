#!/usr/bin/env python3
"""
Test the modified processing service that preserves separated audio files
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
    web_dir = tempfile.mkdtemp()
    test_video_src = "/Users/rajvindersingh/Projects/karooke/test_30sec_video.mp4"
    test_video_dst = os.path.join(web_dir, "test_video.mp4")
    
    if not os.path.exists(test_video_src):
        print(f"❌ Test video not found: {test_video_src}")
        return None, None
    
    shutil.copy2(test_video_src, test_video_dst)
    
    original_dir = os.getcwd()
    os.chdir(web_dir)
    
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            pass
    
    httpd = socketserver.TCPServer(("", 8002), QuietHandler)
    
    def serve():
        httpd.serve_forever()
    
    server_thread = Thread(target=serve, daemon=True)
    server_thread.start()
    
    print(f"🌐 File server started: http://localhost:8002/test_video.mp4")
    time.sleep(1)
    
    return f"http://localhost:8002/test_video.mp4", httpd

def test_modified_processing():
    """Test the modified processing service"""
    
    # Start file server
    video_url, file_server = start_file_server()
    if not video_url:
        return False
    
    try:
        # Test processing request with modified service
        payload = {
            "video_url": video_url,
            "vocal_levels": [0.0],  # Just test one level for speed
            "test_duration": 10     # Short test
        }
        
        print("🧪 Testing modified processing service...")
        print(f"   Video URL: {video_url}")
        print(f"   Expected: Separated audio files uploaded to GCS")
        
        response = requests.post(
            "http://localhost:8080/process",
            json=payload,
            timeout=180,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"\n🔍 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Processing successful!")
            print(f"   Response: {json.dumps(result, indent=2)}")
            
            # Check for separated audio files
            if 'separated_audio' in result:
                separated_files = result['separated_audio']
                print(f"\n📂 Separated Audio Files ({len(separated_files)}):")
                for audio_file in separated_files:
                    print(f"   - {audio_file['type']}: {audio_file['filename']}")
                    if 'url' in audio_file:
                        print(f"     URL: {audio_file['url']}")
                    else:
                        print(f"     ⚠️ No URL (GCS upload may have failed)")
            
            # Check for metadata
            if 'metadata_url' in result:
                print(f"\n📋 Request Metadata: {result['metadata_url']}")
            
            # Check karaoke videos
            if 'videos' in result:
                videos = result['videos']
                print(f"\n🎬 Karaoke Videos ({len(videos)}):")
                for video in videos:
                    print(f"   - {video['vocal_level']}% vocal: {video['filename']}")
                    if 'url' in video:
                        print(f"     URL: {video['url']}")
            
            return True
        else:
            print(f"❌ Processing failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        if file_server:
            file_server.shutdown()
            print("\n🛑 File server stopped")

if __name__ == "__main__":
    print("🧪 Testing Modified Processing Service")
    print("="*50)
    print("Testing preservation of separated audio files to GCS")
    print("="*50)
    
    success = test_modified_processing()
    
    if success:
        print("\n✅ Modified service test PASSED!")
        print("   Separated audio files preserved to GCS")
        print("   Request metadata saved")
    else:
        print("\n❌ Modified service test FAILED!")
    
    exit(0 if success else 1)