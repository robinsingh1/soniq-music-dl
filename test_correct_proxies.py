#!/usr/bin/env python3
"""
Test correct ScraperAPI proxy endpoints
"""
import yt_dlp
import requests
import socket

SCRAPERAPI_KEY = "1c2e172a2133f9cb5d9328371ec4b196"
TEST_URL = "https://www.youtube.com/watch?v=V9PVRfjEBTI"

def test_correct_hostnames():
    """Test correct ScraperAPI hostnames"""
    print("🔍 Testing Correct ScraperAPI Hostnames...")
    
    hostnames = [
        "proxy.scraperapi.com",  # Correct format from docs
        "api.scraperapi.com",    # API endpoint  
        "async.scraperapi.com",  # Async endpoint
    ]
    
    for hostname in hostnames:
        try:
            ip = socket.gethostbyname(hostname)
            print(f"✅ {hostname} → {ip}")
        except socket.gaierror as e:
            print(f"❌ {hostname} → DNS failed: {e}")

def test_working_proxy():
    """Test the documented proxy format"""
    print("\n🔧 Testing Documented Proxy Format...")
    
    # From ScraperAPI docs: scraperapi:API_KEY@proxy.scraperapi.com:8001
    proxy_url = f"http://scraperapi:{SCRAPERAPI_KEY}@proxy.scraperapi.com:8001"
    
    print(f"🔗 Proxy: scraperapi:***@proxy.scraperapi.com:8001")
    
    try:
        # Test with simple HTTP request
        proxies = {'http': proxy_url, 'https': proxy_url}
        response = requests.get('http://httpbin.org/ip', proxies=proxies, timeout=70)
        
        if response.status_code == 200:
            print(f"✅ HTTP test passed: {response.text}")
            
            # Test with yt-dlp
            print("🎬 Testing with yt-dlp...")
            ydl_opts = {
                'proxy': proxy_url,
                'quiet': False,
                'extract_flat': True,
                'socket_timeout': 70,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(TEST_URL, download=False)
                if info:
                    print(f"✅ yt-dlp success: {info.get('title', 'Unknown')}")
                    return proxy_url
        else:
            print(f"❌ HTTP test failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Proxy test failed: {e}")
    
    return None

def main():
    print("🔧 CORRECT SCRAPERAPI CONFIGURATION TEST 🔧")
    print("=" * 55)
    
    # Test DNS resolution for correct hostnames
    test_correct_hostnames()
    
    # Test the documented proxy configuration
    working_proxy = test_working_proxy()
    
    if working_proxy:
        print(f"\n🎉 SUCCESS! Use this proxy configuration:")
        print(f"✅ {working_proxy}")
    else:
        print(f"\n⚠️ Proxy still not working - network or service issue")

if __name__ == "__main__":
    main()