#!/usr/bin/env python3
"""
Process Billie Eilish video with Docker Spleeter and create karaoke
"""
import os
import tempfile
import subprocess
import openai

# Configuration
OPENAI_API_KEY = "sk-proj-c1j5Eh0vqyFFKxjMRWdKOtgWA5hNEiBPe-BkiK_YhVnlTNuC3z8KtQ2HI8jBOZp5lzPZ7wWJ_T3BlbkFJvMPE0vv4sMfr_qJLPzYEQjjHOEhOE8zVIzwV6EKiCa3jdB9I4PbfOTQzYA7dLOXwmh7zcQ5lYA"
VIDEO_PATH = "/Users/rajvindersingh/Projects/karooke/billie_birds_direct.mp4"
TEMP_DIR = tempfile.gettempdir()
FFMPEG_PATH = '/opt/homebrew/bin/ffmpeg'
PROJECT_DIR = "/Users/rajvindersingh/Projects/karooke"
DOCKER_PATH = '/usr/local/bin/docker'

def docker_spleeter_separation():
    """Use Docker Spleeter for audio separation"""
    print("🐳 Docker Spleeter Audio Separation")
    print("Separating vocals and accompaniment...")
    
    # Extract audio from video first
    audio_path = os.path.join(TEMP_DIR, "billie_audio.wav")
    print("🎵 Extracting audio from video...")
    
    extract_cmd = [
        FFMPEG_PATH, '-i', VIDEO_PATH,
        '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2',
        audio_path, '-y'
    ]
    
    result = subprocess.run(extract_cmd, capture_output=True, text=True)
    if not os.path.exists(audio_path):
        print("❌ Audio extraction failed")
        print(result.stderr)
        return None, None
    
    print(f"✅ Audio extracted: {os.path.getsize(audio_path) / (1024*1024):.1f}MB")
    
    # Create output directory
    output_dir = os.path.join(TEMP_DIR, "billie_spleeter_output")
    os.makedirs(output_dir, exist_ok=True)
    
    # Docker Spleeter command
    print("🎤 Running Docker Spleeter ML separation...")
    docker_cmd = [
        DOCKER_PATH, 'run',
        '-v', f"{TEMP_DIR}:/tmp",
        '--rm',
        'researchdeezer/spleeter',
        'separate',
        '-i', '/tmp/billie_audio.wav',
        '-p', 'spleeter:2stems-16kHz',
        '-o', '/tmp/billie_spleeter_output'
    ]
    
    print(f"Docker command: {' '.join(docker_cmd)}")
    docker_result = subprocess.run(docker_cmd, capture_output=True, text=True)
    
    # Check results
    audio_name = os.path.splitext(os.path.basename(audio_path))[0]
    vocals_path = os.path.join(output_dir, audio_name, "vocals.wav")
    accompaniment_path = os.path.join(output_dir, audio_name, "accompaniment.wav")
    
    print(f"Looking for vocals at: {vocals_path}")
    print(f"Looking for accompaniment at: {accompaniment_path}")
    
    if os.path.exists(vocals_path) and os.path.exists(accompaniment_path):
        vocals_size = os.path.getsize(vocals_path) / (1024*1024)
        accompaniment_size = os.path.getsize(accompaniment_path) / (1024*1024)
        print("✅ ML separation successful!")
        print(f"  🎤 Vocals: {vocals_size:.1f}MB")
        print(f"  🎼 Accompaniment: {accompaniment_size:.1f}MB")
        
        # Clean up original audio
        os.remove(audio_path)
        return vocals_path, accompaniment_path
    else:
        print("❌ Docker Spleeter separation failed")
        print(f"Docker stdout: {docker_result.stdout}")
        print(f"Docker stderr: {docker_result.stderr}")
        return None, None

def transcribe_audio_chunked(audio_path):
    """Transcribe audio using OpenAI Whisper with chunking for large files"""
    print("🎙️ Transcribing with OpenAI Whisper...")
    
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    
    # Check file size
    file_size = os.path.getsize(audio_path)
    print(f"Audio file size: {file_size / (1024*1024):.1f}MB")
    
    # If file is large (>20MB), chunk it
    if file_size > 20 * 1024 * 1024:
        return transcribe_chunked(client, audio_path)
    else:
        return transcribe_direct(client, audio_path)

