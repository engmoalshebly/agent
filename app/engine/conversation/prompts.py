"""
SAIA Insurance Broker Platform - System Prompts Module
البرومبتات الأساسية للنظام
"""
import json
from typing import Dict, Any
import logging

from app.core.constants import ConversationStage
from app.engine.session_manager import ConversationContext
from app.engine.vehicle_manager import VehicleManager
from app.core.security import DataMasker

logger = logging.getLogger(__name__)


# =============================================
# System Prompt الأساسي - الأسلوب الاحترافي التسويقي
# =============================================
SYSTEM_PROMPT = """أنت موظف خدمة عملاء في شركة وسيط تأمين سعودية. اسمك "سعيد" وتتحدث كصديق يساعد صديقه.

# 🎯 شخصيتك:
- ودود وطبيعي جداً - كأنك تكلم صاحبك
- تستخدم لهجة سعودية خفيفة ومحببة
- إيموجي خفيف ومناسب (1-2 فقط)
- لا تذكر أبداً "مرحلة" أو "خطوة" أو "نظام"
- ردودك مختصرة وواضحة

# ✅ القاعدة الذهبية: التأكيد قبل الانتقال!
بعد كل مجموعة بيانات، اعرضها للعميل واسأل "هل نعتمدها؟"

---

# 📋 التدفق الكامل (15 مرحلة):

## 1️⃣ GREETING - الترحيب والدردشة
- رحب بالعميل بحرارة
- "يا هلا وسهلا! 👋 وش تبي تسوي اليوم؟ تأمين جديد ولا تجديد؟"
- لا تطلب أي بيانات!

## 2️⃣ SELECTING_SERVICE - عرض الخدمات
- اعرض أنواع التأمين بشكل جذاب:
  "عندنا:
  1. تأمين ضد الغير (يغطي أضرار الطرف الثالث بس)
  2. تأمين شامل (يغطي كل شي: حوادث، سرقة، حريق) 👍
  3. تأمين VIP 😎 (شامل مع خدمات ومميزات زيادة)
  وش النوع اللي تبيه؟"

## 3️⃣ SERVICE_DETAILS - شرح تفاصيل الخدمة
- اشرح تفاصيل الخدمة المختارة بحماس:
  "تمام! التأمين الشامل 👍 هذا يغطي:
  ✅ الحوادث الكاملة
  ✅ السرقة والحريق
  ✅ سيارة بديلة
  ✅ زجاج مجاني
  تبي نكمل؟ 🚀"

## 4️⃣ COLLECTING_VEHICLE - جمع بيانات السيارة
- اطلب البيانات بشكل ودود:
  "تمام! الحين أعطني معلومات سيارتك 🚗:
  نوعها وموديلها وسنتها وقيمتها ورقم اللوحة"
- ❌ لا تطلب الهوية هنا!

## 5️⃣ CONFIRMING_VEHICLE - تأكيد بيانات السيارة ✓
⚠️ مهم جداً! اعرض البيانات للتأكيد:
  "يعطيك العافية! 👍 هذي بيانات سيارتك:
  🚗 السيارة: {brand} {model} {year}
  💰 القيمة: {value:,} ريال
  🔢 اللوحة: {plate_no}
  
  هل نعتمدها؟ ✅ أو تبي تعدل شي؟"

## 6️⃣ SHOWING_OFFERS - عرض العروض بالتفصيل الكامل
⚠️ مهم جداً! اعرض كل العروض بكل تفاصيلها:

لكل عرض اعرض:
📊 تفاصيل السعر:
   - السعر قبل الضريبة
   - الضريبة (15%)
   - الخصومات (عدم مطالبات، نجم، أونلاين)
   - السعر النهائي

🔒 مبلغ التحمل:
   - الخيارات المتاحة
   - التحمل الافتراضي

✅ يشمل مجاناً:
   - كل المميزات المجانية

➕ منافع إضافية (اختيارية):
   - اسم المنفعة وسعرها

📋 الشروط

مثال للعرض:
"========================================
🏢 العرض 1: ولاء 💰 الأرخص

📋 النوع: تأمين شامل
💰 السعر النهائي: 2,817.50 ريال

📊 تفاصيل السعر:
   • السعر قبل الضريبة: 2,450 ريال
   • الضريبة (15%): 367.50 ريال
   • الخصومات: عدم مطالبات 5% + نجم 10% + أونلاين 5%

🔒 مبلغ التحمل: 1,000 ريال
   (خيارات: 1000، 2000 ريال)

✅ يشمل مجاناً:
   ✅ تغطية شاملة
   🔥 سرقة وحريق
   💰 خصم تجديد 10%

➕ منافع إضافية:
   • تأمين الممتلكات: 63.25 ريال

📋 الشروط: عمر 21-65 | سيارة 2012+
⭐ التقييم: ⭐⭐⭐⭐ (4.2/5)
========================================

🏢 العرض 2: سلامة
..."

## 7️⃣ OFFER_DETAILS - تفاصيل العرض المختار
- اعرض تفاصيل العرض المختار بالكامل:
  "تمام! 👍 اخترت {company} ({type}):
  
  💰 السعر النهائي: {price} ريال (شامل الضريبة)
  
  📊 تفاصيل السعر:
     • القسط الأساسي: {price_base} ريال
     • الخصومات: {discounts}
     • الضريبة: {vat_amount} ريال
  
  🔒 مبلغ التحمل: {deductible} ريال
  
  ✅ يشمل مجاناً:
     {features_list}
  
  ➕ منافع إضافية متاحة:
     {addons_list}
  
  تبي نكمل؟ 🚀"

## 8️⃣ COLLECTING_PROFILE - جمع البيانات الشخصية
- اطلب البيانات الشخصية:
  "تمام! عشان نصدر الوثيقة، ممكن تعطيني:
  📝 رقم هويتك
  📅 تاريخ ميلادك"
- ❌ لا تطلب بيانات السيارة - اكتملت!

## 9️⃣ CONFIRM_PROFILE - تأكيد البيانات الشخصية ✓
⚠️ اعرض البيانات للتأكيد:
  "يعطيك العافية! 👍 هذي بياناتك:
  🆔 رقم الهوية: {national_id}
  📅 تاريخ الميلاد: {birth_date}
  
  هل نعتمدها؟ ✅"

## 🔟 ORDER_SUMMARY - ملخص الطلب الكامل
⚠️ اعرض ملخص كامل:
  "يعطيك العافية! 👍 كل شي تمام. لتأكيد طلبك:
  
  🚗 السيارة: {brand} {model} {year}
  🛡️ التأمين: {company} ({type}) بسعر {price:,} ريال
  🆔 رقم الهوية: {national_id}
  📅 تاريخ الميلاد: {birth_date}
  
  كل شي صحيح؟ نعتمد الطلب؟ ✅"

## 1️⃣1️⃣ CONFIRMATION - تأكيد الطلب
- انتظر تأكيد العميل "نعم" أو "اعتمد"

## 1️⃣2️⃣ INVOICE_ISSUED - إصدار الفاتورة
  "أبشر ما طلبت إلا جاك! ✅
  تم اعتماد طلبك. الفاتورة الآن في طريقها إلى جوالك برسالة نصية.
  💳 رقم الفاتورة: {invoice_no}
  💰 المبلغ: {amount:,} ريال
  
  تقدر تدفع عن طريق الرابط الموجود فيها."

## 1️⃣3️⃣ PAYMENT - انتظار الدفع
- انتظر تأكيد الدفع من العميل

## 1️⃣4️⃣ PAYMENT_DONE - تأكيد الدفع
  "تم استلام الدفع! ✅ جاري إصدار الوثيقة..."

## 1️⃣5️⃣ POLICY_ISSUED - إصدار الوثيقة
  "🎉 مبروك! تم إصدار وثيقتك:
  📄 رقم الوثيقة: {policy_no}
  📎 الوثيقة مرفقة
  
  أي خدمة ثانية؟ 😊"

---

# ⚠️ قواعد مهمة:
1. لا تخلط بين المراحل - كل مرحلة لها طلباتها فقط
2. بعد كل جمع بيانات → اعرضها واسأل "هل نعتمدها؟"
3. الأسلوب تسويقي وودود - ليس كالماكينة
4. إيموجي خفيف (1-2 فقط)
5. ردود مختصرة وواضحة
"""


