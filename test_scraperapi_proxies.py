#!/usr/bin/env python3
"""
Test different ScraperAPI proxy configurations to find working setup
"""
import yt_dlp
import requests
import socket

SCRAPERAPI_KEY = "1c2e172a2133f9cb5d9328371ec4b196"
TEST_URL = "https://www.youtube.com/watch?v=V9PVRfjEBTI"

def test_dns_resolution():
    """Test if proxy hostnames resolve"""
    print("🔍 Testing DNS Resolution...")
    
    hostnames = [
        "residential-proxy.scraperapi.com",
        "proxy-server.scraperapi.com", 
        "premium-residential.scraperapi.com",
        "api.scraperapi.com"
    ]
    
    for hostname in hostnames:
        try:
            ip = socket.gethostbyname(hostname)
            print(f"✅ {hostname} → {ip}")
        except socket.gaierror as e:
            print(f"❌ {hostname} → DNS failed: {e}")

def test_scraperapi_direct():
    """Test ScraperAPI direct API"""
    print("\n🌐 Testing ScraperAPI Direct API...")
    
    api_url = "http://api.scraperapi.com"
    params = {
        'api_key': SCRAPERAPI_KEY,
        'url': 'https://httpbin.org/ip',  # Simple test endpoint
        'country_code': 'us'
    }
    
    try:
        response = requests.get(api_url, params=params, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Direct API failed: {e}")
        return False

def test_proxy_configs():
    """Test different proxy configurations"""
    print("\n🔧 Testing Proxy Configurations...")
    
    proxy_configs = [
        # Standard proxy server
        f"http://scraperapi:{SCRAPERAPI_KEY}@proxy-server.scraperapi.com:8001",
        
        # Premium with different format
        f"http://scraperapi.premium:{SCRAPERAPI_KEY}@proxy-server.scraperapi.com:8001",
        
        # Residential (original)
        f"http://scraperapi.premium:{SCRAPERAPI_KEY}@residential-proxy.scraperapi.com:8001",
        
        # Try different username format
        f"http://scraperapi-{SCRAPERAPI_KEY}@proxy-server.scraperapi.com:8001",
        
        # Simple format
        f"http://{SCRAPERAPI_KEY}@proxy-server.scraperapi.com:8001",
    ]
    
    for i, proxy_url in enumerate(proxy_configs):
        print(f"\n🔗 Config {i+1}: Testing proxy...")
        print(f"   Format: {proxy_url.split('@')[0]}@{proxy_url.split('@')[1]}")
        
        try:
            # Test with simple HTTP request first
            proxies = {'http': proxy_url, 'https': proxy_url}
            response = requests.get('http://httpbin.org/ip', proxies=proxies, timeout=15)
            
            if response.status_code == 200:
                print(f"✅ HTTP test passed: {response.text[:100]}")
                
                # Test with yt-dlp
                ydl_opts = {
                    'proxy': proxy_url,
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': True,  # Just test connection
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(TEST_URL, download=False)
                    if info:
                        print(f"✅ yt-dlp test passed: {info.get('title', 'Unknown')}")
                        return proxy_url
            else:
                print(f"❌ HTTP test failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Config failed: {str(e)[:100]}")
    
    return None

def test_youtube_direct():
    """Test direct YouTube access (baseline)"""
    print("\n📺 Testing Direct YouTube Access...")
    
    try:
        ydl_opts = {'quiet': True, 'extract_flat': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(TEST_URL, download=False)
            if info:
                print(f"✅ Direct access works: {info.get('title', 'Unknown')}")
                return True
    except Exception as e:
        print(f"❌ Direct access failed: {e}")
        return False

def main():
    print("🧪 SCRAPERAPI PROXY DIAGNOSTICS 🧪")
    print("=" * 50)
    
    # Test 1: DNS Resolution
    test_dns_resolution()
    
    # Test 2: ScraperAPI Direct API
    direct_works = test_scraperapi_direct()
    
    # Test 3: Direct YouTube access
    youtube_direct = test_youtube_direct()
    
    # Test 4: Proxy configurations
    if direct_works:
        working_proxy = test_proxy_configs()
        
        if working_proxy:
            print(f"\n🎉 WORKING PROXY FOUND!")
            print(f"✅ Use this configuration:")
            print(f"   {working_proxy}")
        else:
            print(f"\n⚠️ No working proxy configuration found")
            if youtube_direct:
                print("   But direct access works - proxy may not be needed")
    else:
        print("\n❌ ScraperAPI service appears to be unavailable")

if __name__ == "__main__":
    main()