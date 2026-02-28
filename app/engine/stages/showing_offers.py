"""
Showing Offers Stage - مرحلة عرض العروض من قاعدة البيانات
"""
from typing import Dict, Any, List
from app.core.constants import ConversationStage
from app.engine.session_manager import ConversationContext
from .base_stage import BaseStage, StageResponse


class ShowingOffersStage(BaseStage):
    """مرحلة عرض العروض من قاعدة البيانات"""
    
    stage = ConversationStage.SHOWING_OFFERS
    order = 5
    name_ar = "عرض العروض"
    
    def __init__(self):
        super().__init__()
        self.offers_cache = []
    
    def get_stage_info(self) -> Dict[str, str]:
        return {
            "name": "عرض العروض",
            "description": "عرض عروض التأمين المتاحة من قاعدة البيانات",
            "required_action": "اعرض العروض بشكل جذاب ودع العميل يختار"
        }
    
    def get_required_fields(self) -> List[str]:
        """لا توجد حقول مطلوبة - فقط عرض"""
        return []
    
    def get_collected_fields(self, context: ConversationContext) -> Dict[str, Any]:
        """الحقول المجمعة"""
        if context.offers_shown:
            return {"offers_count": len(context.offers_shown)}
        return {}
    
    def get_prompt_instructions(self, context: ConversationContext) -> str:
        # جلب العروض من قاعدة البيانات
        offers = self._fetch_offers_from_db(context)
        
        if not context.offers_shown:
            context.offers_shown = offers
        
        offers_text = self._format_offers(offers)
        
        return f"""⚠️ أنت في مرحلة عرض العروض.

🎯 العروض المتوفرة من قاعدة البيانات:
{offers_text}

تعليمات مهمة:
- اعرض العروض بشكل جذاب ومرتب
- اذكر سعر كل عرض ومميزاته
- اسأل العميل: "أي عرض يناسبك؟ 🤔"
- ساعده في الاختيار إذا كان محتاراً

مثال:
"هذي عروض التأمين المتوفرة لسيارتك! 🌟

1. التعاونية: 2,850 ريال
   ✓ تغطية شاملة + سيارة بديلة 7 أيام

2. تكافل الراجحي: 2,650 ريال
   ✓ تأمين تكافلي + سيارة بديلة 5 أيام

3. ولاء: 2,450 ريال
   ✓ أقل سعر + خصم تجديد 10%

أي عرض يناسبك؟ 🤔"
"""
    
    def _fetch_offers_from_db(self, context: ConversationContext) -> List[Dict]:
        """جلب العروض من قاعدة البيانات"""
        try:
            from sqlalchemy import create_engine, text
            from app.config import settings
            
            engine = create_engine(settings.database_url)
            
            # جلب نوع الخدمة المختارة
            service_type = context.profile_data.get("service_type", "comprehensive")
            
            # تحديد نوع التغطية
            coverage = "comprehensive"
            if "ضد الغير" in str(service_type).lower() or "tpl" in str(service_type).lower():
                coverage = "tpl"
            elif "vip" in str(service_type).lower():
                coverage = "vip"
            
            query = text("""
                SELECT 
                    o.id, o.offer_code, o.price, o.features_json, o.coverage_type,
                    o.price_base, o.min_age, o.max_age, o.min_vehicle_year, o.max_vehicle_year,
                    o.min_vehicle_value, o.max_vehicle_value, o.conditions_json,
                    c.name_ar as company, c.id as company_id,
                    s.id as service_id, s.name_ar as service_name,
                    o.gross_premium, o.ncd_discount_percent, o.ncd_discount_amount,
                    o.premium_exc_vat, o.vat_percent, o.vat_amount, o.total_premium
                FROM insurance_offers o
                JOIN insurance_companies c ON o.company_id = c.id
                JOIN insurance_services s ON o.service_id = s.id
                WHERE o.is_active = true
                  AND o.coverage_type = :coverage
                ORDER BY o.total_premium ASC
                LIMIT 7
            """)
            
            with engine.connect() as conn:
                result = conn.execute(query, {"coverage": coverage})
                offers = []
                for row in result:
                    features = row[3] if row[3] else {}
                    conditions = row[12] if row[12] else {}
                    
                    offers.append({
                        "id": row[0],
                        "code": row[1],
                        "price": float(row[2] or row[5]),
                        "features": features.get("summary", str(features)),
                        "features_json": features,
                        "type": row[4],
                        "price_base": float(row[5]) if row[5] else 0,
                        "min_age": row[6],
                        "max_age": row[7],
                        "min_vehicle_year": row[8],
                        "max_vehicle_year": row[9],
                        "min_vehicle_value": float(row[10]) if row[10] else 0,
                        "max_vehicle_value": float(row[11]) if row[11] else 0,
                        "conditions_json": conditions,
                        "company": row[13],
                        "company_id": row[14],
                        "service_id": row[15],
                        "service_name": row[16],
                        # تفاصيل المبلغ الجديدة
                        "gross_premium": float(row[17]) if row[17] else 0,
                        "ncd_discount_percent": float(row[18]) if row[18] else 0,
                        "ncd_discount_amount": float(row[19]) if row[19] else 0,
                        "premium_exc_vat": float(row[20]) if row[20] else 0,
                        "vat_percent": float(row[21]) if row[21] else 15,
                        "vat_amount": float(row[22]) if row[22] else 0,
                        "total_premium": float(row[23]) if row[23] else 0
                    })


                
                self.logger.info(f"✅ Fetched {len(offers)} offers from DB")
                return offers
                
        except Exception as e:
            self.logger.error(f"Error fetching offers: {e}")
            return self._get_fallback_offers()
    
    def _get_fallback_offers(self) -> List[Dict]:
        """عروض احتياطية في حالة فشل DB - مع جميع حقول الأسعار"""
        # الأسعار الأساسية
        offers_data = [
            {"id": 1, "company": "التعاونية", "base_price": 2850, "features": "تغطية شاملة", "company_id": 1},
            {"id": 2, "company": "تكافل الراجحي", "base_price": 2650, "features": "تأمين تكافلي", "company_id": 2},
            {"id": 3, "company": "ولاء", "base_price": 2450, "features": "خصم تجديد", "company_id": 3},
        ]
        
        result = []
        for offer in offers_data:
            base = offer["base_price"]
            gross = base  # القسط الأساسي
            vat = round(gross * 0.15, 2)  # ضريبة 15%
            total = round(gross + vat, 2)  # الإجمالي
            
            result.append({
                "id": offer["id"],
                "company": offer["company"],
                "type": "comprehensive",
                "features": offer["features"],
                "company_id": offer["company_id"],
                "service_id": 1,
                # === حقول الأسعار الكاملة ===
                "gross_premium": gross,
                "ncd_discount_percent": 0,
                "ncd_discount_amount": 0,
                "premium_exc_vat": gross,
                "vat_percent": 15,
                "vat_amount": vat,
                "total_premium": total,  # السعر الإجمالي المعروض
                "price": total,  # للتوافقية
            })
        
        self.logger.info(f"📋 Generated {len(result)} fallback offers with full price breakdown")
        return result
    
    def _format_offers(self, offers: List[Dict]) -> str:
        """تنسيق العروض للعرض بشكل تفصيلي - مع تفاصيل المبلغ الكاملة"""
        if not offers:
            return "لا توجد عروض متوفرة حالياً"
        
        # 🔍 Logging: تسجيل العروض المعروضة
        self.logger.info(f"📊 Formatting {len(offers)} offers for display:")
        for i, offer in enumerate(offers, 1):
            company = offer.get('company', 'N/A')
            price = offer.get('total_premium') or offer.get('price', 0)
            offer_id = offer.get('id', 'N/A')
            self.logger.info(f"   {i}. {company}: {price:,.2f} ريال (ID: {offer_id})")
        
        lines = []
        for i, offer in enumerate(offers, 1):
            # استخدام البيانات من قاعدة البيانات مباشرة
            gross_premium = offer.get('gross_premium', offer.get('price', 0))
            ncd_discount_percent = offer.get('ncd_discount_percent', 0)
            ncd_discount_amount = offer.get('ncd_discount_amount', 0)
            premium_exc_vat = offer.get('premium_exc_vat', gross_premium)
            vat_percent = offer.get('vat_percent', 15)
            vat_amount = offer.get('vat_amount', premium_exc_vat * 0.15)
            total_premium = offer.get('total_premium', premium_exc_vat * 1.15)
            
            lines.append(f"━━━━━━━━━━━━━━━━━━━━━━━━━")
            lines.append(f"🏢 العرض {i}: {offer.get('company', '')}")
            lines.append(f"━━━━━━━━━━━━━━━━━━━━━━━━━")
            lines.append(f"📋 كود العرض: {offer.get('code', 'N/A')}")
            lines.append(f"🛡️ نوع التغطية: {self._get_coverage_name(offer.get('type', ''))}")
            
            # تفاصيل المبلغ (كما في الصورة)
            lines.append(f"")
            lines.append(f"💰 تفاصيل المبلغ:")
            lines.append(f"   ✓ القسط الأساسي: {gross_premium:,.2f} ريال")
            lines.append(f"   ✓ خصم عدم وجود مطالبات: {ncd_discount_amount:,.2f}- ({ncd_discount_percent:.0f}%)")
            lines.append(f"   ✓ إجمالي المبلغ بدون ضريبة: {premium_exc_vat:,.2f} ريال")
            lines.append(f"   ✓ ضريبة القيمة المضافة ({vat_percent:.0f}%): {vat_amount:,.2f} ريال")
            lines.append(f"   ━━━━━━━━━━━━━━━━━")
            lines.append(f"   💵 إجمالي المبلغ: {total_premium:,.2f} ريال")
            
            # شروط العمر
            min_age = offer.get('min_age')
            max_age = offer.get('max_age')
            if min_age or max_age:
                lines.append(f"👤 العمر المسموح: {min_age or 18} - {max_age or 70} سنة")
            
            # شروط السنة
            min_year = offer.get('min_vehicle_year')
            max_year = offer.get('max_vehicle_year')
            if min_year or max_year:
                lines.append(f"📅 سنة السيارة: {min_year or 2010} - {max_year or 2025}")
            
            # شروط القيمة
            min_val = offer.get('min_vehicle_value', 0)
            max_val = offer.get('max_vehicle_value', 0)
            if max_val:
                lines.append(f"💎 قيمة السيارة: {min_val:,.0f} - {max_val:,.0f} ريال")
            
            # المميزات
            features = offer.get('features_json', {})
            if isinstance(features, dict) and features:
                lines.append(f"✨ المميزات:")
                for key, val in list(features.items())[:5]:
                    lines.append(f"   ✓ {val if isinstance(val, str) else key}")
            elif offer.get('features'):
                lines.append(f"✨ المميزات: {offer.get('features')}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def _get_coverage_name(self, coverage_type: str) -> str:
        """تحويل نوع التغطية لاسم عربي"""
        names = {
            "tpl": "تأمين ضد الغير",
            "comprehensive": "تأمين شامل",
            "vip": "تأمين VIP"
        }
        return names.get(coverage_type, coverage_type)

    def _ai_match_company(self, user_input: str, available_companies: List[str]) -> str:
        """
        استخدام Gemini للتعرف على الشركة المقصودة من إدخال المستخدم
        Returns: اسم الشركة المطابقة أو None
        """
        try:
            import google.generativeai as genai
            from app.config import settings
            
            if not settings.GEMINI_API_KEY:
                self.logger.warning("⚠️ Gemini API key not available")
                return None
            
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel(
                settings.GEMINI_MODEL,
                generation_config=genai.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=100,
                )
            )
            
            companies_list = ", ".join(available_companies)
            
            prompt = f"""أنت محلل ذكي. مهمتك تحديد اسم شركة التأمين التي يقصدها المستخدم.

## الشركات المتوفرة:
{companies_list}

## إدخال المستخدم:
"{user_input}"

## المطلوب:
- إذا كان المستخدم يقصد إحدى الشركات المتوفرة، أرجع اسمها بالضبط كما هو في القائمة
- إذا كتب رقم (1، 2، 3)، أرجع "NUMBER:X" حيث X هو الرقم
- إذا لم تتمكن من التحديد، أرجع "UNKNOWN"

أمثلة:
- "ولاء" → "ولاء" (إذا كانت في القائمة)
- "التعاونيه" → "التعاونية" (تصحيح إملائي)
- "راجحي" → "تكافل الراجحي" (إذا كانت في القائمة)
- "3" → "NUMBER:3"
- "العرض الثالث" → "NUMBER:3"
- "الأخير" → "NUMBER:LAST"

أرجع الإجابة فقط بدون أي شرح."""

            response = model.generate_content(prompt)
            result = response.text.strip()
            
            self.logger.info(f"🤖 AI Company Match: '{user_input}' → '{result}'")
            
            # تحقق من أن النتيجة موجودة في القائمة
            if result in available_companies:
                return result
            elif result.startswith("NUMBER:"):
                return result  # سيُعالج لاحقاً
            else:
                # محاولة مطابقة جزئية
                for company in available_companies:
                    if result.lower() in company.lower() or company.lower() in result.lower():
                        return company
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ AI matching error: {e}")
            return None
    
    def _find_by_company_name(self, offers: List[Dict], search_name: str) -> tuple:
        """
        البحث عن عرض باستخدام Gemini AI للتعرف على الشركة
        Returns: (offer, index) or (None, -1)
        """
        if not search_name or not offers:
            return None, -1
        
        self.logger.info(f"🔍 AI Searching for: '{search_name}' in {len(offers)} offers")
        
        # 1. استخراج أسماء الشركات المتوفرة
        available_companies = [offer.get("company", "") for offer in offers]
        
        # 2. استخدام AI للمطابقة
        ai_result = self._ai_match_company(search_name, available_companies)
        
        if ai_result:
            # 3. التعامل مع نتيجة الرقم
            if ai_result.startswith("NUMBER:"):
                try:
                    num_str = ai_result.replace("NUMBER:", "")
                    if num_str == "LAST":
                        idx = len(offers) - 1
                    else:
                        idx = int(num_str) - 1
                    if 0 <= idx < len(offers):
                        self.logger.info(f"✅ AI matched number: {idx + 1}")
                        return offers[idx], idx
                except ValueError:
                    pass
            else:
                # 4. البحث عن الشركة المطابقة
                for idx, offer in enumerate(offers):
                    if ai_result == offer.get("company", ""):
                        self.logger.info(f"✅ AI matched company: '{ai_result}' at index {idx}")
                        return offer, idx
        
        # 5. Fallback: مطابقة مباشرة بسيطة
        search_lower = search_name.lower().strip()
        for idx, offer in enumerate(offers):
            company = offer.get("company", "").lower()
            if search_lower in company or company in search_lower:
                self.logger.info(f"✅ Direct match fallback: '{company}' at index {idx}")
                return offer, idx
        
        self.logger.warning(f"⚠️ No match found for: '{search_name}'")
        return None, -1

    
    def _fetch_offer_by_company_from_db(self, company_name: str, context: ConversationContext) -> Dict:
        """جلب عرض من قاعدة البيانات مباشرة باسم الشركة"""
        try:
            from sqlalchemy import create_engine, text
            from app.config import settings
            
            engine = create_engine(settings.database_url)
            service_type = context.profile_data.get("service_type", "comprehensive")
            
            coverage = "comprehensive"
            if "ضد الغير" in str(service_type).lower() or "tpl" in str(service_type).lower():
                coverage = "tpl"
            
            # البحث باسم الشركة
            query = text("""
                SELECT 
                    o.id, o.offer_code, o.price, o.features_json, o.coverage_type,
                    o.price_base, c.name_ar as company, c.id as company_id,
                    o.gross_premium, o.ncd_discount_percent, o.ncd_discount_amount,
                    o.premium_exc_vat, o.vat_percent, o.vat_amount, o.total_premium
                FROM insurance_offers o
                JOIN insurance_companies c ON o.company_id = c.id
                WHERE o.is_active = true
                  AND o.coverage_type = :coverage
                  AND LOWER(c.name_ar) LIKE :company_pattern
                ORDER BY o.total_premium ASC
                LIMIT 1
            """)
            
            with engine.connect() as conn:
                result = conn.execute(query, {
                    "coverage": coverage,
                    "company_pattern": f"%{company_name}%"
                })
                row = result.fetchone()
                if row:
                    offer = {
                        "id": row[0],
                        "code": row[1],
                        "price": float(row[2] or row[5]),
                        "type": row[4],
                        "company": row[6],
                        "company_id": row[7],
                        "gross_premium": float(row[8]) if row[8] else 0,
                        "ncd_discount_percent": float(row[9]) if row[9] else 0,
                        "ncd_discount_amount": float(row[10]) if row[10] else 0,
                        "premium_exc_vat": float(row[11]) if row[11] else 0,
                        "vat_percent": float(row[12]) if row[12] else 15,
                        "vat_amount": float(row[13]) if row[13] else 0,
                        "total_premium": float(row[14]) if row[14] else 0
                    }
                    self.logger.info(f"✅ Fetched offer from DB: {offer['company']} - {offer['total_premium']:,.2f} ريال")
                    return offer
        except Exception as e:
            self.logger.error(f"❌ Error fetching offer from DB: {e}")
        return None
    
    def handle_intent(
        self,
        intent,
        context: ConversationContext,
        extracted_data: Dict[str, Any]
    ) -> StageResponse:
        """معالجة النية في مرحلة عرض العروض - مع تحسين المطابقة"""
        from app.engine.ai_intent_analyzer import UserIntent
        
        # 🔍 لوغ تشخيصي
        self.logger.info(f"📋 handle_intent called - offers_shown count: {len(context.offers_shown)}")
        self.logger.info(f"📋 extracted_data: {extracted_data}")
        
        # اختيار عرض محدد
        if intent == UserIntent.SELECT_OFFER:
            offer_num = extracted_data.get("offer_number")
            company_name = extracted_data.get("company_name")
            
            selected_offer = None
            selected_idx = -1
            
            # 1. محاولة اختيار بالرقم
            if offer_num and context.offers_shown:
                try:
                    idx = int(offer_num) - 1
                    if 0 <= idx < len(context.offers_shown):
                        selected_offer = context.offers_shown[idx]
                        selected_idx = idx
                        self.logger.info(f"✅ Selected by number #{offer_num}")
                except (ValueError, IndexError) as e:
                    self.logger.error(f"❌ Error selecting offer #{offer_num}: {e}")
            
            # 2. محاولة اختيار باسم الشركة (مع aliases)
            if not selected_offer and company_name and context.offers_shown:
                selected_offer, selected_idx = self._find_by_company_name(context.offers_shown, company_name)
            
            # 3. إذا لم نجد، ابحث في DB مباشرة
            if not selected_offer and company_name:
                self.logger.info(f"🔍 Offer not found in cache, searching DB for: {company_name}")
                selected_offer = self._fetch_offer_by_company_from_db(company_name, context)
                if selected_offer:
                    # أضف العرض للقائمة
                    context.offers_shown.append(selected_offer)
                    selected_idx = len(context.offers_shown) - 1
            
            # 4. إذا وجدنا العرض، احفظه وانتقل
            if selected_offer:
                context.selected_offer = selected_offer
                context.selected_offer_id = selected_idx + 1
                
                # 🔍 Logging تفصيلي
                selected_company = selected_offer.get('company', 'N/A')
                selected_price = selected_offer.get('total_premium') or selected_offer.get('price', 0)
                selected_id = selected_offer.get('id', 'N/A')
                self.logger.info(f"✅ Final selection: {selected_company} - {selected_price:,.2f} ريال (ID: {selected_id})")
                self.logger.info(f"🔍 Full offer data: {selected_offer}")
                
                self.logger.info(f"🧠 AI Transition: SHOWING_OFFERS -> OFFER_DETAILS")
                return StageResponse(
                    should_transition=True,
                    next_stage=ConversationStage.OFFER_DETAILS,
                    extracted_data={"selected_offer": selected_idx + 1}
                )
            else:
                self.logger.warning(f"⚠️ Could not find offer for: num={offer_num}, company={company_name}")
        
        # البقاء في نفس المرحلة إذا لم يتم اختيار عرض
        return StageResponse(should_transition=False)



# Singleton instance
showing_offers_stage = ShowingOffersStage()

