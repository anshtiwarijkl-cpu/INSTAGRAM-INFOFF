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
import traceback
from datetime import datetime
from instaloader import Instaloader, Profile

app = Flask(__name__)
CORS(app)

# Allow all origins
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# ============================================================================
# DEVICE FINGERPRINT
# ============================================================================

class UltimateDeviceFingerprint:
    def __init__(self):
        self.fingerprint = {}
        self.generation_count = 0
        self.rotation_counter = 0
        self.rotation_interval = 3
        self._generate_fingerprint()
    
    def _generate_fingerprint(self):
        self.generation_count += 1
        self.rotation_counter += 1
        system = platform.system()
        
        browsers = [
            {
                'name': 'Chrome',
                'version': f"{random.randint(110, 122)}.0.{random.randint(6000, 7000)}.{random.randint(0, 200)}",
                'user_agent': f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(110, 122)}.0.0.0 Safari/537.36"
            },
            {
                'name': 'Chrome',
                'version': f"{random.randint(110, 122)}.0.{random.randint(6000, 7000)}.{random.randint(0, 200)}",
                'user_agent': f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_{random.randint(14, 15)}_{random.randint(0, 4)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(110, 122)}.0.0.0 Safari/537.36"
            },
            {
                'name': 'Firefox', 
                'version': f"{random.randint(115, 124)}.0",
                'user_agent': f"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{random.randint(115, 124)}.0) Gecko/20100101 Firefox/{random.randint(115, 124)}.0"
            },
            {
                'name': 'Firefox',
                'version': f"{random.randint(115, 124)}.0",
                'user_agent': f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_{random.randint(14, 15)}_{random.randint(0, 4)}; rv:{random.randint(115, 124)}.0) Gecko/20100101 Firefox/{random.randint(115, 124)}.0"
            },
            {
                'name': 'Edge',
                'version': f"{random.randint(110, 122)}.0.{random.randint(2000, 3000)}.{random.randint(0, 200)}",
                'user_agent': f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(110, 122)}.0.0.0 Safari/537.36 Edg/{random.randint(110, 122)}.0.0.0"
            },
            {
                'name': 'Safari',
                'version': f"{random.randint(16, 17)}.{random.randint(0, 1)}",
                'user_agent': f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_{random.randint(14, 15)}_{random.randint(0, 4)}) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{random.randint(16, 17)}.0 Safari/605.1.15"
            },
        ]
        
        browser = random.choice(browsers)
        screens = [
            (1920, 1080), (2560, 1440), (3840, 2160),
            (1366, 768), (1536, 864), (1440, 900),
            (1600, 900), (1280, 720), (1920, 1200),
            (2560, 1600), (3440, 1440), (1360, 768),
            (1280, 800), (1440, 810), (1680, 1050),
            (1024, 768), (1280, 1024), (1360, 768)
        ]
        width, height = random.choice(screens)
        
        languages = ['en-US', 'en-GB', 'en-IN', 'en-AU', 'en-CA', 
                    'es-ES', 'fr-FR', 'de-DE', 'it-IT', 'pt-BR',
                    'ja-JP', 'ko-KR', 'zh-CN', 'ru-RU', 'ar-SA',
                    'nl-NL', 'sv-SE', 'no-NO', 'da-DK', 'fi-FI']
        
        timezones = ['America/New_York', 'America/Los_Angeles', 'Europe/London', 
                    'Europe/Paris', 'Asia/Kolkata', 'Asia/Tokyo', 'Australia/Sydney',
                    'America/Sao_Paulo', 'Africa/Johannesburg', 'Asia/Dubai',
                    'America/Chicago', 'America/Toronto', 'Europe/Berlin',
                    'Asia/Singapore', 'Asia/Shanghai', 'America/Mexico_City']
        
        fonts = [
            'Arial, Helvetica, sans-serif',
            'Times New Roman, Times, serif',
            'Courier New, Courier, monospace',
            'Georgia, serif',
            'Verdana, Arial, sans-serif',
            'Tahoma, Arial, sans-serif',
            'Trebuchet MS, Arial, sans-serif',
            'Palatino Linotype, Book Antiqua, Palatino, serif',
            'Lucida Grande, Lucida Sans Unicode, Arial, sans-serif',
            'Helvetica Neue, Arial, sans-serif'
        ]
        
        self.fingerprint = {
            'browser': browser,
            'screen': {
                'width': width,
                'height': height,
                'color_depth': random.choice([24, 30, 32]),
                'pixel_ratio': round(random.uniform(1, 3), 1)
            },
            'language': random.choice(languages),
            'timezone': random.choice(timezones),
            'platform': system,
            'platform_version': platform.version(),
            'cpu_cores': random.choice([2, 4, 6, 8, 10, 12, 16, 20, 24, 32]),
            'memory': random.choice(['4 GB', '8 GB', '16 GB', '32 GB', '64 GB', '128 GB', '256 GB']),
            'gpu': random.choice([
                'NVIDIA GeForce RTX 3060', 'NVIDIA GeForce RTX 3070', 'NVIDIA GeForce RTX 3080',
                'NVIDIA GeForce RTX 3090', 'NVIDIA GeForce RTX 4060', 'NVIDIA GeForce RTX 4070',
                'NVIDIA GeForce RTX 4080', 'NVIDIA GeForce RTX 4090', 'AMD Radeon RX 6800 XT',
                'AMD Radeon RX 6900 XT', 'AMD Radeon RX 7800 XT', 'AMD Radeon RX 7900 XTX',
                'Intel Iris Xe Graphics', 'Intel UHD Graphics 620', 'Apple M1 GPU',
                'Apple M2 GPU', 'Apple M3 GPU', 'Apple M3 Pro GPU', 'Apple M3 Max GPU'
            ]),
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
            'fingerprint_id': hashlib.md5(str(time.time() + random.random()).encode()).hexdigest(),
            'generated_at': datetime.now().isoformat(),
            'generation': self.generation_count
        }
    
    def get_fingerprint(self):
        return self.fingerprint
    
    def get_headers(self):
        return {
            'User-Agent': self.fingerprint['browser']['user_agent'],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': f"{self.fingerprint['language']},en;q=0.9",
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
            'Sec-GPC': '1',
            'Referer': 'https://www.google.com/',
            'Sec-Ch-Ua': f'"{self.fingerprint["browser"]["name"]}"; v="{self.fingerprint["browser"]["version"].split(".")[0]}"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': f'"{self.fingerprint["platform"]}"'
        }
    
    def rotate(self):
        self._generate_fingerprint()
        return self.fingerprint
    
    def should_rotate(self):
        return self.rotation_counter >= self.rotation_interval

