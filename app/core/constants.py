"""
SAIA Insurance Broker Platform - Constants & Enums
"""
from enum import Enum


class ConversationStage(str, Enum):
    """Conversation flow stages - 14 مرحلة احترافية"""
    
    # Session management
    SESSION_CHECK = "session_check"
    SESSION_RESUME = "session_resume"
    
    # ===== التدفق الاحترافي (14 مرحلة) =====
    
    # 1. الدردشة والترحيب
    GREETING = "greeting"
    
    # 2. عرض الخدمات
    SHOWING_SERVICES = "showing_services"
    
    # 3. اختيار الخدمة
    SELECTING_SERVICE = "selecting_service"
    
    # 4. شرح تفاصيل الخدمة
    SERVICE_DETAILS = "service_details"
    
    # 5. جمع بيانات السيارة
    COLLECTING_VEHICLE = "collecting_vehicle"
    
    # 6. تأكيد بيانات السيارة
    CONFIRMING_VEHICLE = "confirming_vehicle"
    
    # 7. عرض الأسعار والعروض
    SHOWING_OFFERS = "showing_offers"
    
    # 8. اختيار العرض
    SELECTING_OFFER = "selecting_offer"
    
    # 9. تفاصيل المبلغ
    OFFER_DETAILS = "offer_details"
    
    # 10. جمع البيانات الشخصية
    COLLECTING_PROFILE = "collecting_profile"
    
    # 11. ملخص الطلب الشامل
    ORDER_SUMMARY = "order_summary"
    
    # 12. التأكيد النهائي
    FINAL_CONFIRMATION = "final_confirmation"
    
    # 13. إصدار الفاتورة
    INVOICE_ISSUED = "invoice_issued"
    
    # 14. تأكيد الدفع وإصدار الوثيقة
    PAYMENT_DONE = "payment_done"
    
    # Legacy stages (للتوافق)
    AWAITING_SELECTION = "awaiting_selection"
    CONFIRMATION = "confirmation"
    PENDING_PAYMENT = "pending_payment"
    DONE = "done"
    ASK_ANOTHER_VEHICLE = "ask_another_vehicle"
    FETCHING_OFFERS = "fetching_offers"
    CREATING_INVOICE = "creating_invoice"
    ISSUING_POLICY = "issuing_policy"
    ASK_INSURE_ANOTHER = "ask_insure_another"
    
    # Special states
    DOCUMENTS_VIEW = "documents_view"
    ORDER_TRACKING = "order_tracking"
    HANDOFF_HUMAN = "handoff_human"
    ERROR = "error"


class SessionStatus(str, Enum):
    """Session status"""
    NEW = "new"
    ACTIVE = "active"
    IDLE = "idle"
    EXPIRED = "expired"
    RESUMED = "resumed"


class OrderStatus(str, Enum):
    """Order status"""
    DRAFT = "draft"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    PENDING_PAYMENT = "pending_payment"
    PAID = "paid"
    POLICY_ISSUED = "policy_issued"
    CANCELED = "canceled"
    FAILED = "failed"


class InvoiceStatus(str, Enum):
    """Invoice status"""
    UNPAID = "unpaid"
    PAID = "paid"
    EXPIRED = "expired"
    FAILED = "failed"


class PolicyStatus(str, Enum):
    """Policy status"""
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELED = "canceled"


class CoverageType(str, Enum):
    """Insurance coverage types"""
    TPL = "tpl"  # Third Party Liability
    COMPREHENSIVE = "comprehensive"
    VIP = "vip"


class Channel(str, Enum):
    """Communication channels"""
    WHATSAPP = "whatsapp"
    WEB = "web"
    APP = "app"


class InputType(str, Enum):
    """Expected input types for rule-based parsing"""
    CHOICE_NUMBER = "choice_number"
    NATIONAL_ID = "national_id"
    BIRTH_DATE = "birth_date"
    PHONE = "phone"
    PLATE_NUMBER = "plate_number"
    VEHICLE_INFO = "vehicle_info"
    VEHICLE_VALUE = "vehicle_value"
    AFFIRMATIVE = "affirmative"
    NEGATIVE = "negative"
    PAYMENT_CONFIRM = "payment_confirm"
    FREE_TEXT = "free_text"


# Timeouts
SESSION_TIMEOUT_HOURS = 24
SESSION_IDLE_TIMEOUT_MINUTES = 30
INVOICE_EXPIRY_HOURS = 24
IDEMPOTENCY_WINDOW_MINUTES = 5

# Limits
MAX_VEHICLES_PER_SESSION = 5
MAX_OFFERS_TO_SHOW = 5
MAX_RETRY_COUNT = 3

# Validation patterns
PATTERNS = {
    "national_id": r"^[12]\d{9}$",
    "phone_sa": r"^(05|5|966|\+966)?\d{8,9}$",
    "saudi_plate": r"^[\u0621-\u064A]\s*[\u0621-\u064A]\s*[\u0621-\u064A]\s*\d{4}$",
    "choice_1_9": r"^[1-9]$",
    "affirmative": r"^(نعم|اي|ايه|أي|أيه|yes|y|ok|اوك|تمام|موافق|صح|1)$",
    "negative": r"^(لا|لأ|no|n|إلغاء|الغاء|2|تخطي|skip)$",
    "payment_confirm": r"(تم الدفع|دفعت|paid|تم|done)",
}
