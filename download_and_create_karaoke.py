#!/usr/bin/env python3
"""
YouTube Video Downloader & Karaoke Creator
Downloads videos and creates 0% and 25% vocal karaoke versions
"""

import os
import tempfile
import subprocess
import openai
import yt_dlp

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-api-key-here")
TEMP_DIR = tempfile.gettempdir()
FFMPEG_PATH = '/opt/homebrew/bin/ffmpeg'
PROJECT_DIR = "/Users/rajvindersingh/Projects/karooke"
DOCKER_PATH = '/usr/local/bin/docker'

def download_youtube_video(url):
    """Download YouTube video and return path"""
    print(f"📥 Downloading YouTube video...")
    print(f"🔗 URL: {url}")
    
    # Create safe filename from video ID
    video_id = url.split('watch?v=')[1].split('&')[0] if 'watch?v=' in url else 'video'
    output_path = os.path.join(TEMP_DIR, f"{video_id}.mp4")
    
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Get video info first
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            
            print(f"🎵 Title: {title}")
            print(f"⏱️ Duration: {duration//60}:{duration%60:02d}")
            
            # Download the video
            ydl.download([url])
        
        if os.path.exists(output_path):
            size = os.path.getsize(output_path) / (1024*1024)
            print(f"✅ Downloaded: {size:.1f}MB")
            return output_path, title
        else:
            print("❌ Download failed - file not found")
            return None, None
            
    except Exception as e:
        print(f"❌ Download error: {str(e)}")
        return None, None

def docker_spleeter_separation(video_path):
    """Use Docker Spleeter for professional audio separation"""
    print("🐳 Docker Spleeter Audio Separation")
    
    # Extract audio from video first
    audio_path = os.path.join(TEMP_DIR, "input_audio.wav")
    print("🎵 Extracting audio from video...")
    
    extract_cmd = [
        FFMPEG_PATH, '-i', video_path,
        '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2',
        audio_path, '-y'
    ]
    
    result = subprocess.run(extract_cmd, capture_output=True, text=True)
    if not os.path.exists(audio_path):
        print("❌ Audio extraction failed")
        return None, None
    
    # Create output directory
    output_dir = os.path.join(TEMP_DIR, "spleeter_output")
    os.makedirs(output_dir, exist_ok=True)
    
    # Docker Spleeter command
    print("🎤 Running Docker Spleeter ML separation...")
    docker_cmd = [
        DOCKER_PATH, 'run',
        '-v', f"{TEMP_DIR}:/tmp",
        '--rm',
        'researchdeezer/spleeter',
        'separate',
        '-i', '/tmp/input_audio.wav',
        '-p', 'spleeter:2stems-16kHz',
        '-o', '/tmp/spleeter_output'
    ]
    
    docker_result = subprocess.run(docker_cmd, capture_output=True, text=True)
    
    # Check results
    audio_name = os.path.splitext(os.path.basename(audio_path))[0]
    vocals_path = os.path.join(output_dir, audio_name, "vocals.wav")
    accompaniment_path = os.path.join(output_dir, audio_name, "accompaniment.wav")
    
    if os.path.exists(vocals_path) and os.path.exists(accompaniment_path):
        print("✅ ML separation successful!")
        print(f"  🎤 Vocals: {os.path.getsize(vocals_path) / (1024*1024):.2f}MB")
        print(f"  🎼 Accompaniment: {os.path.getsize(accompaniment_path) / (1024*1024):.2f}MB")
        os.remove(audio_path)
        return vocals_path, accompaniment_path
    else:
        print("❌ Docker Spleeter separation failed")
        return None, None

