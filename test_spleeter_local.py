#!/usr/bin/env python3
"""
Test Python Spleeter locally with 30-second sample
"""
import os
import requests
import tempfile

# Configuration
PROCESSING_SERVICE_URL = "http://localhost:8080"  # Local testing
TEST_VIDEO_URL = "https://storage.googleapis.com/soniq-karaoke-videos/trending/01_Tyla_Water.mp4"

def test_spleeter_locally():
    """Test the local processing service with 30-second sample"""
    print("🧪 TESTING PYTHON SPLEETER LOCALLY (30 seconds)")
    print("=" * 60)
    
    try:
        # Test with 30-second duration
        print(f"📹 Testing with video: {TEST_VIDEO_URL}")
        print("⏱️ Duration limit: 30 seconds")
        
        response = requests.post(
            f"{PROCESSING_SERVICE_URL}/process",
            json={
                "video_url": TEST_VIDEO_URL,
                "vocal_levels": [0.0, 0.25],  # Test with 0% and 25% vocal
                "test_duration": 30  # 30-second test
            },
            timeout=600  # 10 minute timeout for test
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ LOCAL TEST SUCCESSFUL!")
                print(f"🎤 Created {len(result.get('videos', []))} test karaoke videos:")
                
                for video in result.get('videos', []):
                    print(f"  • {video['vocal_level']}% vocal: {video['url']}")
                
                return True
            else:
                print(f"❌ Processing failed: {result}")
                return False
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - make sure processing service is running locally")
        print("   Run: python processing_service.py")
        return False
    except Exception as e:
        print(f"❌ Test error: {str(e)}")
        return False

def test_cloud_run():
    """Test the Cloud Run processing service with 30-second sample"""
    print("\n🌐 TESTING PYTHON SPLEETER ON CLOUD RUN (30 seconds)")
    print("=" * 60)
    
    cloud_url = "https://soniq-processor-894603036612.us-central1.run.app"
    
    try:
        print(f"📹 Testing with video: {TEST_VIDEO_URL}")
        print("⏱️ Duration limit: 30 seconds")
        
        response = requests.post(
            f"{cloud_url}/process",
            json={
                "video_url": TEST_VIDEO_URL,
                "vocal_levels": [0.0],  # Test with just 0% vocal for speed
                "test_duration": 30  # 30-second test
            },
            timeout=600  # 10 minute timeout for test
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ CLOUD RUN TEST SUCCESSFUL!")
                print(f"🎤 Created {len(result.get('videos', []))} test karaoke videos:")
                
                for video in result.get('videos', []):
                    print(f"  • {video['vocal_level']}% vocal: {video['url']}")
                
                return True
            else:
                print(f"❌ Processing failed: {result}")
                return False
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Cloud Run test error: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🧪 SPLEETER TEST SUITE")
    print("=" * 60)
    
    # Test locally first
    local_success = test_spleeter_locally()
    
    # Test on Cloud Run
    cloud_success = test_cloud_run()
    
    # Summary
    print(f"\n📊 TEST RESULTS")
    print("=" * 60)
    print(f"🏠 Local test: {'✅ PASS' if local_success else '❌ FAIL'}")
    print(f"🌐 Cloud Run test: {'✅ PASS' if cloud_success else '❌ FAIL'}")
    
    if local_success and cloud_success:
        print("\n🎉 ALL TESTS PASSED - Python Spleeter is working!")
    elif local_success:
        print("\n⚠️ Local working, Cloud Run needs deployment")
    else:
        print("\n❌ Tests failed - check logs for issues")

if __name__ == "__main__":
    main()