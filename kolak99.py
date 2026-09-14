#!/usr/bin/env python3
# KOLAK99 - Email OSINT + Basic Stress Tester (Educational)
# Usage: python3 kolak99.py

import requests
import json
import threading
import time
import random
import sys
from concurrent.futures import ThreadPoolExecutor

# ============ CONFIG ============
BANNER = """
\033[91m
██╗  ██╗ ██████╗ ██╗      █████╗ ██╗  ██╗ ██████╗  ██████╗ 
██║ ██╔╝██╔═══██╗██║     ██╔══██╗██║ ██╔╝██╔═══██╗██╔════╝ 
█████╔╝ ██║   ██║██║     ███████║█████╔╝ ██║   ██║███████╗ 
██╔═██╗ ██║   ██║██║     ██╔══██║██╔═██╗ ██║   ██║██╔═══██╗
██║  ██╗╚██████╔╝███████╗██║  ██║██║  ██╗╚██████╔╝╚██████╔╝
╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝  ╚═════╝ 
\033[0m
\033[93m[ KOLAK99 - Email OSINT & Stress Tester ]\033[0m
\033[90m[ Educational Purpose Only ]\033[0m
"""

# ============ EMAIL OSINT MODULE ============
class EmailOSINT:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36'
        })
    
    def check_gravatar(self, email):
        """Check Gravatar profile"""
        import hashlib
        email_hash = hashlib.md5(email.lower().strip().encode()).hexdigest()
        url = f"https://www.gravatar.com/{email_hash}.json"
        try:
            r = self.session.get(url, timeout=5)
            if r.status_code == 200:
                data = r.json()
                entry = data.get('entry', [{}])[0]
                return {
                    'found': True,
                    'name': entry.get('displayName', 'N/A'),
                    'username': entry.get('preferredUsername', 'N/A'),
                    'location': entry.get('currentLocation', 'N/A'),
                    'profile_url': entry.get('profileUrl', 'N/A')
                }
        except:
            pass
        return {'found': False}
    
    def check_haveibeenpwned(self, email):
        """Check breach data (public API)"""
        url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
        headers = {'User-Agent': 'KOLAK99-OSINT'}
        try:
            r = self.session.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                breaches = r.json()
                return {
                    'found': True,
                    'breaches': [b['Name'] for b in breaches],
                    'count': len(breaches)
                }
            elif r.status_code == 404:
                return {'found': False, 'breaches': [], 'count': 0}
        except:
            pass
        return {'found': False, 'breaches': [], 'count': 0}
    
    def check_social_platforms(self, email):
        """Check common platforms (simulated responses)"""
        platforms = {
            'Twitter/X': 'https://api.twitter.com/i/users/email_available.json',
            'GitHub': 'https://api.github.com/search/users',
            'Pinterest': 'https://www.pinterest.com/resource/UserResource/get/',
            'Spotify': 'https://www.spotify.com/api/signup/validate',
            'Duolingo': 'https://www.duolingo.com/2017-06-30/users',
            'Imgur': 'https://imgur.com/signin/ajax_email_available',
            'Pastebin': 'https://pastebin.com/signup',
            'Trello': 'https://trello.com/1/Members/email',
            'Flickr': 'https://www.flickr.com/services/rest/',
            'WordPress': 'https://public-api.wordpress.com/rest/v1.1/users/email'
        }
        results = {}
        for platform, url in platforms.items():
            try:
                # Simulated check - in real scenario, different endpoints
                r = self.session.post(url, json={'email': email}, timeout=5)
                results[platform] = r.status_code
            except:
                results[platform] = 'timeout'
        return results
    
    def full_scan(self, email):
        """Run full OSINT scan"""
        print(f"\n\033[96m[+] Scanning: {email}\033[0m")
        print("=" * 50)
        
        # Gravatar
        gravatar = self.check_gravatar(email)
        if gravatar['found']:
            print(f"\033[92m[✓] Gravatar Found!\033[0m")
            print(f"    Name: {gravatar['name']}")
            print(f"    Username: {gravatar['username']}")
            print(f"    Location: {gravatar['location']}")
            print(f"    Profile: {gravatar['profile_url']}")
        else:
            print("\033[90m[✗] No Gravatar\033[0m")
        
        # HaveIBeenPwned
        hibp = self.check_haveibeenpwned(email)
        if hibp['found']:
            print(f"\n\033[91m[!] BREACHED! Found in {hibp['count']} breaches:\033[0m")
            for breach in hibp['breaches']:
                print(f"    - {breach}")
        else:
            print("\n\033[92m[✓] No known breaches\033[0m")
        
        # Social platforms
        print("\n\033[96m[+] Checking platform registrations...\033[0m")
        social = self.check_social_platforms(email)
        for platform, status in social.items():
            if status == 200:
                print(f"\033[92m[✓] {platform}: Registered\033[0m")
            elif status == 404:
                print(f"\033[90m[✗] {platform}: Not registered\033[0m")
            else:
                print(f"\033[93m[?] {platform}: Unknown (status {status})\033[0m")

# ============ STRESS TESTER MODULE ============
class StressTester:
    def __init__(self):
        self.running = False
        self.request_count = 0
        self.lock = threading.Lock()
    
    def send_request(self, url, method='GET', headers=None, data=None):
        """Send single request"""
        try:
            if method.upper() == 'GET':
                r = requests.get(url, headers=headers, timeout=3)
            elif method.upper() == 'POST':
                r = requests.post(url, headers=headers, data=data, timeout=3)
            else:
                r = requests.request(method, url, headers=headers, data=data, timeout=3)
            
            with self.lock:
                self.request_count += 1
            return r.status_code
        except:
            return None
    
    def flood(self, url, threads=50, duration=30, method='GET'):
        """Flood target with requests (for testing YOUR OWN server)"""
        self.running = True
        self.request_count
