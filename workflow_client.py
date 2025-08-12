#!/usr/bin/env python3
"""
Client to demonstrate the split download/processing workflow
"""
import requests
import time
import json

# Service endpoints (update these after deployment)
DOWNLOAD_SERVICE = "https://soniq-downloader-894603036612.us-central1.run.app"
PROCESSING_SERVICE = "https://soniq-processor-894603036612.us-central1.run.app"

def download_video(youtube_url):
    """Step 1: Download video using download service"""
    print(f"📥 Step 1: Downloading video from {youtube_url}")
    
    response = requests.post(f"{DOWNLOAD_SERVICE}/download", 
                           json={'url': youtube_url},
                           timeout=300)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Download successful: {result['title']}")
        print(f"🔗 Video URL: {result['download_url']}")
        return result
    else:
        print(f"❌ Download failed: {response.text}")
        return None

def process_video(video_url, vocal_levels=[0, 25, 50]):
    """Step 2: Process video using processing service"""
    print(f"🎬 Step 2: Processing video for karaoke")
    
    # Convert percentages to decimals
    vocal_decimals = [level/100.0 for level in vocal_levels]
    
    response = requests.post(f"{PROCESSING_SERVICE}/process",
                           json={
                               'video_url': video_url,
                               'vocal_levels': vocal_decimals
                           },
                           timeout=1800)  # 30 minutes for processing
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Processing successful: {len(result['videos'])} videos created")
        for video in result['videos']:
            print(f"  🎤 {video['vocal_level']}% vocal: {video['url']}")
        return result
    else:
        print(f"❌ Processing failed: {response.text}")
        return None

def full_workflow(youtube_url, vocal_levels=[0, 25, 50]):
    """Complete workflow: Download + Process"""
    print("🚀 STARTING KARAOKE WORKFLOW")
    print("=" * 50)
    
    # Step 1: Download
    download_result = download_video(youtube_url)
    if not download_result:
        return None
    
    print("\n" + "=" * 50)
    
    # Step 2: Process
    processing_result = process_video(download_result['download_url'], vocal_levels)
    if not processing_result:
        return None
    
    print("\n🎉 WORKFLOW COMPLETE!")
    print(f"📺 Original: {download_result['title']}")
    print(f"🎤 Karaoke videos: {len(processing_result['videos'])}")
    
    return {
        'download': download_result,
        'processing': processing_result
    }

def test_services():
    """Test both services are healthy"""
    print("🏥 Testing service health...")
    
    try:
        # Test download service
        response = requests.get(f"{DOWNLOAD_SERVICE}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Download service: healthy")
        else:
            print("❌ Download service: unhealthy")
    except Exception as e:
        print(f"❌ Download service: {e}")
    
    try:
        # Test processing service
        response = requests.get(f"{PROCESSING_SERVICE}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Processing service: healthy")
        else:
            print("❌ Processing service: unhealthy")
    except Exception as e:
        print(f"❌ Processing service: {e}")

if __name__ == "__main__":
    # Test services
    test_services()
    
    print("\n" + "=" * 60)
    
    # Example workflow
    test_url = "https://www.youtube.com/watch?v=V9PVRfjEBTI"
    
    result = full_workflow(test_url, vocal_levels=[0, 50])
    
    if result:
        print(f"\n📋 RESULTS SUMMARY:")
        print(f"Download URL: {result['download']['download_url']}")
        for video in result['processing']['videos']:
            print(f"Karaoke {video['vocal_level']}%: {video['url']}")