def split_audio_file(vocal_path, chunk_duration=300):
    """Split audio file into smaller chunks if needed (5 min chunks)"""
    file_size = os.path.getsize(vocal_path) / (1024 * 1024)  # Size in MB
    
    if file_size <= 20:  # If under 20MB, don't split
        return [vocal_path]
    
    print(f"🔧 File size {file_size:.1f}MB > 20MB, splitting into chunks...")
    
    chunks = []
    chunk_dir = os.path.dirname(vocal_path)
    base_name = os.path.splitext(os.path.basename(vocal_path))[0]
    
    # Get audio duration
    probe_cmd = [
        FFMPEG_PATH, '-i', vocal_path,
        '-f', 'null', '-', '-hide_banner', '-loglevel', 'error'
    ]
    result = subprocess.run(probe_cmd, capture_output=True, text=True)
    
    # Split into chunks
    chunk_index = 0
    start_time = 0
    
    while True:
        chunk_path = os.path.join(chunk_dir, f"{base_name}_chunk_{chunk_index}.wav")
        
        split_cmd = [
            FFMPEG_PATH, '-i', vocal_path,
            '-ss', str(start_time), '-t', str(chunk_duration),
            '-c:a', 'pcm_s16le', '-ar', '16000', '-ac', '1',
            chunk_path, '-y'
        ]
        
        result = subprocess.run(split_cmd, capture_output=True, text=True)
        
        if os.path.exists(chunk_path) and os.path.getsize(chunk_path) > 1000:  # If chunk has content
            chunks.append(chunk_path)
            print(f"  📄 Created chunk {chunk_index}: {os.path.getsize(chunk_path) / (1024*1024):.1f}MB")
            chunk_index += 1
            start_time += chunk_duration
        else:
            if os.path.exists(chunk_path):
                os.remove(chunk_path)
            break
    
    print(f"✅ Split into {len(chunks)} chunks")
    return chunks

def transcribe_vocals(vocal_path):
    """Transcribe the ML-separated vocal track, splitting if needed"""
    if not vocal_path or not os.path.exists(vocal_path):
        return None
    
    print("🗣️ Transcribing vocals...")
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    
    # Split file if too large
    chunks = split_audio_file(vocal_path)
    all_words = []
    time_offset = 0
    
    for i, chunk_path in enumerate(chunks):
        print(f"  📝 Transcribing chunk {i+1}/{len(chunks)}...")
        
        try:
            with open(chunk_path, 'rb') as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                    timestamp_granularities=["word"]
                )
            
            # Adjust timestamps for chunk offset
            for word in transcript.words:
                word.start += time_offset
                word.end += time_offset
                all_words.append(word)
            
            # Update offset for next chunk (5 minutes)
            time_offset += 300
            
        except Exception as e:
            print(f"  ⚠️ Chunk {i+1} transcription failed: {e}")
            continue
        
        # Clean up chunk file if it's not the original
        if chunk_path != vocal_path:
            os.remove(chunk_path)
    
    if not all_words:
        print("❌ No words transcribed")
        return None
    
    # Create a transcript-like object
    class TranscriptResult:
        def __init__(self, words):
            self.words = words
            self.text = " ".join([w.word for w in words])
    
    result = TranscriptResult(all_words)
    print(f"✅ Transcription: {len(result.words)} words from {len(chunks)} chunks")
    return result

