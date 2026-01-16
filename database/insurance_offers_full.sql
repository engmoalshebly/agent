-- ================================================================
-- SAIA Insurance Broker Platform - Complete Insurance Offers Schema
-- PostgreSQL 15+
-- ================================================================
-- Author: Mohamed's Insurance Platform
-- Created: 2026-01-16
-- Description: Full insurance_offers table with ALL details:
--   - Price breakdown (base, discount, VAT, total)
--   - Deductible options
--   - Free included features
--   - Optional add-ons with pricing
--   - Coverage conditions
-- ================================================================

-- ================================================================
-- DROP and recreate insurance_offers with ALL columns
-- ================================================================

DROP TABLE IF EXISTS insurance_offer_addons CASCADE;
DROP TABLE IF EXISTS insurance_offers CASCADE;

CREATE TABLE insurance_offers (
    id SERIAL PRIMARY KEY,
    
    -- Relationships
    company_id INTEGER NOT NULL REFERENCES insurance_companies(id) ON DELETE CASCADE,
    service_id INTEGER NOT NULL REFERENCES insurance_services(id) ON DELETE CASCADE,
    
    -- Identification
    offer_code VARCHAR(50) UNIQUE NOT NULL,
    coverage_type VARCHAR(20) NOT NULL CHECK (coverage_type IN ('tpl', 'comprehensive', 'vip')),
    offer_name_ar VARCHAR(100) NOT NULL DEFAULT '',
    offer_name_en VARCHAR(100) NOT NULL DEFAULT '',
    
    -- Age Requirements
    min_age INTEGER NOT NULL DEFAULT 18,
    max_age INTEGER NOT NULL DEFAULT 70,
    
    -- Vehicle Year Requirements
    min_vehicle_year INTEGER NOT NULL DEFAULT 2010,
    max_vehicle_year INTEGER NOT NULL DEFAULT 2026,
    
    -- Vehicle Value Requirements
    min_vehicle_value DECIMAL(12, 2) NOT NULL DEFAULT 10000.00,
    max_vehicle_value DECIMAL(12, 2) NOT NULL DEFAULT 1000000.00,
    
    -- ==========================================
    -- PRICING DETAILS (تفاصيل المبلغ)
    -- ==========================================
    price_base DECIMAL(12, 2) NOT NULL,                    -- القسط الأساسي
    price_rate_percentage DECIMAL(5, 2) DEFAULT 3.00,      -- نسبة من قيمة السيارة
    no_claims_discount_pct DECIMAL(5, 2) DEFAULT 0.00,     -- خصم عدم وجود مطالبات %
    njm_discount_pct DECIMAL(5, 2) DEFAULT 10.00,          -- خصم نجم %
    loyalty_discount_pct DECIMAL(5, 2) DEFAULT 0.00,       -- خصم الولاء %
    online_discount_pct DECIMAL(5, 2) DEFAULT 5.00,        -- خصم الشراء أونلاين %
    vat_rate DECIMAL(5, 2) NOT NULL DEFAULT 15.00,         -- ضريبة القيمة المضافة %
    
    -- Pricing Formula
    pricing_formula_json JSONB NOT NULL DEFAULT '{}',
    
    -- ==========================================
    -- DEDUCTIBLE OPTIONS (مبلغ التحمل)
    -- ==========================================
    deductible_options JSONB DEFAULT '[
        {"amount": 500, "label_ar": "500 ريال", "label_en": "500 SAR", "discount_pct": 0},
        {"amount": 1000, "label_ar": "1000 ريال", "label_en": "1000 SAR", "discount_pct": 5},
        {"amount": 2500, "label_ar": "2500 ريال", "label_en": "2500 SAR", "discount_pct": 10},
        {"amount": 3500, "label_ar": "3500 ريال", "label_en": "3500 SAR", "discount_pct": 15}
    ]',
    default_deductible DECIMAL(12, 2) DEFAULT 1000.00,
    
    -- ==========================================
    -- INCLUDED FEATURES (يشمل مجاناً)
    -- ==========================================
    included_features_json JSONB NOT NULL DEFAULT '[]',
    
    -- ==========================================
    -- OPTIONAL ADD-ONS (منافع إضافية)
    -- ==========================================
    optional_addons_json JSONB NOT NULL DEFAULT '[]',
    
    -- ==========================================
    -- CONDITIONS & REQUIREMENTS
    -- ==========================================
    conditions_json JSONB NOT NULL DEFAULT '[]',
    exclusions_json JSONB NOT NULL DEFAULT '[]',
    
    -- Status & Timestamps
    is_active BOOLEAN NOT NULL DEFAULT true,
    priority_order INTEGER DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_offers_company ON insurance_offers(company_id);
