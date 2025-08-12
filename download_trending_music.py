#!/usr/bin/env python3
"""
Download Trending Music Videos from YouTube
Downloads top trending music videos locally
"""
import os
import yt_dlp
from datetime import datetime
import json

# Configuration
OUTPUT_DIR = "/Users/rajvindersingh/Projects/karooke/trending_music"
MAX_VIDEOS = 10

def get_trending_music_urls():
    """Get URLs of trending music videos from YouTube Music charts"""
    
    # YouTube Music trending/charts URLs
    trending_urls = [
        # YouTube Music Charts - Top Songs Global
        "https://www.youtube.com/playlist?list=PL4fGSI1pDJn5anCaPvChkr_cx6rQ93gKo",
        
        # Alternative: search for trending music
        "https://www.youtube.com/results?search_query=trending+music+2024",
        
        # Billboard Hot 100 playlist
        "https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf",
        
        # YouTube Music - Trending
        "https://music.youtube.com/playlist?list=PLFgquLnL59alCl_2TQvOiD5Vgm1hCaGSI"
    ]
    
    # Search for individual music videos (not playlists)
    search_queries = [
        "official music video 2024",
        "new music video this week",
        "trending song official video",
        "vevo music video 2024",
        "single music video 2024"
    ]
    
    video_urls = []
    
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'force_generic_extractor': False,
        'ignoreerrors': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # Try to get videos from search results
        for query in search_queries[:3]:  # Use first 3 queries
            try:
                print(f"🔍 Searching: {query}")
                search_url = f"ytsearch10:{query}"  # Get 10 results per search
                result = ydl.extract_info(search_url, download=False)
                
                if result and 'entries' in result:
                    for entry in result['entries']:
                        if entry:
                            # Extract video ID properly
                            video_id = None
                            if 'id' in entry:
                                video_id = entry['id']
                            elif 'url' in entry and 'watch?v=' in entry['url']:
                                video_id = entry['url'].split('watch?v=')[-1].split('&')[0]
                            elif 'url' in entry:
                                video_id = entry['url']
                            
                            if video_id:
                                # Clean up video ID if it's already a full URL
                                if video_id.startswith('http'):
                                    video_url = video_id
                                else:
                                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                                
                                if video_url not in video_urls and 'watch?v=' in video_url:
                                    video_urls.append(video_url)
                                    if len(video_urls) >= MAX_VIDEOS:
                                        return video_urls[:MAX_VIDEOS]
                                    
            except Exception as e:
                print(f"⚠️ Search failed for '{query}': {str(e)[:100]}")
    
    return video_urls[:MAX_VIDEOS]

def download_video(url, index):
    """Download a single video"""
    
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Configure yt-dlp options
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': os.path.join(OUTPUT_DIR, f'{index:02d}_%(title)s.%(ext)s'),
        'quiet': False,
        'no_warnings': False,
        'ignoreerrors': True,
        'restrictfilenames': True,  # Avoid special characters in filenames
        'windowsfilenames': True,    # Safe filenames
        'writedescription': False,
        'writeinfojson': True,       # Save metadata
        'writesubtitles': False,
        'max_filesize': 100 * 1024 * 1024,  # Max 100MB per video
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Get video info first
            info = ydl.extract_info(url, download=False)
            
            if info:
                title = info.get('title', 'Unknown')
                duration = info.get('duration', 0)
                channel = info.get('channel', 'Unknown')
                view_count = info.get('view_count', 0)
                
                print(f"\n{'='*60}")
                print(f"📹 Video #{index}: {title}")
                print(f"👤 Channel: {channel}")
                print(f"⏱️ Duration: {duration//60}:{duration%60:02d}")
                print(f"👁️ Views: {view_count:,}" if view_count else "👁️ Views: Unknown")
                
                # Check duration (skip very long videos)
                if duration and duration > 600:  # Skip videos longer than 10 minutes
                    print("⏭️ Skipping: Video too long (>10 minutes)")
                    return False
                
                # Download the video
                print(f"📥 Downloading...")
                ydl.download([url])
                
                print(f"✅ Downloaded successfully!")
                return True
                
    except Exception as e:
        print(f"❌ Failed to download: {str(e)[:100]}")
        return False
    
    return False

def main():
    """Main function to download trending music videos"""
    
    print("🎵 TRENDING MUSIC VIDEO DOWNLOADER 🎵")
    print("=" * 60)
    print(f"📁 Output directory: {OUTPUT_DIR}")
    print(f"🎯 Target: {MAX_VIDEOS} videos")
    print("")
    
    # Get trending video URLs
    print("🔎 Finding trending music videos...")
    video_urls = get_trending_music_urls()
    
    if not video_urls:
        print("❌ Could not find trending videos")
        return
    
    print(f"\n✅ Found {len(video_urls)} trending videos")
    print("=" * 60)
    
    # Download statistics
    successful_downloads = 0
    failed_downloads = 0
    download_info = []
    
    # Download each video
    for i, url in enumerate(video_urls, 1):
        success = download_video(url, i)
        
        if success:
            successful_downloads += 1
            download_info.append({
                'index': i,
                'url': url,
                'status': 'success'
            })
        else:
            failed_downloads += 1
            download_info.append({
                'index': i,
                'url': url,
                'status': 'failed'
            })
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 DOWNLOAD SUMMARY")
    print("=" * 60)
    print(f"✅ Successful: {successful_downloads}/{len(video_urls)}")
    print(f"❌ Failed: {failed_downloads}/{len(video_urls)}")
    print(f"📁 Files saved to: {OUTPUT_DIR}")
    
    # Save download log
    log_file = os.path.join(OUTPUT_DIR, f"download_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(log_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_videos': len(video_urls),
            'successful': successful_downloads,
            'failed': failed_downloads,
            'downloads': download_info
        }, f, indent=2)
    
    print(f"📝 Log saved to: {log_file}")
    
    # List downloaded files
    if successful_downloads > 0:
        print("\n📂 Downloaded files:")
        for file in sorted(os.listdir(OUTPUT_DIR)):
            if file.endswith('.mp4'):
                file_path = os.path.join(OUTPUT_DIR, file)
                size_mb = os.path.getsize(file_path) / (1024 * 1024)
                print(f"  • {file} ({size_mb:.1f} MB)")

if __name__ == "__main__":
    main()