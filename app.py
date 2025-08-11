#!/usr/bin/env python3
"""
Karaoke Service - Cloud Run API
Processes YouTube videos and creates karaoke videos with different vocal levels
"""

import os
import tempfile
import subprocess
import logging
from flask import Flask, request, jsonify, send_file
import openai
import yt_dlp
from google.cloud import storage
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME", "soniq-karaoke-videos")
TEMP_DIR = tempfile.gettempdir()

# Use researchdeezer/spleeter Docker image for separation
def docker_spleeter_separation(video_path, job_id):
    """Use Docker Spleeter for audio separation"""
    logger.info(f"Starting Docker Spleeter separation for job {job_id}")
    
    # Extract audio from video
    audio_path = os.path.join(TEMP_DIR, f"{job_id}_audio.wav")
    extract_cmd = [
        'ffmpeg', '-i', video_path,
        '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2',
        audio_path, '-y'
    ]
    
    result = subprocess.run(extract_cmd, capture_output=True, text=True)
    if not os.path.exists(audio_path):
        logger.error("Audio extraction failed")
        return None, None
    
    # Create output directory
    output_dir = os.path.join(TEMP_DIR, f"spleeter_output_{job_id}")
    os.makedirs(output_dir, exist_ok=True)
    
    # Docker Spleeter command
    docker_cmd = [
        'docker', 'run',
        '-v', f"{TEMP_DIR}:/tmp",
        '--rm',
        'researchdeezer/spleeter',
        'separate',
        '-i', f'/tmp/{job_id}_audio.wav',
        '-p', 'spleeter:2stems-16kHz',
        '-o', f'/tmp/spleeter_output_{job_id}'
    ]
    
    docker_result = subprocess.run(docker_cmd, capture_output=True, text=True)
    
    # Check results
    audio_name = os.path.splitext(os.path.basename(audio_path))[0]
    vocals_path = os.path.join(output_dir, audio_name, "vocals.wav")
    accompaniment_path = os.path.join(output_dir, audio_name, "accompaniment.wav")
    
    if os.path.exists(vocals_path) and os.path.exists(accompaniment_path):
        logger.info("Spleeter separation successful")
        os.remove(audio_path)  # Clean up
        return vocals_path, accompaniment_path
    else:
        logger.error("Spleeter separation failed")
        return None, None

def transcribe_vocals(vocal_path):
    """Transcribe vocals using OpenAI Whisper"""
    if not vocal_path or not os.path.exists(vocal_path):
        return None
    
    logger.info("Starting transcription...")
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    
    with open(vocal_path, 'rb') as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json",
            timestamp_granularities=["word"]
        )
    
    logger.info(f"Transcription complete: {len(transcript.words)} words")
    return transcript

