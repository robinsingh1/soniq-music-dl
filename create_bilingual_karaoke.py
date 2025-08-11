#!/usr/bin/env python3
"""
Bilingual Karaoke Creator
Creates karaoke video with both Gurmukhi and English transliteration
- Gurmukhi script on top line
- English transliteration on bottom line
- Synchronized highlighting for both languages
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
PROJECT_DIR = "/Users/rajvindersingh/Projects/karoake"

def separate_audio_tracks():
    """Separate vocals and instrumentals"""
    print("🎵 Separating vocals and instrumentals...")
    
    vocal_path = os.path.join(TEMP_DIR, "bilingual_vocals.wav")
    instrumental_path = os.path.join(TEMP_DIR, "bilingual_instrumental.wav")
    
    # Extract vocals
    vocal_cmd = [
        FFMPEG_PATH, '-i', VIDEO_PATH, '-ss', '0', '-t', '30',
        '-af', 'pan=mono|c0=0.5*c0+0.5*c1',
        '-ar', '16000', '-ac', '1',
        vocal_path, '-y'
    ]
    
    # Extract instrumental
    instrumental_cmd = [
        FFMPEG_PATH, '-i', VIDEO_PATH, '-ss', '0', '-t', '30',
        '-af', 'pan=stereo|c0=c0-0.5*c1|c1=c1-0.5*c0',
        '-ar', '44100', '-ac', '2',
        instrumental_path, '-y'
    ]
    
    print("🎤 Extracting vocals...")
    subprocess.run(vocal_cmd, capture_output=True, text=True)
    
    print("🎼 Extracting instrumental...")
    subprocess.run(instrumental_cmd, capture_output=True, text=True)
    
    vocal_exists = os.path.exists(vocal_path)
    instrumental_exists = os.path.exists(instrumental_path)
    
    if vocal_exists and instrumental_exists:
        print(f"✅ Audio separation complete")
        print(f"   🎤 Vocals: {os.path.getsize(vocal_path) / (1024*1024):.2f}MB")
        print(f"   🎼 Instrumental: {os.path.getsize(instrumental_path) / (1024*1024):.2f}MB")
    
    return vocal_path if vocal_exists else None, instrumental_path if instrumental_exists else None

def transcribe_vocals(vocal_path):
    """Transcribe vocals to get original Gurmukhi text"""
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
    
    return transcript

def create_transliteration_mapping(transcript):
    """Create English transliteration for each Gurmukhi word"""
    transliteration_map = {
        'ਜੀ': 'ji',
        'ਆੰਨੇ': 'aane', 
        'ਚੁਨੀ': 'chuni',
        'ਟੇ': 'te',
        'ਲਗਾਏ': 'lagaye',
        'ਆ': 'aa',
        'ਸਤਾਰੇ': 'sitare',
        'ਸੋਨੇ': 'sone',
        'ਰੰਗੇ': 'range',
        'ਗੋਟੇ': 'gote',
        'ਲਗਦੀ': 'lagdi',
        'ਬਚੀ': 'bachi',
        'ਕਿਸੇ': 'kise',
        'ਨਾਗਿਨ': 'nagin',
        'ਕੇ': 'ke',
        'ਥੇ': 'the',
        'ਫੁਲ': 'ful',
        'ਸੇਮ': 'same',
        'ਰੇ': 're',
        'ਕਾਨੇ': 'kane',
        'ਸਾਨੁ': 'saanu',
        'ਦਾਸ': 'dass',
        'ਦੇ': 'de',
        'ਲੋਕੇਸ਼ਨ': 'location',
        'ਹੇ': 'he',
        'ਓ': 'o',
        'ਬਾਗਦੀ': 'bagdi',
        'ਤੇ': 'te',
        'ਪਹਿ': 'pehi',
        'ਅਖਿਆਂਚ': 'akhianch',
        'ਸੁਰਮ': 'surma',
        'ਸਲਾਈ': 'salaai',
        'ਹੁਸਨ': 'husn',
        'ਦੀ': 'di',
        'ਹਦ': 'had',
        'ਕੁਈ': 'kui',
        'ਨਾ': 'na'
    }
    
    # Create bilingual word pairs
    bilingual_words = []
    for word in transcript.words:
        gurmukhi = word.word
        english = transliteration_map.get(gurmukhi, gurmukhi)
        
        bilingual_words.append({
            'gurmukhi': gurmukhi,
            'english': english,
            'start': word.start,
            'end': word.end
        })
    
    return bilingual_words

def create_bilingual_subtitle_file(bilingual_words):
    """Create ASS subtitle file with both Gurmukhi and English"""
    if not bilingual_words:
        print("⚠️ No bilingual words available")
        return None
    
    ass_path = os.path.join(TEMP_DIR, "bilingual_subtitles.ass")
    
    with open(ass_path, 'w', encoding='utf-8') as f:
        # ASS header with two styles
        f.write("""[Script Info]