# ============================================================================
# INSTAGRAM SCANNER - COMPLETE
# ============================================================================

class InstagramScanner:
    def __init__(self):
        self.fingerprint = UltimateDeviceFingerprint()
        self.loader = None
    
    def initialize_loader(self):
        try:
            fp = self.fingerprint.get_fingerprint()
            user_agent = fp['browser']['user_agent']
            
            self.loader = Instaloader(
                max_connection_attempts=5,
                request_timeout=45,
                user_agent=user_agent,
                sleep=True,
                quiet=True
            )
            
            if hasattr(self.loader, 'context') and hasattr(self.loader.context, '_session'):
                headers = self.fingerprint.get_headers()
                for key, value in headers.items():
                    self.loader.context._session.headers.update({key: value})
            
            return True
            
        except Exception as e:
            return False
    
    def estimate_account_creation_year(self, user_id):
        id_ranges = [
            (1, 2010), (100000, 2011), (1000000, 2011), (10000000, 2012),
            (50000000, 2013), (100000000, 2014), (300000000, 2015),
            (500000000, 2016), (1000000000, 2017), (3000000000, 2018),
            (5000000000, 2019), (8000000000, 2020), (12000000000, 2021),
            (18000000000, 2022), (25000000000, 2023), (35000000000, 2024),
            (45000000000, 2025),
        ]
        
        try:
            uid = int(user_id)
        except:
            return None
        
        for max_id, year in id_ranges:
            if uid <= max_id:
                return year
        
        if uid > 45000000000:
            return 2025 + (uid - 45000000000) // 5000000000
        
        return None
    
    def scan_profile(self, username):
        start_time = time.time()
        result = {}
        
        try:
            if not self.initialize_loader():
                result['error'] = 'Failed to initialize Instagram loader'
                return result
            
            profile = Profile.from_username(self.loader.context, username)
            
            response_time = (time.time() - start_time) * 1000
            
            estimated_year = self.estimate_account_creation_year(profile.userid)
            
            # ALL DATA EXTRACTION
            username_val = profile.username
            user_id = profile.userid
            full_name = profile.full_name
            biography = profile.biography
            
            try:
                business_category = profile.business_category_name
            except:
                business_category = None
            
            try:
                is_business = profile.is_business_account
            except:
                is_business = False
            
            try:
                is_professional = getattr(profile, 'is_professional_account', False)
            except:
                is_professional = False
            
            try:
                category = getattr(profile, 'category_name', None)
                if category == '':
                    category = None
            except:
                category = None
            
            followers = profile.followers
            following = profile.followees
            post_count = profile.mediacount
            
            try:
                igtv_count = profile.igtv_count
            except:
                igtv_count = 0
            
            is_private = profile.is_private
            is_verified = profile.is_verified
            
            try:
                has_highlights = profile.has_highlight_reels
            except:
                has_highlights = False
            
            highlight_count = getattr(profile, 'highlight_reel_count', 0)
            
            external_url = profile.external_url
            
            profile_pic_hd = None
            profile_pic = None
            try:
                profile_pic_hd = getattr(profile, 'profile_pic_url_hd', None)
                if not profile_pic_hd:
                    profile_pic_hd = profile.profile_pic_url
                profile_pic = profile.profile_pic_url
            except:
                profile_pic_hd = None
                profile_pic = None
            
            bio_links = []
            try:
                if hasattr(profile, 'biography_links'):
                    for link in profile.biography_links:
                        if isinstance(link, dict) and 'url' in link:
                            bio_links.append(link['url'])
                        elif isinstance(link, str):
                            bio_links.append(link)
            except:
                bio_links = []
            
            try:
                is_joined_recently = getattr(profile, 'is_joined_recently', False)
            except:
                is_joined_recently = False
            
            result = {
                "status": "ok",
                "collected_at": datetime.now().isoformat(),
                "response_time_seconds": round(response_time / 1000, 3),
                "profile": {
                    "username": username_val,
                    "user_id": str(user_id),
                    "full_name": full_name,
                    "biography": biography[:500] if biography else 'No bio available',
                    "business_category": business_category,
                    "is_business_account": is_business,
                    "is_professional_account": is_professional,
                    "category_name": category,
                    "followers": followers,
                    "following": following,
                    "posts": post_count,
                    "igtv_count": igtv_count,
                    "is_private": is_private,
                    "is_verified": is_verified,
                    "has_highlights": has_highlights or highlight_count > 0,
                    "external_url": external_url,
                    "profile_pic_url": profile_pic,
                    "profile_pic_url_hd": profile_pic_hd,
                    "bio_links": bio_links,
                    "account_creation_year": estimated_year,
                    "is_joined_recently": is_joined_recently,
                }
            }
            
            return result
            
        except instaloader.exceptions.ProfileNotExistsException:
            return {
                "status": "error",
                "error": "Profile does not exist",
                "username": username
            }
        except instaloader.exceptions.PrivateProfileNotFollowedException:
            return {
                "status": "error",
                "error": "Private profile cannot be accessed",
                "username": username
            }
        except instaloader.exceptions.QueryReturnedBadRequestException:
            return {
                "status": "error",
                "error": "Instagram API rate limit or request error",
                "username": username
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "username": username
            }

# ============================================================================
# API ROUTES
# ============================================================================

scanner = InstagramScanner()

@app.route('/')
def home():
    return jsonify({
        "name": "Instagram Scanner API",
        "version": "2.0.0",
        "status": "running",
        "time": datetime.now().isoformat(),
        "endpoints": {
            "/health": "GET - Health check",
            "/api/scan?username=NAME": "GET - Scan profile",
            "/api/scan/NAME": "GET - Scan profile"
        },
        "fields_returned": [
            "username", "user_id", "full_name", "biography",
            "business_category", "is_business_account", "is_professional_account",
            "category_name", "followers", "following", "posts",
            "igtv_count", "is_private", "is_verified", "has_highlights",
            "external_url", "profile_pic_url", "profile_pic_url_hd",
            "bio_links", "account_creation_year", "is_joined_recently"
        ]
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat()
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

# Vercel requires this
app.debug = False
