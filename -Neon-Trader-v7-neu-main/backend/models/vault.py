"""
Security Vault for Key Management
Handles encryption, decryption, and key rotation for sensitive data
"""

import os
import json
import logging
from datetime import datetime, timezone
from cryptography.fernet import Fernet
from typing import Optional, Dict, Any

class SecurityVault:
    """Manages encryption keys and sensitive data storage"""
    
    def __init__(self):
        self.fernet_key = os.environ.get('FERNET_KEY')
        if self.fernet_key:
            self.cipher_suite = Fernet(self.fernet_key.encode())
        else:
            logging.warning("FERNET_KEY not found in environment")
            self.cipher_suite = None
    
    def encrypt_data(self, data: str) -> Optional[str]:
        """Encrypt sensitive data"""
        if not self.cipher_suite:
            logging.error("Cipher suite not initialized")
            return None
        
        try:
            encrypted_data = self.cipher_suite.encrypt(data.encode())
            return encrypted_data.decode()
        except Exception as e:
            logging.error(f"Encryption failed: {e}")
            return None
    
    def decrypt_data(self, encrypted_data: str) -> Optional[str]:
        """Decrypt sensitive data"""
        if not self.cipher_suite:
            logging.error("Cipher suite not initialized")
            return None
        
        try:
            decrypted_data = self.cipher_suite.decrypt(encrypted_data.encode())
            return decrypted_data.decode()
        except Exception as e:
            logging.error(f"Decryption failed: {e}")
            return None
    
    def encrypt_api_keys(self, api_keys: Dict[str, str]) -> Optional[Dict[str, str]]:
        """Encrypt API keys for storage"""
        if not api_keys:
            return {}
        
        encrypted_keys = {}
        for key_name, key_value in api_keys.items():
            encrypted_value = self.encrypt_data(key_value)
            if encrypted_value:
                encrypted_keys[key_name] = encrypted_value
            else:
                logging.error(f"Failed to encrypt key: {key_name}")
                return None
        
        return encrypted_keys
    
    def decrypt_api_keys(self, encrypted_keys: Dict[str, str]) -> Optional[Dict[str, str]]:
        """Decrypt API keys for use"""
        if not encrypted_keys:
            return {}
        
        decrypted_keys = {}
        for key_name, encrypted_value in encrypted_keys.items():
            decrypted_value = self.decrypt_data(encrypted_value)
            if decrypted_value:
                decrypted_keys[key_name] = decrypted_value
            else:
                logging.error(f"Failed to decrypt key: {key_name}")
                return None
        
        return decrypted_keys
    
    @staticmethod
    def generate_rotation_schedule() -> Dict[str, Any]:
        """Generate key rotation schedule"""
        now = datetime.now(timezone.utc)
        return {
            "current_key_generated": now.isoformat(),
            "next_rotation_due": (now.replace(month=now.month + 1 if now.month < 12 else 1,
                                            year=now.year + (1 if now.month == 12 else 0))).isoformat(),
            "rotation_frequency_days": 30,
            "backup_keys_count": 2
        }
    
    @staticmethod
    def validate_key_strength(key: str) -> Dict[str, bool]:
        """Validate key strength and security"""
        return {
            "min_length": len(key) >= 32,
            "has_special_chars": any(c in key for c in "!@#$%^&*()_+-=[]{}|;:,.<>?"),
            "has_numbers": any(c.isdigit() for c in key),
            "has_letters": any(c.isalpha() for c in key),
            "is_base64": key.replace("-", "+").replace("_", "/").isalnum() or "=" in key
        }

# Global vault instance
vault = SecurityVault()

# Usage functions for the application
def encrypt_platform_keys(platform_data: Dict[str, Any]) -> Dict[str, Any]:
    """Encrypt platform API keys before storage"""
    if 'api_key' in platform_data or 'secret_key' in platform_data:
        keys_to_encrypt = {
            'api_key': platform_data.get('api_key', ''),
            'secret_key': platform_data.get('secret_key', ''),
            'passphrase': platform_data.get('passphrase', '')
        }
        
        encrypted_keys = vault.encrypt_api_keys(keys_to_encrypt)
        if encrypted_keys:
            platform_data.update(encrypted_keys)
    
    return platform_data

def decrypt_platform_keys(platform_data: Dict[str, Any]) -> Dict[str, Any]:
    """Decrypt platform API keys for use"""
    if 'api_key' in platform_data or 'secret_key' in platform_data:
        keys_to_decrypt = {
            'api_key': platform_data.get('api_key', ''),
            'secret_key': platform_data.get('secret_key', ''),
            'passphrase': platform_data.get('passphrase', '')
        }
        
        decrypted_keys = vault.decrypt_api_keys(keys_to_decrypt)
        if decrypted_keys:
            platform_data.update(decrypted_keys)
    
    return platform_data