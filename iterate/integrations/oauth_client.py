"""
GitHub OAuth client for proper authentication.
"""

import os
import json
import webbrowser
import http.server
import socketserver
import urllib.parse
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path
import requests

# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file."""
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key] = value

# Load .env file on import
load_env_file()


@dataclass
class OAuthConfig:
    """OAuth configuration for GitHub."""
    client_id: str
    client_secret: str
    redirect_uri: str
    scopes: list


class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    """HTTP server to handle OAuth callback."""
    
    def __init__(self, *args, **kwargs):
        self.auth_code = None
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle OAuth callback."""
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        
        if 'code' in params:
            self.auth_code = params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
            <html>
            <body>
            <h1>Authentication Successful!</h1>
            <p>You can close this window now.</p>
            </body>
            </html>
            """)
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
            <html>
            <body>
            <h1>Authentication Failed!</h1>
            <p>Please try again.</p>
            </body>
            </html>
            """)


class GitHubOAuthClient:
    """GitHub OAuth client for proper authentication."""
    
    def __init__(self):
        self.config = self._load_config()
        self.access_token = None
        self.user_info = None
    
    def _load_config(self) -> OAuthConfig:
        """Load OAuth configuration."""
        # For development, we'll use a simple config
        # In production, this would be loaded from environment or config file
        return OAuthConfig(
            client_id=os.getenv("GITHUB_CLIENT_ID", "demo_client_id"),
            client_secret=os.getenv("GITHUB_CLIENT_SECRET", "demo_client_secret"),
            redirect_uri="http://localhost:8081/callback",  # Changed port to avoid conflicts
            scopes=["repo", "read:user", "write:issues"]
        )
    
    def authenticate(self) -> bool:
        """Authenticate with GitHub using OAuth."""
        try:
            print("🔐 Starting GitHub OAuth authentication...")
            
            # Check if we have proper credentials
            if self.config.client_id == "demo_client_id":
                print("⚠️  Using demo credentials. For production, set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET")
                print("📖 See docs/github_setup.md for setup instructions")
                return False
            
            # Step 1: Generate authorization URL
            auth_url = self._generate_auth_url()
            
            # Step 2: Open browser for user authorization
            print("🌐 Opening browser for GitHub authorization...")
            print(f"🔗 Authorization URL: {auth_url}")
            webbrowser.open(auth_url)
            
            # Step 3: Start local server to handle callback
            print("📡 Waiting for authorization callback...")
            auth_code = self._handle_callback()
            
            if not auth_code:
                print("❌ Authentication failed: No authorization code received")
                return False
            
            # Step 4: Exchange code for access token
            print("🔄 Exchanging authorization code for access token...")
            self.access_token = self._exchange_code_for_token(auth_code)
            
            if not self.access_token:
                print("❌ Authentication failed: Could not obtain access token")
                return False
            
            # Step 5: Get user information
            print("👤 Fetching user information...")
            self.user_info = self._get_user_info()
            
            if not self.user_info:
                print("❌ Authentication failed: Could not fetch user info")
                return False
            
            # Step 6: Save token securely
            self._save_token()
            
            print(f"✅ Successfully authenticated as: {self.user_info.get('login', 'Unknown')}")
            return True
            
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False
    
    def _generate_auth_url(self) -> str:
        """Generate GitHub authorization URL."""
        params = {
            'client_id': self.config.client_id,
            'redirect_uri': self.config.redirect_uri,
            'scope': ','.join(self.config.scopes),
            'response_type': 'code'
        }
        
        query = urllib.parse.urlencode(params)
        return f"https://github.com/login/oauth/authorize?{query}"
    
    def _handle_callback(self) -> Optional[str]:
        """Handle OAuth callback and return authorization code."""
        auth_code = None
        
        class CallbackHandler(OAuthCallbackHandler):
            def __init__(self, *args, **kwargs):
                self.auth_code = None
                super().__init__(*args, **kwargs)
            
            def do_GET(self):
                """Handle OAuth callback."""
                nonlocal auth_code
                query = urllib.parse.urlparse(self.path).query
                params = urllib.parse.parse_qs(query)
                
                if 'code' in params:
                    auth_code = params['code'][0]
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b"""
                    <html>
                    <body>
                    <h1>Authentication Successful!</h1>
                    <p>You can close this window now.</p>
                    </body>
                    </html>
                    """)
                else:
                    self.send_response(400)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b"""
                    <html>
                    <body>
                    <h1>Authentication Failed!</h1>
                    <p>Please try again.</p>
                    </body>
                    </html>
                    """)
        
        try:
            # Try different ports if one is in use
            for port in [8081, 8082, 8083, 8084, 8085]:
                try:
                    with socketserver.TCPServer(("localhost", port), CallbackHandler) as httpd:
                        print(f"📡 Listening for callback on http://localhost:{port}")
                        httpd.handle_request()
                        return auth_code
                except OSError as e:
                    if "Address already in use" in str(e):
                        print(f"⚠️  Port {port} in use, trying next port...")
                        continue
                    else:
                        raise e
            print("❌ All ports 8081-8085 are in use")
            return None
                
        except Exception as e:
            print(f"❌ Callback handling failed: {e}")
            return None
    
    def _exchange_code_for_token(self, auth_code: str) -> Optional[str]:
        """Exchange authorization code for access token."""
        try:
            response = requests.post(
                "https://github.com/login/oauth/access_token",
                data={
                    'client_id': self.config.client_id,
                    'client_secret': self.config.client_secret,
                    'code': auth_code,
                    'redirect_uri': self.config.redirect_uri
                },
                headers={'Accept': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('access_token')
            else:
                print(f"❌ Token exchange failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Token exchange error: {e}")
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