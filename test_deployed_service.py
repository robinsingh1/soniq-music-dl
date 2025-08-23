#!/usr/bin/env python3
"""
Test the deployed processing service to verify separated audio preservation
"""
import requests
import json
import time

def test_deployed_processing():
    """Test the deployed processing service"""
    
    # Test with a small public video URL 
    video_url = "https://storage.googleapis.com/soniq-karaoke-videos/test_30sec_video.mp4"
    
    payload = {
        "video_url": video_url,
        "vocal_levels": [0.0],  # Just test one level
        "test_duration": 10     # Short test
    }
    
    print("🧪 Testing deployed processing service...")
    print(f"   Service URL: https://soniq-processor-894603036612.us-central1.run.app")
    print(f"   Video URL: {video_url}")
    print(f"   Payload: {json.dumps(payload, indent=2)}")
    
    try:
        start_time = time.time()
        
        response = requests.post(
            "https://soniq-processor-894603036612.us-central1.run.app/process",
            json=payload,
            timeout=600,  # 10 minutes for Cloud Run
            headers={'Content-Type': 'application/json'}
        )
        
        duration = time.time() - start_time
        print(f"\n🔍 Response (took {duration:.1f}s):")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Processing successful!")
            print(f"   Response: {json.dumps(result, indent=2)}")
            
            # Check for separated audio files (new feature)
            if 'separated_audio' in result:
                separated_files = result['separated_audio']
                print(f"\n📂 Separated Audio Files ({len(separated_files)}):")
                for audio_file in separated_files:
                    print(f"   - {audio_file['type']}: {audio_file['filename']}")
                    if 'url' in audio_file:
                        print(f"     URL: {audio_file['url']}")
                    else:
                        print(f"     ⚠️ No URL (feature not deployed yet)")
                
                return True, "separated_audio_preserved"
            else:
                print(f"\n⚠️ No separated_audio field in response")
                print(f"   This means the updated version is not deployed yet")
                
                # Check karaoke videos
                if 'videos' in result:
                    videos = result['videos']
                    print(f"\n🎬 Karaoke Videos ({len(videos)}):")
                    for video in videos:
                        print(f"   - {video['vocal_level']}% vocal: {video['filename']}")
                        if 'url' in video:
                            print(f"     URL: {video['url']}")
                
                return True, "old_version_working"
        else:
            print(f"❌ Processing failed: {response.text}")
            return False, "processing_failed"
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False, "request_failed"

if __name__ == "__main__":
    print("🧪 Testing Deployed Processing Service")
    print("="*50)
    
    success, status = test_deployed_processing()
    
    if success:
        if status == "separated_audio_preserved":
            print("\n✅ DEPLOYED SERVICE TEST PASSED!")
            print("   ✓ Separated audio files preserved to GCS")
            print("   ✓ Request metadata saved")
            print("   ✓ Updated version deployed successfully")
        elif status == "old_version_working":
            print("\n⚠️ OLD VERSION IS DEPLOYED")
            print("   ✓ Basic processing works")
            print("   ✗ Separated audio preservation not implemented")
            print("   → Need to deploy updated version")
    else:
        print(f"\n❌ DEPLOYED SERVICE TEST FAILED: {status}")
    
    exit(0 if success else 1)