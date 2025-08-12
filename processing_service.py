#!/usr/bin/env python3
"""
Karaoke Processing Service for Cloud Run
Takes downloaded video URL and creates karaoke versions
"""
import os
import tempfile
import subprocess
import uuid
from flask import Flask, request, jsonify
import openai
import requests
from google.cloud import storage
import numpy as np
import librosa
import soundfile as sf
from spleeter.separator import Separator

app = Flask(__name__)

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
BUCKET_NAME = os.getenv('BUCKET_NAME', 'soniq-karaoke-videos')
TEMP_DIR = tempfile.gettempdir()
FFMPEG_PATH = '/usr/bin/ffmpeg'  # Cloud Run path

def download_from_url(url, local_filename):
    """Download file from URL to local storage"""
    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        with open(local_filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return os.path.exists(local_filename)
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False

def upload_to_gcs(local_path, gcs_filename):
    """Upload file to Google Cloud Storage"""
    try:
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(f"karaoke/{gcs_filename}")
        
        blob.upload_from_filename(local_path)
        blob.make_public()
        
        return f"https://storage.googleapis.com/{BUCKET_NAME}/karaoke/{gcs_filename}"
    except Exception as e:
        print(f"❌ GCS upload failed: {e}")
        return None

def python_spleeter_separation(video_path, test_duration=None):
    """Use Python Spleeter library for audio separation"""
    print("🎤 Python Spleeter Audio Separation")
    
    # Extract audio from video
    audio_path = os.path.join(TEMP_DIR, "input_audio.wav")
    print("🎵 Extracting audio from video...")
    
    extract_cmd = [
        FFMPEG_PATH, '-i', video_path,
        '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2'
    ]
    
    # Add test duration limit if specified
    if test_duration:
        extract_cmd.extend(['-t', str(test_duration)])
        print(f"⏱️ Test mode: limiting to {test_duration} seconds")
    
    extract_cmd.extend([audio_path, '-y'])
    
    result = subprocess.run(extract_cmd, capture_output=True, text=True)
    if not os.path.exists(audio_path):
        print("❌ Audio extraction failed")
        print(f"FFmpeg stderr: {result.stderr}")
        return None, None
    
    try:
        # Initialize Spleeter separator
        print("🔧 Initializing Spleeter...")
        separator = Separator('spleeter:2stems-16kHz')
        
        # Load audio file
        print("📂 Loading audio...")
        waveform, sample_rate = librosa.load(audio_path, sr=44100, mono=False)
        
        # Ensure stereo format
        if len(waveform.shape) == 1:
            waveform = np.array([waveform, waveform])
        elif waveform.shape[0] == 1:
            waveform = np.repeat(waveform, 2, axis=0)
        
        # Transpose for Spleeter (time, channels)
        waveform = waveform.T
        
        print(f"🎵 Audio shape: {waveform.shape}, Sample rate: {sample_rate}")
        
        # Separate using Spleeter
        print("🎤 Running Spleeter ML separation...")
        prediction = separator.separate(waveform)
        
        # Save separated tracks
        vocals_path = os.path.join(TEMP_DIR, "vocals.wav")
        accompaniment_path = os.path.join(TEMP_DIR, "accompaniment.wav")
        
        # Save vocals
        vocals_audio = prediction['vocals']
        sf.write(vocals_path, vocals_audio, sample_rate)
        print(f"💾 Saved vocals: {vocals_path}")
        
        # Save accompaniment
        accompaniment_audio = prediction['accompaniment']
        sf.write(accompaniment_path, accompaniment_audio, sample_rate)
        print(f"💾 Saved accompaniment: {accompaniment_path}")
        
        # Cleanup original audio
        os.remove(audio_path)
        
        print("✅ Python Spleeter separation successful!")
        return vocals_path, accompaniment_path
        
    except Exception as e:
        print(f"❌ Python Spleeter separation failed: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def transcribe_audio(audio_path):
    """Transcribe audio using OpenAI Whisper"""
    print("🎙️ Transcribing with OpenAI Whisper...")
    
    try:
        openai.api_key = OPENAI_API_KEY
        
        # Check file size and chunk if needed
        file_size = os.path.getsize(audio_path)
        if file_size > 20 * 1024 * 1024:  # 20MB limit
            return transcribe_chunked(audio_path)
        
        with open(audio_path, 'rb') as audio_file:
            transcript = openai.Audio.transcribe(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["word"]
            )
        
        print(f"✅ Transcribed: {len(transcript.words)} words")
        return transcript
        
    except Exception as e:
        print(f"❌ Transcription failed: {e}")
        return None

def transcribe_chunked(audio_path):
    """Transcribe large audio files in chunks"""
    print("📦 Chunking large audio file...")
    
    chunk_dir = os.path.join(TEMP_DIR, "audio_chunks")
    os.makedirs(chunk_dir, exist_ok=True)
    
    # Split into 5-minute chunks
    chunk_duration = 300
    chunk_files = []
    chunk_index = 0
    start_time = 0
    
    while start_time < 600:  # Process up to 10 minutes
        chunk_path = os.path.join(chunk_dir, f"chunk_{chunk_index:03d}.wav")
        
        chunk_cmd = [
            FFMPEG_PATH, '-i', audio_path,
            '-ss', str(start_time),
            '-t', str(chunk_duration),
            '-acodec', 'pcm_s16le',
            chunk_path, '-y'
        ]
        
        result = subprocess.run(chunk_cmd, capture_output=True, text=True)
        
        if os.path.exists(chunk_path) and os.path.getsize(chunk_path) > 1000:
            chunk_files.append((start_time, chunk_path))
            chunk_index += 1
            start_time += chunk_duration
        else:
            break
    
    # Transcribe each chunk
    all_words = []
    
    for start_offset, chunk_path in chunk_files:
        try:
            with open(chunk_path, 'rb') as audio_file:
                transcript = openai.Audio.transcribe(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                    timestamp_granularities=["word"]
                )
            
            # Adjust timestamps
            for word in transcript.words:
                word.start += start_offset
                word.end += start_offset
                all_words.append(word)
                
            print(f"✅ Chunk transcribed: {len(transcript.words)} words")
            
        except Exception as e:
            print(f"❌ Chunk failed: {e}")
        
        os.remove(chunk_path)
    
    # Return combined transcript
    class CombinedTranscript:
        def __init__(self, words):
            self.words = words
    
    return CombinedTranscript(all_words)

def create_karaoke_video(accompaniment_path, transcript, vocal_level, output_filename):
    """Create karaoke video with specified vocal level"""
    print(f"🎬 Creating karaoke video ({int(vocal_level*100)}% vocal)...")
    
    if not transcript or not transcript.words:
        return None
    
    # Create ASS subtitle file
    ass_path = os.path.join(TEMP_DIR, "karaoke_subtitles.ass")
    
    ass_content = """[Script Info]
Title: Karaoke Video
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,28,&Hffffff,&Hffffff,&H000000,&H80000000,1,0,0,0,100,100,0,0,1,3,0,2,10,10,30,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    # Group words into lines
    lines = []
    current_line = []
    
    for word in transcript.words:
        current_line.append(word)
        if len(current_line) >= 8 or (word.word.rstrip() and word.word.rstrip()[-1] in '.!?'):
            if current_line:
                lines.append(current_line)
                current_line = []
    
    if current_line:
        lines.append(current_line)
    
    # Create karaoke subtitles
    for line_words in lines:
        if not line_words:
            continue
        
        line_start = line_words[0].start
        line_end = line_words[-1].end
        
        # ASS time format
        start_time = f"{int(line_start//3600):01d}:{int((line_start%3600)//60):02d}:{int(line_start%60):02d}.{int((line_start%1)*100):02d}"
        end_time = f"{int(line_end//3600):01d}:{int((line_end%3600)//60):02d}:{int(line_end%60):02d}.{int((line_end%1)*100):02d}"
        
        # Build karaoke effect
        text_parts = []
        current_time = line_start
        
        for word in line_words:
            word_duration = max(0.1, word.end - current_time)
            highlight_duration = int(word_duration * 100)
            
            clean_word = word.word.strip()
            text_parts.append(f"{{\\k{highlight_duration}}}{clean_word}")
            current_time = word.end
        
        karaoke_text = "".join(text_parts)
        ass_content += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{karaoke_text}\\N\n"
    
    with open(ass_path, 'w', encoding='utf-8') as f:
        f.write(ass_content)
    
    # Create video
    output_path = os.path.join(TEMP_DIR, output_filename)
    
    ffmpeg_cmd = [
        FFMPEG_PATH,
        '-i', accompaniment_path,
        '-vf', f"color=black:size=1280x720:duration={min(300, transcript.words[-1].end)},subtitles={ass_path}:force_style='FontSize=32'",
        '-c:a', 'aac',
        '-c:v', 'libx264',
        '-t', str(min(300, transcript.words[-1].end)),
        output_path, '-y'
    ]
    
    result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
    
    if os.path.exists(output_path):
        return output_path
    else:
        print(f"❌ Video creation failed: {result.stderr}")
        return None

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'karaoke-processor',
        'version': '1.0'
    })

@app.route('/process', methods=['POST'])
def process_video():
    """Process downloaded video into karaoke versions"""
    try:
        data = request.get_json()
        
        if not data or 'video_url' not in data:
            return jsonify({'error': 'Missing video_url'}), 400
        
        video_url = data['video_url']
        vocal_levels = data.get('vocal_levels', [0.0, 0.25, 0.5])
        
        print(f"🎯 Processing: {video_url}")
        
        # Download video from storage
        job_id = str(uuid.uuid4())[:8]
        local_video_path = os.path.join(TEMP_DIR, f"input_{job_id}.mp4")
        
        if not download_from_url(video_url, local_video_path):
            return jsonify({'error': 'Failed to download video from URL'}), 500
        
        # Check for test mode
        test_duration = data.get('test_duration')  # 30 seconds for testing
        
        # Separate audio
        vocals_path, accompaniment_path = python_spleeter_separation(local_video_path, test_duration)
        
        if not vocals_path or not accompaniment_path:
            return jsonify({'error': 'Audio separation failed'}), 500
        
        # Transcribe vocals
        transcript = transcribe_audio(vocals_path)
        
        if not transcript:
            return jsonify({'error': 'Transcription failed'}), 500
        
        # Create karaoke videos
        results = []
        
        for vocal_level in vocal_levels:
            output_filename = f"karaoke_{job_id}_{int(vocal_level*100)}vocal.mp4"
            video_path = create_karaoke_video(accompaniment_path, transcript, vocal_level, output_filename)
            
            if video_path:
                # Upload to storage
                gcs_url = upload_to_gcs(video_path, output_filename)
                
                if gcs_url:
                    results.append({
                        'vocal_level': int(vocal_level * 100),
                        'url': gcs_url,
                        'filename': output_filename
                    })
                    
                    os.remove(video_path)
        
        # Cleanup
        os.remove(local_video_path)
        if os.path.exists(vocals_path):
            os.remove(vocals_path)
        if os.path.exists(accompaniment_path):
            os.remove(accompaniment_path)
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'videos': results
        })
        
    except Exception as e:
        print(f"❌ Processing error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)