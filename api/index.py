from flask import Flask, request, jsonify
from flask_cors import CORS
import instaloader
import random
import time
import hashlib
import platform
import re
import json
import sys
import os
import threading
from datetime import datetime, timedelta
from instaloader import Instaloader, Profile

app = Flask(__name__)
CORS(app)

# ============================================================================
# CONFIGURATION
# ============================================================================

DEVICE_ROTATION_INTERVAL = 3  # Change device every 3 requests
PROXY_ROTATION_INTERVAL = 8   # Change proxy every 8 requests
SPEED_CHECK_INTERVAL = 300    # Check speed every 5 minutes

# ============================================================================
# SPEED CHECKER
# ============================================================================

class SpeedChecker:
    def __init__(self):
        self.last_check = datetime.now()
        self.response_times = []
        self.average_speed = 0
        self.status = "unknown"
        self.lock = threading.Lock()
    
    def add_response_time(self, time_ms):
        with self.lock:
            self.response_times.append(time_ms)
            if len(self.response_times) > 100:
                self.response_times.pop(0)
            self.average_speed = sum(self.response_times) / len(self.response_times)
    
    def check_speed(self):
        with self.lock:
            now = datetime.now()
            if (now - self.last_check).seconds >= SPEED_CHECK_INTERVAL:
                self.last_check = now
                if self.average_speed > 5000:
                    self.status = "slow"
                elif self.average_speed > 2000:
                    self.status = "medium"
                else:
                    self.status = "fast"
                return True
            return False
    
    def get_status(self):
        self.check_speed()
        return {
            "status": self.status,
            "average_response_ms": round(self.average_speed, 2),
            "total_requests": len(self.response_times),
            "last_check": self.last_check.isoformat()
        }

speed_checker = SpeedChecker()

# ============================================================================
# DEVICE MANAGER
# ============================================================================

