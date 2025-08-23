#!/usr/bin/env python3
"""
Test only the Spleeter audio separation functionality
"""
import os
import sys
import tempfile

# Update ffmpeg path for local testing
import processing_service
processing_service.FFMPEG_PATH = '/opt/homebrew/bin/ffmpeg'

from processing_service import python_spleeter_separation

def test_spleeter_only():
    """Test only Spleeter separation"""
    
    # Use the test video file
    test_video = "/Users/rajvindersingh/Projects/karooke/test_30sec_video.mp4"
    
    if not os.path.exists(test_video):
        print(f"❌ Test video not found: {test_video}")
        return False
    
    print(f"🎯 Testing Spleeter with: {test_video}")
    
    # Test Spleeter separation
    print("🎤 Testing Spleeter separation (30 seconds)...")
    vocals_path, accompaniment_path = python_spleeter_separation(test_video, test_duration=30)
    
    if not vocals_path or not accompaniment_path:
        print("❌ Spleeter separation failed")
        return False
    
    print(f"✅ Spleeter separation successful!")
    print(f"   Vocals: {vocals_path}")
    print(f"   Vocals size: {os.path.getsize(vocals_path)} bytes")
    print(f"   Accompaniment: {accompaniment_path}")
    print(f"   Accompaniment size: {os.path.getsize(accompaniment_path)} bytes")
    
    # Play a few seconds of each file to verify
    print("🔊 Testing playback (5 seconds each)...")
    
    # Test accompaniment audio (should be instrumental)
    print("🎵 Playing accompaniment (instrumental)...")
    os.system(f"afplay {accompaniment_path} &")
    os.system("sleep 5")
    os.system("killall afplay 2>/dev/null")
    
    print("🎤 Playing vocals...")
    os.system(f"afplay {vocals_path} &")
    os.system("sleep 5") 
    os.system("killall afplay 2>/dev/null")
    
    # Cleanup
    if os.path.exists(vocals_path):
        os.remove(vocals_path)
    if os.path.exists(accompaniment_path):
        os.remove(accompaniment_path)
    
    print("✅ Spleeter test completed successfully!")
    return True

if __name__ == "__main__":
    print("🧪 Testing Spleeter audio separation...")
    success = test_spleeter_only()
    
    if success:
        print("✅ Spleeter test passed!")
        sys.exit(0)
    else:
        print("❌ Spleeter test failed!")
        sys.exit(1)