"""
Neon Trader V7 - Two-Factor Authentication Service
Secure 2FA implementation using TOTP
"""

import pyotp
import qrcode
import io
import base64
from typing import Dict, Any, Optional, Tuple
import secrets
import logging

class TwoFactorAuthService:
    """Handles Two-Factor Authentication operations"""
    
    @staticmethod
    def generate_secret_key() -> str:
        """Generate a new secret key for 2FA"""
        return pyotp.random_base32()
    
    @staticmethod
    def generate_qr_code(user_email: str, secret_key: str, app_name: str = "Neon Trader V7") -> str:
        """
        Generate QR code for 2FA setup
        Returns base64 encoded QR code image
        """
        try:
            # Create TOTP URL
            totp = pyotp.TOTP(secret_key)
            provisioning_uri = totp.provisioning_uri(
                name=user_email,
                issuer_name=app_name
            )
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(provisioning_uri)
            qr.make(fit=True)
            
            # Create QR code image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_str = base64.b64encode(img_buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            logging.error(f"QR code generation failed: {e}")
            raise
    
    @staticmethod
    def verify_token(secret_key: str, token: str, window: int = 1) -> bool:
        """
        Verify TOTP token
        window: Number of 30-second windows to check (for clock skew tolerance)
        """
        if not secret_key or not token:
            return False
        
        try:
            totp = pyotp.TOTP(secret_key)
            return totp.verify(token, valid_window=window)
        except Exception as e:
            logging.error(f"Token verification failed: {e}")
            return False
    
    @staticmethod
    def generate_backup_codes(count: int = 8) -> list[str]:
        """Generate backup codes for 2FA recovery"""
        backup_codes = []
        for _ in range(count):
            # Generate 8-character alphanumeric codes
            code = secrets.token_hex(4).upper()
            backup_codes.append(f"{code[:4]}-{code[4:]}")
        return backup_codes
    
    @staticmethod
    def validate_backup_code(stored_codes: list[str], input_code: str) -> Tuple[bool, list[str]]:
        """
        Validate backup code and remove it from available codes
        Returns (is_valid, remaining_codes)
        """
        input_code = input_code.upper().strip()
        
        if input_code in stored_codes:
            remaining_codes = [code for code in stored_codes if code != input_code]
            return True, remaining_codes
        
        return False, stored_codes
    
    @staticmethod
    def get_current_token(secret_key: str) -> str:
        """Get current TOTP token (for testing purposes)"""
        totp = pyotp.TOTP(secret_key)
        return totp.now()
    
    @staticmethod
    def is_setup_complete(user_data: Dict[str, Any]) -> bool:
        """Check if 2FA setup is complete for user"""
        return (
            user_data.get('two_factor_secret') and 
            user_data.get('two_factor_enabled', False)
        )

class SecurityAuditLogger:
    """Logs security-related events for audit trail"""
    
    @staticmethod
    def log_2fa_setup(user_id: str, success: bool, ip_address: str = None):
        """Log 2FA setup attempt"""
        logging.info(f"2FA Setup - User: {user_id}, Success: {success}, IP: {ip_address}")
    
    @staticmethod
    def log_2fa_verification(user_id: str, success: bool, method: str = "totp", ip_address: str = None):
        """Log 2FA verification attempt"""
        logging.info(f"2FA Verify - User: {user_id}, Success: {success}, Method: {method}, IP: {ip_address}")
    
    @staticmethod
    def log_backup_code_usage(user_id: str, success: bool, ip_address: str = None):
        """Log backup code usage"""
        logging.warning(f"2FA Backup Code - User: {user_id}, Success: {success}, IP: {ip_address}")
    
    @staticmethod
    def log_2fa_disable(user_id: str, ip_address: str = None):
        """Log 2FA disable event"""
        logging.warning(f"2FA Disabled - User: {user_id}, IP: {ip_address}")

# Validation Functions
def validate_totp_token_format(token: str) -> bool:
    """Validate TOTP token format (6 digits)"""
    return token.isdigit() and len(token) == 6

def validate_backup_code_format(code: str) -> bool:
    """Validate backup code format (XXXX-XXXX)"""
    import re
    pattern = r'^[A-F0-9]{4}-[A-F0-9]{4}$'
    return bool(re.match(pattern, code.upper()))