class DeviceManager:
    def __init__(self):
        self.devices = []
        self.current_index = 0
        self.request_count = 0
        self.rotation_interval = DEVICE_ROTATION_INTERVAL
        self.lock = threading.Lock()
        self._generate_devices()
    
    def _generate_devices(self):
        browsers = [
            {
                'name': 'Chrome',
                'version': f"{random.randint(110, 122)}.0.{random.randint(6000, 7000)}.{random.randint(0, 200)}",
                'user_agent': f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(110, 122)}.0.0.0 Safari/537.36",
                'platform': 'Windows',
                'platform_version': '10.0',
                'cpu_cores': random.choice([4, 6, 8, 12, 16]),
                'memory': random.choice(['8 GB', '16 GB', '32 GB'])
            },
            {
                'name': 'Chrome',
                'version': f"{random.randint(110, 122)}.0.{random.randint(6000, 7000)}.{random.randint(0, 200)}",
                'user_agent': f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_{random.randint(14, 15)}_{random.randint(0, 4)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(110, 122)}.0.0.0 Safari/537.36",
                'platform': 'macOS',
                'platform_version': f"10_{random.randint(14, 15)}_{random.randint(0, 4)}",
                'cpu_cores': random.choice([4, 6, 8, 10, 12]),
                'memory': random.choice(['8 GB', '16 GB', '24 GB', '32 GB'])
            },
            {
                'name': 'Firefox',
                'version': f"{random.randint(115, 124)}.0",
                'user_agent': f"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{random.randint(115, 124)}.0) Gecko/20100101 Firefox/{random.randint(115, 124)}.0",
                'platform': 'Windows',
                'platform_version': '10.0',
                'cpu_cores': random.choice([4, 6, 8, 12, 16]),
                'memory': random.choice(['8 GB', '16 GB', '32 GB'])
            },
            {
                'name': 'Firefox',
                'version': f"{random.randint(115, 124)}.0",
                'user_agent': f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_{random.randint(14, 15)}_{random.randint(0, 4)}; rv:{random.randint(115, 124)}.0) Gecko/20100101 Firefox/{random.randint(115, 124)}.0",
                'platform': 'macOS',
                'platform_version': f"10_{random.randint(14, 15)}_{random.randint(0, 4)}",
                'cpu_cores': random.choice([4, 6, 8, 10, 12]),
                'memory': random.choice(['8 GB', '16 GB', '24 GB', '32 GB'])
            },
            {
                'name': 'Edge',
                'version': f"{random.randint(110, 122)}.0.{random.randint(2000, 3000)}.{random.randint(0, 200)}",
                'user_agent': f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(110, 122)}.0.0.0 Safari/537.36 Edg/{random.randint(110, 122)}.0.0.0",
                'platform': 'Windows',
                'platform_version': '10.0',
                'cpu_cores': random.choice([4, 6, 8, 12, 16]),
                'memory': random.choice(['8 GB', '16 GB', '32 GB'])
            },
            {
                'name': 'Safari',
                'version': f"{random.randint(16, 17)}.{random.randint(0, 1)}",
                'user_agent': f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_{random.randint(14, 15)}_{random.randint(0, 4)}) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{random.randint(16, 17)}.0 Safari/605.1.15",
                'platform': 'macOS',
                'platform_version': f"10_{random.randint(14, 15)}_{random.randint(0, 4)}",
                'cpu_cores': random.choice([4, 6, 8, 10]),
                'memory': random.choice(['8 GB', '16 GB', '24 GB'])
            }
        ]
        
        screens = [
            (1920, 1080), (2560, 1440), (3840, 2160),
            (1366, 768), (1536, 864), (1440, 900),
            (1600, 900), (1280, 720), (1920, 1200),
            (2560, 1600), (3440, 1440), (1360, 768)
        ]
        
        languages = ['en-US', 'en-GB', 'en-IN', 'en-AU', 'en-CA', 
                    'es-ES', 'fr-FR', 'de-DE', 'it-IT', 'pt-BR',
                    'ja-JP', 'ko-KR', 'zh-CN', 'ru-RU', 'ar-SA']
        
        timezones = ['America/New_York', 'America/Los_Angeles', 'Europe/London', 
                    'Europe/Paris', 'Asia/Kolkata', 'Asia/Tokyo', 'Australia/Sydney',
                    'America/Sao_Paulo', 'Africa/Johannesburg', 'Asia/Dubai',
                    'America/Chicago', 'America/Toronto', 'Europe/Berlin']
        
        gpus = [
            'NVIDIA GeForce RTX 3060', 'NVIDIA GeForce RTX 3070', 'NVIDIA GeForce RTX 3080',
            'NVIDIA GeForce RTX 3090', 'NVIDIA GeForce RTX 4060', 'NVIDIA GeForce RTX 4070',
            'NVIDIA GeForce RTX 4080', 'NVIDIA GeForce RTX 4090', 'AMD Radeon RX 6800 XT',
            'AMD Radeon RX 6900 XT', 'AMD Radeon RX 7800 XT', 'AMD Radeon RX 7900 XTX',
            'Intel Iris Xe Graphics', 'Intel UHD Graphics 620', 'Apple M1 GPU',
            'Apple M2 GPU', 'Apple M3 GPU'
        ]
        
        fonts = [
            'Arial, Helvetica, sans-serif',
            'Times New Roman, Times, serif',
            'Courier New, Courier, monospace',
            'Georgia, serif',
            'Verdana, Arial, sans-serif',
            'Tahoma, Arial, sans-serif',
            'Trebuchet MS, Arial, sans-serif',
            'Helvetica Neue, Arial, sans-serif'
        ]
        
        # Generate 10 different devices
        for i in range(10):
            browser = random.choice(browsers)
            screen = random.choice(screens)
            
            device = {
                'id': f"device_{i+1}_{hashlib.md5(str(time.time() + random.random()).encode()).hexdigest()[:8]}",
                'browser': browser,
                'screen': {
                    'width': screen[0],
                    'height': screen[1],
                    'color_depth': random.choice([24, 30, 32]),
                    'pixel_ratio': round(random.uniform(1, 3), 1)
                },
                'language': random.choice(languages),
                'timezone': random.choice(timezones),
                'platform': browser['platform'],
                'platform_version': browser['platform_version'],
                'cpu_cores': browser['cpu_cores'],
                'memory': browser['memory'],
                'gpu': random.choice(gpus),
                'fonts': random.choice(fonts),
                'canvas_hash': hashlib.md5(str(random.randint(1, 99999999)).encode()).hexdigest()[:16],
                'webgl_hash': hashlib.md5(str(random.randint(1, 99999999)).encode()).hexdigest()[:16],
                'audio_hash': hashlib.md5(str(random.randint(1, 99999999)).encode()).hexdigest()[:16],
                'webgl_vendor': random.choice(['Google Inc.', 'Apple Inc.', 'Mozilla Foundation', 'NVIDIA Corporation', 'AMD', 'Intel Corporation']),
                'webgl_renderer': random.choice([
                    'ANGLE (NVIDIA, NVIDIA GeForce RTX 3080, Direct3D11 vs_5_0 ps_5_0, D3D11)', 
                    'ANGLE (AMD, AMD Radeon RX 6800 XT, Direct3D11 vs_5_0 ps_5_0, D3D11)',
                    'ANGLE (Intel, Intel(R) UHD Graphics 620, Direct3D11 vs_5_0 ps_5_0, D3D11)',
                    'ANGLE (NVIDIA, NVIDIA GeForce RTX 4090, Direct3D12 vs_6_0 ps_6_0, D3D12)',
                    'ANGLE (AMD, AMD Radeon RX 7900 XTX, Direct3D12 vs_6_0 ps_6_0, D3D12)'
                ]),
                'created_at': datetime.now().isoformat()
            }
            self.devices.append(device)
    
    def get_next_device(self):
        with self.lock:
            if not self.devices:
                return None
            
            self.request_count += 1
            if self.request_count % self.rotation_interval == 0:
                self.current_index = (self.current_index + 1) % len(self.devices)
                print(f"🔄 Rotated device to {self.current_index + 1}")
            
            return self.devices[self.current_index]
    
    def get_current_device(self):
        if not self.devices:
            return None
        return self.devices[self.current_index]
    
    def get_stats(self):
        return {
            "total_devices": len(self.devices),
            "current_index": self.current_index + 1,
            "request_count": self.request_count,
            "rotation_interval": self.rotation_interval,
            "current_device": self.get_current_device()['browser']['name'] if self.get_current_device() else None
        }