CREATE INDEX idx_offers_service ON insurance_offers(service_id);
CREATE INDEX idx_offers_code ON insurance_offers(offer_code);
CREATE INDEX idx_offers_coverage ON insurance_offers(coverage_type);
CREATE INDEX idx_offers_active ON insurance_offers(is_active);
CREATE INDEX idx_offers_priority ON insurance_offers(priority_order);
CREATE INDEX idx_offers_vehicle_year ON insurance_offers(min_vehicle_year, max_vehicle_year);
CREATE INDEX idx_offers_vehicle_value ON insurance_offers(min_vehicle_value, max_vehicle_value);

-- Comments
COMMENT ON TABLE insurance_offers IS 'Insurance offers with complete pricing, features, and add-ons';
COMMENT ON COLUMN insurance_offers.price_base IS 'Base premium amount before calculations';
COMMENT ON COLUMN insurance_offers.price_rate_percentage IS 'Percentage of vehicle value to add to base price';
COMMENT ON COLUMN insurance_offers.no_claims_discount_pct IS 'Discount for no claims history';
COMMENT ON COLUMN insurance_offers.deductible_options IS 'Available deductible amounts with discounts';
COMMENT ON COLUMN insurance_offers.included_features_json IS 'Free features included in offer';
COMMENT ON COLUMN insurance_offers.optional_addons_json IS 'Optional add-ons with prices';

-- Trigger
CREATE OR REPLACE FUNCTION update_offers_timestamp()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = CURRENT_TIMESTAMP; RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_offers_updated 
    BEFORE UPDATE ON insurance_offers 
    FOR EACH ROW EXECUTE FUNCTION update_offers_timestamp();

-- ================================================================
-- INSERT COMPLETE TEST DATA - 14 Offers
-- ================================================================

-- 1. التعاونية - ضد الغير
INSERT INTO insurance_offers (
    company_id, service_id, offer_code, coverage_type,
    offer_name_ar, offer_name_en,
    min_age, max_age, min_vehicle_year, max_vehicle_year,
    min_vehicle_value, max_vehicle_value,
    price_base, price_rate_percentage, no_claims_discount_pct, njm_discount_pct, vat_rate,
    deductible_options, default_deductible,
    pricing_formula_json,
    included_features_json,
    optional_addons_json,
    conditions_json,
    is_active, priority_order
) VALUES
(1, 1, 'TAW-TPL-2026-001', 'tpl',
 'تأمين ضد الغير - التعاونية', 'Third Party Liability - Tawuniya',
 18, 70, 2010, 2026, 15000.00, 500000.00,
 950.00, 0.00, 0.00, 10.00, 15.00,
 '[{"amount": 0, "label_ar": "بدون تحمل", "label_en": "No Deductible", "discount_pct": 0}]',
 0.00,
 '{"type": "tpl", "formula": "price_base + (price_base * age_factor)"}',
 '[
   {"name_ar": "تغطية الطرف الثالث", "name_en": "Third Party Coverage", "icon": "shield-check"},
   {"name_ar": "مساعدة على الطريق", "name_en": "Road Assistance", "icon": "truck"},
   {"name_ar": "تعويض سريع", "name_en": "Fast Claims", "icon": "clock"}
 ]',
 '[]',
 '[
   {"text_ar": "عمر السائق 18-70 سنة", "text_en": "Driver age 18-70"},
   {"text_ar": "رخصة قيادة سارية", "text_en": "Valid driving license"}
 ]',
 true, 1),

