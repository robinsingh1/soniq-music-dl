#!/usr/bin/env python3
"""
Multi-Vocal Level Karaoke Creator with Docker Spleeter
Creates 4 karaoke videos with different vocal levels: 0%, 25%, 50%, 75%
Equal-sized English and Gurmukhi text
"""

import os
import tempfile
import subprocess
import openai

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-api-key-here")
TEMP_DIR = tempfile.gettempdir()
VIDEO_PATH = "/var/folders/j6/h6tdc4yx1470x8t912hlhfmw0000gn/T/test_video.mp4"
FFMPEG_PATH = '/opt/homebrew/bin/ffmpeg'
PROJECT_DIR = "/Users/rajvindersingh/Projects/karooke"
DOCKER_PATH = '/usr/local/bin/docker'

def docker_spleeter_separation():
    """Use Docker Spleeter for professional audio separation"""
    print("🐳 Docker Spleeter Audio Separation")
    print("Separating vocals and accompaniment using ML...")
    
    # Extract audio from video first
    audio_path = os.path.join(TEMP_DIR, "input_audio.wav")
    print("🎵 Extracting audio from video...")
    
    extract_cmd = [
        FFMPEG_PATH, '-i', VIDEO_PATH, '-ss', '0', '-t', '30',
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

def transcribe_vocals(vocal_path):
    """Transcribe the ML-separated vocal track"""
    if not vocal_path or not os.path.exists(vocal_path):
        return None
    
    print("🗣️ Transcribing vocals...")
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    
    with open(vocal_path, 'rb') as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json",
            timestamp_granularities=["word"]
        )
    
    print(f"✅ Transcription: {len(transcript.words)} words")
    return transcript