def create_bilingual_subtitles(transcript, video_title):
    """Create bilingual subtitles with original sizing"""
    if not transcript or not hasattr(transcript, 'words'):
        return None
    
    # Basic transliteration - can be enhanced for specific languages
    transliteration_map = {
        # Add language-specific mappings as needed
        'ਜੀ': 'ji', 'ਆੰਨੇ': 'aane', 'ਚੁਨੀ': 'chuni', 'ਟੇ': 'te', 'ਲਗਾਏ': 'lagaye',
        'ਆ': 'aa', 'ਸਤਾਰੇ': 'sitare', 'ਸੋਨੇ': 'sone', 'ਰੰਗੇ': 'range', 'ਗੋਟੇ': 'gote'
    }
    
    ass_path = os.path.join(TEMP_DIR, f"{video_title}_bilingual.ass")
    
    with open(ass_path, 'w', encoding='utf-8') as f:
        f.write("""[Script Info]
Title: Bilingual Karaoke
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Original,Arial Unicode MS,28,&Hffffff,&Hffffff,&H000000,&H80000000,1,0,0,0,100,100,0,0,1,3,1,2,10,10,70,1
Style: Translation,Arial,22,&Hdddddd,&Hdddddd,&H000000,&H80000000,0,0,0,0,100,100,0,0,1,2,1,2,10,10,25,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""")
        
        # Group into lines
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
        
        print(f"📝 Creating {len(lines)} bilingual subtitle lines")
        
        def format_time(seconds):
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = seconds % 60
            return f"{h}:{m:02d}:{s:05.2f}"
        
        # Create synchronized subtitles
        for line_words in lines:
            for word_idx, word in enumerate(line_words):
                start_time = format_time(word.start)
                end_time = format_time(word.end)
                
                # Build highlighted lines
                original_line = ""
                translation_line = ""
                
                for i, w in enumerate(line_words):
                    original_word = w.word
                    translated_word = transliteration_map.get(original_word, original_word.lower())
                    
                    if i == word_idx:
                        # Orange highlighting for current word
                        original_line += "{\\c&H0088ff&}" + original_word + "{\\c&Hffffff&}"
                        translation_line += "{\\c&H0088ff&}" + translated_word + "{\\c&Hdddddd&}"
                    else:
                        original_line += original_word
                        translation_line += translated_word
                    
                    if i < len(line_words) - 1:
                        original_line += " "
                        translation_line += " "
                
                # Write both lines
                f.write(f"Dialogue: 0,{start_time},{end_time},Original,,0,0,0,,{original_line}\\N\n")
                f.write(f"Dialogue: 1,{start_time},{end_time},Translation,,0,0,0,,{translation_line}\\N\n")
    
    print(f"✅ Bilingual subtitles created")
    return ass_path