-- 2. التعاونية - شامل
(1, 2, 'TAW-COMP-2026-001', 'comprehensive',
 'تأمين شامل - التعاونية', 'Comprehensive - Tawuniya',
 21, 65, 2015, 2026, 50000.00, 800000.00,
 1200.00, 2.80, 10.00, 15.00, 15.00,
 '[
   {"amount": 500, "label_ar": "500 ريال", "label_en": "500 SAR", "discount_pct": 0},
   {"amount": 1000, "label_ar": "1000 ريال", "label_en": "1000 SAR", "discount_pct": 3},
   {"amount": 2500, "label_ar": "2500 ريال", "label_en": "2500 SAR", "discount_pct": 7},
   {"amount": 3500, "label_ar": "3500 ريال", "label_en": "3500 SAR", "discount_pct": 10}
 ]',
 1000.00,
 '{"type": "comprehensive", "formula": "price_base + (vehicle_value * rate_pct / 100)"}',
 '[
   {"name_ar": "تأمين الحوادث الشخصية", "name_en": "Personal Accident Coverage", "icon": "user-shield"},
   {"name_ar": "الحماية القانونية", "name_en": "Legal Protection", "icon": "scale"},
   {"name_ar": "السيارة البديلة 7 أيام", "name_en": "Replacement Car 7 Days", "icon": "car"},
   {"name_ar": "التمديد الجغرافي", "name_en": "Geographic Extension", "icon": "globe"},
   {"name_ar": "تغطية السرقة والحريق", "name_en": "Theft & Fire Coverage", "icon": "fire"},
   {"name_ar": "زجاج مجاني", "name_en": "Free Windshield", "icon": "square"}
 ]',
 '[
   {"name_ar": "تأمين الممتلكات الشخصية", "name_en": "Personal Belongings", "price": 75.00, "vat": 11.25, "icon": "briefcase"},
   {"name_ar": "تأمين المفاتيح", "name_en": "Key Protection", "price": 50.00, "vat": 7.50, "icon": "key"},
   {"name_ar": "أضرار الكوارث الطبيعية", "name_en": "Natural Disasters", "price": 350.00, "vat": 52.50, "icon": "cloud-rain"},
   {"name_ar": "مساعدة على الطريق متقدمة", "name_en": "Advanced Road Assistance", "price": 500.00, "vat": 75.00, "icon": "wrench"}
 ]',
 '[
   {"text_ar": "عمر السائق 21-65 سنة", "text_en": "Driver age 21-65"},
   {"text_ar": "سيارة 2015 وأحدث", "text_en": "Vehicle 2015 or newer"}
 ]',
 true, 2),

-- 3. التعاونية - VIP
(1, 3, 'TAW-VIP-2026-001', 'vip',
 'تأمين VIP - التعاونية', 'VIP Insurance - Tawuniya',
 25, 60, 2018, 2026, 100000.00, 1500000.00,
 2500.00, 3.50, 15.00, 20.00, 15.00,
 '[
   {"amount": 0, "label_ar": "بدون تحمل", "label_en": "Zero Deductible", "discount_pct": 0}
 ]',
 0.00,
 '{"type": "vip", "formula": "price_base + (vehicle_value * rate_pct / 100)", "zero_deductible": true}',
 '[
   {"name_ar": "تأمين الحوادث الشخصية", "name_en": "Personal Accident Coverage", "icon": "user-shield"},
   {"name_ar": "الحماية القانونية", "name_en": "Legal Protection", "icon": "scale"},
   {"name_ar": "السيارة البديلة 14 يوم", "name_en": "Replacement Car 14 Days", "icon": "car"},
   {"name_ar": "التمديد الجغرافي (دول الخليج)", "name_en": "GCC Extension", "icon": "globe"},
   {"name_ar": "تغطية إضافية كاملة", "name_en": "Full Additional Coverage", "icon": "plus-circle"},
   {"name_ar": "تغطية الطوارئ 24/7", "name_en": "24/7 Emergency Coverage", "icon": "phone"},
   {"name_ar": "بدون تحمل", "name_en": "Zero Deductible", "icon": "check-circle"},
   {"name_ar": "خدمة كونسيرج", "name_en": "Concierge Service", "icon": "star"},
   {"name_ar": "تعويض فوري", "name_en": "Instant Claims", "icon": "zap"}
 ]',
 '[
   {"name_ar": "تأمين الممتلكات الشخصية", "name_en": "Personal Belongings", "price": 0.00, "vat": 0.00, "included": true, "icon": "briefcase"},
   {"name_ar": "أضرار الكوارث الطبيعية", "name_en": "Natural Disasters", "price": 0.00, "vat": 0.00, "included": true, "icon": "cloud-rain"},
   {"name_ar": "مساعدة على الطريق VIP", "name_en": "VIP Road Assistance", "price": 0.00, "vat": 0.00, "included": true, "icon": "wrench"}
 ]',
 '[
   {"text_ar": "عمر السائق 25-60 سنة", "text_en": "Driver age 25-60"},
   {"text_ar": "سيارة 2018 وأحدث", "text_en": "Vehicle 2018 or newer"},
   {"text_ar": "قيمة السيارة 100,000+ ريال", "text_en": "Vehicle value 100K+ SAR"}
 ]',
 true, 3),