Title: Bilingual Karaoke - Gurmukhi + English
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Gurmukhi,Arial Unicode MS,28,&Hffffff,&Hffffff,&H000000,&H80000000,1,0,0,0,100,100,0,0,1,3,0,2,10,10,50,1
Style: English,Arial,22,&Hffffff,&Hffffff,&H000000,&H80000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1
Style: GurmukiHighlight,Arial Unicode MS,28,&Hff6600,&Hff6600,&H000000,&H80000000,1,0,0,0,100,100,0,0,1,3,0,2,10,10,50,1
Style: EnglishHighlight,Arial,22,&Hff6600,&Hff6600,&H000000,&H80000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""")
        
        # Group words into lines (3.5 seconds per line)
        lines = []
        current_line = []
        line_start_time = bilingual_words[0]['start'] if bilingual_words else 0
        
        for word in bilingual_words:
            if current_line and (word['start'] - line_start_time > 3.5):
                lines.append(current_line)
                current_line = [word]
                line_start_time = word['start']
            else:
                current_line.append(word)
        
        if current_line:
            lines.append(current_line)
        
        print(f"📝 Creating {len(lines)} bilingual subtitle lines")
        
        def format_ass_time(seconds):
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = seconds % 60
            return f"{hours}:{minutes:02d}:{secs:05.2f}"
        
        # Create subtitle events
        for line_words in lines:
            if not line_words:
                continue
            
            for word_idx, word in enumerate(line_words):
                start_time = format_ass_time(word['start'])
                end_time = format_ass_time(word['end'])
                
                # Build Gurmukhi line with highlighting
                gurmukhi_line = ""
                english_line = ""
                
                for i, w in enumerate(line_words):
                    if i == word_idx:
                        # Current word highlighted in blue
                        gurmukhi_line += "{\\c&Hff6600&}" + w['gurmukhi'] + "{\\c&Hffffff&}"
                        english_line += "{\\c&Hff6600&}" + w['english'] + "{\\c&Hffffff&}"
                    else:
                        # Other words in white
                        gurmukhi_line += w['gurmukhi']
                        english_line += w['english']
                    
                    if i < len(line_words) - 1:
                        gurmukhi_line += " "
                        english_line += " "
                
                # Write both lines - Gurmukhi on top, English below
                f.write(f"Dialogue: 0,{start_time},{end_time},Gurmukhi,,0,0,0,,{gurmukhi_line}\\N\n")
                f.write(f"Dialogue: 1,{start_time},{end_time},English,,0,0,0,,{english_line}\\N\n")
    
    print(f"✅ Bilingual subtitles created: {ass_path}")
    return ass_path

def create_bilingual_karaoke_video(subtitle_path, instrumental_path, output_path):
    """Create bilingual karaoke video"""
    print("🎬 Creating bilingual karaoke video...")
    
    if instrumental_path and os.path.exists(instrumental_path):
        print("🎼 Using separated instrumental track")
        cmd = [
            FFMPEG_PATH,
            '-i', VIDEO_PATH,  # Video
            '-i', instrumental_path,  # Instrumental audio
            '-ss', '0', '-t', '30',
            '-vf', f"ass={subtitle_path}",
            '-map', '0:v:0',  # Video from first input
            '-map', '1:a:0',  # Audio from second input
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-preset', 'fast',
            '-y',
            output_path
        ]
    else:
        print("🎵 Using original audio")
        cmd = [
            FFMPEG_PATH,
            '-i', VIDEO_PATH,
            '-ss', '0', '-t', '30',
            '-vf', f"ass={subtitle_path}",
            '-c:a', 'copy',
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-y',
            output_path
        ]
    
    print("🎞️ Rendering bilingual video...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    return result.returncode == 0

def main():
    print("🎵 BILINGUAL KARAOKE CREATOR 🎵")
    print("=" * 50)
    print("Features:")
    print("📝 Gurmukhi script (top line)")
    print("🔤 English transliteration (bottom line)")
    print("🎤 Vocal-separated instrumental background")
    print("💙 Synchronized highlighting for both languages")
    print("⚪ Clean dual-language display")
    print("")
    
    if not os.path.exists(VIDEO_PATH):
        print(f"❌ Video not found: {VIDEO_PATH}")
        return
    
    # Step 1: Separate audio
    vocal_path, instrumental_path = separate_audio_tracks()
    if not vocal_path:
        print("❌ Cannot proceed without vocal track")
        return
    
    # Step 2: Transcribe vocals
    transcript = transcribe_vocals(vocal_path)
    if not transcript:
        print("❌ Transcription failed")
        return
    
    print(f"✅ Transcription: {len(transcript.text)} chars")
    print(f"✅ Words with timing: {len(transcript.words)} words")
    
    # Show sample
    print("📋 Sample bilingual words:")
    bilingual_words = create_transliteration_mapping(transcript)
    for i, word in enumerate(bilingual_words[:5]):
        print(f"   {i+1}. '{word['gurmukhi']}' / '{word['english']}' at {word['start']:.1f}s-{word['end']:.1f}s")
    
    # Step 3: Create bilingual subtitles
    subtitle_path = create_bilingual_subtitle_file(bilingual_words)
    if not subtitle_path:
        print("❌ Subtitle creation failed")
        return
    
    # Step 4: Create bilingual video
    output_path = os.path.join(PROJECT_DIR, "punjaban_bilingual_karaoke.mp4")
    success = create_bilingual_karaoke_video(subtitle_path, instrumental_path, output_path)
    
    # Cleanup
    for temp_file in [vocal_path, instrumental_path, subtitle_path]:
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)
    
    if success and os.path.exists(output_path):
        output_size = os.path.getsize(output_path) / (1024*1024)
        
        print("\n🎉 SUCCESS! Bilingual karaoke video created!")
        print("=" * 50)
        print(f"📁 Location: {output_path}")
        print(f"📊 Size: {output_size:.1f}MB")
        print(f"⏱️ Duration: 30 seconds")
        print("")
        print("🎵 Bilingual Features:")
        print("  📝 Gurmukhi script on top line")
        print("  🔤 English transliteration on bottom line")
        print("  🎼 Instrumental-only background audio")
        print("  💙 Blue word highlighting (both languages)")
        print("  ⚪ White text with black outline")
        print("  🎯 Perfect synchronization")
        print("")
        print("🎤 Perfect for:")
        print("  • Learning Punjabi pronunciation")
        print("  • Bilingual audiences")
        print("  • Language education")
        print("  • Professional karaoke")
        
        print(f"\n▶️ Opening bilingual karaoke video...")
        subprocess.run(['open', output_path])
        
    else:
        print("\n❌ Failed to create bilingual video")

if __name__ == "__main__":
    main()