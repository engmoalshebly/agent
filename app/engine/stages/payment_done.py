"""
Payment Done Stage - مرحلة تأكيد الدفع وإصدار الوثيقة مع PDF
"""
from typing import Dict, Any, List
from app.core.constants import ConversationStage
from app.engine.session_manager import ConversationContext
from .base_stage import BaseStage, StageResponse


class PaymentDoneStage(BaseStage):
    """مرحلة تأكيد الدفع وإصدار وثيقة التأمين + PDF"""
    
    stage = ConversationStage.PAYMENT_DONE
    order = 12
    name_ar = "الدفع"
    
    def __init__(self):
        super().__init__()
        self.invoice_repo = None
        self.order_repo = None
        self.policy_repo = None
        self._init_repos()
    
    def _init_repos(self):
        try:
            from app.db.repositories.invoice_repository import invoice_repository
            from app.db.repositories.order_repository import order_repository
            from app.db.repositories.policy_repository import policy_repository
            self.invoice_repo = invoice_repository
            self.order_repo = order_repository
            self.policy_repo = policy_repository
        except Exception as e:
            self.logger.warning(f"Could not init repos: {e}")
    
    def get_stage_info(self) -> Dict[str, str]:
        return {
            "name": "تم الدفع - إصدار الوثيقة",
            "description": "تأكيد الدفع وإصدار وثيقة التأمين مع PDF",
            "required_action": "أكد استلام الدفع وأعط العميل الفاتورة والوثيقة"
        }
    
    def get_required_fields(self) -> List[str]:
        """لا توجد حقول - هذه المرحلة النهائية"""
        return []
    
    def get_collected_fields(self, context: ConversationContext) -> Dict[str, Any]:
        """الحقول المجمعة"""
        collected = {}
        if context.policy_id:
            collected["policy_id"] = context.policy_id
        return collected
    
    def get_prompt_instructions(self, context: ConversationContext) -> str:
        offer = context.selected_offer or {}
        policy_expiry = getattr(context, 'policy_expiry', None) or self._get_expiry_date()
        
        # روابط المستندات
        invoice_link = getattr(context, 'invoice_pdf_path', None)
        policy_link = getattr(context, 'policy_pdf_path', None)
        
        docs_section = ""
        if invoice_link or policy_link:
            docs_section = f"""
📎 **المستندات المرفقة:**
"""
            if invoice_link:
                docs_section += f"• 🧾 الفاتورة: تم إرسالها\n"
            if policy_link:
                docs_section += f"• 📄 وثيقة التأمين: تم إرسالها\n"
        
        return f"""⚠️ أنت في مرحلة إصدار الوثيقة النهائية!

🎉 **تم الدفع بنجاح!**

📄 **بيانات الوثيقة:**
━━━━━━━━━━━━━━━━━━━
📋 رقم الوثيقة: {context.policy_id}
🏢 الشركة: {offer.get('company', 'غير محدد')}
🛡️ نوع التغطية: {offer.get('type', 'شامل')}
📅 صالحة حتى: {policy_expiry}
{docs_section}
**تعليمات مهمة:**
- ✅ أخبره أن الفاتورة ووثيقة التأمين مرفقة
- ✅ أعط رقم الوثيقة
- ✅ هنئه واسأله إذا يحتاج شيء آخر

**مثال الرد:**
"مبروك! 🎉🎊

تم إصدار وثيقة التأمين بنجاح!

━━━━━━━━━━━━━━━━━━━
📋 **رقم الوثيقة:** {context.policy_id}
🛡️ **التغطية:** {offer.get('type', 'تأمين شامل')}
🏢 **الشركة:** {offer.get('company', 'غير محدد')}
📅 **صالحة حتى:** {policy_expiry}
━━━━━━━━━━━━━━━━━━━

📎 **المرفقات:**
🧾 فاتورة السداد - مرفقة
📄 وثيقة التأمين - مرفقة

شكراً لثقتك فينا! 🙏
تحتاج أي شي ثاني?"
"""

    
    def _get_expiry_date(self) -> str:
        """حساب تاريخ انتهاء الوثيقة (سنة من الآن)"""
        from datetime import datetime, timedelta
        expiry = datetime.now() + timedelta(days=365)
        return expiry.strftime("%Y/%m/%d")
    
    def handle_intent(
        self,
        intent,
        context: ConversationContext,
        extracted_data: Dict[str, Any]
    ) -> StageResponse:
        """معالجة النية في مرحلة إصدار الوثيقة"""
        from app.engine.ai_intent_analyzer import UserIntent
        from app.engine.session_manager import ConversationStage
        from datetime import datetime
        
        # ✅ معالجة طلب تأمين جديد
        if intent == UserIntent.SELECT_SERVICE or extracted_data.get("service_type"):
            self.logger.info("🆕 User wants new insurance - transitioning to collecting_vehicle")
            # حفظ الوثيقة الحالية في السجل قبل بدء الجديد
            self._save_policy_to_history(context)
            
            # تهيئة بيانات السيارة الجديدة
            from app.engine.vehicle_manager import VehicleManager
            service_type = extracted_data.get("service_type", "comprehensive")
            context.profile_data["service_type"] = service_type
            
            # مسح بيانات السيارة القديمة فقط (الاحتفاظ بالبيانات الشخصية)
            vm = VehicleManager(context.conversation_id)
            vm.start_new_vehicle()
            context.vehicle_data = {"manager": vm.to_dict()}
            
            # مسح بيانات الطلب السابق
            context.selected_offer = None
            context.order_id = None
            context.invoice_id = None
            context.policy_id = None
            
            return StageResponse(
                should_transition=True,
                next_stage=ConversationStage.COLLECTING_VEHICLE,
                prompt_addition="ممتاز! نبدأ بتأمين جديد. أعطني بيانات السيارة الجديدة 🚗"
            )
        
        # ✅ معالجة طلب السجل مع السعر
        if intent == UserIntent.ASK_HISTORY:
            self.logger.info("📋 User asking for history - showing price details")
            offer = context.selected_offer or {}
            price = offer.get("total_premium", offer.get("price", 0))
            
            history_msg = f"""
📋 **آخر تأمين لك:**
• رقم الوثيقة: {context.policy_id}
• الشركة: {offer.get('company', 'غير محدد')}
• السعر الإجمالي: {price:,.2f} ريال
• التغطية: {offer.get('type', 'شامل')}
"""
            return StageResponse(
                should_transition=False,
                prompt_addition=history_msg
            )
        
        # تسجيل الدفع وإصدار الوثيقة + توليد PDF
        self._process_payment_and_issue_policy(context)
        self._generate_documents(context)
        
        # ✅ حفظ الوثيقة في سجل العميل
        self._save_policy_to_history(context)
        
        # هذه هي المرحلة النهائية
        return StageResponse(should_transition=False)
    
    def _save_policy_to_history(self, context: ConversationContext):
        """حفظ الوثيقة في سجل العميل"""
        from datetime import datetime
        
        if not context.policy_id:
            return
        
        offer = context.selected_offer or {}
        
        # بيانات الوثيقة
        policy_record = {
            "policy_id": context.policy_id,
            "order_id": context.order_id,
            "invoice_id": context.invoice_id,
            "company": offer.get("company", ""),
            "coverage_type": offer.get("type", "شامل"),
            "price": offer.get("total_premium", offer.get("price", 0)),
            "vehicle_brand": context.vehicle_data.get("brand", ""),
            "vehicle_model": context.vehicle_data.get("model", ""),
            "created_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        # إضافة للقائمة (تجنب التكرار)
        if not hasattr(context, 'policies') or context.policies is None:
            context.policies = []
        
        if not any(p.get("policy_id") == context.policy_id for p in context.policies):
            context.policies.append(policy_record)
            self.logger.info(f"✅ Policy {context.policy_id} added to customer history (total: {len(context.policies)})")
    
    def _generate_documents(self, context: ConversationContext):
        """توليد ملفات الفاتورة والوثيقة"""
        try:
            from app.services.pdf_generator import generate_payment_documents
            from app.engine.vehicle_manager import VehicleManager
            
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
    
    def _process_payment_and_issue_policy(self, context: ConversationContext):
        """تسجيل الدفع وإصدار الوثيقة"""
        if not context.invoice_id:
            self._generate_fallback_ids(context)
            return
        
        try:
            # تسجيل الدفع
            if self.invoice_repo:
                self.invoice_repo.mark_as_paid(context.invoice_id)
                self.logger.info(f"✅ Invoice {context.invoice_id} marked as paid")
            
            # تحديث حالة الطلب
            if self.order_repo and context.order_id:
                self.order_repo.update_order_status(context.order_id, "policy_issued")
            
            # إصدار الوثيقة
            if self.policy_repo and not context.policy_id:
                selected_offer = context.selected_offer or {}
                policy = self.policy_repo.create_policy(
                    order_id=context.order_id,
                    user_id=int(context.user_id) if context.user_id else 1,
                    vehicle_id=context.vehicle_data.get("db_id", 1),
                    company_id=selected_offer.get("company_id", 1)
                )
                if policy and policy.get("id"):
                    context.policy_id = policy["id"]
                    self.logger.info(f"✅ Policy issued: {policy.get('policy_no')}")
                    
        except Exception as e:
            self.logger.error(f"Error processing payment: {e}")
            self._generate_fallback_ids(context)
    
    def _generate_fallback_ids(self, context: ConversationContext):
        """IDs احتياطية"""
        import random
        if not context.policy_id:
            context.policy_id = random.randint(10000, 99999)


# Singleton instance
payment_done_stage = PaymentDoneStage()