device_manager = DeviceManager()

# ============================================================================
# PROXY MANAGER - Webshare Proxies
# ============================================================================

class ProxyManager:
    def __init__(self, proxy_file='proxies.txt'):
        self.proxies = []
        self.current_index = 0
        self.request_count = 0
        self.rotation_interval = PROXY_ROTATION_INTERVAL
        self.lock = threading.Lock()
        self.load_proxies(proxy_file)
    
    def load_proxies(self, proxy_file):
        try:
            if os.path.exists(proxy_file):
                with open(proxy_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            self.proxies.append(line)
                print(f"✅ Loaded {len(self.proxies)} proxies from {proxy_file}")
            else:
                # Default Webshare proxies
                self.proxies = [
                    "yywgbajj:ddd3c4hnpxer8@31.59.20.176:6754",
                    "yywgbajj:ddd3c4hnpxer8@45.38.107.97:6014",
                    "yywgbajj:ddd3c4hnpxer8@198.105.121.200:6462",
                    "yywgbajj:ddd3c4hnpxer8@64.137.96.74:6641",
                    "yywgbajj:ddd3c4hnpxer8@198.23.243.226:6361",
                    "yywgbajj:ddd3c4hnpxer8@84.247.60.125:6095",
                    "yywgbajj:ddd3c4hnpxer8@142.111.67.146:5611",
                    "yywgbajj:ddd3c4hnpxer8@191.96.254.138:6185"
                ]
                print(f"⚠️ Using {len(self.proxies)} default proxies")
            
            random.shuffle(self.proxies)
            
        except Exception as e:
            print(f"❌ Error loading proxies: {e}")
            self.proxies = []
    
    def get_next_proxy(self):
        with self.lock:
            if not self.proxies:
                return None
            
            self.request_count += 1
            if self.request_count % self.rotation_interval == 0:
                self.current_index = (self.current_index + 1) % len(self.proxies)
                print(f"🔄 Rotated proxy to {self.current_index + 1}")
            
            return self.proxies[self.current_index]
    
    def get_proxy_url(self, proxy_string):
        if not proxy_string:
            return None
        return f"http://{proxy_string}"
    
    def get_current_proxy(self):
        if not self.proxies:
            return None
        return self.proxies[self.current_index]
    
    def get_stats(self):
        return {
            "total_proxies": len(self.proxies),
            "current_index": self.current_index + 1,
            "request_count": self.request_count,
            "rotation_interval": self.rotation_interval,
            "current_proxy": self.get_current_proxy().split('@')[-1] if self.get_current_proxy() else None
        }

proxy_manager = ProxyManager()

# ============================================================================
# CORS
# ============================================================================

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# ============================================================================
# INSTAGRAM SCANNER
# ============================================================================

class InstagramScanner:
    def __init__(self):
        self.loader = None
    
    def initialize_loader(self, device, proxy_string=None):
        try:
            user_agent = device['browser']['user_agent']
            
            self.loader = Instaloader(
                max_connection_attempts=3,
                request_timeout=30,
                user_agent=user_agent,
                sleep=True,
                quiet=True
            )
            
            # Set proxy
            if proxy_string:
                proxy_url = f"http://{proxy_string}"
                if hasattr(self.loader, 'context') and hasattr(self.loader.context, '_session'):
                    self.loader.context._session.proxies = {
                        'http': proxy_url,
                        'https': proxy_url
                    }
                    print(f"🌐 Using proxy: {proxy_string.split('@')[-1]}")
            
            # Set headers
            if hasattr(self.loader, 'context') and hasattr(self.loader.context, '_session'):
                headers = {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': f"{device['language']},en;q=0.9",
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Sec-Ch-Ua': f'"{device["browser"]["name"]}"; v="120"',
                    'Sec-Ch-Ua-Platform': f'"{device["platform"]}"'
                }
                for key, value in headers.items():
                    self.loader.context._session.headers.update({key: value})
            
            return True
            
        except Exception as e:
            print(f"❌ Loader error: {e}")
            return False
    
    def estimate_creation_year(self, user_id):
        ranges = [
            (1, 2010), (100000, 2011), (1000000, 2011), (10000000, 2012),
            (50000000, 2013), (100000000, 2014), (300000000, 2015),
            (500000000, 2016), (1000000000, 2017), (3000000000, 2018),
            (5000000000, 2019), (8000000000, 2020), (12000000000, 2021),
            (18000000000, 2022), (25000000000, 2023), (35000000000, 2024),
        ]
        try:
            uid = int(user_id)
            for max_id, year in ranges:
                if uid <= max_id:
                    return year
        except:
            pass
        return None
    
    def scan_profile(self, username):
        start_time = time.time()
        
        # 1. Get device (rotates every 3 requests)
        device = device_manager.get_next_device()
        if not device:
            return {"status": "error", "error": "No device available"}
        
        # 2. Get proxy (rotates every 8 requests)
        proxy_string = proxy_manager.get_next_proxy()
        
        # 3. Initialize loader with device and proxy
        if not self.initialize_loader(device, proxy_string):
            return {"status": "error", "error": "Failed to initialize loader"}
        
        try:
            profile = Profile.from_username(self.loader.context, username)
            
            response_time = (time.time() - start_time) * 1000
            
            # Add to speed checker
            speed_checker.add_response_time(response_time)
            speed_checker.check_speed()
            
            result = {
                "status": "ok",
                "device_used": {
                    "id": device['id'],
                    "browser": device['browser']['name'],
                    "platform": device['platform'],
                    "language": device['language']
                },
                "proxy_used": proxy_string.split('@')[-1] if proxy_string and '@' in proxy_string else proxy_string,
                "speed_status": speed_checker.get_status(),
                "collected_at": datetime.now().isoformat(),
                "response_time_seconds": round(response_time / 1000, 3),
                "profile": {
                    "username": profile.username,
                    "user_id": str(profile.userid),
                    "full_name": profile.full_name,
                    "biography": profile.biography[:500] if profile.biography else 'No bio available',
                    "business_category": getattr(profile, 'business_category_name', None),
                    "is_business_account": getattr(profile, 'is_business_account', False),
                    "is_professional_account": getattr(profile, 'is_professional_account', False),
                    "category_name": getattr(profile, 'category_name', None),
                    "followers": profile.followers,
                    "following": profile.followees,
                    "posts": profile.mediacount,
                    "igtv_count": getattr(profile, 'igtv_count', 0),
                    "is_private": profile.is_private,
                    "is_verified": profile.is_verified,
                    "has_highlights": getattr(profile, 'has_highlight_reels', False),
                    "external_url": profile.external_url,
                    "profile_pic_url": profile.profile_pic_url,
                    "bio_links": self._extract_bio_links(profile),
                    "account_creation_year": self.estimate_creation_year(profile.userid),
                    "is_joined_recently": getattr(profile, 'is_joined_recently', False),
                }
            }
            
            return result
            
        except instaloader.exceptions.ProfileNotExistsException:
            return {"status": "error", "error": "Profile does not exist", "username": username}
        except instaloader.exceptions.PrivateProfileNotFollowedException:
            return {"status": "error", "error": "Private profile", "username": username}
        except instaloader.exceptions.QueryReturnedBadRequestException:
            # Rate limit - rotate proxy and device
            proxy_manager.current_index = (proxy_manager.current_index + 1) % len(proxy_manager.proxies)
            device_manager.current_index = (device_manager.current_index + 1) % len(device_manager.devices)
            return {"status": "error", "error": "Rate limit - rotated proxy & device", "username": username}
        except Exception as e:
            return {"status": "error", "error": str(e), "username": username}
    
    def _extract_bio_links(self, profile):
        bio_links = []
        try:
            if hasattr(profile, 'biography_links'):
                for link in profile.biography_links:
                    if isinstance(link, dict) and 'url' in link:
                        bio_links.append(link['url'])
                    elif isinstance(link, str):
                        bio_links.append(link)
        except:
            pass
        return bio_links

# ============================================================================
# API ROUTES
# ============================================================================

scanner = InstagramScanner()

@app.route('/')
def home():
    return jsonify({
        "name": "Instagram Scanner API",
        "version": "4.0.0",
        "status": "running",
        "rotation_config": {
            "device_rotation": f"{DEVICE_ROTATION_INTERVAL} requests",
            "proxy_rotation": f"{PROXY_ROTATION_INTERVAL} requests",
            "speed_check": f"{SPEED_CHECK_INTERVAL} seconds"
        },
        "device_stats": device_manager.get_stats(),
        "proxy_stats": proxy_manager.get_stats(),
        "speed_stats": speed_checker.get_status(),
        "endpoints": {
            "/health": "GET - Health check",
            "/api/scan?username=NAME": "GET - Scan profile",
            "/api/scan/NAME": "GET - Scan profile",
            "/api/stats": "GET - All stats",
            "/api/device-stats": "GET - Device stats",
            "/api/proxy-stats": "GET - Proxy stats",
            "/api/speed-stats": "GET - Speed stats"
        }
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "device_stats": device_manager.get_stats(),
        "proxy_stats": proxy_manager.get_stats(),
        "speed_stats": speed_checker.get_status()
    })

@app.route('/api/stats')
def stats():
    return jsonify({
        "device_stats": device_manager.get_stats(),
        "proxy_stats": proxy_manager.get_stats(),
        "speed_stats": speed_checker.get_status()
    })

@app.route('/api/device-stats')
def device_stats():
    return jsonify(device_manager.get_stats())

@app.route('/api/proxy-stats')
def proxy_stats():
    return jsonify(proxy_manager.get_stats())

@app.route('/api/speed-stats')
def speed_stats():
    return jsonify(speed_checker.get_status())

@app.route('/api/scan')
def scan():
    username = request.args.get('username', '').strip()
    
    if not username:
        return jsonify({"error": "Username required"}), 400
    
    result = scanner.scan_profile(username)
    
    if result.get('status') == 'error':
        return jsonify(result), 404
    
    return jsonify({
        "status": "success",
        "data": result
    })

@app.route('/api/scan/<username>')
def scan_path(username):
    username = username.strip().replace('@', '')
    
    if not username:
        return jsonify({"error": "Username required"}), 400
    
    result = scanner.scan_profile(username)
    
    if result.get('status') == 'error':
        return jsonify(result), 404
    
    return jsonify({
        "status": "success",
        "data": result
    })

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "status": "error",
        "error": "Endpoint not found",
        "available": ["/", "/health", "/api/stats", "/api/scan?username=NAME", "/api/scan/NAME"]
    }), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({
        "status": "error",
        "error": "Internal server error"
    })