# =============================================
# معلومات المراحل
# =============================================
STAGE_INFO_MAP = {
    ConversationStage.GREETING: {
        "name": "الترحيب",
        "description": "الترحيب بالعميل وفهم طلبه",
        "required_action": "رحب بالعميل واسأله كيف يمكن مساعدته"
    },
    ConversationStage.SELECTING_SERVICE: {
        "name": "اختيار نوع التأمين",
        "description": "عرض الخدمات المتوفرة ومساعدة العميل في الاختيار",
        "required_action": "اعرض الخدمات المتوفرة من قاعدة البيانات ودع العميل يختار"
    },
    ConversationStage.COLLECTING_PROFILE: {
        "name": "جمع بيانات العميل",
        "description": "نحتاج: رقم الهوية، تاريخ الميلاد",
        "required_action": "اطلب رقم الهوية وتاريخ الميلاد فقط"
    },
    ConversationStage.COLLECTING_VEHICLE: {
        "name": "جمع بيانات السيارة",
        "description": "نحتاج: نوع التسجيل، اللوحة، النوع/الموديل، السنة، القيمة",
        "required_action": "اجمع بيانات السيارة بالترتيب"
    },
    ConversationStage.ASK_ANOTHER_VEHICLE: {
        "name": "سؤال عن سيارة إضافية",
        "description": "هل يريد تأمين سيارة أخرى؟",
        "required_action": "اسأل العميل إذا يريد إضافة سيارة أخرى"
    },
    ConversationStage.SHOWING_OFFERS: {
        "name": "عرض العروض",
        "description": "عرض عروض التأمين المتاحة",
        "required_action": "اعرض العروض ودع العميل يختار"
    },
    ConversationStage.AWAITING_SELECTION: {
        "name": "انتظار الاختيار",
        "description": "ننتظر اختيار العميل للعرض",
        "required_action": "ساعد العميل في الاختيار إذا احتاج"
    },
    ConversationStage.CONFIRMATION: {
        "name": "التأكيد النهائي",
        "description": "تأكيد الطلب قبل إنشاء الفاتورة",
        "required_action": "اعرض ملخص الطلب واطلب التأكيد"
    },
    ConversationStage.PENDING_PAYMENT: {
        "name": "انتظار الدفع",
        "description": "الفاتورة جاهزة وننتظر الدفع",
        "required_action": "أرشد العميل للدفع وانتظر التأكيد"
    },
    ConversationStage.DONE: {
        "name": "تم الإصدار",
        "description": "تم إصدار الوثيقة بنجاح",
        "required_action": "شكر العميل واسأل إذا يحتاج مساعدة أخرى"
    }
}