def transcribe_direct(client, audio_path):
    """Direct transcription for smaller files"""
    try:
        with open(audio_path, 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(
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

def transcribe_chunked(client, audio_path):
    """Transcribe audio in chunks for large files"""
    print("📦 Large file - chunking for transcription...")
    
    chunk_dir = os.path.join(TEMP_DIR, "audio_chunks")
    os.makedirs(chunk_dir, exist_ok=True)
    
    # Split audio into 10-minute chunks
    chunk_duration = 600  # 10 minutes
    chunk_files = []
    
    # Get audio duration first
    probe_cmd = [FFMPEG_PATH, '-i', audio_path, '-f', 'null', '-']
    probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
    
    # Extract chunks
    chunk_index = 0
    start_time = 0
    
    while start_time < 240:  # Process up to 4 minutes for testing
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
            print(f"📦 Created chunk {chunk_index}: {start_time}s")
            chunk_index += 1
            start_time += chunk_duration
        else:
            break
    
    # Transcribe each chunk
    all_words = []
    
    for start_offset, chunk_path in chunk_files:
        try:
            with open(chunk_path, 'rb') as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                    timestamp_granularities=["word"]
                )
            
            # Adjust timestamps based on chunk offset
            for word in transcript.words:
                word.start += start_offset
                word.end += start_offset
                all_words.append(word)
            
            print(f"✅ Transcribed chunk: {len(transcript.words)} words")
            
        except Exception as e:
            print(f"❌ Chunk transcription failed: {e}")
        
        # Clean up chunk file
        os.remove(chunk_path)
    
    # Create combined transcript object
    class CombinedTranscript:
        def __init__(self, words):
            self.words = words
            self.text = " ".join([w.word for w in words])
    
    print(f"✅ Combined transcription: {len(all_words)} words")
    return CombinedTranscript(all_words)

def create_basic_karaoke_video(accompaniment_path, transcript, output_path):
    """Create a basic karaoke video with lyrics"""
    print("🎬 Creating karaoke video...")
    
    if not transcript or not transcript.words:
        print("❌ No transcript available")
        return False
    
    # Create ASS subtitle file
    ass_path = os.path.join(PROJECT_DIR, "billie_subtitles.ass")
    
    # ASS file header
    ass_content = """[Script Info]
Title: Billie Eilish - BIRDS OF A FEATHER Karaoke
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,24,&Hffffff,&Hffffff,&H000000,&H80000000,1,0,0,0,100,100,0,0,1,3,0,2,10,10,30,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    # Group words into lines (roughly every 6-8 words)
    lines = []
    current_line = []
    
    for i, word in enumerate(transcript.words):
        current_line.append(word)
        
        # End line on punctuation or after 8 words
        if len(current_line) >= 8 or (word.word.rstrip() and word.word.rstrip()[-1] in '.!?'):
            if current_line:
                lines.append(current_line)
                current_line = []
    
    # Add remaining words as final line
    if current_line:
        lines.append(current_line)
    
    # Create karaoke subtitles
    for line_words in lines:
        if not line_words:
            continue
        
        line_start = line_words[0].start
        line_end = line_words[-1].end
        
        # Convert to ASS time format (centiseconds)
        start_time = f"{int(line_start//3600):01d}:{int((line_start%3600)//60):02d}:{int(line_start%60):02d}.{int((line_start%1)*100):02d}"
        end_time = f"{int(line_end//3600):01d}:{int((line_end%3600)//60):02d}:{int(line_end%60):02d}.{int((line_end%1)*100):02d}"
        
        # Build karaoke effect
        text_parts = []
        current_time = line_start
        
        for word in line_words:
            word_duration = max(0.1, word.end - current_time)
            highlight_duration = int(word_duration * 100)  # Convert to centiseconds
            
            clean_word = word.word.strip()
            text_parts.append(f"{{\\k{highlight_duration}}}{clean_word}")
            current_time = word.end
        
        karaoke_text = "".join(text_parts)
        ass_content += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{karaoke_text}\\N\n"
    
    # Write ASS file
    with open(ass_path, 'w', encoding='utf-8') as f:
        f.write(ass_content)
    
    print(f"✅ Created subtitle file: {ass_path}")
    
    # Create video with subtitles
    ffmpeg_cmd = [
        FFMPEG_PATH,
        '-i', accompaniment_path,  # Audio only (instrumental)
        '-vf', f"color=black:size=1280x720:duration={transcript.words[-1].end if transcript.words else 30},subtitles={ass_path}:force_style='FontSize=32,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=3'",
        '-c:a', 'aac',
        '-c:v', 'libx264',
        '-t', str(min(240, transcript.words[-1].end if transcript.words else 30)),  # Limit to 4 minutes for testing
        output_path, '-y'
    ]
    
    print("🎬 Rendering karaoke video...")
    print(f"Command: {' '.join(ffmpeg_cmd)}")
    
    result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
    
    if os.path.exists(output_path):
        size = os.path.getsize(output_path) / (1024*1024)
        print(f"✅ Karaoke video created: {size:.1f}MB")
        return True
    else:
        print("❌ Video creation failed")
        print(f"FFmpeg error: {result.stderr}")
        return False

def main():
    print("🎵 BILLIE EILISH KARAOKE CREATOR 🎵")
    print("=" * 50)
    print(f"Video: {VIDEO_PATH}")
    print("")
    
    # Step 1: Separate audio using Docker Spleeter
    vocals_path, accompaniment_path = docker_spleeter_separation()
    
    if not vocals_path or not accompaniment_path:
        print("❌ Audio separation failed")
        return False
    
    # Step 2: Transcribe vocals
    transcript = transcribe_audio_chunked(vocals_path)
    
    if not transcript:
        print("❌ Transcription failed")
        return False
    
    # Step 3: Create karaoke video
    output_path = os.path.join(PROJECT_DIR, "billie_birds_karaoke.mp4")
    success = create_basic_karaoke_video(accompaniment_path, transcript, output_path)
    
    if success:
        print(f"\n🎉 Karaoke created successfully!")
        print(f"📁 Output: {output_path}")
        return True
    else:
        print("\n❌ Karaoke creation failed")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🚀 Ready to sing along!")