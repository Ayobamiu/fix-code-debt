"""
Simple GitHub OAuth client that doesn't require a local server.
"""

import os
import json
import webbrowser
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path
import requests


@dataclass
class SimpleOAuthConfig:
    """Simple OAuth configuration for GitHub."""
    client_id: str
    client_secret: str
    scopes: list


class SimpleGitHubOAuthClient:
    """Simple GitHub OAuth client without local server."""
    
    def __init__(self):
        self.config = self._load_config()
        self.access_token = None
        self.user_info = None
    
    def _load_config(self) -> SimpleOAuthConfig:
        """Load OAuth configuration."""
        return SimpleOAuthConfig(
            client_id=os.getenv("GITHUB_CLIENT_ID", "demo_client_id"),
            client_secret=os.getenv("GITHUB_CLIENT_SECRET", "demo_client_secret"),
            scopes=["repo", "read:user", "write:issues"]
        )
    
    def authenticate(self) -> bool:
        """Authenticate with GitHub using device flow."""
        try:
            print("🔐 Starting GitHub OAuth authentication...")
            
            # Check if we have proper credentials
            if self.config.client_id == "demo_client_id":
                print("⚠️  Using demo credentials. For production, set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET")
                print("📖 See docs/github_setup.md for setup instructions")
                return False
            
            # Use GitHub's device flow (no local server needed)
            print("🌐 Using GitHub device flow...")
            device_code = self._get_device_code()
            
            if not device_code:
                print("❌ Failed to get device code")
                return False
            
            # Show user the verification URL and code
            print(f"🔗 Please visit: {device_code['verification_uri']}")
            print(f"📝 Enter code: {device_code['user_code']}")
            print("⏳ Waiting for authorization...")
            
            # Poll for access token
            self.access_token = self._poll_for_token(device_code['device_code'])
            
            if not self.access_token:
                print("❌ Failed to get access token")
                return False
            
            # Get user information
            print("👤 Fetching user information...")
            self.user_info = self._get_user_info()
            
            if not self.user_info:
                print("❌ Failed to get user info")
                return False
            
            # Save token securely
            self._save_token()
            
            print(f"✅ Successfully authenticated as: {self.user_info.get('login', 'Unknown')}")
            return True
            
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False
    
    def _get_device_code(self) -> Optional[Dict[str, Any]]:
        """Get device code from GitHub."""
        try:
            response = requests.post(
                "https://github.com/login/device/code",
                data={
                    'client_id': self.config.client_id,
                    'scope': ','.join(self.config.scopes)
                },
                headers={'Accept': 'application/json'}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Failed to get device code: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Device code error: {e}")
            return None
    
    def _poll_for_token(self, device_code: str) -> Optional[str]:
        """Poll for access token."""
        import time
        
        for _ in range(60):  # Poll for up to 5 minutes
            try:
                response = requests.post(
                    "https://github.com/login/oauth/access_token",
                    data={
                        'client_id': self.config.client_id,
                        'client_secret': self.config.client_secret,
                        'device_code': device_code,
                        'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'
                    },
                    headers={'Accept': 'application/json'}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'access_token' in data:
                        return data['access_token']
                    elif data.get('error') == 'authorization_pending':
                        print("⏳ Still waiting for authorization...")
                        time.sleep(5)
                        continue
                    else:
                        print(f"❌ Token polling failed: {data}")
                        return None
                else:
                    print(f"❌ Token polling failed: {response.status_code}")
                    return None
                    
            except Exception as e:
                print(f"❌ Token polling error: {e}")
                return None
        
        print("❌ Authorization timeout")
        return None
    
    def _get_user_info(self) -> Optional[Dict[str, Any]]:
        """Get authenticated user information."""
        try:
            response = requests.get(
                "https://api.github.com/user",
                headers={
                    'Authorization': f'token {self.access_token}',
                    'Accept': 'application/vnd.github.v3+json'
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Failed to get user info: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ User info error: {e}")
            return None
    
    def _save_token(self):
        """Save access token securely."""
        try:
            token_dir = Path.home() / '.iterate'
            token_dir.mkdir(exist_ok=True)
            
            token_file = token_dir / 'github_token.json'
            token_data = {
                'access_token': self.access_token,
                'user_info': self.user_info,
                'scopes': self.config.scopes
            }
            
            with open(token_file, 'w') as f:
                json.dump(token_data, f)
            
            # Set secure permissions
            os.chmod(token_file, 0o600)
            
        except Exception as e:
            print(f"⚠️  Warning: Could not save token: {e}")
    
    def load_token(self) -> bool:
        """Load saved access token."""
        try:
            token_file = Path.home() / '.iterate' / 'github_token.json'
            
            if not token_file.exists():
                return False
            
            with open(token_file, 'r') as f:
                token_data = json.load(f)
            
            self.access_token = token_data.get('access_token')
            self.user_info = token_data.get('user_info')
            
            if self.access_token and self.user_info:
                print(f"✅ Loaded existing authentication for: {self.user_info.get('login', 'Unknown')}")
                return True
            
            return False
            
        except Exception as e:
            print(f"⚠️  Warning: Could not load token: {e}")
            return False
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self.access_token is not None
    
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Get current user information."""
        return self.user_info
    
    def make_authenticated_request(self, url: str, method: str = 'GET', data: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Make authenticated request to GitHub API."""
        if not self.is_authenticated():
            return None
        
        try:
            headers = {
                'Authorization': f'token {self.access_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data)
            else:
                return None
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ API request failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ API request error: {e}")
            return None 