def create_equal_size_bilingual_subtitles(transcript):
    """Create bilingual subtitles with EQUAL-SIZED text for both languages"""
    if not transcript or not hasattr(transcript, 'words'):
        return None
    
    transliteration_map = {
        'ਜੀ': 'ji', 'ਆੰਨੇ': 'aane', 'ਅੰਨੇ': 'aane', 'ਚੁਨੀ': 'chuni', 'ਟੇ': 'te', 'ਲਗਾਏ': 'lagaye',
        'ਆ': 'aa', 'ਸਤਾਰੇ': 'sitare', 'ਸੋਨੇ': 'sone', 'ਰੰਗੇ': 'range', 'ਗੋਟੇ': 'gote',
        'ਲਗਦੀ': 'lagdi', 'ਬਚੀ': 'bachi', 'ਕਿਸੇ': 'kise', 'ਨਾਗਿਨ': 'nagin', 'ਕੇ': 'ke',
        'ਥੇ': 'the', 'ਫੁਲ': 'ful', 'ਸੇਮ': 'same', 'ਰੇ': 're', 'ਕਾਨੇ': 'kane',
        'ਸਾਨੁ': 'saanu', 'ਦਾਸ': 'dass', 'ਦੇ': 'de', 'ਲੋਕੇਸ਼ਨ': 'location',
        'ਹੇ': 'he', 'ਓ': 'o', 'ਬਾਗਦੀ': 'bagdi', 'ਤੇ': 'te', 'ਪਹਿ': 'pehi'
    }
    
    ass_path = os.path.join(TEMP_DIR, "equal_size_bilingual.ass")
    
    with open(ass_path, 'w', encoding='utf-8') as f:
        # EQUAL SIZE FONTS - Both languages at 32pt
        f.write("""[Script Info]
Title: Equal-Size Bilingual Karaoke
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Gurmukhi,Arial Unicode MS,32,&Hffffff,&Hffffff,&H000000,&H80000000,1,0,0,0,100,100,0,0,1,3,1,2,10,10,80,1
Style: English,Arial,32,&Hffffff,&Hffffff,&H000000,&H80000000,1,0,0,0,100,100,0,0,1,3,1,2,10,10,30,1

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
        
        print(f"📝 Creating {len(lines)} equal-sized bilingual lines")
        
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
                gurmukhi_line = ""
                english_line = ""
                
                for i, w in enumerate(line_words):
                    gurmukhi_word = w.word
                    english_word = transliteration_map.get(gurmukhi_word, gurmukhi_word.lower())
                    
                    if i == word_idx:
                        # Gold highlighting for current word
                        gurmukhi_line += "{\\c&H00ccff&\\3c&H0066cc&}" + gurmukhi_word + "{\\c&Hffffff&\\3c&H000000&}"
                        english_line += "{\\c&H00ccff&\\3c&H0066cc&}" + english_word + "{\\c&Hffffff&\\3c&H000000&}"
                    else:
                        gurmukhi_line += gurmukhi_word
                        english_line += english_word
                    
                    if i < len(line_words) - 1:
                        gurmukhi_line += " "
                        english_line += " "
                
                # Write both lines with equal font size
                f.write(f"Dialogue: 0,{start_time},{end_time},Gurmukhi,,0,0,0,,{gurmukhi_line}\\N\n")
                f.write(f"Dialogue: 1,{start_time},{end_time},English,,0,0,0,,{english_line}\\N\n")
    
    print(f"✅ Equal-size bilingual subtitles created")
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

def create_karaoke_video(subtitle_path, audio_path, vocal_level, output_filename):
    """Create karaoke video with specific vocal level"""
    print(f"🎬 Creating karaoke video ({int(vocal_level*100)}% vocals)...")
    
    output_path = os.path.join(PROJECT_DIR, output_filename)
    
    cmd = [
        FFMPEG_PATH,
        '-i', VIDEO_PATH,           # Original video
        '-i', audio_path,            # Mixed audio
        '-ss', '0', '-t', '30',
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

def main():
    print("🎵 MULTI-VOCAL LEVEL KARAOKE CREATOR 🎵")
    print("=" * 60)
    print("Creating 4 videos with different vocal levels:")
    print("  📹 0% vocals (pure instrumental)")
    print("  📹 25% vocals (guide track)")
    print("  📹 50% vocals (practice mode)")
    print("  📹 75% vocals (sing-along)")
    print("  📝 Equal-sized Gurmukhi & English text")
    print("")
    
    # Check Docker
    try:
        subprocess.run([DOCKER_PATH, '--version'], capture_output=True, check=True)
        print("✅ Docker is ready")
    except:
        print("❌ Docker not found")
        return False
    
    if not os.path.exists(VIDEO_PATH):
        print("❌ Video not found")
        return False
    
    # Step 1: Docker Spleeter separation
    print("\n🔄 Step 1: ML Audio Separation")
    vocals_path, accompaniment_path = docker_spleeter_separation()
    if not (vocals_path and accompaniment_path):
        print("❌ Audio separation failed")
        return False
    
    # Step 2: Transcribe vocals
    print("\n🔄 Step 2: Transcription")
    transcript = transcribe_vocals(vocals_path)
    if not transcript:
        print("❌ Transcription failed")
        return False
    
    # Step 3: Create equal-size bilingual subtitles
    print("\n🔄 Step 3: Equal-Size Bilingual Subtitles")
    subtitle_path = create_equal_size_bilingual_subtitles(transcript)
    if not subtitle_path:
        print("❌ Subtitle creation failed")
        return False
    
    # Step 4: Create videos with different vocal levels
    print("\n🔄 Step 4: Creating Multi-Vocal Videos")
    
    vocal_configs = [
        (0.0, "punjaban_karaoke_0_vocal.mp4", "Pure Instrumental"),
        (0.25, "punjaban_karaoke_25_vocal.mp4", "Guide Track"),
        (0.5, "punjaban_karaoke_50_vocal.mp4", "Practice Mode"),
        (0.75, "punjaban_karaoke_75_vocal.mp4", "Sing-Along")
    ]
    
    success_count = 0
    
    for vocal_level, filename, description in vocal_configs:
        print(f"\n📹 Creating {description} ({int(vocal_level*100)}% vocals)...")
        
        # Mix audio with specified vocal level
        mixed_audio_path = os.path.join(TEMP_DIR, f"mixed_{int(vocal_level*100)}.wav")
        if mix_audio_with_vocal_level(vocals_path, accompaniment_path, vocal_level, mixed_audio_path):
            # Create video
            if create_karaoke_video(subtitle_path, mixed_audio_path, vocal_level, filename):
                success_count += 1
            # Clean up mixed audio
            if os.path.exists(mixed_audio_path):
                os.remove(mixed_audio_path)
    
    # Cleanup
    for temp_file in [vocals_path, accompaniment_path, subtitle_path]:
        if temp_file and os.path.exists(temp_file):
            if os.path.isfile(temp_file):
                os.remove(temp_file)
            elif os.path.isdir(temp_file):
                import shutil
                shutil.rmtree(temp_file)
    
    # Summary
    print("\n" + "=" * 60)
    print("🎉 KARAOKE CREATION COMPLETE!")
    print(f"✅ Successfully created {success_count}/4 videos")
    print("\n📹 Videos created:")
    print("  1️⃣ punjaban_karaoke_0_vocal.mp4 - Pure Instrumental (0%)")
    print("  2️⃣ punjaban_karaoke_25_vocal.mp4 - Guide Track (25%)")
    print("  3️⃣ punjaban_karaoke_50_vocal.mp4 - Practice Mode (50%)")
    print("  4️⃣ punjaban_karaoke_75_vocal.mp4 - Sing-Along (75%)")
    print("\n🎨 Features:")
    print("  ✅ Equal-sized Gurmukhi & English text (32pt)")
    print("  ✅ Gold highlighting for current word")
    print("  ✅ ML-separated audio (Docker Spleeter)")
    print("  ✅ Professional quality encoding")
    
    return success_count == 4

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🚀 All videos ready for karaoke!")
    else:
        print("\n⚠️ Some videos may have failed - check output above")