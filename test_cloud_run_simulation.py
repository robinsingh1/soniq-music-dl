#!/usr/bin/env python3
"""
Test processing service as close as possible to Cloud Run environment
Starts Flask service locally and makes HTTP requests to simulate Cloud Run
"""
import subprocess
import time
import requests
import json
import os
import tempfile
import shutil
from urllib.parse import urlparse

def create_local_file_server():
    """Create a simple local file server to serve test video"""
    import http.server
    import socketserver
    from threading import Thread
    
    # Copy test video to a web-accessible location
    web_dir = tempfile.mkdtemp()
    test_video_src = "/Users/rajvindersingh/Projects/karooke/test_30sec_video.mp4"
    test_video_dst = os.path.join(web_dir, "test_video.mp4")
    
    if not os.path.exists(test_video_src):
        print(f"❌ Test video not found: {test_video_src}")
        return None, None
    
    shutil.copy2(test_video_src, test_video_dst)
    print(f"📁 Copied test video to: {test_video_dst}")
    
    # Start simple HTTP server
    os.chdir(web_dir)
    
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            pass  # Suppress server logs
    
    httpd = socketserver.TCPServer(("", 8000), Handler)
    
    def serve():
        httpd.serve_forever()
    
    server_thread = Thread(target=serve, daemon=True)
    server_thread.start()
    
    print("🌐 Local file server started on http://localhost:8000")
    time.sleep(1)
    
    return f"http://localhost:8000/test_video.mp4", httpd

def start_processing_service():
    """Start the processing service locally with Cloud Run-like environment"""
    
    # Set environment variables similar to Cloud Run
    env = os.environ.copy()
    env['PORT'] = '8080'
    env['FFMPEG_PATH'] = '/opt/homebrew/bin/ffmpeg'  # Local ffmpeg path
    env['BUCKET_NAME'] = 'soniq-karaoke-videos'
    
    print("🚀 Starting processing service (simulating Cloud Run)...")
    
    # Start the service
    process = subprocess.Popen([
        'python3', 'processing_service.py'
    ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Wait for service to start
    print("⏳ Waiting for service to start...")
    max_retries = 10
    for i in range(max_retries):
        try:
            response = requests.get("http://localhost:8080/health", timeout=2)
            if response.status_code == 200:
                print("✅ Processing service is ready!")
                return process
        except:
            pass
        time.sleep(1)
        print(f"   Attempt {i+1}/{max_retries}...")
    
    print("❌ Service failed to start")
    return None

def test_health_endpoint():
    """Test the health endpoint"""
    try:
        print("🩺 Testing health endpoint...")
        response = requests.get("http://localhost:8080/health", timeout=10)
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"   Response: {json.dumps(health_data, indent=2)}")
            return True
        else:
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_processing_endpoint(video_url):
    """Test the processing endpoint with real HTTP request"""
    
    # Prepare request payload like Cloud Run would receive
    payload = {
        "video_url": video_url,
        "vocal_levels": [0.0, 0.25],  # Test with two vocal levels
        "test_duration": 15  # Test with 15 seconds
    }
    
    print("🎯 Testing processing endpoint...")
    print(f"   Video URL: {video_url}")
    print(f"   Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            "http://localhost:8080/process",
            json=payload,
            timeout=180,  # 3 minutes timeout
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"🔍 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Processing successful!")
            print(f"   Response: {json.dumps(result, indent=2)}")
            
            # Verify response structure
            if 'success' in result and result['success']:
                print(f"   Job ID: {result.get('job_id')}")
                videos = result.get('videos', [])
                print(f"   Videos generated: {len(videos)}")
                
                for video in videos:
                    print(f"     - {video['vocal_level']}% vocal: {video['filename']}")
                    if 'url' in video:
                        print(f"       URL: {video['url']}")
                
                return True
            else:
                print(f"❌ Processing returned success=false")
                return False
        else:
            print(f"❌ Processing failed with status {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Processing request timed out")
        return False
    except Exception as e:
        print(f"❌ Processing request failed: {e}")
        return False

def show_service_logs(process):
    """Show service logs for debugging"""
    if process and process.poll() is None:
        try:
            stdout, stderr = process.communicate(timeout=1)
            if stdout:
                print("📝 Service stdout:")
                print(stdout)
            if stderr:
                print("📝 Service stderr:")
                print(stderr)
        except subprocess.TimeoutExpired:
            pass

def main():
    """Main test function simulating Cloud Run environment"""
    
    print("🧪 Testing processing service (Cloud Run simulation)")
    print("="*60)
    
    # Start local file server for test video
    video_url, file_server = create_local_file_server()
    if not video_url:
        return False
    
    # Start processing service
    process = start_processing_service()
    if not process:
        return False
    
    try:
        # Test health endpoint
        health_ok = test_health_endpoint()
        if not health_ok:
            print("❌ Health check failed")
            return False
        
        # Test processing endpoint
        processing_ok = test_processing_endpoint(video_url)
        
        if processing_ok:
            print("\n" + "="*60)
            print("✅ Cloud Run simulation test PASSED!")
            print("   All endpoints working correctly")
            print("   Processing pipeline functional")
        else:
            print("\n" + "="*60)
            print("❌ Cloud Run simulation test FAILED!")
            print("   Processing endpoint issues")
            
            # Show logs for debugging
            show_service_logs(process)
            
        return processing_ok
        
    finally:
        # Cleanup
        print("\n🛑 Cleaning up...")
        
        if file_server:
            file_server.shutdown()
            print("   File server stopped")
        
        if process:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            print("   Processing service stopped")

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)