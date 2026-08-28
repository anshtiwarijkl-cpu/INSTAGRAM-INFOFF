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

DEVICE_ROTATION_INTERVAL = 3
PROXY_ROTATION_INTERVAL = 8
SPEED_CHECK_INTERVAL = 300

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
                'user_agent': f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(110, 122)}.0.0.0 Safari/537.36",
                'platform': 'Windows'
            },
            {
                'name': 'Chrome',
                'user_agent': f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_{random.randint(14, 15)}_{random.randint(0, 4)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(110, 122)}.0.0.0 Safari/537.36",
                'platform': 'macOS'
            },
            {
                'name': 'Firefox',
                'user_agent': f"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{random.randint(115, 124)}.0) Gecko/20100101 Firefox/{random.randint(115, 124)}.0",
                'platform': 'Windows'
            },
            {
                'name': 'Firefox',
                'user_agent': f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_{random.randint(14, 15)}_{random.randint(0, 4)}; rv:{random.randint(115, 124)}.0) Gecko/20100101 Firefox/{random.randint(115, 124)}.0",
                'platform': 'macOS'
            },
            {
                'name': 'Edge',
                'user_agent': f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(110, 122)}.0.0.0 Safari/537.36 Edg/{random.randint(110, 122)}.0.0.0",
                'platform': 'Windows'
            },
            {
                'name': 'Safari',
                'user_agent': f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_{random.randint(14, 15)}_{random.randint(0, 4)}) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{random.randint(16, 17)}.0 Safari/605.1.15",
                'platform': 'macOS'
            }
        ]
        
        languages = ['en-US', 'en-GB', 'en-IN', 'es-ES', 'fr-FR', 'de-DE']
        
        # Generate 10 devices
        for i in range(10):
            browser = random.choice(browsers)
            device = {
                'id': f"device_{i+1}_{hashlib.md5(str(time.time() + random.random()).encode()).hexdigest()[:8]}",
                'browser': browser,
                'language': random.choice(languages),
                'platform': browser['platform'],
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
            
            return self.devices[self.current_index]
    
    def get_stats(self):
        return {
            "total_devices": len(self.devices),
            "current_index": self.current_index + 1,
            "request_count": self.request_count,
            "rotation_interval": self.rotation_interval,
            "current_device": self.devices[self.current_index]['browser']['name'] if self.devices else None
        }

device_manager = DeviceManager()

# ============================================================================
# PROXY MANAGER - FIXED
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
            # Try to load from file
            if os.path.exists(proxy_file):
                with open(proxy_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            self.proxies.append(line)
                print(f"✅ Loaded {len(self.proxies)} proxies from {proxy_file}")
            else:
                print(f"⚠️ File {proxy_file} not found, using default proxies")
                # Default Webshare proxies from your screenshot
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
                print(f"✅ Using {len(self.proxies)} default proxies")
            
            # Shuffle for randomness
            random.shuffle(self.proxies)
            
        except Exception as e:
            print(f"❌ Error loading proxies: {e}")
            # Fallback proxies
            self.proxies = [
                "yywgbajj:ddd3c4hnpxer8@31.59.20.176:6754",
                "yywgbajj:ddd3c4hnpxer8@45.38.107.97:6014"
            ]
    
    def get_next_proxy(self):
        with self.lock:
            if not self.proxies:
                return None
            
            self.request_count += 1
            if self.request_count % self.rotation_interval == 0:
                self.current_index = (self.current_index + 1) % len(self.proxies)
                print(f"🔄 Rotated proxy to {self.current_index + 1}")
            
            return self.proxies[self.current_index]
    
    def get_current_proxy(self):
        if not self.proxies:
            return None
        return self.proxies[self.current_index]
    
    def get_stats(self):
        current = self.get_current_proxy()
        return {
            "total_proxies": len(self.proxies),
            "current_index": self.current_index + 1,
            "request_count": self.request_count,
            "rotation_interval": self.rotation_interval,
            "current_proxy": current.split('@')[-1] if current and '@' in current else current
        }

# Initialize proxy manager
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
                    print(f"🌐 Using proxy: {proxy_string.split('@')[-1] if '@' in proxy_string else proxy_string}")
            
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
        
        # 1. Get device
        device = device_manager.get_next_device()
        if not device:
            return {"status": "error", "error": "No device available"}
        
        # 2. Get proxy
        proxy_string = proxy_manager.get_next_proxy()
        
        # 3. Initialize loader
        if not self.initialize_loader(device, proxy_string):
            return {"status": "error", "error": "Failed to initialize loader"}
        
        try:
            profile = Profile.from_username(self.loader.context, username)
            
            response_time = (time.time() - start_time) * 1000
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
            proxy_manager.current_index = (proxy_manager.current_index + 1) % len(proxy_manager.proxies)
            device_manager.current_index = (device_manager.current_index + 1) % len(device_manager.devices)
            return {"status": "error", "error": "Rate limit - rotated", "username": username}
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
            "/api/stats": "GET - All stats"
        }
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "proxy_stats": proxy_manager.get_stats()
    })

@app.route('/api/stats')
def stats():
    return jsonify({
        "device_stats": device_manager.get_stats(),
        "proxy_stats": proxy_manager.get_stats(),
        "speed_stats": speed_checker.get_status()
    })

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
        "error": "Endpoint not found"
    }), 404

app.debug = False
