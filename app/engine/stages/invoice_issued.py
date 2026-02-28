"""
Invoice Issued Stage - مرحلة إصدار الفاتورة
"""
from typing import Dict, Any, List
from app.core.constants import ConversationStage
from app.engine.session_manager import ConversationContext
from .base_stage import BaseStage, StageResponse


class InvoiceIssuedStage(BaseStage):
    """مرحلة إصدار الفاتورة وإرشاد العميل للدفع"""
    
    stage = ConversationStage.INVOICE_ISSUED
    order = 11
    name_ar = "الفاتورة"
    
    def __init__(self):
        super().__init__()
        self.order_repo = None
        self.invoice_repo = None
        self._init_repos()
    
    def _init_repos(self):
        try:
            from app.db.repositories.order_repository import order_repository
            from app.db.repositories.invoice_repository import invoice_repository
            self.order_repo = order_repository
            self.invoice_repo = invoice_repository
        except Exception as e:
            self.logger.warning(f"Could not init repos: {e}")
    
    def get_stage_info(self) -> Dict[str, str]:
        return {
            "name": "إصدار الفاتورة",
            "description": "إصدار رقم الفاتورة وإرشاد العميل للدفع",
            "required_action": "أعط العميل رقم الفاتورة وأرشده لطريقة الدفع"
        }
    
    def get_required_fields(self) -> List[str]:
        """الحقول المطلوبة: دفع الفاتورة"""
        return ["payment_confirmed"]
    
    def get_collected_fields(self, context: ConversationContext) -> Dict[str, Any]:
        """الحقول المجمعة"""
        collected = {}
        if context.invoice_id:
            collected["invoice_id"] = context.invoice_id
        if context.order_id:
            collected["order_id"] = context.order_id
        return collected
    
    def get_prompt_instructions(self, context: ConversationContext) -> str:
        offer = context.selected_offer or {}
        
        # استخدام total_premium مباشرة (يتضمن الضريبة)
        total = float(offer.get("total_premium", 0)) or float(offer.get("price", 0))
        
        sadad_number = getattr(context, 'sadad_number', None) or self._generate_sadad()
        biller_code = getattr(context, 'biller_code', None) or "177"
        
        # حفظ رقم السداد في context
        if not context.sadad_number:
            context.sadad_number = sadad_number
        if not context.biller_code:
            context.biller_code = biller_code
        
        # ✅ توليد ملف الفاتورة الآن
        invoice_url = self._generate_invoice_file(context)
        
        self.logger.info(f"📄 INVOICE_ISSUED - total: {total}, sadad: {sadad_number}, invoice_url: {invoice_url}")
        
        # إضافة رابط الفاتورة في التعليمات
        invoice_link_text = ""
        if invoice_url:
            invoice_link_text = f"\n📎 رابط الفاتورة: {invoice_url}"
        
        return f"""⚠️ أنت في مرحلة إصدار الفاتورة.

📄 **بيانات الفاتورة:**
━━━━━━━━━━━━━━━━━━━
📋 رقم الفاتورة: {context.invoice_id}
📋 رقم الطلب: {context.order_id}
💰 المبلغ الإجمالي: {total:,.2f} ريال

💳 **بيانات السداد:**
━━━━━━━━━━━━━━━━━━━
🏦 رقم المُفوتر: {biller_code}
🔢 رقم السداد: {sadad_number}
⏰ صلاحية السداد: 24 ساعة

✅ المطلوب:
"تمام! 🎉 تم إصدار فاتورتك!

📋 رقم الفاتورة: {context.invoice_id}
💰 المبلغ: {total:,.2f} ريال

💳 بيانات السداد:
🏦 رقم المُفوتر: {biller_code}
🔢 رقم السداد: {sadad_number}

طرق الدفع: سداد، تطبيق البنك، الصراف
{invoice_link_text}

بعد ما تدفع قولي 'تم الدفع'! 😊"
"""

    def _generate_invoice_file(self, context: ConversationContext) -> str:
        """توليد ملف الفاتورة فقط"""
        try:
            from app.services.pdf_generator import PDFGenerator
            from app.engine.vehicle_manager import VehicleManager
            
            self.logger.info("📄 Generating invoice document...")
            
            # تحضير بيانات السيارة
            vehicle_brand, vehicle_model, vehicle_year, plate_no, vehicle_value = "", "", "", "", 0
            
            manager_data = context.vehicle_data.get("manager", {})
            if manager_data:
                vm = VehicleManager.from_dict(manager_data)
                if vm.current_vehicle:
                    v = vm.current_vehicle
                    vehicle_brand = v.brand or ""
                    vehicle_model = v.model or ""
                    vehicle_year = v.year or ""
                    plate_no = v.plate_no or ""
                    vehicle_value = v.value or 0
            
            offer = context.selected_offer or {}
            
            # تحضير البيانات
            doc_data = {
                'invoice_id': context.invoice_id,
                'sadad_number': getattr(context, 'sadad_number', None),
                'national_id': context.profile_data.get('national_id', ''),
                'vehicle_brand': vehicle_brand,
                'vehicle_model': vehicle_model,
                'vehicle_year': vehicle_year,
                'plate_no': plate_no,
                'vehicle_value': vehicle_value,
                'company_name': offer.get('company', 'شركة التأمين'),
                'coverage_type': offer.get('type', 'تأمين شامل'),
                'total_amount': offer.get('total_premium', offer.get('price', 0)),
            }
            
            # توليد الفاتورة
            generator = PDFGenerator()
            invoice_path = generator.save_invoice_html(doc_data)
            
            if invoice_path:
                import os
                filename = os.path.basename(invoice_path)
                context.invoice_pdf_path = invoice_path
                url = f"/api/v1/documents/{filename}"
                self.logger.info(f"✅ Invoice generated: {invoice_path}")
                return url
                
        except Exception as e:
            self.logger.error(f"Error generating invoice: {e}")
        
        return ""

    def _generate_sadad(self) -> str:
        """توليد رقم سداد افتراضي"""
        import random
        return f"177{random.randint(10000000000, 99999999999)}"
    

    
    def handle_intent(
        self,
        intent,
        context: ConversationContext,
        extracted_data: Dict[str, Any]
    ) -> StageResponse:
        """معالجة النية في مرحلة إصدار الفاتورة"""
        from app.engine.ai_intent_analyzer import UserIntent
        
        # إذا أكد الدفع
        if intent == UserIntent.CONFIRM:
            self.logger.info("🧠 AI Transition: INVOICE_ISSUED -> PAYMENT_DONE")
            
            # ✅ توليد ملفات الفاتورة والوثيقة عند تأكيد الدفع
            self._generate_documents(context)
            
            return StageResponse(
                should_transition=True,
                next_stage=ConversationStage.PAYMENT_DONE
            )
        
        return StageResponse(should_transition=False)
    
    def _generate_documents(self, context: ConversationContext):
        """توليد ملفات الفاتورة والوثيقة"""
        try:
            from app.services.pdf_generator import generate_payment_documents
            from app.engine.vehicle_manager import VehicleManager
            
            self.logger.info("📄 Generating invoice and policy documents...")
            
            # تحضير بيانات السيارة
            vehicle_brand = ""
            vehicle_model = ""
            vehicle_year = ""
            plate_no = ""
            vehicle_value = 0
            
            manager_data = context.vehicle_data.get("manager", {})
            if manager_data:
                vm = VehicleManager.from_dict(manager_data)
                if vm.current_vehicle:
                    v = vm.current_vehicle
                    vehicle_brand = v.brand or ""
                    vehicle_model = v.model or ""
                    vehicle_year = v.year or ""
                    plate_no = v.plate_no or ""
                    vehicle_value = v.value or 0
            
            offer = context.selected_offer or {}
            
            # تحضير البيانات للـ PDF Generator
            doc_data = {
                'invoice_id': context.invoice_id,
                'policy_id': context.policy_id,
                'sadad_number': getattr(context, 'sadad_number', None),
                'national_id': context.profile_data.get('national_id', ''),
                'birth_date': context.profile_data.get('birth_date', ''),
                'phone': context.profile_data.get('phone', ''),
                'vehicle_brand': vehicle_brand,
                'vehicle_model': vehicle_model,
                'vehicle_year': vehicle_year,
                'plate_no': plate_no,
                'vehicle_value': vehicle_value,
                'company_name': offer.get('company', 'شركة التأمين'),
                'coverage_type': offer.get('type', 'تأمين شامل'),
                'offer_code': offer.get('code', 'N/A'),
                'total_amount': offer.get('total_premium', offer.get('price', 0)),
            }
            
            # توليد المستندات
            result = generate_payment_documents(doc_data)
            
            if result.get('success'):
                context.invoice_pdf_path = result.get('invoice_path')
                context.policy_pdf_path = result.get('policy_path')
                self.logger.info(f"✅ Documents generated: Invoice={result.get('invoice_path')}, Policy={result.get('policy_path')}")
            else:
                self.logger.warning(f"⚠️ Document generation failed: {result.get('error')}")
                
        except Exception as e:
            self.logger.error(f"Error generating documents: {e}")


# Singleton instance
invoice_issued_stage = InvoiceIssuedStage()
