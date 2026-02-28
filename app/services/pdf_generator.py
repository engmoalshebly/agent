"""
SAIA Insurance Broker Platform - PDF Generator Service
خدمة توليد ملفات PDF للفاتورة ووثيقة التأمين
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path
import base64

logger = logging.getLogger(__name__)

# المسارات الأساسية
BASE_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
LOGOS_DIR = STATIC_DIR / "logos"
OUTPUT_DIR = Path("/tmp/saia_documents")  # مجلد قابل للكتابة

# التأكد من وجود مجلد الإخراج
try:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass  # سيتم إنشاؤه عند الحاجة



class PDFGenerator:
    """
    مولد PDF للفاتورة ووثيقة التأمين
    يستخدم HTML templates ويحولها لـ PDF
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._ensure_directories()
    
    def _ensure_directories(self):
        """التأكد من وجود المجلدات المطلوبة"""
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    def _load_template(self, template_name: str) -> str:
        """تحميل قالب HTML"""
        template_path = TEMPLATES_DIR / template_name
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        return template_path.read_text(encoding='utf-8')
    
    def _get_logo_base64(self, logo_name: str, max_size_kb: int = 150) -> str:
        """تحويل الشعار لـ Base64 للتضمين في HTML - تجاهل الصور الكبيرة"""
        logo_path = LOGOS_DIR / logo_name
        if logo_path.exists():
            # تجاهل الصور الكبيرة لمنع مشاكل الذاكرة
            file_size_kb = logo_path.stat().st_size / 1024
            if file_size_kb > max_size_kb:
                self.logger.warning(f"Logo {logo_name} too large ({file_size_kb:.0f}KB > {max_size_kb}KB), skipping")
                return ""
            with open(logo_path, 'rb') as f:
                return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
        return ""
    
    def _render_template(self, template: str, data: Dict[str, Any]) -> str:
        """تعبئة القالب بالبيانات"""
        # استبدال الشعارات بـ Base64
        data['saia_logo'] = self._get_logo_base64('saia_logo.png')
        data['bineyes_logo'] = self._get_logo_base64('bineyes_logo.png')
        data['qr_code'] = self._get_logo_base64('qr_sample.png')
        
        # استبدال المتغيرات في القالب
        for key, value in data.items():
            template = template.replace(f"{{{{ {key} }}}}", str(value))
        
        return template
    
    def generate_invoice_html(self, context_data: Dict[str, Any]) -> str:
        """
        توليد HTML للفاتورة
        """
        # تحضير البيانات
        today = datetime.now()
        next_year = today + timedelta(days=365)
        
        # استخراج بيانات السيارة
        vehicle_info = self._get_vehicle_info(context_data)
        
        data = {
            'invoice_number': context_data.get('invoice_id', f"INV-{today.strftime('%Y%m%d')}-{today.strftime('%H%M%S')}"),
            'issue_date': today.strftime('%Y-%m-%d'),
            'sadad_number': context_data.get('sadad_number', f"177{today.strftime('%Y%m%d%H%M%S')}"),
            'national_id': context_data.get('national_id', 'غير محدد'),
            'total_amount': f"{context_data.get('total_amount', 0):,.2f}",
            'coverage_type': context_data.get('coverage_type', 'تأمين شامل'),
            'vehicle_info': vehicle_info,
            'company_name': context_data.get('company_name', 'شركة التأمين'),
            'policy_start': today.strftime('%Y-%m-%d'),
            'policy_end': next_year.strftime('%Y-%m-%d'),
        }
        
        template = self._load_template('invoice.html')
        return self._render_template(template, data)
    
    def generate_policy_html(self, context_data: Dict[str, Any]) -> str:
        """
        توليد HTML لوثيقة التأمين
        """
        today = datetime.now()
        next_year = today + timedelta(days=365)
        
        data = {
            'policy_number': context_data.get('policy_id', f"POL-{today.strftime('%Y%m%d')}-{today.strftime('%H%M%S')}"),
            'issue_date': today.strftime('%Y-%m-%d'),
            'expiry_date': next_year.strftime('%Y-%m-%d'),
            'national_id': context_data.get('national_id', 'غير محدد'),
            'birth_date': context_data.get('birth_date', 'غير محدد'),
            'phone': context_data.get('phone', 'غير محدد'),
            'invoice_number': context_data.get('invoice_id', 'غير محدد'),
            'vehicle_brand': context_data.get('vehicle_brand', 'غير محدد'),
            'vehicle_model': context_data.get('vehicle_model', 'غير محدد'),
            'vehicle_year': context_data.get('vehicle_year', 'غير محدد'),
            'plate_no': context_data.get('plate_no', 'غير محدد'),
            'vehicle_value': f"{context_data.get('vehicle_value', 0):,}",
            'coverage_type': context_data.get('coverage_type', 'تأمين شامل'),
            'company_name': context_data.get('company_name', 'شركة التأمين'),
            'offer_code': context_data.get('offer_code', 'N/A'),
            'premium': f"{context_data.get('total_amount', 0):,.2f}",
        }
        
        template = self._load_template('policy.html')
        return self._render_template(template, data)
    
    def save_invoice_html(self, context_data: Dict[str, Any]) -> str:
        """
        حفظ الفاتورة كملف PDF
        Returns: مسار الملف
        """
        html = self.generate_invoice_html(context_data)
        
        # إنشاء اسم ملف فريد
        invoice_id = context_data.get('invoice_id', datetime.now().strftime('%Y%m%d%H%M%S'))
        filename = f"invoice_{invoice_id}.pdf"
        filepath = OUTPUT_DIR / filename
        
        # تحويل HTML إلى PDF باستخدام weasyprint
        try:
            from weasyprint import HTML
            HTML(string=html, base_url=str(TEMPLATES_DIR)).write_pdf(str(filepath))
            self.logger.info(f"✅ Invoice PDF saved: {filepath}")
        except Exception as e:
            self.logger.error(f"PDF generation failed, falling back to HTML: {e}")
            # Fallback to HTML if PDF fails
            filename = f"invoice_{invoice_id}.html"
            filepath = OUTPUT_DIR / filename
            filepath.write_text(html, encoding='utf-8')
            self.logger.info(f"⚠️ Invoice HTML saved (fallback): {filepath}")
        
        return str(filepath)
    
    def save_policy_html(self, context_data: Dict[str, Any]) -> str:
        """
        حفظ الوثيقة كملف PDF
        Returns: مسار الملف
        """
        html = self.generate_policy_html(context_data)
        
        # إنشاء اسم ملف فريد
        policy_id = context_data.get('policy_id', datetime.now().strftime('%Y%m%d%H%M%S'))
        filename = f"policy_{policy_id}.pdf"
        filepath = OUTPUT_DIR / filename
        
        # تحويل HTML إلى PDF باستخدام weasyprint
        try:
            from weasyprint import HTML
            HTML(string=html, base_url=str(TEMPLATES_DIR)).write_pdf(str(filepath))
            self.logger.info(f"✅ Policy PDF saved: {filepath}")
        except Exception as e:
            self.logger.error(f"PDF generation failed, falling back to HTML: {e}")
            # Fallback to HTML if PDF fails
            filename = f"policy_{policy_id}.html"
            filepath = OUTPUT_DIR / filename
            filepath.write_text(html, encoding='utf-8')
            self.logger.info(f"⚠️ Policy HTML saved (fallback): {filepath}")
        
        return str(filepath)
    
    def _get_vehicle_info(self, context_data: Dict[str, Any]) -> str:
        """تنسيق معلومات السيارة"""
        brand = context_data.get('vehicle_brand', '')
        model = context_data.get('vehicle_model', '')
        year = context_data.get('vehicle_year', '')
        plate = context_data.get('plate_no', '')
        
        parts = [p for p in [brand, model, str(year) if year else '', plate] if p]
        return ' - '.join(parts) if parts else 'غير محدد'
    
    def generate_documents(self, context_data: Dict[str, Any]) -> Dict[str, str]:
        """
        توليد كلا المستندين (الفاتورة والوثيقة)
        Returns: dict مع مسارات الملفات
        """
        try:
            invoice_path = self.save_invoice_html(context_data)
            policy_path = self.save_policy_html(context_data)
            
            return {
                'invoice_path': invoice_path,
                'policy_path': policy_path,
                'success': True
            }
        except Exception as e:
            self.logger.error(f"Error generating documents: {e}")
            return {
                'invoice_path': None,
                'policy_path': None,
                'success': False,
                'error': str(e)
            }


# Singleton instance
pdf_generator = PDFGenerator()


def generate_payment_documents(context_data: Dict[str, Any]) -> Dict[str, str]:
    """
    دالة مساعدة لتوليد مستندات الدفع
    """
    return pdf_generator.generate_documents(context_data)