def create_subtitles(transcript, job_id):
    """Create ASS subtitle file"""
    if not transcript:
        return None
    
    ass_path = os.path.join(TEMP_DIR, f"{job_id}_subtitles.ass")
    
    with open(ass_path, 'w', encoding='utf-8') as f:
        f.write("""[Script Info]
Title: Cloud Karaoke
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,28,&Hffffff,&Hffffff,&H000000,&H80000000,1,0,0,0,100,100,0,0,1,3,1,2,10,10,50,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""")
        
        # Group words into lines
        lines = []
        current_line = []
        line_start = transcript.words[0].start if transcript.words else 0
        
        for word in transcript.words:
            if current_line and (word.start - line_start > 3.0):
                lines.append(current_line)
                current_line = [word]
                line_start = word.start
            else:
                current_line.append(word)
        
        if current_line:
            lines.append(current_line)
        
        def format_time(seconds):
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = seconds % 60
            return f"{h}:{m:02d}:{s:05.2f}"
        
        # Create subtitles with highlighting
        for line_words in lines:
            for word_idx, word in enumerate(line_words):
                start_time = format_time(word.start)
                end_time = format_time(word.end)
                
                line_text = ""
                for i, w in enumerate(line_words):
                    if i == word_idx:
                        line_text += "{\\c&H00ccff&}" + w.word + "{\\c&Hffffff&}"
                    else:
                        line_text += w.word
                    if i < len(line_words) - 1:
                        line_text += " "
                
                f.write(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{line_text}\\N\n")
    
    return ass_path

def mix_audio(vocals_path, accompaniment_path, vocal_level, job_id):
    """Mix vocals and accompaniment at specified level"""
    output_path = os.path.join(TEMP_DIR, f"{job_id}_mixed_{int(vocal_level*100)}.wav")
    
    if vocal_level == 0:
        # Pure instrumental
        cmd = ['ffmpeg', '-i', accompaniment_path, '-c:a', 'pcm_s16le', output_path, '-y']
    else:
        # Mix with vocals
        cmd = [
            'ffmpeg',
            '-i', accompaniment_path, '-i', vocals_path,
            '-filter_complex', f'[1:a]volume={vocal_level}[v];[0:a][v]amix=inputs=2:duration=longest',
            '-c:a', 'pcm_s16le', output_path, '-y'
        ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return output_path if os.path.exists(output_path) else None

def create_karaoke_video(video_path, subtitle_path, audio_path, vocal_level, job_id):
    """Create final karaoke video"""
    output_path = os.path.join(TEMP_DIR, f"{job_id}_karaoke_{int(vocal_level*100)}_vocal.mp4")
    
    cmd = [
        'ffmpeg',
        '-i', video_path, '-i', audio_path,
        '-vf', f"ass={subtitle_path}",
        '-map', '0:v:0', '-map', '1:a:0',
        '-c:v', 'libx264', '-c:a', 'aac',
        '-b:a', '256k', '-preset', 'fast', '-crf', '20',
        '-y', output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return output_path if os.path.exists(output_path) else None

def upload_to_gcs(file_path, filename):
    """Upload file to Google Cloud Storage"""
    try:
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_filename(file_path)
        
        # Make it publicly readable
        blob.make_public()
        return blob.public_url
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return None

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"})

@app.route('/process', methods=['POST'])
def process_video():
    """Main endpoint to process YouTube video"""
    try:
        data = request.get_json()
        youtube_url = data.get('url')
        vocal_levels = data.get('vocal_levels', [0.0, 0.25])  # Default: 0% and 25%
        
        if not youtube_url:
            return jsonify({"error": "URL is required"}), 400
        
        job_id = str(uuid.uuid4())
        logger.info(f"Starting job {job_id} for URL: {youtube_url}")
        
        # Step 1: Download video
        video_path = os.path.join(TEMP_DIR, f"{job_id}_video.mp4")
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': video_path,
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            title = info.get('title', 'Unknown')
            ydl.download([youtube_url])
        
        if not os.path.exists(video_path):
            return jsonify({"error": "Video download failed"}), 500
        
        logger.info(f"Downloaded: {title}")
        
        # Step 2: Spleeter separation
        vocals_path, accompaniment_path = docker_spleeter_separation(video_path, job_id)
        if not (vocals_path and accompaniment_path):
            return jsonify({"error": "Audio separation failed"}), 500
        
        # Step 3: Transcription
        transcript = transcribe_vocals(vocals_path)
        if not transcript:
            return jsonify({"error": "Transcription failed"}), 500
        
        # Step 4: Create subtitles
        subtitle_path = create_subtitles(transcript, job_id)
        if not subtitle_path:
            return jsonify({"error": "Subtitle creation failed"}), 500
        
        # Step 5: Create karaoke videos
        results = []
        for vocal_level in vocal_levels:
            # Mix audio
            mixed_audio = mix_audio(vocals_path, accompaniment_path, vocal_level, job_id)
            if not mixed_audio:
                continue
            
            # Create video
            video_output = create_karaoke_video(video_path, subtitle_path, mixed_audio, vocal_level, job_id)
            if not video_output:
                continue
            
            # Upload to GCS
            filename = f"{job_id}_karaoke_{int(vocal_level*100)}_vocal.mp4"
            public_url = upload_to_gcs(video_output, filename)
            
            if public_url:
                results.append({
                    "vocal_level": int(vocal_level * 100),
                    "url": public_url,
                    "filename": filename
                })
            
            # Cleanup
            os.remove(mixed_audio)
            os.remove(video_output)
        
        # Cleanup remaining files
        cleanup_files = [video_path, vocals_path, accompaniment_path, subtitle_path]
        for file_path in cleanup_files:
            if file_path and os.path.exists(file_path):
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    import shutil
                    shutil.rmtree(file_path)
        
        return jsonify({
            "job_id": job_id,
            "title": title,
            "videos": results
        })
        
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)