def mix_audio_with_vocal_level(vocals_path, accompaniment_path, vocal_level, output_path):
    """Mix vocals and accompaniment with specified vocal level (0-1.0)"""
    print(f"🎚️ Mixing audio with {int(vocal_level*100)}% vocal volume...")
    
    if vocal_level == 0:
        # Pure instrumental - just copy accompaniment
        cmd = [
            FFMPEG_PATH,
            '-i', accompaniment_path,
            '-c:a', 'pcm_s16le',
            output_path, '-y'
        ]
    else:
        # Mix vocals and accompaniment with specified level
        cmd = [
            FFMPEG_PATH,
            '-i', accompaniment_path,
            '-i', vocals_path,
            '-filter_complex',
            f'[1:a]volume={vocal_level}[v];[0:a][v]amix=inputs=2:duration=longest',
            '-c:a', 'pcm_s16le',
            output_path, '-y'
        ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return os.path.exists(output_path)

def create_karaoke_video(video_path, subtitle_path, audio_path, vocal_level, output_filename):
    """Create karaoke video with specific vocal level"""
    print(f"🎬 Creating karaoke video ({int(vocal_level*100)}% vocals)...")
    
    output_path = os.path.join(PROJECT_DIR, output_filename)
    
    cmd = [
        FFMPEG_PATH,
        '-i', video_path,           # Original video
        '-i', audio_path,            # Mixed audio
        '-vf', f"ass={subtitle_path}",
        '-map', '0:v:0',            # Video
        '-map', '1:a:0',            # Mixed audio
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-b:a', '256k',
        '-preset', 'fast',
        '-crf', '18',
        '-y',
        output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0 and os.path.exists(output_path):
        size = os.path.getsize(output_path) / (1024*1024)
        print(f"✅ Created: {output_filename} ({size:.1f}MB)")
        return True
    else:
        print(f"❌ Failed to create {output_filename}")
        return False

def process_youtube_video(url, video_name):
    """Complete pipeline: download, separate, transcribe, create karaoke"""
    print(f"\n🎵 PROCESSING: {video_name}")
    print("=" * 60)
    
    # Step 1: Download video
    video_path, title = download_youtube_video(url)
    if not video_path:
        return False
    
    # Step 2: Docker Spleeter separation
    vocals_path, accompaniment_path = docker_spleeter_separation(video_path)
    if not (vocals_path and accompaniment_path):
        print("❌ Audio separation failed")
        return False
    
    # Step 3: Transcribe vocals
    transcript = transcribe_vocals(vocals_path)
    if not transcript:
        print("❌ Transcription failed")
        return False
    
    # Step 4: Create bilingual subtitles
    subtitle_path = create_bilingual_subtitles(transcript, video_name)
    if not subtitle_path:
        print("❌ Subtitle creation failed")
        return False
    
    # Step 5: Create karaoke videos with 0% and 25% vocals
    vocal_configs = [
        (0.0, f"{video_name}_karaoke_0_vocal.mp4", "Pure Instrumental"),
        (0.25, f"{video_name}_karaoke_25_vocal.mp4", "Guide Track")
    ]
    
    success_count = 0
    
    for vocal_level, filename, description in vocal_configs:
        print(f"\n📹 Creating {description} ({int(vocal_level*100)}% vocals)...")
        
        # Mix audio with specified vocal level
        mixed_audio_path = os.path.join(TEMP_DIR, f"{video_name}_mixed_{int(vocal_level*100)}.wav")
        if mix_audio_with_vocal_level(vocals_path, accompaniment_path, vocal_level, mixed_audio_path):
            # Create video
            if create_karaoke_video(video_path, subtitle_path, mixed_audio_path, vocal_level, filename):
                success_count += 1
            # Clean up mixed audio
            if os.path.exists(mixed_audio_path):
                os.remove(mixed_audio_path)
    
    # Cleanup
    for temp_file in [video_path, vocals_path, accompaniment_path, subtitle_path]:
        if temp_file and os.path.exists(temp_file):
            if os.path.isfile(temp_file):
                os.remove(temp_file)
            elif os.path.isdir(temp_file):
                import shutil
                shutil.rmtree(temp_file)
    
    # Clean up spleeter output directory
    spleeter_dir = os.path.join(TEMP_DIR, "spleeter_output")
    if os.path.exists(spleeter_dir):
        import shutil
        shutil.rmtree(spleeter_dir)
    
    print(f"\n✅ Created {success_count}/2 karaoke videos for {video_name}")
    return success_count == 2

def main():
    print("🎵 YOUTUBE KARAOKE CREATOR 🎵")
    print("=" * 60)
    print("Processing 2 YouTube videos:")
    print("  📹 Creating 0% and 25% vocal versions")
    print("  📝 Bilingual subtitles with highlighting")
    print("  🤖 Docker Spleeter ML separation")
    print("")
    
    # Check Docker
    try:
        subprocess.run([DOCKER_PATH, '--version'], capture_output=True, check=True)
        print("✅ Docker is ready")
    except:
        print("❌ Docker not found")
        return False
    
    # Video URLs
    videos = [
        ("https://www.youtube.com/watch?v=Fbv6-50S1lc", "video1"),
        ("https://www.youtube.com/watch?v=JgDNFQ2RaLQ", "video2")
    ]
    
    total_success = 0
    
    for url, video_name in videos:
        if process_youtube_video(url, video_name):
            total_success += 1
    
    print("\n" + "=" * 60)
    print("🎉 YOUTUBE KARAOKE CREATION COMPLETE!")
    print(f"✅ Successfully processed {total_success}/2 videos")
    print("\n📹 Videos created:")
    print("  1️⃣ video1_karaoke_0_vocal.mp4 - Pure Instrumental")
    print("  2️⃣ video1_karaoke_25_vocal.mp4 - Guide Track")
    print("  3️⃣ video2_karaoke_0_vocal.mp4 - Pure Instrumental")
    print("  4️⃣ video2_karaoke_25_vocal.mp4 - Guide Track")
    
    return total_success == 2

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🚀 All YouTube karaoke videos ready!")
    else:
        print("\n⚠️ Some videos may have failed - check output above")