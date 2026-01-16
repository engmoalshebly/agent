"""
SAIA Insurance Broker Platform - Database Operations Module
عمليات قاعدة البيانات
"""
from typing import Dict, Any, Optional, List
import logging

from app.engine.session_manager import ConversationContext

logger = logging.getLogger(__name__)


class DatabaseOperations:
    """
    إدارة عمليات قاعدة البيانات
    يتعامل مع:
    - حفظ المستخدمين والسيارات
    - جلب العروض والخدمات
    - إنشاء الطلبات والفواتير
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.user_repo = None
        self.vehicle_repo = None
        self.order_repo = None
        self.invoice_repo = None
        self.policy_repo = None
        self.service_repo = None
        self.offer_repo = None
        self._initialized = False
    
    def initialize(self):
        """تهيئة الـ Repositories"""
        if self._initialized:
            return
        
        try:
            from app.db.repositories.user_repository import user_repository
            from app.db.repositories.vehicle_repository import vehicle_repository
            from app.db.repositories.order_repository import order_repository
            from app.db.repositories.invoice_repository import invoice_repository
            from app.db.repositories.policy_repository import policy_repository
            from app.db.repositories.service_repository import service_repository
            
            self.user_repo = user_repository
            self.vehicle_repo = vehicle_repository
            self.order_repo = order_repository
            self.invoice_repo = invoice_repository
            self.policy_repo = policy_repository
            self.service_repo = service_repository
            
            self._initialized = True
            self.logger.info("✅ Database repositories initialized")
        except Exception as e:
            self.logger.warning(f"Could not init repositories: {e}")
    
    def save_user(
        self,
        context: ConversationContext,
        national_id: str,
        birth_date: str,
        phone: Optional[str] = None
    ) -> Optional[Dict]:
        """حفظ المستخدم في قاعدة البيانات"""
        if not self.user_repo:
            return None
        
        try:
            # التحقق من عدم وجود المستخدم مسبقاً
            existing = self.user_repo.get_by_national_id(national_id)
            if existing:
                context.user_id = str(existing["id"])
                self.logger.info(f"✅ Found existing user: {existing.get('user_code')}")
                return existing
            
            # إنشاء مستخدم جديد
            user = self.user_repo.create_user(
                national_id=national_id,
                birth_date=birth_date,
                phone=phone
            )
            
            if user and user.get("id"):
                context.user_id = str(user["id"])
                self.logger.info(f"✅ Saved user to DB: {user.get('user_code')}")
                return user
        except Exception as e:
            self.logger.error(f"Error saving user: {e}")
        
        return None
    
    def save_vehicle(
        self,
        context: ConversationContext,
        plate_no: str,
        brand: str,
        model: str,
        year: int,
        value: float
    ) -> Optional[Dict]:
        """حفظ السيارة في قاعدة البيانات"""
        if not self.vehicle_repo or not context.user_id:
            return None
        
        try:
            vehicle = self.vehicle_repo.create_vehicle(
                user_id=int(context.user_id),
                plate_no=plate_no,
                brand=brand,
                model=model,
                model_year=year,
                vehicle_value=value
            )
            
            if vehicle and vehicle.get("id"):
                context.vehicle_data["db_id"] = vehicle["id"]
                self.logger.info(f"✅ Saved vehicle to DB: {vehicle.get('plate_no')}")
                return vehicle
        except Exception as e:
            self.logger.error(f"Error saving vehicle: {e}")
        
        return None
    
    def get_services(self) -> List[Dict]:
        """جلب الخدمات المتوفرة"""
        if not self.service_repo:
            return []
        
        try:
            return self.service_repo.get_active_services()
        except Exception as e:
            self.logger.error(f"Error fetching services: {e}")
            return []
    
    def get_services_formatted(self) -> str:
        """جلب الخدمات بصيغة نصية"""
        services = self.get_services()
        if not services:
            return "- لا توجد خدمات معروضة حالياً"
        
        lines = []
        for i, svc in enumerate(services, 1):
            name = svc.get("name_ar", svc.get("code", ""))
            desc = svc.get("description", "")
            lines.append(f"{i}. {name}")
            if desc:
                lines.append(f"   ({desc})")
        
        return "\n".join(lines)
    
    def get_offers(self, context: ConversationContext) -> List[Dict]:
        """جلب العروض من قاعدة البيانات"""
        try:
            from app.engine.sql_engine import insurance_sql_engine
            
            # جلب العروض باستخدام SQL Engine
            result = insurance_sql_engine._execute_sql(
                "SELECT * FROM offers WHERE is_active = true ORDER BY price ASC LIMIT 10"
            )
            
            if result and result.get("data"):
                return result["data"]
        except Exception as e:
            self.logger.warning(f"Could not fetch offers from DB: {e}")
        
        # Fallback للعروض الافتراضية
        return self._get_default_offers(context)
    
    def _get_default_offers(self, context: ConversationContext) -> List[Dict]:
        """عروض افتراضية مع كل التفاصيل"""
        vehicle_value = 0
        manager_data = context.vehicle_data.get("manager", {})
        if manager_data:
            try:
                from app.engine.vehicle_manager import VehicleManager
                vm = VehicleManager.from_dict(manager_data)
                if vm.current_vehicle and vm.current_vehicle.value:
                    vehicle_value = vm.current_vehicle.value
            except:
                pass
        
        # حساب الأسعار بناءً على قيمة السيارة
        base_rate = 0.03  # 3% من قيمة السيارة
        base_price = max(vehicle_value * base_rate, 1500)
        
        # تحديد نوع التغطية
        coverage_type = context.profile_data.get("service_type", "comprehensive")
        
        return [
            {
                "id": 1,
                "company": "ولاء",
                "company_logo": "walaa.png",
                "type": "شامل" if coverage_type == "comprehensive" else "ضد الغير",
                "coverage_type": coverage_type,
                
                # === تفاصيل التسعير ===
                "price_base": round(base_price * 0.85),
                "price_rate_pct": 2.4,
                "no_claims_discount": 5,
                "njm_discount": 10,
                "online_discount": 5,
                "vat_rate": 15,
                "price_before_vat": round(base_price * 0.85 * 0.80),  # بعد الخصومات
                "vat_amount": round(base_price * 0.85 * 0.80 * 0.15),
                "price": round(base_price * 0.85 * 0.80 * 1.15),  # السعر النهائي
                
                # === مبلغ التحمل ===
                "deductible_options": [
                    {"amount": 1000, "label": "1000 ريال", "discount_pct": 0},
                    {"amount": 2000, "label": "2000 ريال", "discount_pct": 6},
                ],
                "default_deductible": 1000,
                
                # === المميزات المجانية ===
                "included_features": [
                    {"name": "تغطية شاملة", "icon": "✅"},
                    {"name": "سرقة وحريق", "icon": "🔥"},
                    {"name": "خصم تجديد 10%", "icon": "💰"},
                ],
                
                # === منافع إضافية ===
                "optional_addons": [
                    {"name": "تأمين الممتلكات", "price": 55, "vat": 8.25},
                ],
                
                # === الشروط ===
                "conditions": ["عمر السائق 21-65 سنة", "سيارة 2012 وأحدث"],
                
                "rating": 4.2,
                "is_cheapest": True
            },
            {
                "id": 2,
                "company": "سلامة",
                "company_logo": "salama.png",
                "type": "شامل" if coverage_type == "comprehensive" else "ضد الغير",
                "coverage_type": coverage_type,
                
                # === تفاصيل التسعير ===
                "price_base": round(base_price * 0.90),
                "price_rate_pct": 2.5,
                "no_claims_discount": 8,
                "njm_discount": 10,
                "online_discount": 5,
                "vat_rate": 15,
                "price_before_vat": round(base_price * 0.90 * 0.77),
                "vat_amount": round(base_price * 0.90 * 0.77 * 0.15),
                "price": round(base_price * 0.90 * 0.77 * 1.15),
                
                # === مبلغ التحمل ===
                "deductible_options": [
                    {"amount": 750, "label": "750 ريال", "discount_pct": 0},
                    {"amount": 1500, "label": "1500 ريال", "discount_pct": 5},
                    {"amount": 2500, "label": "2500 ريال", "discount_pct": 8},
                ],
                "default_deductible": 750,
                
                # === المميزات المجانية ===
                "included_features": [
                    {"name": "تغطية شاملة", "icon": "✅"},
                    {"name": "سرقة وحريق", "icon": "🔥"},
                    {"name": "السيارة البديلة 5 أيام", "icon": "🚗"},
                ],
                
                # === منافع إضافية ===
                "optional_addons": [
                    {"name": "تأمين الممتلكات", "price": 50, "vat": 7.50},
                    {"name": "كوارث طبيعية", "price": 280, "vat": 42},
                ],
                
                "conditions": ["عمر السائق 21-65 سنة", "سيارة 2013 وأحدث"],
                "rating": 4.3
            },
            {
                "id": 3,
                "company": "تكافل الراجحي",
                "company_logo": "rajhi.png",
                "type": "شامل" if coverage_type == "comprehensive" else "ضد الغير",
                "coverage_type": coverage_type,
                
                # === تفاصيل التسعير ===
                "price_base": round(base_price * 0.95),
                "price_rate_pct": 2.6,
                "no_claims_discount": 8,
                "njm_discount": 12,
                "online_discount": 5,
                "vat_rate": 15,
                "price_before_vat": round(base_price * 0.95 * 0.75),
                "vat_amount": round(base_price * 0.95 * 0.75 * 0.15),
                "price": round(base_price * 0.95 * 0.75 * 1.15),
                
                # === مبلغ التحمل ===
                "deductible_options": [
                    {"amount": 750, "label": "750 ريال", "discount_pct": 0},
                    {"amount": 1500, "label": "1500 ريال", "discount_pct": 5},
                    {"amount": 3000, "label": "3000 ريال", "discount_pct": 10},
                ],
                "default_deductible": 750,
                
                # === المميزات المجانية ===
                "included_features": [
                    {"name": "تأمين تكافلي شامل", "icon": "✅"},
                    {"name": "سرقة وحريق", "icon": "🔥"},
                    {"name": "السيارة البديلة 5 أيام", "icon": "🚗"},
                    {"name": "متوافق مع الشريعة", "icon": "🕌"},
                ],
                
                # === منافع إضافية ===
                "optional_addons": [
                    {"name": "تأمين الممتلكات الشخصية", "price": 60, "vat": 9},
                    {"name": "كوارث طبيعية", "price": 300, "vat": 45},
                ],
                
                "conditions": ["عمر السائق 21-65 سنة", "سيارة 2014 وأحدث"],
                "rating": 4.5,
                "is_recommended": True
            },
            {
                "id": 4,
                "company": "التعاونية",
                "company_logo": "tawuniya.png",
                "type": "شامل" if coverage_type == "comprehensive" else "ضد الغير",
                "coverage_type": coverage_type,
                
                # === تفاصيل التسعير ===
                "price_base": round(base_price * 1.0),
                "price_rate_pct": 2.8,
                "no_claims_discount": 10,
                "njm_discount": 15,
                "online_discount": 5,
                "vat_rate": 15,
                "price_before_vat": round(base_price * 1.0 * 0.70),
                "vat_amount": round(base_price * 1.0 * 0.70 * 0.15),
                "price": round(base_price * 1.0 * 0.70 * 1.15),
                
                # === مبلغ التحمل ===
                "deductible_options": [
                    {"amount": 500, "label": "500 ريال", "discount_pct": 0},
                    {"amount": 1000, "label": "1000 ريال", "discount_pct": 3},
                    {"amount": 2500, "label": "2500 ريال", "discount_pct": 7},
                    {"amount": 3500, "label": "3500 ريال", "discount_pct": 10},
                ],
                "default_deductible": 1000,
                
                # === المميزات المجانية ===
                "included_features": [
                    {"name": "تأمين الحوادث الشخصية", "icon": "👤"},
                    {"name": "الحماية القانونية", "icon": "⚖️"},
                    {"name": "السيارة البديلة 7 أيام", "icon": "🚗"},
                    {"name": "التمديد الجغرافي", "icon": "🌍"},
                    {"name": "تغطية السرقة والحريق", "icon": "🔥"},
                    {"name": "زجاج مجاني", "icon": "🪟"},
                ],
                
                # === منافع إضافية ===
                "optional_addons": [
                    {"name": "تأمين الممتلكات الشخصية", "price": 75, "vat": 11.25},
                    {"name": "تأمين المفاتيح", "price": 50, "vat": 7.50},
                    {"name": "أضرار الكوارث الطبيعية", "price": 350, "vat": 52.50},
                    {"name": "مساعدة على الطريق متقدمة", "price": 500, "vat": 75},
                ],
                
                "conditions": ["عمر السائق 21-65 سنة", "سيارة 2015 وأحدث"],
                "rating": 4.7,
                "is_premium": True
            },
        ]
    
    def get_offers_formatted(self, context: ConversationContext) -> str:
        """جلب العروض بصيغة نصية مفصلة"""
        offers = self.get_offers(context)
        if not offers:
            return ""
        
        # حفظ العروض في السياق
        context.offers_shown = offers
        
        lines = ["=== العروض المتوفرة ==="]
        
        for i, offer in enumerate(offers, 1):
            company = offer.get('company', 'شركة')
            price = offer.get('price', 0)
            offer_type = offer.get('type', 'تأمين')
            
            # Badge
            badge = ""
            if offer.get("is_cheapest"):
                badge = " 💰 الأرخص"
            elif offer.get("is_recommended"):
                badge = " ⭐ موصى به"
            elif offer.get("is_premium"):
                badge = " 👑 مميز"
            
            lines.append(f"\n{'='*40}")
            lines.append(f"🏢 العرض {i}: {company}{badge}")
            lines.append(f"📋 النوع: {offer_type}")
            lines.append(f"💰 السعر النهائي: {price:,.2f} ريال (شامل الضريبة)")
            
            # تفاصيل السعر
            if offer.get("price_before_vat"):
                lines.append(f"\n📊 تفاصيل السعر:")
                lines.append(f"   • السعر قبل الضريبة: {offer.get('price_before_vat', 0):,.2f} ريال")
                lines.append(f"   • الضريبة ({offer.get('vat_rate', 15)}%): {offer.get('vat_amount', 0):,.2f} ريال")
            
            # الخصومات
            discounts = []
            if offer.get("no_claims_discount"):
                discounts.append(f"عدم مطالبات {offer['no_claims_discount']}%")
            if offer.get("njm_discount"):
                discounts.append(f"نجم {offer['njm_discount']}%")
            if offer.get("online_discount"):
                discounts.append(f"شراء أونلاين {offer['online_discount']}%")
            if discounts:
                lines.append(f"   • الخصومات: {' + '.join(discounts)}")
            
            # مبلغ التحمل
            deductibles = offer.get("deductible_options", [])
            if deductibles:
                default_ded = offer.get("default_deductible", 0)
                ded_text = ", ".join([d["label"] for d in deductibles])
                lines.append(f"\n🔒 مبلغ التحمل: {default_ded:,} ريال (خيارات: {ded_text})")
            
            # المميزات المجانية
            features = offer.get("included_features", []) or offer.get("features", [])
            if features:
                lines.append(f"\n✅ يشمل مجاناً:")
                for f in features:
                    if isinstance(f, dict):
                        lines.append(f"   {f.get('icon', '•')} {f.get('name', '')}")
                    else:
                        lines.append(f"   • {f}")
            
            # المنافع الإضافية
            addons = offer.get("optional_addons", [])
            if addons:
                lines.append(f"\n➕ منافع إضافية (اختيارية):")
                for addon in addons:
                    addon_price = addon.get("price", 0)
                    addon_vat = addon.get("vat", 0)
                    lines.append(f"   • {addon.get('name', '')}: {addon_price + addon_vat:.2f} ريال")
            
            # الشروط
            conditions = offer.get("conditions", [])
            if conditions:
                lines.append(f"\n📋 الشروط: {' | '.join(conditions)}")
            
            # التقييم
            rating = offer.get("rating", 0)
            if rating:
                stars = "⭐" * int(rating)
                lines.append(f"\n⭐ التقييم: {stars} ({rating}/5)")
        
        lines.append(f"\n{'='*40}")
        lines.append("\n💬 أي عرض يناسبك؟ اختر رقم العرض أو اسم الشركة")
        
        return "\n".join(lines)
    
    def create_order(
        self,
        context: ConversationContext,
        offer: Dict
    ) -> Optional[Dict]:
        """إنشاء طلب جديد"""
        if not self.order_repo:
            return None
        
        try:
            price = float(offer.get("price", 0))
            vat = price * 0.15
            total = price + vat
            
            order = self.order_repo.create_order(
                user_id=int(context.user_id) if context.user_id else 1,
                offer_id=offer.get("id", 1),
                company_id=offer.get("company_id", 1),
                service_id=offer.get("service_id", 1),
                total_price=total
            )
            
            if order and order.get("id"):
                context.order_id = order["id"]
                self.logger.info(f"✅ Created order in DB: {order.get('order_code')}")
                return order
        except Exception as e:
            self.logger.error(f"Error creating order: {e}")
        
        return None
    
    def create_invoice(
        self,
        context: ConversationContext,
        order_id: int,
        amount: float
    ) -> Optional[Dict]:
        """إنشاء فاتورة"""
        if not self.invoice_repo:
            return None
        
        try:
            invoice = self.invoice_repo.create_invoice(
                order_id=order_id,
                amount=amount
            )
            
            if invoice and invoice.get("id"):
                context.invoice_id = invoice["id"]
                self.logger.info(f"✅ Created invoice in DB: {invoice.get('invoice_no')}")
                return invoice
        except Exception as e:
            self.logger.error(f"Error creating invoice: {e}")
        
        return None


# Global instance
db_operations = DatabaseOperations()