-- 4. الراجحي - ضد الغير
(3, 1, 'RAJ-TPL-2026-001', 'tpl',
 'تكافل ضد الغير - الراجحي', 'Takaful TPL - Al Rajhi',
 18, 75, 2008, 2026, 10000.00, 400000.00,
 850.00, 0.00, 0.00, 8.00, 15.00,
 '[{"amount": 0, "label_ar": "بدون تحمل", "label_en": "No Deductible", "discount_pct": 0}]',
 0.00,
 '{"type": "tpl", "sharia_compliant": true}',
 '[
   {"name_ar": "تغطية الطرف الثالث", "name_en": "Third Party Coverage", "icon": "shield-check"},
   {"name_ar": "متوافق مع الشريعة", "name_en": "Sharia Compliant", "icon": "mosque"},
   {"name_ar": "سعر منافس", "name_en": "Competitive Price", "icon": "tag"}
 ]',
 '[]',
 '[{"text_ar": "عمر السائق 18-75 سنة", "text_en": "Driver age 18-75"}]',
 true, 4),

-- 5. الراجحي - شامل
(3, 2, 'RAJ-COMP-2026-001', 'comprehensive',
 'تكافل شامل - الراجحي', 'Takaful Comprehensive - Al Rajhi',
 21, 65, 2014, 2026, 40000.00, 700000.00,
 1100.00, 2.60, 8.00, 12.00, 15.00,
 '[
   {"amount": 750, "label_ar": "750 ريال", "label_en": "750 SAR", "discount_pct": 0},
   {"amount": 1500, "label_ar": "1500 ريال", "label_en": "1500 SAR", "discount_pct": 5},
   {"amount": 3000, "label_ar": "3000 ريال", "label_en": "3000 SAR", "discount_pct": 10}
 ]',
 750.00,
 '{"type": "comprehensive", "sharia_compliant": true}',
 '[
   {"name_ar": "تأمين تكافلي شامل", "name_en": "Takaful Comprehensive", "icon": "shield"},
   {"name_ar": "سرقة وحريق", "name_en": "Theft & Fire", "icon": "fire"},
   {"name_ar": "السيارة البديلة 5 أيام", "name_en": "Replacement Car 5 Days", "icon": "car"},
   {"name_ar": "متوافق مع الشريعة", "name_en": "Sharia Compliant", "icon": "mosque"}
 ]',
 '[
   {"name_ar": "تأمين الممتلكات الشخصية", "name_en": "Personal Belongings", "price": 60.00, "vat": 9.00, "icon": "briefcase"},
   {"name_ar": "كوارث طبيعية", "name_en": "Natural Disasters", "price": 300.00, "vat": 45.00, "icon": "cloud-rain"}
 ]',
 '[{"text_ar": "عمر السائق 21-65 سنة", "text_en": "Driver age 21-65"}]',
 true, 5),

-- 6. ميدغلف - ضد الغير
(4, 1, 'MED-TPL-2026-001', 'tpl',
 'تأمين ضد الغير - ميدغلف', 'TPL - MedGulf',
 18, 70, 2010, 2026, 15000.00, 450000.00,
 920.00, 0.00, 0.00, 10.00, 15.00,
 '[{"amount": 0, "label_ar": "بدون تحمل", "label_en": "No Deductible", "discount_pct": 0}]',
 0.00,
 '{"type": "tpl"}',
 '[
   {"name_ar": "تغطية الطرف الثالث", "name_en": "Third Party Coverage", "icon": "shield-check"},
   {"name_ar": "خدمة عملاء متميزة", "name_en": "Premium Service", "icon": "headset"}
 ]',
 '[]',
 '[{"text_ar": "عمر السائق 18-70 سنة", "text_en": "Driver age 18-70"}]',
 true, 6),

