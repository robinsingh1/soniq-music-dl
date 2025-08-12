#!/usr/bin/env python3
"""
YouTube Download Service for Cloud Run
Downloads videos and stores them in Google Cloud Storage
"""
import os
import tempfile
import uuid
from flask import Flask, request, jsonify
import yt_dlp
from google.cloud import storage

app = Flask(__name__)

# Configuration
BUCKET_NAME = os.getenv('BUCKET_NAME', 'soniq-karaoke-videos')
TEMP_DIR = tempfile.gettempdir()

def upload_to_gcs(local_path, gcs_filename):
    """Upload file to Google Cloud Storage"""
    try:
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(f"downloads/{gcs_filename}")
        
        blob.upload_from_filename(local_path)
        
        # Make it publicly readable
        blob.make_public()
        
        return f"https://storage.googleapis.com/{BUCKET_NAME}/downloads/{gcs_filename}"
    except Exception as e:
        print(f"❌ GCS upload failed: {e}")
        return None

def download_youtube_video(url):
    """Download YouTube video"""
    try:
        # Generate unique filename
        job_id = str(uuid.uuid4())[:8]
        video_id = url.split('watch?v=')[1].split('&')[0] if 'watch?v=' in url else job_id
        output_filename = f"{video_id}_{job_id}.mp4"
        local_path = os.path.join(TEMP_DIR, output_filename)
        
        # Download with yt-dlp
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': local_path,
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Get video info
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            
            # Download the video
            ydl.download([url])
        
        if not os.path.exists(local_path):
            return None, None, None, "Download failed - file not found"
        
        # Upload to GCS
        gcs_url = upload_to_gcs(local_path, output_filename)
        
        if gcs_url:
            # Clean up local file
            os.remove(local_path)
            
            return {
                'job_id': job_id,
                'video_id': video_id,
                'title': title,
                'duration': duration,
                'download_url': gcs_url,
                'filename': output_filename
            }, None
        else:
            return None, "Upload to storage failed"
            
    except Exception as e:
        return None, str(e)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'youtube-downloader',
        'version': '1.0'
    })

@app.route('/download', methods=['POST'])
def download_video():
    """Download YouTube video endpoint"""
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({'error': 'Missing YouTube URL'}), 400
        
        url = data['url']
        
        # Validate YouTube URL
        if not ('youtube.com/watch' in url or 'youtu.be/' in url):
            return jsonify({'error': 'Invalid YouTube URL'}), 400
        
        print(f"📥 Downloading: {url}")
        
        # Download video
        result, error = download_youtube_video(url)
        
        if error:
            print(f"❌ Download failed: {error}")
            return jsonify({'error': error}), 500
        
        print(f"✅ Download successful: {result['title']}")
        
        return jsonify({
            'success': True,
            'job_id': result['job_id'],
            'title': result['title'],
            'duration': result['duration'],
            'download_url': result['download_url'],
            'filename': result['filename']
        })
        
    except Exception as e:
        print(f"❌ Server error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/status/<job_id>', methods=['GET'])
def get_status(job_id):
    """Get download status"""
    # In a real implementation, you'd track job status in a database
    return jsonify({
        'job_id': job_id,
        'status': 'completed',  # Simplified for demo
        'message': 'Download completed successfully'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)