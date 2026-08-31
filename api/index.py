"""
Instagram Scanner API - Vercel Serverless Deployment
Supports GET request with scan=username parameter
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import instaloader
import time
import json
import random
import hashlib
import requests
import uuid
import os
import re
from datetime import datetime
from instaloader import Instaloader, Profile
import traceback
from requests.auth import HTTPProxyAuth
from contextlib import asynccontextmanager
import asyncio
from threading import Lock

# ============================================================================
# PROXY LIST WITH AUTHENTICATION - UPDATED WITH ALL 6 PROXIES
# ============================================================================

# ============================================================================
# PROXY LIST WITH AUTHENTICATION - UPDATED WITH 10 PROXIES
# ============================================================================

PROXY_LIST = [
 
    {"ip": "103.125.17.106", "port": "8080", "username": "", "password": "", "country": "ID", "city": "Jakarta"},
    {"ip": "123.138.24.112", "port": "8800", "username": "", "password": "", "country": "CN", "city": "Beijing"},
    {"ip": "176.12.72.62", "port": "3128", "username": "", "password": "", "country": "KZ", "city": "Almaty"},
    {"ip": "5.129.214.191", "port": "8080", "username": "", "password": "", "country": "NL", "city": "Amsterdam"},
    {"ip": "186.227.196.104", "port": "3128", "username": "", "password": "", "country": "BR", "city": "Sao Paulo"},
    {"ip": "103.54.119.5", "port": "8000", "username": "", "password": "", "country": "HK", "city": "Hong Kong"},
    {"ip": "185.140.232.54", "port": "8080", "username": "", "password": "", "country": "IR", "city": "Tehran"},
    {"ip": "65.109.186.67", "port": "10808", "username": "", "password": "", "country": "FI", "city": "Helsinki"},
    {"ip": "145.220.226.216", "port": "8080", "username": "", "password": "", "country": "DE", "city": "Berlin"},
]

# ============================================================================
# COUNTRY TO LANGUAGE MAPPING - UPDATED WITH NEW COUNTRIES
# ============================================================================

COUNTRY_LANGUAGE = {
    'US': 'en-US', 'GB': 'en-GB', 'IN': 'en-IN', 'AU': 'en-AU', 'CA': 'en-CA',
    'DE': 'de-DE', 'FR': 'fr-FR', 'ES': 'es-ES', 'IT': 'it-IT', 'JP': 'ja-JP',
    'CN': 'zh-CN', 'KR': 'ko-KR', 'BR': 'pt-BR', 'RU': 'ru-RU', 'NL': 'nl-NL',
    'SE': 'sv-SE', 'NO': 'no-NO', 'DK': 'da-DK', 'FI': 'fi-FI', 'PL': 'pl-PL',
    'TR': 'tr-TR', 'AR': 'ar-SA', 'IL': 'he-IL', 'ZA': 'en-ZA', 'NZ': 'en-NZ',
    'SG': 'en-SG', 'MY': 'en-MY', 'PH': 'en-PH', 'PK': 'en-PK', 'BD': 'en-BD',
    'EG': 'ar-EG', 'SA': 'ar-SA', 'AE': 'ar-AE', 'KW': 'ar-KW', 'QA': 'ar-QA',
    'OM': 'ar-OM', 'BH': 'ar-BH', 'ID': 'id-ID', 'KZ': 'kk-KZ', 'HK': 'zh-HK',
    'IR': 'fa-IR',
}
# ============================================================================
# COUNTRY TO LANGUAGE MAPPING - UPDATED
# ============================================================================

COUNTRY_LANGUAGE = {
    'US': 'en-US', 'GB': 'en-GB', 'IN': 'en-IN', 'AU': 'en-AU', 'CA': 'en-CA',
    'DE': 'de-DE', 'FR': 'fr-FR', 'ES': 'es-ES', 'IT': 'it-IT', 'JP': 'ja-JP',
    'CN': 'zh-CN', 'KR': 'ko-KR', 'BR': 'pt-BR', 'RU': 'ru-RU', 'NL': 'nl-NL',
    'SE': 'sv-SE', 'NO': 'no-NO', 'DK': 'da-DK', 'FI': 'fi-FI', 'PL': 'pl-PL',
    'TR': 'tr-TR', 'AR': 'ar-SA', 'IL': 'he-IL', 'ZA': 'en-ZA', 'NZ': 'en-NZ',
    'SG': 'en-SG', 'MY': 'en-MY', 'PH': 'en-PH', 'PK': 'en-PK', 'BD': 'en-BD',
    'EG': 'ar-EG', 'SA': 'ar-SA', 'AE': 'ar-AE', 'KW': 'ar-KW', 'QA': 'ar-QA',
    'OM': 'ar-OM', 'BH': 'ar-BH',
}

# ============================================================================
# PYDANTIC MODELS FOR API
# ============================================================================

class ScanRequest(BaseModel):
    username: str = Field(..., description="Instagram username to scan")
    country_code: Optional[str] = Field("US", description="Country code for language preferences")
    use_proxy: Optional[bool] = Field(True, description="Use proxy for scanning")

class ScanResponse(BaseModel):
    status: str
    collected_at: str
    response_time_seconds: float
    profile: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    proxy_used: Optional[Dict[str, str]] = None

# ============================================================================
# FINGERPRINT GENERATOR
# ============================================================================

class Fingerprint:
    def __init__(self):
        self.fingerprint = {}
        self.counter = 0
        self._generate()
    
    def _generate_browser(self):
        browsers = [
            {
                'name': 'Chrome',
                'versions': ['120.0.6099.109', '120.0.6099.129', '120.0.6099.199', 
                            '121.0.6167.85', '121.0.6167.160', '122.0.6261.69',
                            '123.0.6312.58', '123.0.6312.86', '124.0.6367.91'],
                'user_agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36"
            },
            {
                'name': 'Chrome',
                'versions': ['120.0.6099.109', '121.0.6167.85', '122.0.6261.69'],
                'user_agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36"
            },
            {
                'name': 'Firefox',
                'versions': ['121.0', '122.0', '123.0', '124.0', '125.0'],
                'user_agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{version}.0) Gecko/20100101 Firefox/{version}.0"
            },
            {
                'name': 'Firefox',
                'versions': ['121.0', '122.0', '123.0', '124.0', '125.0'],
                'user_agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7; rv:{version}.0) Gecko/20100101 Firefox/{version}.0"
            },
            {
                'name': 'Edge',
                'versions': ['120.0.2210.91', '120.0.2210.133', '121.0.2277.128'],
                'user_agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/{version}"
            },
        ]
        browser = random.choice(browsers)
        version = random.choice(browser['versions'])
        ua = browser['user_agent'].replace('{version}', version)
        return {
            'name': browser['name'],
            'version': version,
            'user_agent': ua
        }
    
    def _generate_screen(self):
        screens = [
            (1920, 1080), (2560, 1440), (3840, 2160),
            (1366, 768), (1536, 864), (1440, 900),
            (1600, 900), (1280, 720), (1920, 1200),
        ]
        width, height = random.choice(screens)
        return {
            'width': width,
            'height': height,
            'color_depth': random.choice([24, 30, 32]),
        }
    
    def _generate_os(self):
        os_list = [
            {'name': 'Windows', 'version': '10.0'},
            {'name': 'Windows', 'version': '11.0'},
            {'name': 'macOS', 'version': '10.15.7'},
            {'name': 'macOS', 'version': '11.0.1'},
            {'name': 'macOS', 'version': '12.0.1'},
            {'name': 'macOS', 'version': '13.0'},
            {'name': 'macOS', 'version': '14.0'},
        ]
        return random.choice(os_list)
    
    def _get_language_for_country(self, country_code):
        return COUNTRY_LANGUAGE.get(country_code, 'en-US')
    
    def _generate(self, country_code='US'):
        self.counter += 1
        browser = self._generate_browser()
        screen = self._generate_screen()
        os_info = self._generate_os()
        language = self._get_language_for_country(country_code)
        delay_between_requests = random.uniform(3.0, 8.0)
        
        self.fingerprint = {
            'browser': browser,
            'screen': screen,
            'os': os_info,
            'language': language,
            'country': country_code,
            'fingerprint_id': hashlib.md5(str(time.time() + random.random()).encode()).hexdigest()[:16],
            'session_id': str(uuid.uuid4())[:8],
            'generation': self.counter,
            'delay_between_requests': delay_between_requests,
        }
    
    def get(self):
        return self.fingerprint
    
    def rotate(self, country_code='US'):
        self._generate(country_code)
        return self.fingerprint
    
    def get_headers(self):
        fp = self.fingerprint
        headers = {
            'User-Agent': fp['browser']['user_agent'],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': f"{fp['language']},en;q=0.9",
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
        }
        if fp['browser']['name'] in ['Chrome', 'Edge']:
            headers['Sec-Ch-Ua'] = f'"{fp["browser"]["name"]}"; v="{fp["browser"]["version"].split(".")[0]}"'
            headers['Sec-Ch-Ua-Mobile'] = '?0'
            headers['Sec-Ch-Ua-Platform'] = f'"{fp["os"]["name"]}"'
        return headers
    
    def get_random_delay(self):
        return self.fingerprint['delay_between_requests']


# ============================================================================
# PROXY MANAGER WITH AUTHENTICATION
# ============================================================================

class ProxyManager:
    def __init__(self, proxy_list):
        self.all_proxies = proxy_list
        self.working_proxies = []
        self.failed_proxies = []
        self.current_index = 0
        self.request_count = 0
        self.lock = Lock()
        self._test_all_proxies()
    
    def _test_proxy(self, proxy):
        try:
            proxy_url = f"http://{proxy['ip']}:{proxy['port']}"
            proxies = {"http": proxy_url, "https": proxy_url}
            
            # Test without auth (since these proxies don't need authentication)
            response = requests.get(
                "https://api.ipify.org?format=json",
                proxies=proxies,
                timeout=10,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            return response.status_code == 200
        except:
            return False
    
    def _test_all_proxies(self):
        """Test all proxies and update working/failed lists"""
        self.working_proxies = []
        self.failed_proxies = []
        
        print(f"🔍 Testing {len(self.all_proxies)} proxies...")
        
        for proxy in self.all_proxies:
            if self._test_proxy(proxy):
                self.working_proxies.append(proxy)
                print(f"  ✅ {proxy['ip']}:{proxy['port']} - WORKING")
            else:
                self.failed_proxies.append(proxy)
                print(f"  ❌ {proxy['ip']}:{proxy['port']} - FAILED")
            time.sleep(0.3)
        
        # If no working proxies, use all proxies anyway
        if not self.working_proxies:
            print("⚠️ No working proxies! Using all proxies anyway...")
            self.working_proxies = self.all_proxies.copy()
            self.failed_proxies = []
        
        print(f"✅ Working: {len(self.working_proxies)}, Failed: {len(self.failed_proxies)}")
    
    def get_proxy(self):
        with self.lock:
            if not self.working_proxies:
                return None
            self.request_count += 1
            self.current_index = (self.current_index + 1) % len(self.working_proxies)
            return self.working_proxies[self.current_index]
    
    def get_proxy_with_auth(self):
        proxy = self.get_proxy()
        if not proxy:
            return None, None, None, None
        proxy_url = f"http://{proxy['ip']}:{proxy['port']}"
        # No authentication needed for these proxies
        username = proxy.get('username', '')
        password = proxy.get('password', '')
        return proxy_url, username, password, proxy.get('country', 'US')
    
    def get_current_proxy(self):
        with self.lock:
            if not self.working_proxies:
                return None
            if self.current_index >= len(self.working_proxies):
                self.current_index = 0
            return self.working_proxies[self.current_index]
    
    def mark_failed(self, proxy):
        with self.lock:
            if proxy in self.working_proxies:
                self.working_proxies.remove(proxy)
                self.failed_proxies.append(proxy)
                print(f"⚠️ Removed {proxy['ip']}:{proxy['port']} from working proxies")
                if self.current_index >= len(self.working_proxies):
                    self.current_index = 0
    
    def get_stats(self):
        """Return proxy statistics"""
        return {
            "total": len(self.all_proxies),
            "working": len(self.working_proxies),
            "failed": len(self.failed_proxies)
        }

# ============================================================================
# INSTAGRAM SCANNER - VERCELL VERSION
# ============================================================================

class InstagramScannerVercel:
    def __init__(self):
        self.fingerprint = Fingerprint()
        self.proxy_manager = ProxyManager(PROXY_LIST)
        self.loader = None
        self.request_counter = 0
        self.success_count = 0
        self.fail_count = 0
        self.last_request_time = 0
        self.session_cookies = {}
        self.start_time = time.time()
        self.lock = Lock()
    
    def _wait_between_requests(self):
        with self.lock:
            now = time.time()
            delay = self.fingerprint.get_random_delay()
            elapsed = now - self.last_request_time
            if elapsed < delay:
                sleep_time = delay - elapsed + random.uniform(0.5, 2.0)
                time.sleep(sleep_time)
            self.last_request_time = time.time()
    
    def _create_session(self, country_code='US'):
        try:
            fp = self.fingerprint.rotate(country_code)
            proxy_url, username, password, proxy_country = self.proxy_manager.get_proxy_with_auth()
            proxy_info = self.proxy_manager.get_current_proxy()
            
            session = requests.Session()
            if proxy_url:
                session.proxies.update({
                    "http": proxy_url,
                    "https": proxy_url
                })
                # Only set auth if username and password are provided
                if username and password:
                    session.auth = HTTPProxyAuth(username, password)
            
            headers = self.fingerprint.get_headers()
            for key, value in headers.items():
                session.headers.update({key: value})
            
            session.headers.update({
                'Origin': 'https://www.instagram.com',
                'Referer': 'https://www.instagram.com/',
            })
            
            if self.session_cookies:
                session.cookies.update(self.session_cookies)
            
            self.loader = Instaloader(
                max_connection_attempts=3,
                request_timeout=60,
                sleep=True,
                quiet=True,
                user_agent=fp['browser']['user_agent']
            )
            self.loader.context._session = session
            time.sleep(random.uniform(0.5, 1.5))
            return True, fp, proxy_info
        except Exception as e:
            return False, None, None
    
    def _estimate_year(self, user_id):
        try:
            uid = int(user_id)
            ranges = [
                (1, 2010), (100000, 2011), (1000000, 2011), (10000000, 2012),
                (50000000, 2013), (100000000, 2014), (300000000, 2015),
                (500000000, 2016), (1000000000, 2017), (3000000000, 2018),
                (5000000000, 2019), (8000000000, 2020), (12000000000, 2021),
                (18000000000, 2022), (25000000000, 2023), (35000000000, 2024),
                (45000000000, 2025),
            ]
            for max_id, year in ranges:
                if uid <= max_id:
                    return year
            return None
        except:
            return None
    
    def scan(self, username, country_code='US', use_proxy=True):
        start_time = time.time()
        proxy_info = None
        
        try:
            with self.lock:
                self.request_counter += 1
                self._wait_between_requests()
            
            if use_proxy:
                proxy_url, username_proxy, password_proxy, country_code = self.proxy_manager.get_proxy_with_auth()
                proxy_info = self.proxy_manager.get_current_proxy()
            
            if not proxy_url:
                country_code = 'US'
            
            success, fp, proxy_info = self._create_session(country_code)
            if not success:
                with self.lock:
                    self.fail_count += 1
                return {
                    "status": "error",
                    "error": "Failed to create session",
                    "collected_at": datetime.now().isoformat()
                }
            
            profile = None
            max_retries = 2
            
            for attempt in range(max_retries):
                try:
                    if attempt > 0:
                        success, fp, proxy_info = self._create_session(country_code)
                        if not success:
                            continue
                    profile = Profile.from_username(self.loader.context, username)
                    break
                except instaloader.exceptions.LoginRequiredException:
                    time.sleep(random.uniform(3, 5))
                    continue
                except Exception as e:
                    if attempt < max_retries - 1:
                        time.sleep(random.uniform(5, 8))
                        continue
                    else:
                        raise e
            
            if profile is None:
                raise Exception("Could not fetch profile")
            
            is_business = getattr(profile, 'is_business_account', False)
            is_professional = getattr(profile, 'is_professional_account', False)
            category = getattr(profile, 'category_name', None)
            business_category = getattr(profile, 'business_category_name', None)
            highlight_count = getattr(profile, 'highlight_reel_count', 0)
            has_highlights = getattr(profile, 'has_highlight_reels', False)
            is_joined_recently = getattr(profile, 'is_joined_recently', False)
            
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
            
            response_time = (time.time() - start_time)
            
            result = {
                "status": "ok",
                "collected_at": datetime.now().isoformat(),
                "response_time_seconds": round(response_time, 3),
                "proxy_used": {
                    "ip": proxy_info['ip'] if proxy_info else None,
                    "port": proxy_info['port'] if proxy_info else None,
                    "country": proxy_info.get('country', 'Unknown') if proxy_info else None
                } if proxy_info else None,
                "profile": {
                    "id": str(profile.userid),
                    "username": profile.username,
                    "full_name": profile.full_name or 'N/A',
                    "biography": (profile.biography[:200] if profile.biography else 'No bio available'),
                    "is_private": profile.is_private,
                    "is_verified": profile.is_verified,
                    "is_business_account": is_business,
                    "is_professional_account": is_professional,
                    "category_name": category,
                    "business_category_name": business_category,
                    "profile_pic_url_hd": getattr(profile, 'profile_pic_url_hd', None) or getattr(profile, 'profile_pic_url', None),
                    "external_url": profile.external_url or None,
                    "followers": profile.followers,
                    "following": profile.followees,
                    "posts": profile.mediacount,
                    "account_creation_year": self._estimate_year(profile.userid),
                    "has_highlights": has_highlights or highlight_count > 0,
                    "is_joined_recently": is_joined_recently,
                    "bio_links": bio_links
                }
            }
            
            with self.lock:
                self.success_count += 1
            
            if hasattr(self.loader.context, '_session'):
                with self.lock:
                    self.session_cookies = self.loader.context._session.cookies.get_dict()
            
            return result
            
        except instaloader.exceptions.ProfileNotExistsException:
            with self.lock:
                self.fail_count += 1
            return {
                "status": "error",
                "error": f"Profile @{username} does not exist",
                "collected_at": datetime.now().isoformat()
            }
        except instaloader.exceptions.PrivateProfileNotFollowedException:
            with self.lock:
                self.fail_count += 1
            return {
                "status": "error",
                "error": f"Profile @{username} is private",
                "collected_at": datetime.now().isoformat()
            }
        except instaloader.exceptions.LoginRequiredException:
            with self.lock:
                self.fail_count += 1
            if proxy_info:
                self.proxy_manager.mark_failed(proxy_info)
            return {
                "status": "error",
                "error": "Login required",
                "collected_at": datetime.now().isoformat()
            }
        except instaloader.exceptions.ConnectionException as e:
            with self.lock:
                self.fail_count += 1
            return {
                "status": "error",
                "error": f"Connection error: {str(e)[:100]}",
                "collected_at": datetime.now().isoformat()
            }
        except Exception as e:
            error_str = str(e)
            if any(x in error_str.lower() for x in ['401', '403', '429', 'rate', 'wait', 'block']):
                with self.lock:
                    self.fail_count += 1
                if proxy_info:
                    self.proxy_manager.mark_failed(proxy_info)
                return {
                    "status": "error",
                    "error": f"Rate limited: {error_str[:100]}",
                    "collected_at": datetime.now().isoformat()
                }
            else:
                with self.lock:
                    self.fail_count += 1
                return {
                    "status": "error",
                    "error": f"Error: {error_str[:100]}",
                    "collected_at": datetime.now().isoformat()
                }
    
    def get_stats(self):
        total = self.success_count + self.fail_count
        return {
            "requests": self.request_counter,
            "success": self.success_count,
            "fail": self.fail_count,
            "success_rate": round((self.success_count / total * 100) if total > 0 else 0, 1),
            "proxy_stats": self.proxy_manager.get_stats()
        }
    
    def get_uptime(self):
        return time.time() - self.start_time


# ============================================================================
# FASTAPI APPLICATION FOR VERCEL
# ============================================================================

# Global scanner instance (will be initialized on first request)
scanner = None

def get_scanner():
    global scanner
    if scanner is None:
        scanner = InstagramScannerVercel()
    return scanner

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - initialize scanner
    get_scanner()
    print("✅ Instagram Scanner API initialized for Vercel")
    yield
    # Shutdown
    print("👋 Shutting down...")

app = FastAPI(
    title="Instagram Scanner API",
    description="API for scanning Instagram profiles with proxy rotation and fingerprint management",
    version="1.0.0",
    lifespan=lifespan
)

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    return {
        "message": "Instagram Scanner API",
        "version": "1.0.0",
        "deployment": "Vercel",
        "endpoints": {
            "/scan": "GET - Scan Instagram profile (URL param: ?username=xyz)",
            "/scan": "POST - Scan Instagram profile (JSON body)",
            "/health": "GET - Health check",
            "/stats": "GET - Scanner statistics",
            "/proxy/status": "GET - Proxy status",
            "/docs": "GET - API documentation"
        }
    }

@app.get("/health")
async def health_check():
    try:
        scanner = get_scanner()
        stats = scanner.get_stats()
        return {
            "status": "healthy",
            "version": "1.0.0",
            "uptime_seconds": round(scanner.get_uptime(), 1),
            "proxy_count": stats["proxy_stats"]["total"],
            "working_proxy_count": stats["proxy_stats"]["working"],
            "stats": {
                "requests": stats["requests"],
                "success": stats["success"],
                "fail": stats["fail"],
                "success_rate": stats["success_rate"]
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

@app.get("/stats")
async def get_stats():
    try:
        scanner = get_scanner()
        return scanner.get_stats()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

# ============================================================================
# GET REQUEST WITH scan=username PARAMETER
# ============================================================================

@app.get("/scan")
async def scan_profile_get(
    username: str = Query(..., description="Instagram username to scan"),
    country_code: str = Query("US", description="Country code for language preferences"),
    use_proxy: bool = Query(True, description="Use proxy for scanning")
):
    """
    Scan Instagram profile using GET request with query parameters.
    
    Example: https://instagram-infoff.vercel.app/scan?username=instagram
    """
    try:
        scanner = get_scanner()
        result = scanner.scan(
            username=username,
            country_code=country_code,
            use_proxy=use_proxy
        )
        
        if result.get("status") == "error":
            return JSONResponse(
                status_code=404 if "does not exist" in result.get("error", "") else 400,
                content={
                    "status": "error",
                    "collected_at": result.get("collected_at", datetime.now().isoformat()),
                    "error": result.get("error")
                }
            )
        
        return {
            "status": result.get("status", "ok"),
            "collected_at": result.get("collected_at", datetime.now().isoformat()),
            "response_time_seconds": result.get("response_time_seconds", 0),
            "profile": result.get("profile"),
            "proxy_used": result.get("proxy_used")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# POST REQUEST - JSON body
# ============================================================================

@app.post("/scan", response_model=ScanResponse)
async def scan_profile_post(request: ScanRequest):
    """
    Scan Instagram profile using POST request with JSON body.
    
    Example: 
    {
        "username": "instagram",
        "country_code": "US",
        "use_proxy": true
    }
    """
    try:
        scanner = get_scanner()
        result = scanner.scan(
            username=request.username,
            country_code=request.country_code,
            use_proxy=request.use_proxy
        )
        
        if result.get("status") == "error":
            return ScanResponse(
                status="error",
                collected_at=result.get("collected_at", datetime.now().isoformat()),
                response_time_seconds=0,
                error=result.get("error")
            )
        
        return ScanResponse(
            status=result.get("status", "ok"),
            collected_at=result.get("collected_at", datetime.now().isoformat()),
            response_time_seconds=result.get("response_time_seconds", 0),
            profile=result.get("profile"),
            proxy_used=result.get("proxy_used")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# BULK SCAN - POST Request
# ============================================================================

@app.post("/scan/bulk")
async def scan_bulk_profiles(usernames: List[str], country_code: str = "US", use_proxy: bool = True):
    """
    Scan multiple Instagram profiles using POST request.
    
    Example: ["instagram", "narendra_modi"]
    """
    try:
        scanner = get_scanner()
        if len(usernames) > 20:
            raise HTTPException(status_code=400, detail="Maximum 20 usernames per request")
        
        results = []
        for username in usernames:
            result = scanner.scan(
                username=username,
                country_code=country_code,
                use_proxy=use_proxy
            )
            results.append(result)
            await asyncio.sleep(2)
        
        return {
            "status": "completed",
            "total": len(usernames),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# PROXY ENDPOINTS
# ============================================================================

@app.get("/proxy/status")
async def proxy_status():
    try:
        scanner = get_scanner()
        return scanner.proxy_manager.get_stats()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@app.post("/proxy/refresh")
async def refresh_proxies():
    try:
        scanner = get_scanner()
        scanner.proxy_manager._test_all_proxies()
        return {
            "status": "refreshed",
            "working": len(scanner.proxy_manager.working_proxies),
            "failed": len(scanner.proxy_manager.failed_proxies)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# VERCEL SERVERLESS HANDLER
# ============================================================================

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "instagram_scanner_vercel:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        workers=1
    )