-- 7. ميدغلف - شامل
(4, 2, 'MED-COMP-2026-001', 'comprehensive',
 'تأمين شامل - ميدغلف', 'Comprehensive - MedGulf',
 21, 65, 2015, 2026, 45000.00, 750000.00,
 1150.00, 2.70, 10.00, 12.00, 15.00,
 '[
   {"amount": 500, "label_ar": "500 ريال", "label_en": "500 SAR", "discount_pct": 0},
   {"amount": 1000, "label_ar": "1000 ريال", "label_en": "1000 SAR", "discount_pct": 4},
   {"amount": 2000, "label_ar": "2000 ريال", "label_en": "2000 SAR", "discount_pct": 8}
 ]',
 500.00,
 '{"type": "comprehensive"}',
 '[
   {"name_ar": "تغطية شاملة", "name_en": "Comprehensive Coverage", "icon": "shield"},
   {"name_ar": "سرقة وحريق", "name_en": "Theft & Fire", "icon": "fire"},
   {"name_ar": "السيارة البديلة 7 أيام", "name_en": "Replacement Car 7 Days", "icon": "car"},
   {"name_ar": "كوارث طبيعية", "name_en": "Natural Disasters", "icon": "cloud-rain"}
 ]',
 '[
   {"name_ar": "تأمين الممتلكات", "name_en": "Personal Belongings", "price": 70.00, "vat": 10.50, "icon": "briefcase"},
   {"name_ar": "مساعدة على الطريق", "name_en": "Road Assistance", "price": 450.00, "vat": 67.50, "icon": "wrench"}
 ]',
 '[{"text_ar": "عمر السائق 21-65 سنة", "text_en": "Driver age 21-65"}]',
 true, 7),

-- 8. ولاء - ضد الغير (الأرخص)
(5, 1, 'WAL-TPL-2026-001', 'tpl',
 'تأمين ضد الغير - ولاء', 'TPL - Walaa',
 18, 80, 2005, 2026, 5000.00, 300000.00,
 750.00, 0.00, 0.00, 8.00, 15.00,
 '[{"amount": 0, "label_ar": "بدون تحمل", "label_en": "No Deductible", "discount_pct": 0}]',
 0.00,
 '{"type": "tpl", "budget_option": true}',
 '[
   {"name_ar": "تغطية الطرف الثالث", "name_en": "Third Party Coverage", "icon": "shield-check"},
   {"name_ar": "أقل سعر", "name_en": "Lowest Price", "icon": "tag"}
 ]',
 '[]',
 '[{"text_ar": "عمر السائق 18-80 سنة", "text_en": "Driver age 18-80"}]',
 true, 8),

-- 9. ولاء - شامل
(5, 2, 'WAL-COMP-2026-001', 'comprehensive',
 'تأمين شامل - ولاء', 'Comprehensive - Walaa',
 21, 65, 2012, 2026, 30000.00, 600000.00,
 1000.00, 2.40, 5.00, 10.00, 15.00,
 '[
   {"amount": 1000, "label_ar": "1000 ريال", "label_en": "1000 SAR", "discount_pct": 0},
   {"amount": 2000, "label_ar": "2000 ريال", "label_en": "2000 SAR", "discount_pct": 6}
 ]',
 1000.00,
 '{"type": "comprehensive", "renewal_discount": 10}',
 '[
   {"name_ar": "تغطية شاملة", "name_en": "Comprehensive Coverage", "icon": "shield"},
   {"name_ar": "سرقة وحريق", "name_en": "Theft & Fire", "icon": "fire"},
   {"name_ar": "خصم تجديد 10%", "name_en": "Renewal Discount 10%", "icon": "percent"}
 ]',
 '[
   {"name_ar": "تأمين الممتلكات", "name_en": "Personal Belongings", "price": 55.00, "vat": 8.25, "icon": "briefcase"}
 ]',
 '[{"text_ar": "عمر السائق 21-65 سنة", "text_en": "Driver age 21-65"}]',
 true, 9),

-- 10. أكسا - ضد الغير
(6, 1, 'AXA-TPL-2026-001', 'tpl',
 'تأمين ضد الغير - أكسا', 'TPL - AXA',
 18, 70, 2010, 2026, 20000.00, 500000.00,
 980.00, 0.00, 0.00, 10.00, 15.00,
 '[{"amount": 0, "label_ar": "بدون تحمل", "label_en": "No Deductible", "discount_pct": 0}]',
 0.00,
 '{"type": "tpl", "international": true}',
 '[
   {"name_ar": "تغطية الطرف الثالث", "name_en": "Third Party Coverage", "icon": "shield-check"},
   {"name_ar": "حماية دولية", "name_en": "International Coverage", "icon": "globe"},
   {"name_ar": "مساعدة على الطريق", "name_en": "Road Assistance", "icon": "truck"}
 ]',
 '[]',
 '[{"text_ar": "عمر السائق 18-70 سنة", "text_en": "Driver age 18-70"}]',
 true, 10),

