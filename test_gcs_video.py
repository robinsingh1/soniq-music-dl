#!/usr/bin/env python3
"""
Test processing service with a GCS video
"""
import requests
import json

# Configuration
PROCESSING_SERVICE_URL = "https://soniq-processor-894603036612.us-central1.run.app"
TEST_VIDEO_URL = "https://storage.googleapis.com/soniq-karaoke-videos/trending/01_Tyla_-_PUSH_2_START_Official_Music_Video.mp4"

def test_processing_service():
    """Test the processing service with a GCS video"""
    print("🎬 TESTING PROCESSING SERVICE WITH GCS VIDEO")
    print("=" * 60)
    print(f"🎯 Processing Service: {PROCESSING_SERVICE_URL}")
    print(f"📹 Video URL: {TEST_VIDEO_URL}")
    print(f"⏱️ Test Duration: 30 seconds")
    print()
    
    # Test health endpoint first
    print("🏥 Checking service health...")
    try:
        health_response = requests.get(f"{PROCESSING_SERVICE_URL}/health", timeout=10)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"✅ Service healthy: {health_data}")
        else:
            print(f"⚠️ Health check failed: {health_response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    print()
    
    # Test processing with 30-second sample
    try:
        print("🔄 Starting 30-second test processing...")
        print("📤 Sending request to processing service...")
        
        request_data = {
            "video_url": TEST_VIDEO_URL,
            "vocal_levels": [0.0, 0.25],  # 0% and 25% vocal levels
            "test_duration": 30  # 30-second test
        }
        
        print(f"📋 Request payload: {json.dumps(request_data, indent=2)}")
        print()
        
        response = requests.post(
            f"{PROCESSING_SERVICE_URL}/process",
            json=request_data,
            timeout=600  # 10 minute timeout for processing
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("🎉 PROCESSING SUCCESSFUL!")
                print()
                print(f"🆔 Job ID: {result.get('job_id')}")
                print(f"🎤 Created {len(result.get('videos', []))} karaoke videos:")
                
                for i, video in enumerate(result.get('videos', []), 1):
                    print(f"  {i}. {video['vocal_level']}% vocal: {video['url']}")
                    print(f"     📄 Filename: {video['filename']}")
                
                print()
                print("✅ Test completed successfully!")
                return True
            else:
                print(f"❌ Processing failed: {result}")
                return False
        else:
            print(f"❌ HTTP Error {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Processing timed out (this may be normal for first run)")
        print("   The processing may still be running in the background")
        return False
    except Exception as e:
        print(f"❌ Processing error: {str(e)}")
        return False

def main():
    """Main test function"""
    success = test_processing_service()
    
    print()
    print("=" * 60)
    if success:
        print("🏁 TEST RESULT: SUCCESS")
        print("✅ Python Spleeter is working on Cloud Run!")
        print("🎵 Ready to process full trending music videos")
    else:
        print("🏁 TEST RESULT: FAILED")
        print("❌ Check service logs for issues")
        print("🔧 May need to redeploy with dependency fixes")

if __name__ == "__main__":
    main()