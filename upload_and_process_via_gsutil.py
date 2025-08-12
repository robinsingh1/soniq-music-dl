#!/usr/bin/env python3
"""
Upload videos using gsutil and process through karaoke service
"""
import os
import glob
import subprocess
import requests
import json

# Configuration
LOCAL_VIDEO_DIR = "/Users/rajvindersingh/Projects/karooke/trending_music"
BUCKET_NAME = "soniq-karaoke-videos"
PROCESSING_SERVICE_URL = "https://soniq-processor-894603036612.us-central1.run.app"

def upload_video_with_gsutil(local_path, gcs_filename):
    """Upload video using gsutil command"""
    try:
        gcs_path = f"gs://{BUCKET_NAME}/trending/{gcs_filename}"
        
        print(f"📤 Uploading: {gcs_filename}")
        
        # Upload with gsutil
        result = subprocess.run([
            'gsutil', 'cp', local_path, gcs_path
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            # Make public
            public_result = subprocess.run([
                'gsutil', 'acl', 'ch', '-u', 'AllUsers:R', gcs_path
            ], capture_output=True, text=True)
            
            if public_result.returncode == 0:
                gcs_url = f"https://storage.googleapis.com/{BUCKET_NAME}/trending/{gcs_filename}"
                print(f"✅ Uploaded and made public: {gcs_url}")
                return gcs_url
            else:
                print(f"⚠️ Uploaded but failed to make public: {public_result.stderr}")
                gcs_url = f"https://storage.googleapis.com/{BUCKET_NAME}/trending/{gcs_filename}"
                return gcs_url
        else:
            print(f"❌ Upload failed: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Upload error for {gcs_filename}: {e}")
        return None

def process_video_with_karaoke_service(video_url, video_name, vocal_level, test_duration=None):
    """Send video to processing service for karaoke creation - one level at a time"""
    try:
        duration_text = f" ({test_duration}s test)" if test_duration else ""
        print(f"\n🎬 Processing: {video_name} ({int(vocal_level*100)}% vocal{duration_text})")
        print(f"📁 Video URL: {video_url}")
        
        # Prepare request data
        request_data = {
            "video_url": video_url,
            "vocal_levels": [vocal_level]  # Single vocal level per request
        }
        
        # Add test duration if specified
        if test_duration:
            request_data["test_duration"] = test_duration
            print(f"⏱️ Test mode: {test_duration} seconds")
        
        # Call processing service with single vocal level
        timeout_duration = 300 if test_duration else 1200  # 5 min for test, 20 min for full
        expected_time = "2-5 minutes" if test_duration else "5-10 minutes"
        print(f"⏳ Starting karaoke processing for {int(vocal_level*100)}% vocal ({expected_time})...")
        
        response = requests.post(
            f"{PROCESSING_SERVICE_URL}/process",
            json=request_data,
            timeout=timeout_duration
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
            
    except requests.exceptions.Timeout:
        print(f"⏰ Processing timed out (may still be running in background)")
        return None
    except Exception as e:
        print(f"❌ Processing error: {str(e)}")
        return None

def main():
    """Main function to upload and process trending videos"""
    print("🎵 GSUTIL BATCH KARAOKE PROCESSOR 🎵")
    print("=" * 60)
    
    # Check if gsutil is available
    try:
        result = subprocess.run(['gsutil', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ gsutil not available. Please install Google Cloud SDK.")
            return
        print("✅ gsutil is available")
    except FileNotFoundError:
        print("❌ gsutil not found. Please install Google Cloud SDK.")
        return
    
    # Get all video files
    video_files = glob.glob(os.path.join(LOCAL_VIDEO_DIR, "*.mp4"))
    if not video_files:
        print("❌ No video files found")
        return
    
    print(f"📂 Found {len(video_files)} videos to process")
    
    # Process first 3 videos to start (to avoid timeouts)
    video_files = sorted(video_files)[:3]  # Just first 3 for testing
    
    results = []
    successful_uploads = 0
    successful_processing = 0
    
    for i, video_path in enumerate(video_files, 1):
        video_filename = os.path.basename(video_path)
        video_name = os.path.splitext(video_filename)[0]
        
        print(f"\n{'='*60}")
        print(f"🎯 VIDEO {i}/{len(video_files)}: {video_name}")
        print(f"📁 Local: {video_path}")
        
        # Step 1: Upload to GCS with gsutil
        gcs_url = upload_video_with_gsutil(video_path, video_filename)
        
        if gcs_url:
            successful_uploads += 1
            
            # Step 2: Process with karaoke service - one vocal level at a time
            vocal_levels = [0.0, 0.25]  # 0% and 25% vocal levels
            all_karaoke_videos = []
            processing_success = True
            
            for vocal_level in vocal_levels:
                # Add test_duration=30 for 30-second test, or remove for full processing
                processing_result = process_video_with_karaoke_service(gcs_url, video_name, vocal_level, test_duration=30)
                
                if processing_result and processing_result.get('success'):
                    videos = processing_result.get('videos', [])
                    all_karaoke_videos.extend(videos)
                    print(f"✅ Success for {int(vocal_level*100)}% vocal level")
                else:
                    print(f"❌ Failed for {int(vocal_level*100)}% vocal level")
                    processing_success = False
            
            if processing_success:
                successful_processing += 1
                results.append({
                    'video_name': video_name,
                    'gcs_url': gcs_url,
                    'processing_result': {'videos': all_karaoke_videos},
                    'status': 'success'
                })
                print(f"🎉 Complete success: {video_name}")
            else:
                results.append({
                    'video_name': video_name,
                    'gcs_url': gcs_url,
                    'processing_result': {'videos': all_karaoke_videos},
                    'status': 'partial_success'
                })
                print(f"⚠️ Partial success: {video_name}")
        else:
            results.append({
                'video_name': video_name,
                'gcs_url': None,
                'processing_result': None,
                'status': 'upload_failed'
            })
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 BATCH PROCESSING SUMMARY")
    print(f"{'='*60}")
    print(f"📂 Videos processed: {len(video_files)}")
    print(f"📤 Successful uploads: {successful_uploads}/{len(video_files)}")
    print(f"🎬 Successful processing: {successful_processing}/{len(video_files)}")
    
    # Save results
    results_file = os.path.join(LOCAL_VIDEO_DIR, "processing_results.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"📝 Results saved to: {results_file}")
    
    if successful_processing > 0:
        print(f"\n🎉 SUCCESSFULLY PROCESSED:")
        for result in results:
            if result['status'] == 'success':
                print(f"✅ {result['video_name']}")
                processing_result = result['processing_result']
                if processing_result and 'videos' in processing_result:
                    for video in processing_result['videos']:
                        print(f"   🎤 {video['vocal_level']}% vocal: {video['url']}")

if __name__ == "__main__":
    main()