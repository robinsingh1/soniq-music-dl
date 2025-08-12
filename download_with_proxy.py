#!/usr/bin/env python3
"""
YouTube Video Downloader with ScraperAPI Proxy
Downloads videos using proxy to bypass bot protection
"""

import os
import tempfile
import subprocess
import openai
import yt_dlp
import requests

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-api-key-here")
SCRAPERAPI_KEY = "1c2e172a2133f9cb5d9328371ec4b196"
TEMP_DIR = tempfile.gettempdir()
FFMPEG_PATH = '/opt/homebrew/bin/ffmpeg'
PROJECT_DIR = "/Users/rajvindersingh/Projects/karooke"
DOCKER_PATH = '/usr/local/bin/docker'

def download_youtube_with_proxy(url):
    """Download YouTube video using ScraperAPI proxy"""
    print(f"📥 Downloading YouTube video with proxy...")
    print(f"🔗 URL: {url}")
    
    # Create safe filename from video ID
    video_id = url.split('watch?v=')[1].split('&')[0] if 'watch?v=' in url else 'video'
    output_path = os.path.join(TEMP_DIR, f"{video_id}_proxy.mp4")
    
    # Configure yt-dlp with ScraperAPI residential proxy (fixed format)
    proxy_url = f"http://scraperapi.premium:{SCRAPERAPI_KEY}@residential-proxy.scraperapi.com:8001"
    
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': output_path,
        'quiet': False,
        'no_warnings': False,
        'proxy': proxy_url,
        'verbose': True,
        # Additional options to help with bot protection
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'referer': 'https://www.youtube.com/',
        'cookiefile': None,  # Can add cookies if needed
        'extract_flat': False,
        'force_generic_extractor': False,
        'nocheckcertificate': True,  # Disable SSL certificate verification for proxy
        'legacyserverconnect': True,  # Use legacy connection method
        'sleep_interval': 1,  # Add delay between requests
        'max_sleep_interval': 5,  # Maximum delay
        'extractor_retries': 3,  # Retry failed extractions
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Get video info first
            print("🔍 Fetching video info through proxy...")
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            
            print(f"🎵 Title: {title}")
            print(f"⏱️ Duration: {duration//60}:{duration%60:02d}")
            
            # Download the video
            print("📦 Downloading through ScraperAPI proxy...")
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
        print("🔄 Trying alternative method...")
        
        # Alternative: Use requests with ScraperAPI
        try:
            return download_with_scraperapi_direct(url)
        except Exception as e2:
            print(f"❌ Alternative method also failed: {str(e2)}")
            return None, None

def download_with_scraperapi_direct(url):
    """Alternative download method using ScraperAPI directly"""
    print("🔄 Using ScraperAPI direct method...")
    
    # ScraperAPI endpoint
    api_url = "http://api.scraperapi.com"
    
    params = {
        'api_key': SCRAPERAPI_KEY,
        'url': url,
        'render': 'true',  # Render JavaScript
        'country_code': 'us',
        'premium': 'true',  # Use premium proxies
    }
    
    # First get the page to extract video info
    response = requests.get(api_url, params=params)
    
    if response.status_code == 200:
        print("✅ Successfully accessed YouTube through proxy")
        # Would need additional parsing here to extract video URL
        # For now, fall back to standard method
        return None, None
    else:
        print(f"❌ ScraperAPI returned status: {response.status_code}")
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
        os.remove(audio_path)
        return vocals_path, accompaniment_path
    else:
        print("❌ Docker Spleeter separation failed")
        return None, None

def download_without_proxy(url):
    """Fallback: download without proxy"""
    print("🔄 Trying direct download without proxy...")
    
    video_id = url.split('watch?v=')[1].split('&')[0] if 'watch?v=' in url else 'video'
    output_path = os.path.join(TEMP_DIR, f"{video_id}_direct.mp4")
    
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': output_path,
        'quiet': False,
        'no_warnings': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("🔍 Fetching video info directly...")
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            
            print(f"🎵 Title: {title}")
            print(f"⏱️ Duration: {duration//60}:{duration%60:02d}")
            
            # Download the video
            print("📦 Downloading directly...")
            ydl.download([url])
        
        if os.path.exists(output_path):
            size = os.path.getsize(output_path) / (1024*1024)
            print(f"✅ Downloaded: {size:.1f}MB")
            return output_path, title
        else:
            print("❌ Download failed - file not found")
            return None, None
            
    except Exception as e:
        print(f"❌ Direct download error: {str(e)}")
        return None, None

def main():
    print("🌐 YOUTUBE DOWNLOADER WITH SCRAPERAPI PROXY 🌐")
    print("=" * 60)
    print("Using ScraperAPI to bypass bot protection")
    print("")
    
    # Test URL
    test_url = "https://www.youtube.com/watch?v=V9PVRfjEBTI"
    
    print(f"🎯 Target: {test_url}")
    print("")
    
    # Try proxy first, then fallback to direct
    video_path, title = download_youtube_with_proxy(test_url)
    
    if not video_path:
        print("\n🔄 Proxy failed, trying direct download...")
        video_path, title = download_without_proxy(test_url)
    
    if video_path:
        print(f"\n✅ Successfully downloaded: {title}")
        print(f"📁 Path: {video_path}")
        
        # Optional: Continue with Spleeter processing
        print("\n🔄 Processing with Docker Spleeter...")
        vocals_path, accompaniment_path = docker_spleeter_separation(video_path)
        
        if vocals_path and accompaniment_path:
            print("\n🎉 Complete processing successful!")
            print("  🎤 Vocals extracted")
            print("  🎼 Instrumentals extracted")
            print("  Ready for karaoke creation!")
        
        return True
    else:
        print("\n❌ All download methods failed")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🚀 Proxy download successful!")
    else:
        print("\n⚠️ Check proxy settings and try again")