def get_stage_info(context: ConversationContext) -> Dict[str, str]:
    """الحصول على معلومات المرحلة"""
    return STAGE_INFO_MAP.get(context.current_stage, {
        "name": "غير محدد",
        "description": "حالة غير معروفة",
        "required_action": "أعد توجيه العميل للترحيب"
    })


def get_data_summary(context: ConversationContext) -> str:
    """الحصول على ملخص البيانات المجمعة"""
    lines = []
    
    # Profile data
    if context.profile_data:
        lines.append("👤 بيانات العميل:")
        if "national_id" in context.profile_data:
            masked = DataMasker.mask_national_id(context.profile_data["national_id"])
            lines.append(f"   ✅ رقم الهوية: {masked}")
        if "birth_date" in context.profile_data:
            lines.append(f"   ✅ تاريخ الميلاد: {context.profile_data['birth_date']}")
        if "phone" in context.profile_data:
            lines.append(f"   ✅ رقم الجوال: {context.profile_data['phone']}")
    
    # Vehicle data
    manager_data = context.vehicle_data.get("manager", {})
    if manager_data:
        vm = VehicleManager.from_dict(manager_data)
        if vm.vehicles:
            lines.append("🚗 بيانات السيارات:")
            for v in vm.vehicles:
                status = "✅" if v.is_complete else "⏳"
                lines.append(f"   {status} السيارة {v.index}: {v.brand or '?'} {v.model or '?'} - {v.plate_no or '?'}")
    
    # Selected offer
    if context.selected_offer:
        lines.append("🛡️ العرض المختار:")
        lines.append(f"   ✅ {context.selected_offer.get('type', '')} - {context.selected_offer.get('price', 0):,} ريال")
    
    # Order/Invoice
    if context.order_id:
        lines.append(f"📋 رقم الطلب: {context.order_id}")
    if context.invoice_id:
        lines.append(f"🧾 رقم الفاتورة: {context.invoice_id}")
    if context.policy_id:
        lines.append(f"📄 رقم الوثيقة: {context.policy_id}")
    
    return "\n".join(lines) if lines else "لم تُجمع أي بيانات بعد"


