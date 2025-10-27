#!/usr/bin/env python3
"""
Key Generation Script for Neon Trader V7
Generates cryptographic keys for JWT and encryption services
"""

import secrets
import os
from cryptography.fernet import Fernet

def generate_jwt_secret():
    """Generate a secure JWT secret key"""
    return secrets.token_urlsafe(48)

def generate_fernet_key():
    """Generate a Fernet encryption key"""
    return Fernet.generate_key().decode()

def generate_api_key():
    """Generate a general API key"""
    return secrets.token_hex(32)

def main():
    """Generate all keys and print in .env format"""
    print("# Generated Security Keys for Neon Trader V7")
    print(f"JWT_SECRET_KEY={generate_jwt_secret()}")
    print(f"FERNET_KEY={generate_fernet_key()}")
    print(f"API_ENCRYPTION_KEY={generate_api_key()}")
    print(f"SESSION_SECRET={generate_jwt_secret()}")
    
    # Additional keys for different environments
    print("\n# Environment-specific keys")
    print(f"DEV_JWT_SECRET={generate_jwt_secret()}")
    print(f"PROD_JWT_SECRET={generate_jwt_secret()}")
    
    print("\n# Key rotation timestamp")
    from datetime import datetime
    print(f"KEY_GENERATED_AT={datetime.utcnow().isoformat()}Z")

if __name__ == "__main__":
    main()