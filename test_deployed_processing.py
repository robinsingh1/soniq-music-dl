#!/usr/bin/env python3
"""
Test the currently deployed processing service
"""
import requests
import json
import time

def test_current_deployment():
    """Test the processing service that was deployed yesterday"""
    
    # Use the test video that's already in GCS
    test_payload = {
        "video_url": "https://storage.googleapis.com/soniq-karaoke-videos/test_30sec_video.mp4",
        "vocal_levels": [0.0],  # Just test 0% vocal (instrumental)
        "test_duration": 10     # Short 10-second test
    }
    
    service_url = "https://soniq-processor-scqr2wnnya-uc.a.run.app"
    
    print(f"🧪 Testing deployed processing service")
    print(f"   Service: {service_url}")
    print(f"   Test video: 10 seconds of test_30sec_video.mp4")
    print(f"   Expected: Basic processing (no separated audio preservation yet)")
    
    try:
        start_time = time.time()
        
        response = requests.post(
            f"{service_url}/process",
            json=test_payload,
            timeout=300,  # 5 minutes max
            headers={'Content-Type': 'application/json'}
        )
        
        duration = time.time() - start_time
        print(f"\n🔍 Response (took {duration:.1f}s):")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Processing successful!")
            print(f"   Job ID: {result.get('job_id', 'N/A')}")
            
            # Check for old vs new version features
            if 'separated_audio' in result:
                print(f"   🆕 NEW VERSION: Separated audio files preserved!")
                separated_files = result['separated_audio']
                for audio_file in separated_files:
                    print(f"     - {audio_file['type']}: {audio_file.get('url', 'No URL')}")
            else:
                print(f"   📼 OLD VERSION: Basic processing only")
            
            if 'videos' in result:
                videos = result['videos']
                print(f"   🎬 Karaoke videos: {len(videos)} generated")
                for video in videos:
                    print(f"     - {video['vocal_level']}% vocal: {video.get('url', 'No URL')}")
            
            if 'metadata_url' in result:
                print(f"   📋 Request metadata: {result['metadata_url']}")
            
            return True, result
        else:
            print(f"❌ Processing failed:")
            print(f"   Status: {response.status_code}")
            print(f"   Error: {response.text}")
            return False, None
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out (>5 minutes)")
        return False, None
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False, None

if __name__ == "__main__":
    print("🔍 Testing Currently Deployed Processing Service")
    print("="*60)
    
    success, result = test_current_deployment()
    
    if success:
        print(f"\n✅ DEPLOYED SERVICE IS WORKING!")
        print(f"   The service deployed yesterday is functional")
        if result and 'separated_audio' in result:
            print(f"   🎉 NEW FEATURES: Separated audio preservation active")
        else:
            print(f"   📦 OLD VERSION: Need to deploy updated version for new features")
    else:
        print(f"\n❌ DEPLOYED SERVICE HAS ISSUES")
        print(f"   The current deployment may need to be updated")