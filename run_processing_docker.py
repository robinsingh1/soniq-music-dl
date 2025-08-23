#!/usr/bin/env python3
"""
Script to run processing function directly using Docker
"""
import subprocess
import time
import requests
import json
import os

def start_processing_service():
    """Start the processing service locally for testing"""
    
    # Update ffmpeg path for local testing
    env = os.environ.copy()
    env['FFMPEG_PATH'] = '/opt/homebrew/bin/ffmpeg'
    env['PORT'] = '8080'
    
    print("🚀 Starting processing service locally...")
    
    # Start the service in background
    process = subprocess.Popen([
        'python3', 'processing_service.py'
    ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for service to start
    print("⏳ Waiting for service to start...")
    time.sleep(3)
    
    return process

def test_processing_endpoint():
    """Test the processing endpoint with a real file"""
    
    # First upload the test file to a temporary web server or use existing file
    test_video_path = "/Users/rajvindersingh/Projects/karooke/test_30sec_video.mp4"
    
    if not os.path.exists(test_video_path):
        print(f"❌ Test video not found: {test_video_path}")
        return False
    
    # Copy file to temp location accessible by the service
    import tempfile
    import shutil
    
    # Create temp file with public URL
    temp_dir = tempfile.mkdtemp()
    temp_video = os.path.join(temp_dir, "test_video.mp4")
    shutil.copy2(test_video_path, temp_video)
    
    print(f"📁 Test video copied to: {temp_video}")
    
    # Test health endpoint first
    try:
        health_response = requests.get("http://localhost:8080/health", timeout=10)
        print(f"🩺 Health check: {health_response.status_code}")
        print(f"   Response: {health_response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test processing with direct file path (modify service to accept local files for testing)
    payload = {
        "video_url": f"file://{temp_video}",
        "vocal_levels": [0.0],
        "test_duration": 10
    }
    
    try:
        print("🎯 Testing processing endpoint...")
        response = requests.post(
            "http://localhost:8080/process",
            json=payload,
            timeout=120  # 2 minutes timeout
        )
        
        print(f"🔍 Processing response: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Processing successful!")
            print(f"   Job ID: {result.get('job_id')}")
            print(f"   Videos generated: {len(result.get('videos', []))}")
            return True
        else:
            print(f"❌ Processing failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Processing request failed: {e}")
        return False
    finally:
        # Cleanup
        try:
            os.remove(temp_video)
            os.rmdir(temp_dir)
        except:
            pass

def main():
    """Main test function"""
    
    # Start the service
    process = start_processing_service()
    
    try:
        # Test the service
        success = test_processing_endpoint()
        
        if success:
            print("✅ Processing function works locally!")
        else:
            print("❌ Processing function test failed!")
            
    finally:
        # Stop the service
        print("🛑 Stopping processing service...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()

if __name__ == "__main__":
    main()