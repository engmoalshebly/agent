"""
Context Builder - Builds clean context snapshots for LLM
"""
import json
from typing import Dict, Any
from datetime import datetime
import logging

from app.engine.session_manager import ConversationContext
from app.core.constants import ConversationStage

logger = logging.getLogger(__name__)


class ContextBuilder:
    """Builds structured context snapshots instead of long chat history"""
    
    def build_snapshot(self, context: ConversationContext) -> str:
        """
        Build a clean, structured context snapshot for LLM.
        This replaces long chat history with current state summary.
        """
        
        stage_info = self._get_stage_info(context.current_stage)
        profile_summary = self._summarize_profile(context.profile_data or {})
        vehicle_summary = self._summarize_vehicle(context.vehicle_data or {})
        progress_summary = self._summarize_progress(context)
        
        snapshot = f"""📍 CURRENT STAGE: {context.current_stage.value}
{stage_info}

📋 COLLECTED DATA:
{profile_summary}
{vehicle_summary}

📈 PROGRESS:
{progress_summary}

⏳ LAST QUESTION: {context.last_question or 'None'}
🔤 EXPECTED INPUT: {context.awaiting_input_type or 'Any'}

🆔 CONVERSATION ID: {context.conversation_id}
⏰ LAST UPDATED: {context.updated_at.strftime('%H:%M') if context.updated_at else 'Unknown'}"""

        return snapshot
    
    def _get_stage_info(self, stage: ConversationStage) -> str:
        """Get detailed info about current stage"""
        
        stage_details = {
            ConversationStage.GREETING: {
                "desc": "الترحيب بالعميل وفهم طلبه",
                "next": "انتقل لجمع البيانات إذا طلب تأمين",
                "questions": ["كيف أقدر أساعدك؟", "تريد تأمين سيارة؟"]
            },
            ConversationStage.COLLECTING_PROFILE: {
                "desc": "جمع بيانات العميل الشخصية",
                "next": "انتقل لبيانات السيارة عند اكتمال البيانات",
                "questions": ["رقم الهوية (10 أرقام)", "تاريخ الميلاد", "رقم الجوال"]
            },
            ConversationStage.COLLECTING_VEHICLE: {
                "desc": "جمع بيانات السيارة",
                "next": "اسأل عن سيارة إضافية أو انتقل للعروض",
                "questions": ["نوع التسجيل", "رقم اللوحة", "نوع وموديل السيارة", "قيمة السيارة"]
            },
            ConversationStage.ASK_ANOTHER_VEHICLE: {
                "desc": "سؤال العميل عن سيارة إضافية",
                "next": "عد لجمع بيانات سيارة أو انتقل للعروض",
                "questions": ["هل تريد تأمين سيارة أخرى؟"]
            },
            ConversationStage.SHOWING_OFFERS: {
                "desc": "عرض عروض التأمين المتاحة",
                "next": "انتظار اختيار العميل",
                "questions": ["اختر العرض المناسب لك"]
            },
            ConversationStage.AWAITING_SELECTION: {
                "desc": "انتظار اختيار العميل لأحد العروض",
                "next": "انتقل للتأكيد",
                "questions": ["أي عرض تختار؟"]
            },
            ConversationStage.CONFIRMATION: {
                "desc": "تأكيد الطلب النهائي",
                "next": "إنشاء فاتورة أو تعديل البيانات",
                "questions": ["هل تؤكد الطلب؟", "تريد تعديل شيء؟"]
            },
            ConversationStage.PENDING_PAYMENT: {
                "desc": "انتظار تأكيد الدفع",
                "next": "إصدار الوثيقة عند تأكيد الدفع",
                "questions": ["هل تم الدفع؟"]
            },
            ConversationStage.ISSUING_POLICY: {
                "desc": "إصدار وثيقة التأمين",
                "next": "اكتمال العملية",
                "questions": []
            },
            ConversationStage.DONE: {
                "desc": "تم إصدار الوثيقة بنجاح",
                "next": "عملية جديدة أو مساعدة إضافية",
                "questions": ["هل تحتاج مساعدة أخرى؟"]
            }
        }
        
        info = stage_details.get(stage, {
            "desc": "مرحلة غير محددة",
            "next": "تحديد المرحلة التالية",
            "questions": []
        })
        
        return f"""الوصف: {info['desc']}
التالي: {info['next']}
الأسئلة المتوقعة: {', '.join(info['questions']) if info['questions'] else 'لا توجد'}"""
    
    def _summarize_profile(self, profile_data: Dict[str, Any]) -> str:
        """Summarize profile data"""
        
        if not profile_data:
            return "👤 بيانات العميل: لم تُجمع بعد"
        
        summary_parts = ["👤 بيانات العميل:"]
        
        if "national_id" in profile_data:
            masked_id = profile_data["national_id"][:3] + "*******"
            summary_parts.append(f"  • الهوية: {masked_id} ✅")
        else:
            summary_parts.append("  • الهوية: مطلوبة ❌")
        
        if "birth_date" in profile_data:
            summary_parts.append(f"  • تاريخ الميلاد: {profile_data['birth_date']} ✅")
        else:
            summary_parts.append("  • تاريخ الميلاد: مطلوب ❌")
        
        if "phone" in profile_data:
            masked_phone = profile_data["phone"][:4] + "******"
            summary_parts.append(f"  • الجوال: {masked_phone} ✅")
        else:
            summary_parts.append("  • الجوال: مطلوب ❌")
        
        return "\n".join(summary_parts)
    
    def _summarize_vehicle(self, vehicle_data: Dict[str, Any]) -> str:
        """Summarize vehicle data"""
        
        if not vehicle_data:
            return "🚗 بيانات السيارة: لم تُجمع بعد"
        
        summary_parts = ["🚗 بيانات السيارة:"]
        
        # Handle VehicleManager data structure
        if "manager" in vehicle_data:
            manager_data = vehicle_data["manager"]
            vehicles = manager_data.get("vehicles", [])
            
            if vehicles:
                for i, vehicle in enumerate(vehicles, 1):
                    summary_parts.append(f"  السيارة {i}:")
                    
                    if vehicle.get("plate_no"):
                        summary_parts.append(f"    • اللوحة: {vehicle['plate_no']} ✅")
                    else:
                        summary_parts.append("    • اللوحة: مطلوبة ❌")
                    
                    if vehicle.get("brand"):
                        brand_model = f"{vehicle['brand']} {vehicle.get('model', '')}"
                        summary_parts.append(f"    • النوع: {brand_model.strip()} ✅")
                    else:
                        summary_parts.append("    • النوع: مطلوب ❌")
                    
                    if vehicle.get("value"):
                        summary_parts.append(f"    • القيمة: {vehicle['value']:,} ريال ✅")
                    else:
                        summary_parts.append("    • القيمة: مطلوبة ❌")
            else:
                summary_parts.append("  • لا توجد سيارات مُسجلة")
        else:
            # Direct vehicle data
            if "plate_no" in vehicle_data:
                summary_parts.append(f"  • اللوحة: {vehicle_data['plate_no']} ✅")
            
            if "brand" in vehicle_data:
                brand_model = f"{vehicle_data['brand']} {vehicle_data.get('model', '')}"
                summary_parts.append(f"  • النوع: {brand_model.strip()} ✅")
            
            if "value" in vehicle_data:
                summary_parts.append(f"  • القيمة: {vehicle_data['value']:,} ريال ✅")
        
        return "\n".join(summary_parts)
    
    def _summarize_progress(self, context: ConversationContext) -> str:
        """Summarize overall progress"""
        
        progress_parts = []
        
        # Profile completion
        profile_complete = bool(
            context.profile_data and 
            "national_id" in context.profile_data and 
            "birth_date" in context.profile_data
        )
        progress_parts.append(f"البيانات الشخصية: {'مكتملة ✅' if profile_complete else 'ناقصة ❌'}")
        
        # Vehicle completion
        vehicle_complete = bool(
            context.vehicle_data and 
            context.vehicle_data.get("manager", {}).get("vehicles")
        )
        progress_parts.append(f"بيانات السيارة: {'مكتملة ✅' if vehicle_complete else 'ناقصة ❌'}")
        
        # Offer selection
        if context.selected_offer:
            offer_type = context.selected_offer.get("type", "غير محدد")
            offer_price = context.selected_offer.get("price", 0)
            progress_parts.append(f"العرض المختار: {offer_type} ({offer_price:,} ريال) ✅")
        else:
            progress_parts.append("العرض المختار: لم يُختر بعد ❌")
        
        # Order status
        if context.order_id:
            progress_parts.append(f"رقم الطلب: {context.order_id} ✅")
        
        if context.invoice_id:
            progress_parts.append(f"رقم الفاتورة: {context.invoice_id} ✅")
        
        if context.policy_id:
            progress_parts.append(f"رقم الوثيقة: {context.policy_id} ✅")
        
        return "\n".join(progress_parts)
    
    def build_minimal_context(self, context: ConversationContext) -> str:
        """Build minimal context for simple operations"""
        
        return f"""Stage: {context.current_stage.value}
Last Question: {context.last_question or 'None'}
Profile Complete: {bool(context.profile_data and 'national_id' in context.profile_data)}
Vehicle Complete: {bool(context.vehicle_data)}
Selected Offer: {bool(context.selected_offer)}"""