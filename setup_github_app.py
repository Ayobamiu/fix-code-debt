#!/usr/bin/env python3
"""
GitHub App Setup Helper

This script helps you set up GitHub OAuth credentials for the Iterate tool.
"""

import os
import json
from pathlib import Path


def main():
    """Main setup function."""
    print("🔧 GitHub App Setup Helper")
    print("=" * 50)
    
    print("\n📋 To use GitHub OAuth authentication, you need to:")
    print("1. Create a GitHub App")
    print("2. Get your Client ID and Client Secret")
    print("3. Set environment variables")
    
    print("\n🚀 Step 1: Create GitHub App")
    print("- Go to: https://github.com/settings/apps")
    print("- Click 'New GitHub App'")
    print("- Fill in the details:")
    print("  • App name: iterate-code-debt")
    print("  • Homepage URL: https://github.com/your-username/iterate-code-debt")
    print("  • App description: Code debt analysis tool")
    print("  • Callback URL: http://localhost:8080/callback")
    
    print("\n🔐 Step 2: Set Permissions")
    print("Repository permissions:")
    print("- Contents: Read")
    print("- Issues: Write")
    print("- Metadata: Read")
    print("\nUser permissions:")
    print("- Email addresses: Read")
    
    print("\n📝 Step 3: Get Credentials")
    print("After creating the app, you'll get:")
    print("- Client ID (copy this)")
    print("- Client Secret (generate a new one)")
    
    # Ask user for credentials
    print("\n" + "=" * 50)
    client_id = input("Enter your GitHub Client ID: ").strip()
    client_secret = input("Enter your GitHub Client Secret: ").strip()
    
    if not client_id or not client_secret:
        print("❌ Client ID and Client Secret are required!")
        return
    
    # Create .env file
    env_file = Path(".env")
    env_content = f"""# GitHub OAuth Configuration
GITHUB_CLIENT_ID={client_id}
GITHUB_CLIENT_SECRET={client_secret}
"""
    
    with open(env_file, "w") as f:
        f.write(env_content)
    
    print(f"\n✅ Created {env_file} with your credentials")
    print("🔒 Make sure to add .env to your .gitignore file!")
    
    # Update .gitignore
    gitignore_file = Path(".gitignore")
    if gitignore_file.exists():
        with open(gitignore_file, "r") as f:
            content = f.read()
        
        if ".env" not in content:
            with open(gitignore_file, "a") as f:
                f.write("\n# Environment variables\n.env\n")
            print("✅ Added .env to .gitignore")
    
    print("\n🎉 Setup complete!")
    print("You can now run: python3 -m iterate.cli . --github-oauth")
    
    # Test the credentials
    print("\n🧪 Testing credentials...")
    os.environ["GITHUB_CLIENT_ID"] = client_id
    os.environ["GITHUB_CLIENT_SECRET"] = client_secret
    
    try:
        from iterate.integrations.oauth_client import GitHubOAuthClient
        oauth_client = GitHubOAuthClient()
        
        if oauth_client.config.client_id == client_id:
            print("✅ Credentials loaded successfully!")
        else:
            print("❌ Credentials not loaded correctly")
            
    except ImportError:
        print("⚠️  Could not test credentials (import error)")
    except Exception as e:
        print(f"❌ Error testing credentials: {e}")


if __name__ == "__main__":
    main() 