#!/usr/bin/env python3
"""
Standalone Transcription Service
Provides audio transcription functionality using OpenAI Whisper
"""
import os
import tempfile
import subprocess
import openai
import librosa
import soundfile as sf

class TranscriptionService:
    """Standalone transcription service using OpenAI Whisper"""
    
    def __init__(self, openai_api_key=None, ffmpeg_path='/opt/homebrew/bin/ffmpeg'):
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY', '')
        self.ffmpeg_path = ffmpeg_path
        self.temp_dir = tempfile.gettempdir()
        
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
    
    def extract_audio_from_video(self, video_path, output_path=None, duration=None):
        """Extract audio from video file"""
        if not output_path:
            output_path = os.path.join(self.temp_dir, "extracted_audio.wav")
        
        print(f"🎵 Extracting audio from {video_path}...")
        
        extract_cmd = [
            self.ffmpeg_path, '-i', video_path,
            '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2'
        ]
        
        if duration:
            extract_cmd.extend(['-t', str(duration)])
            print(f"⏱️ Limiting to {duration} seconds")
        
        extract_cmd.extend([output_path, '-y'])
        
        result = subprocess.run(extract_cmd, capture_output=True, text=True)
        
        if not os.path.exists(output_path):
            print(f"❌ Audio extraction failed: {result.stderr}")
            return None
        
        print(f"✅ Audio extracted to {output_path}")
        return output_path
    
    def transcribe_audio_file(self, audio_path, response_format="verbose_json"):
        """Transcribe a single audio file using OpenAI Whisper"""
        print(f"🎙️ Transcribing {audio_path} with OpenAI Whisper...")
        
        if not self.openai_api_key:
            print("❌ No OpenAI API key provided")
            return None
        
        try:
            # Check file size and chunk if needed
            file_size = os.path.getsize(audio_path)
            if file_size > 20 * 1024 * 1024:  # 20MB limit
                return self._transcribe_chunked(audio_path, response_format)
            
            with open(audio_path, 'rb') as audio_file:
                transcript = openai.Audio.transcribe(
                    model="whisper-1",
                    file=audio_file,
                    response_format=response_format,
                    timestamp_granularities=["word"] if response_format == "verbose_json" else None
                )
            
            if response_format == "verbose_json" and hasattr(transcript, 'words'):
                print(f"✅ Transcribed: {len(transcript.words)} words")
            else:
                print("✅ Transcription completed")
            
            return transcript
            
        except Exception as e:
            print(f"❌ Transcription failed: {e}")
            return None
    
    def transcribe_video(self, video_path, duration=None, response_format="verbose_json"):
        """Transcribe audio from video file"""
        print(f"🎬 Transcribing video: {video_path}")
        
        # Extract audio first
        audio_path = self.extract_audio_from_video(video_path, duration=duration)
        if not audio_path:
            return None
        
        # Transcribe extracted audio
        transcript = self.transcribe_audio_file(audio_path, response_format)
        
        # Cleanup extracted audio
        if os.path.exists(audio_path):
            os.remove(audio_path)
        
        return transcript
    
    def _transcribe_chunked(self, audio_path, response_format="verbose_json"):
        """Transcribe large audio files in chunks"""
        print("📦 Chunking large audio file...")
        
        chunk_dir = os.path.join(self.temp_dir, "audio_chunks")
        os.makedirs(chunk_dir, exist_ok=True)
        
        # Split into 5-minute chunks
        chunk_duration = 300
        chunk_files = []
        chunk_index = 0
        start_time = 0
        
        # Get audio duration first
        duration_cmd = [
            self.ffmpeg_path, '-i', audio_path,
            '-f', 'null', '-'
        ]
        result = subprocess.run(duration_cmd, capture_output=True, text=True)
        
        # Parse duration from stderr (ffmpeg outputs to stderr)
        import re
        duration_match = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', result.stderr)
        if duration_match:
            hours, minutes, seconds = duration_match.groups()
            total_duration = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
            max_duration = min(600, total_duration)  # Process up to 10 minutes
        else:
            max_duration = 600
        
        while start_time < max_duration:
            chunk_path = os.path.join(chunk_dir, f"chunk_{chunk_index:03d}.wav")
            
            chunk_cmd = [
                self.ffmpeg_path, '-i', audio_path,
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
        if response_format == "verbose_json":
            all_words = []
        all_text = []
        
        for start_offset, chunk_path in chunk_files:
            try:
                with open(chunk_path, 'rb') as audio_file:
                    transcript = openai.Audio.transcribe(
                        model="whisper-1",
                        file=audio_file,
                        response_format=response_format,
                        timestamp_granularities=["word"] if response_format == "verbose_json" else None
                    )
                
                if response_format == "verbose_json" and hasattr(transcript, 'words'):
                    # Adjust timestamps
                    for word in transcript.words:
                        word.start += start_offset
                        word.end += start_offset
                        all_words.append(word)
                    
                    all_text.append(transcript.text)
                    print(f"✅ Chunk transcribed: {len(transcript.words)} words")
                else:
                    all_text.append(str(transcript))
                    print("✅ Chunk transcribed")
                    
            except Exception as e:
                print(f"❌ Chunk failed: {e}")
            
            os.remove(chunk_path)
        
        # Cleanup chunk directory
        os.rmdir(chunk_dir)
        
        # Return combined transcript
        if response_format == "verbose_json":
            class CombinedTranscript:
                def __init__(self, words, text):
                    self.words = words
                    self.text = text
            
            return CombinedTranscript(all_words, " ".join(all_text))
        else:
            return " ".join(all_text)
    
    def get_transcript_text(self, transcript):
        """Extract plain text from transcript object"""
        if hasattr(transcript, 'text'):
            return transcript.text
        elif isinstance(transcript, str):
            return transcript
        elif hasattr(transcript, 'words'):
            return " ".join([word.word for word in transcript.words])
        else:
            return str(transcript)
    
    def get_transcript_with_timestamps(self, transcript):
        """Extract words with timestamps from transcript"""
        if hasattr(transcript, 'words'):
            return [
                {
                    'word': word.word,
                    'start': word.start,
                    'end': word.end
                }
                for word in transcript.words
            ]
        return []

# Standalone function for easy importing
def transcribe_audio(audio_path, openai_api_key=None, response_format="verbose_json"):
    """Simple function to transcribe audio file"""
    service = TranscriptionService(openai_api_key)
    return service.transcribe_audio_file(audio_path, response_format)

def transcribe_video(video_path, openai_api_key=None, duration=None, response_format="verbose_json"):
    """Simple function to transcribe video file"""
    service = TranscriptionService(openai_api_key)
    return service.transcribe_video(video_path, duration, response_format)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python transcription_service.py <audio_or_video_file> [duration_seconds]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    service = TranscriptionService()
    
    if file_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):
        transcript = service.transcribe_video(file_path, duration=duration)
    else:
        transcript = service.transcribe_audio_file(file_path)
    
    if transcript:
        print("\n" + "="*50)
        print("TRANSCRIPTION RESULT:")
        print("="*50)
        print(service.get_transcript_text(transcript))
        
        if hasattr(transcript, 'words'):
            print(f"\nTotal words: {len(transcript.words)}")
            print("First few words with timestamps:")
            for word in transcript.words[:10]:
                print(f"  {word.start:.2f}s - {word.end:.2f}s: '{word.word}'")
    else:
        print("❌ Transcription failed")
        sys.exit(1)