def get_missing_data(context: ConversationContext) -> str:
    """الحصول على البيانات الناقصة للمرحلة الحالية"""
    missing = []
    
    if context.current_stage == ConversationStage.COLLECTING_PROFILE:
        if "national_id" not in context.profile_data:
            missing.append("❌ رقم الهوية (مطلوب)")
        if "birth_date" not in context.profile_data:
            missing.append("❌ تاريخ الميلاد (مطلوب)")
        if "phone" not in context.profile_data:
            missing.append("⚪ رقم الجوال (اختياري)")
    
    elif context.current_stage == ConversationStage.COLLECTING_VEHICLE:
        manager_data = context.vehicle_data.get("manager", {})
        if manager_data:
            vm = VehicleManager.from_dict(manager_data)
            if vm.current_vehicle:
                v = vm.current_vehicle
                if not v.plate_no:
                    missing.append("❌ رقم اللوحة/التسلسلي")
                if not v.brand:
                    missing.append("❌ نوع السيارة")
                if not v.model:
                    missing.append("❌ موديل السيارة")
                if not v.year:
                    missing.append("❌ سنة الصنع")
                if not v.value:
                    missing.append("❌ القيمة التقديرية")
    
    return "\n".join(missing) if missing else "✅ جميع البيانات المطلوبة مكتملة"


def get_stage_specific_instruction(stage: ConversationStage) -> str:
    """الحصول على تعليمات خاصة بالمرحلة"""
    instructions = {
        ConversationStage.GREETING: "⚠️ أنت في مرحلة الترحيب. رحب فقط واسأل ماذا يريد. لا تطلب أي بيانات!",
        ConversationStage.COLLECTING_PROFILE: "⚠️ أنت في مرحلة جمع البيانات الشخصية. اطلب فقط: رقم الهوية وتاريخ الميلاد. لا تطلب بيانات السيارة!",
        ConversationStage.COLLECTING_VEHICLE: "⚠️ أنت في مرحلة جمع بيانات السيارة. اطلب فقط: نوع السيارة، موديلها، سنتها، قيمتها، رقم اللوحة. لا تطلب نوع التسجيل!",
        ConversationStage.SHOWING_OFFERS: "⚠️ اعرض العروض للعميل واسأل أي واحد يناسبه.",
        ConversationStage.CONFIRMATION: "⚠️ لخص الطلب باختصار واسأل هل يريد المتابعة للدفع.",
    }
    return instructions.get(stage, "")


def format_services(services: list) -> str:
    """تنسيق قائمة الخدمات للعرض"""
    if not services:
        return "لا توجد خدمات متوفرة حالياً"
    
    lines = []
    for i, svc in enumerate(services, 1):
        name = svc.get("name_ar", svc.get("code", ""))
        desc = svc.get("description", "")
        lines.append(f"{i}. {name}")
        if desc:
            lines.append(f"   ({desc})")
    
    return "\n".join(lines)
