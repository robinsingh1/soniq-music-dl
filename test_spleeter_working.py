#!/usr/bin/env python3
"""
Demonstrate that Spleeter integration works correctly
"""
import os
import sys
import tempfile
import subprocess
from spleeter.separator import Separator
import numpy as np
import librosa
import soundfile as sf

def test_spleeter_functionality():
    """Test core Spleeter functionality that will work in Docker"""
    
    test_video = "/Users/rajvindersingh/Projects/karooke/test_30sec_video.mp4"
    if not os.path.exists(test_video):
        print(f"❌ Test video not found: {test_video}")
        return False
    
    print("🎯 Testing Spleeter integration...")
    
    # Extract audio using ffmpeg
    print("🎵 Step 1: Extract audio from video...")
    audio_path = os.path.join(tempfile.gettempdir(), "test_audio.wav")
    
    ffmpeg_cmd = [
        '/opt/homebrew/bin/ffmpeg',  # Local path
        '-i', test_video,
        '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2',
        '-t', '10',  # Only 10 seconds
        audio_path, '-y'
    ]
    
    result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
    if not os.path.exists(audio_path):
        print(f"❌ Audio extraction failed: {result.stderr}")
        return False
    
    print(f"✅ Audio extracted: {audio_path}")
    print(f"   File size: {os.path.getsize(audio_path)} bytes")
    
    # Initialize Spleeter
    print("🔧 Step 2: Initialize Spleeter...")
    try:
        separator = Separator('spleeter:2stems-16kHz')
        print("✅ Spleeter initialized successfully")
    except Exception as e:
        print(f"❌ Spleeter initialization failed: {e}")
        return False
    
    # Load audio
    print("📂 Step 3: Load audio file...")
    try:
        waveform, sample_rate = librosa.load(audio_path, sr=44100, mono=False)
        
        # Ensure stereo format for Spleeter
        if len(waveform.shape) == 1:
            waveform = np.array([waveform, waveform])
        elif waveform.shape[0] == 1:
            waveform = np.repeat(waveform, 2, axis=0)
        
        # Transpose for Spleeter (time, channels)
        waveform = waveform.T
        
        print(f"✅ Audio loaded: shape={waveform.shape}, sr={sample_rate}")
    except Exception as e:
        print(f"❌ Audio loading failed: {e}")
        return False
    
    # Run Spleeter separation
    print("🎤 Step 4: Run Spleeter separation...")
    try:
        prediction = separator.separate(waveform)
        print("✅ Spleeter separation completed")
        
        # Check results
        if 'vocals' in prediction and 'accompaniment' in prediction:
            vocals_shape = prediction['vocals'].shape
            accompaniment_shape = prediction['accompaniment'].shape
            print(f"   Vocals shape: {vocals_shape}")
            print(f"   Accompaniment shape: {accompaniment_shape}")
        else:
            print("❌ Expected vocals and accompaniment not found in results")
            return False
            
    except Exception as e:
        print(f"❌ Spleeter separation failed: {e}")
        return False
    
    # Save separated tracks
    print("💾 Step 5: Save separated tracks...")
    try:
        vocals_path = os.path.join(tempfile.gettempdir(), "test_vocals.wav")
        accompaniment_path = os.path.join(tempfile.gettempdir(), "test_accompaniment.wav")
        
        # Save vocals
        vocals_audio = prediction['vocals']
        sf.write(vocals_path, vocals_audio, sample_rate)
        
        # Save accompaniment  
        accompaniment_audio = prediction['accompaniment']
        sf.write(accompaniment_path, accompaniment_audio, sample_rate)
        
        print(f"✅ Vocals saved: {vocals_path} ({os.path.getsize(vocals_path)} bytes)")
        print(f"✅ Accompaniment saved: {accompaniment_path} ({os.path.getsize(accompaniment_path)} bytes)")
        
        # Cleanup
        os.remove(audio_path)
        os.remove(vocals_path)
        os.remove(accompaniment_path)
        
    except Exception as e:
        print(f"❌ Saving tracks failed: {e}")
        return False
    
    print("🎉 All Spleeter functionality works correctly!")
    return True

def show_docker_commands():
    """Show the Docker commands to run the processing service"""
    
    print("\n" + "="*60)
    print("🐳 DOCKER COMMANDS TO RUN PROCESSING SERVICE")
    print("="*60)
    
    print("\n1. Build the Docker image:")
    print("   docker build --platform linux/amd64 -f Dockerfile.processing -t karaoke-processing .")
    
    print("\n2. Run the container:")
    print("   docker run --platform linux/amd64 -p 8080:8080 karaoke-processing")
    
    print("\n3. Test the health endpoint:")
    print("   curl http://localhost:8080/health")
    
    print("\n4. Test processing with a video URL:")
    print("""   curl -X POST http://localhost:8080/process \\
        -H "Content-Type: application/json" \\
        -d '{
            "video_url": "https://your-video-url.mp4",
            "vocal_levels": [0.0, 0.25, 0.5],
            "test_duration": 30
        }'""")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    print("🧪 Testing Spleeter functionality locally...")
    
    success = test_spleeter_functionality()
    
    if success:
        print("\n✅ SUCCESS: Spleeter integration works correctly!")
        print("   - Audio extraction: ✅")
        print("   - Spleeter initialization: ✅") 
        print("   - Audio loading: ✅")
        print("   - ML separation: ✅")
        print("   - Track saving: ✅")
        
        show_docker_commands()
        
        print("\n🔧 NEXT STEPS:")
        print("   1. The processing function works locally with Spleeter")
        print("   2. Build Docker image using the commands above")
        print("   3. The Docker container will use x86_64 platform for TensorFlow compatibility")
        print("   4. Models will be pre-downloaded during Docker build")
        
    else:
        print("\n❌ FAILED: Spleeter integration has issues")
        
    sys.exit(0 if success else 1)