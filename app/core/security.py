"""
SAIA Insurance Broker Platform - Security & Data Masking
"""
from typing import Dict, Any


class DataMasker:
    """Utility class for masking sensitive data"""
    
    @staticmethod
    def mask_national_id(national_id: str) -> str:
        """
        Mask national ID: 1122334455 → 112*****55
        """
        if not national_id or len(national_id) != 10:
            return "***"
        return f"{national_id[:3]}*****{national_id[-2:]}"
    
    @staticmethod
    def mask_phone(phone: str) -> str:
        """
        Mask phone number: 0501234567 → 050****567
        """
        if not phone:
            return "***"
        clean = phone.replace(" ", "").replace("-", "")
        if len(clean) < 10:
            return "***"
        return f"{clean[:3]}****{clean[-3:]}"
    
    @staticmethod
    def mask_plate(plate: str) -> str:
        """
        Mask license plate: س ك ر 5678 → س ك ر ****
        """
        if not plate:
            return "****"
        parts = plate.strip().split()
        if len(parts) >= 2:
            letters = " ".join(parts[:-1])
            return f"{letters} ****"
        return "****"
    
    @staticmethod
    def mask_email(email: str) -> str:
        """
        Mask email: example@email.com → ex***@email.com
        """
        if not email or "@" not in email:
            return "***"
        local, domain = email.split("@", 1)
        masked_local = f"{local[:2]}***" if len(local) > 2 else "***"
        return f"{masked_local}@{domain}"
    
    @classmethod
    def mask_for_context(cls, data: Dict[str, Any], context: str) -> Dict[str, Any]:
        """
        Mask data based on display context
        
        Contexts:
        - customer_confirmation: Partial masking for customer
        - admin_dashboard: More masking for admin view
        - internal_log: Full redaction for logs
        """
        if not data:
            return {}
        
        result = data.copy()
        
        if context == "customer_confirmation":
            # Customer sees partial masking
            if "national_id" in result:
                result["national_id"] = cls.mask_national_id(result["national_id"])
            # Phone and plate visible to customer
            
        elif context == "admin_dashboard":
            # Admin sees more masking
            if "national_id" in result:
                result["national_id"] = cls.mask_national_id(result["national_id"])
            if "phone" in result:
                result["phone"] = cls.mask_phone(result["phone"])
            if "plate_no" in result:
                result["plate_no"] = cls.mask_plate(result["plate_no"])
                
        elif context == "internal_log":
            # Full redaction for logs
            sensitive_fields = ["national_id", "phone", "email", "plate_no"]
            for field in sensitive_fields:
                if field in result:
                    result[field] = "***REDACTED***"
        
        return result


def format_currency(amount: float, currency: str = "SAR") -> str:
    """Format amount as currency string"""
    return f"{amount:,.2f} {currency}"


def format_date_ar(date_str: str) -> str:
    """Format date string for Arabic display"""
    # Simple format, can be enhanced with hijri conversion
    return date_str
