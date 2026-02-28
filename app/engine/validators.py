"""
Data Validators - Production-ready validation for extracted data
"""
import re
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DataValidator:
    """Validates extracted data with proper regex and business rules"""
    
    def validate_extracted_data(self, extracted: Dict[str, Any]) -> Dict[str, Any]:
        """Validate all extracted data and return cleaned version"""
        
        validated = {}
        
        for field, value in extracted.items():
            if field == "national_id":
                validated_id = self.validate_national_id(value)
                if validated_id:
                    validated[field] = validated_id
            
            elif field == "phone":
                validated_phone = self.validate_phone(value)
                if validated_phone:
                    validated[field] = validated_phone
            
            elif field == "birth_date":
                validated_date = self.validate_birth_date(value)
                if validated_date:
                    validated[field] = validated_date
            
            elif field == "vehicle_value":
                validated_value = self.validate_vehicle_value(value)
                if validated_value:
                    validated[field] = validated_value
            
            elif field == "plate_number":
                validated_plate = self.validate_plate_number(value)
                if validated_plate:
                    validated[field] = validated_plate
            
            else:
                # For other fields, basic string validation
                if isinstance(value, str) and len(value.strip()) > 0:
                    validated[field] = value.strip()
        
        if validated:
            logger.info(f"✅ Validated fields: {list(validated.keys())}")
        
        return validated
    
    def validate_national_id(self, value: Any) -> Optional[str]:
        """Validate Saudi national ID"""
        if not isinstance(value, (str, int)):
            return None
        
        # Convert to string and clean
        id_str = str(value).strip().replace(' ', '').replace('-', '')
        
        # Must be exactly 10 digits
        if not re.match(r'^\d{10}$', id_str):
            return None
        
        # Must start with 1 (Saudi) or 2 (Resident)
        if not id_str.startswith(('1', '2')):
            return None
        
        # Additional checksum validation could be added here
        logger.info(f"✅ Valid national ID: {id_str[:3]}*******")
        return id_str
    
    def validate_phone(self, value: Any) -> Optional[str]:
        """Validate Saudi phone number"""
        if not isinstance(value, (str, int)):
            return None
        
        # Clean the input
        phone_str = str(value).strip().replace(' ', '').replace('-', '').replace('+', '')
        
        # Remove country code if present
        if phone_str.startswith('966'):
            phone_str = '0' + phone_str[3:]
        
        # Must be 10 digits starting with 05
        if re.match(r'^05\d{8}$', phone_str):
            logger.info(f"✅ Valid phone: {phone_str[:4]}******")
            return phone_str
        
        # Try 9 digits starting with 5 (add 0)
        if re.match(r'^5\d{8}$', phone_str):
            validated = '0' + phone_str
            logger.info(f"✅ Valid phone (added 0): {validated[:4]}******")
            return validated
        
        return None
    
    def validate_birth_date(self, value: Any) -> Optional[str]:
        """Validate birth date with multiple formats"""
        if not isinstance(value, str):
            return None
        
        date_str = value.strip()
        
        # Common Saudi date formats
        patterns = [
            (r'^(\d{1,2})/(\d{1,2})/(\d{4})$', '%d/%m/%Y'),  # DD/MM/YYYY
            (r'^(\d{1,2})-(\d{1,2})-(\d{4})$', '%d-%m-%Y'),  # DD-MM-YYYY
            (r'^(\d{4})/(\d{1,2})/(\d{1,2})$', '%Y/%m/%d'),  # YYYY/MM/DD
            (r'^(\d{4})-(\d{1,2})-(\d{1,2})$', '%Y-%m-%d'),  # YYYY-MM-DD
        ]
        
        for pattern, date_format in patterns:
            if re.match(pattern, date_str):
                try:
                    # Try to parse the date
                    parsed_date = datetime.strptime(date_str, date_format)
                    
                    # Validate age (must be between 18 and 100)
                    age = (datetime.now() - parsed_date).days // 365
                    if 18 <= age <= 100:
                        # Return in standard format
                        standard_format = parsed_date.strftime('%d/%m/%Y')
                        logger.info(f"✅ Valid birth date: {standard_format}")
                        return standard_format
                    else:
                        logger.warning(f"⚠️ Invalid age: {age} years")
                        return None
                        
                except ValueError:
                    continue
        
        # Try to extract year and validate
        year_match = re.search(r'\b(19|20)\d{2}\b', date_str)
        if year_match:
            year = int(year_match.group())
            current_year = datetime.now().year
            if 1924 <= year <= current_year - 18:  # Age 18-100
                logger.info(f"✅ Extracted birth year: {year}")
                return f"01/01/{year}"  # Default to Jan 1st
        
        return None
    
    def validate_vehicle_value(self, value: Any) -> Optional[int]:
        """Validate vehicle value"""
        if isinstance(value, int) and value > 0:
            return value
        
        if isinstance(value, str):
            # Clean the string
            clean_value = value.replace(',', '').replace('،', '').replace(' ', '')
            
            # Handle "ألف" (thousand)
            if 'ألف' in clean_value or 'الف' in clean_value:
                numbers = re.findall(r'\d+', clean_value)
                if numbers:
                    base_value = int(numbers[0])
                    if 10 <= base_value <= 500:  # 10k to 500k SAR
                        result = base_value * 1000
                        logger.info(f"✅ Valid vehicle value: {result:,} SAR")
                        return result
            
            # Extract pure number
            numbers = re.findall(r'\d+', clean_value)
            if numbers:
                value_int = int(numbers[0])
                if 10000 <= value_int <= 500000:  # 10k to 500k SAR
                    logger.info(f"✅ Valid vehicle value: {value_int:,} SAR")
                    return value_int
        
        return None
    
    def validate_plate_number(self, value: Any) -> Optional[str]:
        """Validate Saudi plate number"""
        if not isinstance(value, str):
            return None
        
        plate = value.strip().upper()
        
        # Saudi plate patterns (simplified)
        patterns = [
            r'^[A-Z]{3}\s?\d{3,4}$',  # ABC 123 or ABC 1234
            r'^\d{3,4}\s?[A-Z]{3}$',  # 123 ABC or 1234 ABC
            r'^[A-Z]{1,2}\s?\d{3,4}$',  # A 123 or AB 1234
        ]
        
        for pattern in patterns:
            if re.match(pattern, plate):
                # Standardize format
                standardized = re.sub(r'\s+', ' ', plate)
                logger.info(f"✅ Valid plate number: {standardized}")
                return standardized
        
        # If no pattern matches, still accept if it looks reasonable
        if 3 <= len(plate.replace(' ', '')) <= 8:
            logger.info(f"✅ Accepted plate number: {plate}")
            return plate
        
        return None
    
    def validate_choice(self, value: Any, max_options: int) -> Optional[int]:
        """Validate user choice (1, 2, 3, etc.)"""
        if isinstance(value, int):
            if 1 <= value <= max_options:
                return value
        
        if isinstance(value, str):
            # Extract number from string
            numbers = re.findall(r'\d+', value)
            if numbers:
                choice = int(numbers[0])
                if 1 <= choice <= max_options:
                    return choice
        
        return None