-- 11. أكسا - شامل
(6, 2, 'AXA-COMP-2026-001', 'comprehensive',
 'تأمين شامل - أكسا', 'Comprehensive - AXA',
 21, 65, 2016, 2026, 60000.00, 900000.00,
 1400.00, 3.00, 12.00, 15.00, 15.00,
 '[
   {"amount": 500, "label_ar": "500 ريال", "label_en": "500 SAR", "discount_pct": 0},
   {"amount": 1000, "label_ar": "1000 ريال", "label_en": "1000 SAR", "discount_pct": 4}
 ]',
 500.00,
 '{"type": "comprehensive", "international": true}',
 '[
   {"name_ar": "تغطية شاملة عالمية", "name_en": "Global Comprehensive", "icon": "globe"},
   {"name_ar": "كوارث طبيعية", "name_en": "Natural Disasters", "icon": "cloud-rain"},
   {"name_ar": "مساعدة 24/7", "name_en": "24/7 Assistance", "icon": "phone"},
   {"name_ar": "السيارة البديلة 10 أيام", "name_en": "Replacement Car 10 Days", "icon": "car"},
   {"name_ar": "تغطية دول الخليج", "name_en": "GCC Coverage", "icon": "map"}
 ]',
 '[
   {"name_ar": "تأمين الممتلكات الشخصية", "name_en": "Personal Belongings", "price": 85.00, "vat": 12.75, "icon": "briefcase"},
   {"name_ar": "تأمين المفاتيح", "name_en": "Key Protection", "price": 65.00, "vat": 9.75, "icon": "key"},
   {"name_ar": "مساعدة VIP على الطريق", "name_en": "VIP Road Assistance", "price": 600.00, "vat": 90.00, "icon": "wrench"}
 ]',
 '[{"text_ar": "عمر السائق 21-65 سنة", "text_en": "Driver age 21-65"}]',
 true, 11),

-- 12. سلامة - ضد الغير
(7, 1, 'SAL-TPL-2026-001', 'tpl',
 'تأمين ضد الغير - سلامة', 'TPL - Salama',
 18, 75, 2008, 2026, 12000.00, 400000.00,
 800.00, 0.00, 0.00, 8.00, 15.00,
 '[{"amount": 0, "label_ar": "بدون تحمل", "label_en": "No Deductible", "discount_pct": 0}]',
 0.00,
 '{"type": "tpl"}',
 '[
   {"name_ar": "تغطية الطرف الثالث", "name_en": "Third Party Coverage", "icon": "shield-check"},
   {"name_ar": "إجراءات سريعة", "name_en": "Fast Procedures", "icon": "zap"}
 ]',
 '[]',
 '[{"text_ar": "عمر السائق 18-75 سنة", "text_en": "Driver age 18-75"}]',
 true, 12),

-- 13. سلامة - شامل
(7, 2, 'SAL-COMP-2026-001', 'comprehensive',
 'تأمين شامل - سلامة', 'Comprehensive - Salama',
 21, 65, 2013, 2026, 35000.00, 650000.00,
 1050.00, 2.50, 8.00, 10.00, 15.00,
 '[
   {"amount": 750, "label_ar": "750 ريال", "label_en": "750 SAR", "discount_pct": 0},
   {"amount": 1500, "label_ar": "1500 ريال", "label_en": "1500 SAR", "discount_pct": 5},
   {"amount": 2500, "label_ar": "2500 ريال", "label_en": "2500 SAR", "discount_pct": 8}
 ]',
 750.00,
 '{"type": "comprehensive"}',
 '[
   {"name_ar": "تغطية شاملة", "name_en": "Comprehensive Coverage", "icon": "shield"},
   {"name_ar": "سرقة وحريق", "name_en": "Theft & Fire", "icon": "fire"},
   {"name_ar": "السيارة البديلة 5 أيام", "name_en": "Replacement Car 5 Days", "icon": "car"}
 ]',
 '[
   {"name_ar": "تأمين الممتلكات", "name_en": "Personal Belongings", "price": 50.00, "vat": 7.50, "icon": "briefcase"},
   {"name_ar": "كوارث طبيعية", "name_en": "Natural Disasters", "price": 280.00, "vat": 42.00, "icon": "cloud-rain"}
 ]',
 '[{"text_ar": "عمر السائق 21-65 سنة", "text_en": "Driver age 21-65"}]',
 true, 13),

