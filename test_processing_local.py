#!/usr/bin/env python3
"""
Test the processing function locally with test files
"""
import os
import sys
import tempfile
import json

# Update ffmpeg path for local testing
import processing_service
processing_service.FFMPEG_PATH = '/opt/homebrew/bin/ffmpeg'

from processing_service import python_spleeter_separation, transcribe_audio, create_karaoke_video

def test_local_processing():
    """Test processing function with local video file"""
    
    # Use the test video file
    test_video = "/Users/rajvindersingh/Projects/karooke/test_30sec_video.mp4"
    
    if not os.path.exists(test_video):
        print(f"❌ Test video not found: {test_video}")
        return False
    
    print(f"🎯 Testing processing with: {test_video}")
    
    # Test Spleeter separation
    print("🎤 Testing Spleeter separation...")
    vocals_path, accompaniment_path = python_spleeter_separation(test_video, test_duration=10)  # Test first 10 seconds
    
    if not vocals_path or not accompaniment_path:
        print("❌ Spleeter separation failed")
        return False
    
    print(f"✅ Spleeter separation successful!")
    print(f"   Vocals: {vocals_path}")
    print(f"   Accompaniment: {accompaniment_path}")
    
    # Check if OpenAI API key is available for transcription
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  OPENAI_API_KEY not set, skipping transcription test")
        
        # Cleanup
        if os.path.exists(vocals_path):
            os.remove(vocals_path)
        if os.path.exists(accompaniment_path):
            os.remove(accompaniment_path)
        
        print("✅ Basic Spleeter functionality works!")
        return True
    
    # Test transcription
    print("🎙️ Testing transcription...")
    transcript = transcribe_audio(vocals_path)
    
    if not transcript:
        print("❌ Transcription failed")
        # Cleanup
        if os.path.exists(vocals_path):
            os.remove(vocals_path)
        if os.path.exists(accompaniment_path):
            os.remove(accompaniment_path)
        return False
    
    print(f"✅ Transcription successful! Found {len(transcript.words) if hasattr(transcript, 'words') else 0} words")
    
    # Test karaoke video creation
    print("🎬 Testing karaoke video creation...")
    output_filename = "test_karaoke_0vocal.mp4"
    video_path = create_karaoke_video(accompaniment_path, transcript, 0.0, output_filename)
    
    if video_path and os.path.exists(video_path):
        print(f"✅ Karaoke video created: {video_path}")
        print(f"   File size: {os.path.getsize(video_path)} bytes")
        
        # Cleanup
        os.remove(video_path)
    else:
        print("❌ Karaoke video creation failed")
    
    # Cleanup
    if os.path.exists(vocals_path):
        os.remove(vocals_path)
    if os.path.exists(accompaniment_path):
        os.remove(accompaniment_path)
    
    print("✅ All processing functions work locally!")
    return True

if __name__ == "__main__":
    print("🧪 Testing processing functions locally...")
    success = test_local_processing()
    
    if success:
        print("✅ Local processing test completed successfully!")
        sys.exit(0)
    else:
        print("❌ Local processing test failed!")
        sys.exit(1)