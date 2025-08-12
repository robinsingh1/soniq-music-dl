#!/usr/bin/env python3
"""
Test processing service async with GCS video - kick off and monitor
"""
import requests
import json
import time
import threading
from datetime import datetime

# Configuration
PROCESSING_SERVICE_URL = "https://soniq-processor-scqr2wnnya-uc.a.run.app"
TEST_VIDEO_URL = "https://storage.googleapis.com/soniq-karaoke-videos/trending/01_Tyla_-_PUSH_2_START_Official_Music_Video.mp4"

def kick_off_processing():
    """Start processing job asynchronously"""
    print("🚀 ASYNC PROCESSING TEST - KICK OFF & MONITOR")
    print("=" * 60)
    print(f"🎯 Processing Service: {PROCESSING_SERVICE_URL}")
    print(f"📹 Video: Tyla - PUSH 2 START")
    print(f"⏱️ Test Duration: 30 seconds")
    print(f"🕐 Started at: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    # Health check first
    try:
        health_response = requests.get(f"{PROCESSING_SERVICE_URL}/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ Service is healthy")
        else:
            print(f"⚠️ Service health check failed: {health_response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Can't reach service: {e}")
        return None
    
    # Start processing request
    request_data = {
        "video_url": TEST_VIDEO_URL,
        "vocal_levels": [0.0],  # Just 0% vocal for faster test
        "test_duration": 30  # 30-second test
    }
    
    print("📤 Kicking off processing job...")
    print(f"📋 Request: {json.dumps(request_data, indent=2)}")
    print()
    
    try:
        # Start the request in a separate thread
        response_data = {}
        
        def make_request():
            try:
                response = requests.post(
                    f"{PROCESSING_SERVICE_URL}/process",
                    json=request_data,
                    timeout=900  # 15 minute timeout
                )
                response_data['status_code'] = response.status_code
                response_data['response'] = response.json() if response.status_code == 200 else response.text
                response_data['completed'] = True
            except requests.exceptions.Timeout:
                response_data['timeout'] = True
                response_data['completed'] = True
            except Exception as e:
                response_data['error'] = str(e)
                response_data['completed'] = True
        
        # Start processing in background thread
        processing_thread = threading.Thread(target=make_request)
        processing_thread.daemon = True
        processing_thread.start()
        
        print("🔄 Processing started in background...")
        print("📊 Monitoring progress (will check every 30 seconds):")
        print()
        
        # Monitor progress
        start_time = time.time()
        check_count = 0
        
        while not response_data.get('completed', False):
            check_count += 1
            elapsed = int(time.time() - start_time)
            
            print(f"⏳ Check #{check_count} - Elapsed: {elapsed}s - Status: Processing...")
            
            # Check if thread is still alive
            if processing_thread.is_alive():
                print("   🔄 Job is still running in Cloud Run")
            else:
                print("   ✅ Background thread completed")
                break
            
            # Wait 30 seconds before next check
            time.sleep(30)
        
        # Get final results
        print()
        print("🏁 FINAL RESULTS:")
        print("=" * 40)
        
        if response_data.get('timeout'):
            print("⏰ Request timed out (job may still be running)")
            print("   This is normal for first-time Spleeter model download")
            return False
        elif response_data.get('error'):
            print(f"❌ Error: {response_data['error']}")
            return False
        elif response_data.get('status_code') == 200:
            result = response_data['response']
            if result.get('success'):
                print("🎉 SUCCESS!")
                print(f"🆔 Job ID: {result.get('job_id')}")
                print(f"🎤 Videos created: {len(result.get('videos', []))}")
                
                for video in result.get('videos', []):
                    print(f"  • {video['vocal_level']}% vocal: {video['url']}")
                
                total_time = int(time.time() - start_time)
                print(f"⏱️ Total processing time: {total_time}s")
                return True
            else:
                print(f"❌ Processing failed: {result}")
                return False
        else:
            print(f"❌ HTTP {response_data.get('status_code')}: {response_data.get('response')}")
            return False
    
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        return False

def main():
    """Main async test function"""
    try:
        success = kick_off_processing()
        
        print()
        print("=" * 60)
        if success:
            print("✅ ASYNC TEST COMPLETED SUCCESSFULLY")
            print("🎵 Python Spleeter is working on Cloud Run!")
            print("🚀 Ready for batch processing of trending videos")
        else:
            print("❌ ASYNC TEST FAILED OR INCOMPLETE")
            print("🔍 Check Cloud Run logs for detailed error info")
            print("💡 First run may take longer due to model download")
        
        print()
        print("🔗 Useful links:")
        print(f"   📊 Cloud Run logs: https://console.cloud.google.com/logs/query;query=resource.type%3D%22cloud_run_revision%22?project=soundbyte-e419d")
        print(f"   🎬 Processing service: {PROCESSING_SERVICE_URL}")
        
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")

if __name__ == "__main__":
    main()