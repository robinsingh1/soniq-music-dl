#!/usr/bin/env python3
"""
Simple test to download Billie Eilish video and confirm success
"""
import os
import yt_dlp

# Test direct download only
def test_download():
    url = "https://www.youtube.com/watch?v=V9PVRfjEBTI"
    output_path = "/Users/rajvindersingh/Projects/karooke/billie_birds_direct.mp4"
    
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': output_path,
        'quiet': False,
    }
    
    print(f"🎯 Downloading: {url}")
    print(f"📁 Output: {output_path}")
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            
            print(f"🎵 Title: {title}")
            print(f"⏱️ Duration: {duration//60}:{duration%60:02d}")
            
            # Download
            ydl.download([url])
        
        if os.path.exists(output_path):
            size = os.path.getsize(output_path) / (1024*1024)
            print(f"✅ Success! Downloaded {size:.1f}MB")
            return output_path, title
        else:
            print("❌ File not found after download")
            return None, None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None, None

if __name__ == "__main__":
    video_path, title = test_download()
    if video_path:
        print(f"\n🎉 Ready for karaoke processing!")
        print(f"📁 File: {video_path}")