-- 14. الوطنية - شامل (كما في الصورة)
(1, 2, 'WAT-COMP-2026-001', 'comprehensive',
 'تأمين شامل - الوطنية', 'Comprehensive - Wataniya',
 21, 65, 2015, 2026, 30000.00, 500000.00,
 1200.00, 2.80, 0.00, 0.00, 15.00,
 '[
   {"amount": 1000, "label_ar": "1000 ريال", "label_en": "1000 SAR", "discount_pct": 0},
   {"amount": 2500, "label_ar": "2500 ريال", "label_en": "2500 SAR", "discount_pct": 5},
   {"amount": 3500, "label_ar": "3500 ريال", "label_en": "3500 SAR", "discount_pct": 8}
 ]',
 3500.00,
 '{"type": "comprehensive", "example": true}',
 '[
   {"name_ar": "تأمين الحوادث الشخصية", "name_en": "Personal Accident", "icon": "user-shield"},
   {"name_ar": "الحماية القانونية", "name_en": "Legal Protection", "icon": "scale"},
   {"name_ar": "السيارة البديلة", "name_en": "Replacement Car", "icon": "car"},
   {"name_ar": "التمديد الجغرافي", "name_en": "Geographic Extension", "icon": "globe"},
   {"name_ar": "تغطية إضافية", "name_en": "Additional Coverage", "icon": "plus"},
   {"name_ar": "تغطية الطوارئ", "name_en": "Emergency Coverage", "icon": "alert-circle"}
 ]',
 '[
   {"name_ar": "تأمين الممتلكات الشخصية", "name_en": "Personal Belongings", "price": 75.00, "vat": 11.25, "icon": "briefcase"},
   {"name_ar": "تأمين المفاتيح", "name_en": "Key Protection", "price": 50.00, "vat": 7.50, "icon": "key"},
   {"name_ar": "أضرار الكوارث الطبيعية", "name_en": "Natural Disasters", "price": 350.00, "vat": 52.50, "icon": "cloud-rain"},
   {"name_ar": "مساعدة على الطريق", "name_en": "Road Assistance", "price": 500.00, "vat": 75.00, "icon": "truck"}
 ]',
 '[{"text_ar": "عمر السائق 21-65 سنة", "text_en": "Driver age 21-65"}]',
 true, 14);

-- ================================================================
-- Success Message
-- ================================================================

DO $$
DECLARE
    offer_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO offer_count FROM insurance_offers;
    
    RAISE NOTICE '';
    RAISE NOTICE '✅ =====================================================';
    RAISE NOTICE '✅ Complete Insurance Offers Schema Created!';
    RAISE NOTICE '✅ =====================================================';
    RAISE NOTICE '';
    RAISE NOTICE '📊 TABLE STRUCTURE:';
    RAISE NOTICE '   ├── Basic Info: offer_code, coverage_type, names';
    RAISE NOTICE '   ├── Requirements: age range, vehicle year/value';
    RAISE NOTICE '   ├── Pricing: base, rate%, discounts, VAT';
    RAISE NOTICE '   ├── Deductible: options with discounts';
    RAISE NOTICE '   ├── Included Features: free benefits (يشمل مجاناً)';
    RAISE NOTICE '   ├── Optional Add-ons: prices + VAT (منافع إضافية)';
    RAISE NOTICE '   └── Conditions: requirements text';
    RAISE NOTICE '';
    RAISE NOTICE '📦 DATA INSERTED: % offers', offer_count;
    RAISE NOTICE '   • 3 التعاونية (TPL, Comp, VIP)';
    RAISE NOTICE '   • 2 الراجحي (TPL, Comp)';
    RAISE NOTICE '   • 2 ميدغلف (TPL, Comp)';
    RAISE NOTICE '   • 2 ولاء (TPL, Comp)';
    RAISE NOTICE '   • 2 أكسا (TPL, Comp)';
    RAISE NOTICE '   • 2 سلامة (TPL, Comp)';
    RAISE NOTICE '   • 1 الوطنية (example from screenshot)';
    RAISE NOTICE '';
    RAISE NOTICE '🚀 Ready for Production!';
END $$;
