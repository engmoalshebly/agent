"""
SAIA Insurance - Conversation Stages
كل مرحلة في ملف منفصل لسهولة التتبع والتعديل
التدفق الاحترافي: 14 مرحلة
"""

from .base_stage import BaseStage, StageResponse

# === المراحل الأساسية ===
from .greeting import greeting_stage, GreetingStage
from .selecting_service import selecting_service_stage, SelectingServiceStage
from .service_details import service_details_stage, ServiceDetailsStage
from .collecting_vehicle import collecting_vehicle_stage, CollectingVehicleStage
from .confirming_vehicle import confirming_vehicle_stage, ConfirmingVehicleStage
from .showing_offers import showing_offers_stage, ShowingOffersStage
from .offer_details import offer_details_stage, OfferDetailsStage
from .collecting_profile import collecting_profile_stage, CollectingProfileStage
from .order_summary import order_summary_stage, OrderSummaryStage
from .confirmation import confirmation_stage, ConfirmationStage
from .invoice_issued import invoice_issued_stage, InvoiceIssuedStage
from .payment_done import payment_done_stage, PaymentDoneStage
from .payment import payment_stage, PaymentStage

# تصدير جميع المراحل
__all__ = [
    # Base
    "BaseStage",
    "StageResponse",
    
    # Stage Classes
    "GreetingStage",
    "SelectingServiceStage",
    "ServiceDetailsStage",
    "CollectingVehicleStage",
    "ConfirmingVehicleStage",
    "ShowingOffersStage",
    "OfferDetailsStage",
    "CollectingProfileStage",
    "OrderSummaryStage",
    "ConfirmationStage",
    "InvoiceIssuedStage",
    "PaymentDoneStage",
    "PaymentStage",
    
    # Singleton Instances
    "greeting_stage",
    "selecting_service_stage",
    "service_details_stage",
    "collecting_vehicle_stage",
    "confirming_vehicle_stage",
    "showing_offers_stage",
    "offer_details_stage",
    "collecting_profile_stage",
    "order_summary_stage",
    "confirmation_stage",
    "invoice_issued_stage",
    "payment_done_stage",
    "payment_stage",
]
