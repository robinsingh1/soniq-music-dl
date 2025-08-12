#!/usr/bin/env python3
"""
Upload trending videos to GCS and process them through the karaoke service
"""
import os
import glob
import time
import requests
from google.cloud import storage

# Configuration
LOCAL_VIDEO_DIR = "/Users/rajvindersingh/Projects/karooke/trending_music"
BUCKET_NAME = "soniq-karaoke-videos"
PROCESSING_SERVICE_URL = "https://soniq-processor-894603036612.us-central1.run.app"

def upload_video_to_gcs(local_path, gcs_filename):
    """Upload a video file to Google Cloud Storage"""
    try:
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(f"trending/{gcs_filename}")
        
        print(f"📤 Uploading: {gcs_filename}")
        blob.upload_from_filename(local_path)
        blob.make_public()
        
        gcs_url = f"https://storage.googleapis.com/{BUCKET_NAME}/trending/{gcs_filename}"
        print(f"✅ Uploaded: {gcs_url}")
        return gcs_url
        
    except Exception as e:
        print(f"❌ Upload failed for {gcs_filename}: {e}")
        return None

def process_video_with_karaoke_service(video_url, video_name):
    """Send video to processing service for karaoke creation"""
    try:
        print(f"\n🎬 Processing: {video_name}")
        print(f"📁 Video URL: {video_url}")
        
        # Call processing service
        response = requests.post(
            f"{PROCESSING_SERVICE_URL}/process",
            json={
                "video_url": video_url,
                "vocal_levels": [0.0, 0.25, 0.5]  # 0%, 25%, 50% vocal levels
            },
            timeout=1800  # 30 minute timeout for processing
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Processing successful!")
                print(f"🎤 Created {len(result.get('videos', []))} karaoke versions:")
                
                for video in result.get('videos', []):
                    print(f"  • {video['vocal_level']}% vocal: {video['url']}")
                
                return result
            else:
                print(f"❌ Processing failed: {result}")
                return None
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Processing error: {str(e)}")
        return None

def main():
    """Main function to upload and process all trending videos"""
    print("🎵 BATCH KARAOKE PROCESSOR FOR TRENDING VIDEOS 🎵")
    print("=" * 70)
    
    # Get all downloaded video files
    video_files = glob.glob(os.path.join(LOCAL_VIDEO_DIR, "*.mp4"))
    if not video_files:
        print("❌ No video files found in", LOCAL_VIDEO_DIR)
        return
    
    print(f"📂 Found {len(video_files)} videos to process")
    print("")
    
    # Process each video
    results = []
    successful_uploads = 0
    successful_processing = 0
    
    for i, video_path in enumerate(sorted(video_files), 1):
        video_filename = os.path.basename(video_path)
        video_name = os.path.splitext(video_filename)[0]
        
        print(f"\n{'='*70}")
        print(f"🎯 VIDEO {i}/{len(video_files)}: {video_name}")
        print(f"📁 Local: {video_path}")
        
        # Step 1: Upload to GCS
        gcs_url = upload_video_to_gcs(video_path, video_filename)
        
        if gcs_url:
            successful_uploads += 1
            
            # Step 2: Process with karaoke service
            print(f"⏳ Starting karaoke processing...")
            processing_result = process_video_with_karaoke_service(gcs_url, video_name)
            
            if processing_result:
                successful_processing += 1
                results.append({
                    'video_name': video_name,
                    'gcs_url': gcs_url,
                    'processing_result': processing_result,
                    'status': 'success'
                })
                print(f"🎉 Complete success for: {video_name}")
            else:
                results.append({
                    'video_name': video_name,
                    'gcs_url': gcs_url,
                    'processing_result': None,
                    'status': 'processing_failed'
                })
                print(f"⚠️ Upload success but processing failed: {video_name}")
        else:
            results.append({
                'video_name': video_name,
                'gcs_url': None,
                'processing_result': None,
                'status': 'upload_failed'
            })
            print(f"❌ Upload failed: {video_name}")
    
    # Final summary
    print(f"\n{'='*70}")
    print("📊 BATCH PROCESSING SUMMARY")
    print(f"{'='*70}")
    print(f"📂 Total videos: {len(video_files)}")
    print(f"📤 Successful uploads: {successful_uploads}/{len(video_files)}")
    print(f"🎬 Successful processing: {successful_processing}/{len(video_files)}")
    print("")
    
    # Detailed results
    if successful_processing > 0:
        print("🎉 SUCCESSFULLY PROCESSED VIDEOS:")
        for result in results:
            if result['status'] == 'success':
                print(f"\n🎵 {result['video_name']}")
                print(f"   📁 Original: {result['gcs_url']}")
                
                processing_result = result['processing_result']
                if processing_result and 'videos' in processing_result:
                    for video in processing_result['videos']:
                        print(f"   🎤 {video['vocal_level']}% vocal: {video['url']}")
    
    if successful_processing < len(video_files):
        print(f"\n⚠️ FAILED/PARTIAL RESULTS:")
        for result in results:
            if result['status'] != 'success':
                print(f"   ❌ {result['video_name']}: {result['status']}")
    
    print(f"\n🏁 Batch processing complete!")
    print(f"✅ {successful_processing} videos fully processed into karaoke versions")

if __name__ == "__main__":
    main()