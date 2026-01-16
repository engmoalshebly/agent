-- ================================================================
-- SAIA Insurance Broker Platform - Schema Additions & Seed Data
-- PostgreSQL 15+
-- ================================================================
-- Author: Mohamed's Insurance Platform
-- Created: 2026-01-15
-- Description: Additional tables for conversation stage tracking
--              + Complete demo seed data for all tables
-- ================================================================

-- ================================================================
-- PART 1: ADDITIONAL TABLES (Stage Tracking)
-- ================================================================

-- 21) Conversation Stage Logs - تتبع مراحل المحادثة
DROP TABLE IF EXISTS conversation_stage_logs CASCADE;

CREATE TABLE conversation_stage_logs (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    stage VARCHAR(50) NOT NULL,
    -- greeting, collecting_profile, collecting_vehicle, fetching_offers,
    -- showing_offers, awaiting_selection, confirmation, creating_invoice,
    -- pending_payment, issuing_policy, done, handoff_human, error
    status VARCHAR(20) NOT NULL DEFAULT 'started',
    -- started, in_progress, completed, failed, skipped
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds INTEGER,
    data_collected JSONB,  -- البيانات المجمعة في هذه المرحلة
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_stage_logs_conversation ON conversation_stage_logs(conversation_id);
CREATE INDEX idx_stage_logs_stage ON conversation_stage_logs(stage);
CREATE INDEX idx_stage_logs_status ON conversation_stage_logs(status);
CREATE INDEX idx_stage_logs_started ON conversation_stage_logs(started_at DESC);

COMMENT ON TABLE conversation_stage_logs IS 'Tracks each stage of the conversation flow for analytics and debugging';

-- 22) WhatsApp Sessions - جلسات واتساب
DROP TABLE IF EXISTS whatsapp_sessions CASCADE;

CREATE TABLE whatsapp_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    phone_number VARCHAR(20) NOT NULL,
    whatsapp_id VARCHAR(100) UNIQUE,  -- معرف واتساب
    session_status VARCHAR(20) DEFAULT 'active',  -- active, expired, blocked
    last_message_at TIMESTAMP,
    message_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_wa_sessions_user ON whatsapp_sessions(user_id);
CREATE INDEX idx_wa_sessions_phone ON whatsapp_sessions(phone_number);
CREATE INDEX idx_wa_sessions_status ON whatsapp_sessions(session_status);

COMMENT ON TABLE whatsapp_sessions IS 'WhatsApp session management for users';

-- 23) Conversation Context - سياق المحادثة
DROP TABLE IF EXISTS conversation_context CASCADE;

CREATE TABLE conversation_context (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE UNIQUE,
    current_stage VARCHAR(50) NOT NULL DEFAULT 'greeting',
    profile_data JSONB DEFAULT '{}',
    vehicle_data JSONB DEFAULT '{}',
    offers_shown JSONB DEFAULT '[]',
    selected_offer_id INTEGER,
    order_id INTEGER,
    invoice_id INTEGER,
    policy_id INTEGER,
    last_question VARCHAR(200),
    awaiting_input_type VARCHAR(50),  -- national_id, birth_date, plate_number, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_context_conversation ON conversation_context(conversation_id);
CREATE INDEX idx_context_stage ON conversation_context(current_stage);

COMMENT ON TABLE conversation_context IS 'Stores conversation state and collected data for resumability';

-- Trigger for conversation_context updated_at
CREATE TRIGGER update_conversation_context_updated_at BEFORE UPDATE ON conversation_context 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_whatsapp_sessions_updated_at BEFORE UPDATE ON whatsapp_sessions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ================================================================
-- PART 2: SEED DATA - بيانات تجريبية
-- ================================================================

-- ============================================
-- 1) Insurance Services - أنواع التأمين
-- ============================================
INSERT INTO insurance_services (service_code, name_ar, name_en, description, is_active) VALUES
('AUTO_TPL', 'تأمين ضد الغير', 'Third Party Liability', 'تغطية الأضرار التي تلحق بالطرف الثالث فقط', true),
('AUTO_COMP', 'تأمين شامل', 'Comprehensive Auto', 'تغطية شاملة للمركبة تشمل الحوادث والسرقة والحريق', true),
('AUTO_VIP', 'تأمين VIP', 'VIP Auto Insurance', 'تأمين شامل مع مميزات إضافية وخدمة مميزة', true),
('HEALTH_IND', 'تأمين صحي فردي', 'Individual Health', 'تأمين صحي للأفراد', true),
('HEALTH_FAM', 'تأمين صحي عائلي', 'Family Health', 'تأمين صحي للعائلة', true),
('TRAVEL_INT', 'تأمين سفر دولي', 'International Travel', 'تأمين السفر للخارج', true);

-- ============================================
-- 2) Insurance Companies - شركات التأمين
-- ============================================
INSERT INTO insurance_companies (company_code, name_ar, name_en, logo_url, contact_email, support_phone, rating_score, is_active) VALUES
('TAWUNIYA', 'التعاونية للتأمين', 'Tawuniya Insurance', '/logos/tawuniya.png', 'support@tawuniya.com.sa', '8001249990', 4.5, true),
('BUPA', 'بوبا العربية', 'Bupa Arabia', '/logos/bupa.png', 'care@bupa.com.sa', '8001244400', 4.7, true),
('ALRAJHI', 'تكافل الراجحي', 'Al Rajhi Takaful', '/logos/alrajhi.png', 'info@alrajhitakaful.com', '920004414', 4.3, true),
('MEDGULF', 'ميدغلف للتأمين', 'MedGulf Insurance', '/logos/medgulf.png', 'service@medgulf.com.sa', '920006676', 4.2, true),
('WALAA', 'ولاء للتأمين', 'Walaa Insurance', '/logos/walaa.png', 'info@walaa.com', '920012124', 4.0, true),
('AXA', 'أكسا للتأمين التعاوني', 'AXA Cooperative', '/logos/axa.png', 'customer@axa.com.sa', '920001717', 4.4, true),
('SALAMA', 'سلامة للتأمين', 'Salama Insurance', '/logos/salama.png', 'help@salama.com.sa', '8002440018', 4.1, true);

-- ============================================
-- 3) Company Services - ربط الشركات بالخدمات
-- ============================================
INSERT INTO company_services (company_id, service_id, commission_rate, is_active) VALUES
-- التعاونية
(1, 1, 8.00, true),  -- TPL
(1, 2, 10.00, true), -- Comprehensive
(1, 3, 12.00, true), -- VIP
-- بوبا
(2, 4, 7.50, true),  -- Health Individual
(2, 5, 8.50, true),  -- Health Family
-- الراجحي
(3, 1, 7.00, true),  -- TPL
(3, 2, 9.00, true),  -- Comprehensive
(3, 4, 8.00, true),  -- Health Individual
-- ميدغلف
(4, 1, 7.50, true),  -- TPL
(4, 2, 9.50, true),  -- Comprehensive
(4, 6, 6.00, true),  -- Travel
-- ولاء
(5, 1, 6.50, true),  -- TPL
(5, 2, 8.50, true),  -- Comprehensive
-- أكسا
(6, 1, 7.00, true),  -- TPL
(6, 2, 9.00, true),  -- Comprehensive
(6, 4, 7.00, true),  -- Health Individual
(6, 5, 8.00, true),  -- Health Family
-- سلامة
(7, 1, 6.00, true),  -- TPL
(7, 2, 8.00, true);  -- Comprehensive

-- ============================================
-- 4) Insurance Offers - العروض
-- ============================================
INSERT INTO insurance_offers (company_id, service_id, offer_code, coverage_type, min_age, max_age, min_vehicle_year, max_vehicle_year, min_vehicle_value, max_vehicle_value, price_base, features_json, conditions_json, is_active) VALUES

-- التعاونية - ضد الغير
(1, 1, 'TAW-TPL-001', 'tpl', 18, 70, 2010, 2026, 20000, 500000, 950.00,
 '{"features": ["تغطية الطرف الثالث", "مساعدة على الطريق", "تعويض سريع"]}',
 '{"conditions": ["عمر السائق 18-70", "سيارة 2010 وأحدث"]}', true),

-- التعاونية - شامل
(1, 2, 'TAW-COMP-001', 'comprehensive', 21, 65, 2015, 2026, 50000, 800000, 2850.00,
 '{"features": ["تغطية حوادث كاملة", "سرقة وحريق", "سيارة بديلة 7 أيام", "زجاج مجاني"]}',
 '{"conditions": ["عمر السائق 21-65", "سيارة 2015 وأحدث"]}', true),

-- التعاونية - VIP
(1, 3, 'TAW-VIP-001', 'vip', 25, 60, 2018, 2026, 100000, 1500000, 5500.00,
 '{"features": ["تغطية شاملة بلا حدود", "سيارة بديلة 14 يوم", "صيانة مجانية", "مساعدة 24/7", "تعويض فوري"]}',
 '{"conditions": ["عمر السائق 25-60", "سيارة 2018 وأحدث", "قيمة 100 ألف+"]}', true),

-- الراجحي - ضد الغير
(3, 1, 'RAJ-TPL-001', 'tpl', 18, 75, 2008, 2026, 15000, 400000, 850.00,
 '{"features": ["تغطية الطرف الثالث", "متوافق مع الشريعة", "سعر منافس"]}',
 '{"conditions": ["عمر السائق 18-75"]}', true),

-- الراجحي - شامل
(3, 2, 'RAJ-COMP-001', 'comprehensive', 21, 65, 2014, 2026, 40000, 700000, 2650.00,
 '{"features": ["تأمين تكافلي شامل", "سرقة وحريق", "سيارة بديلة 5 أيام"]}',
 '{"conditions": ["عمر السائق 21-65", "سيارة 2014 وأحدث"]}', true),

-- ميدغلف - ضد الغير
(4, 1, 'MED-TPL-001', 'tpl', 18, 70, 2010, 2026, 20000, 450000, 920.00,
 '{"features": ["تغطية الطرف الثالث", "خدمة عملاء متميزة"]}',
 '{"conditions": ["عمر السائق 18-70"]}', true),

-- ميدغلف - شامل
(4, 2, 'MED-COMP-001', 'comprehensive', 21, 65, 2015, 2026, 45000, 750000, 2750.00,
 '{"features": ["تغطية شاملة", "سرقة وحريق", "سيارة بديلة 7 أيام", "كوارث طبيعية"]}',
 '{"conditions": ["عمر السائق 21-65"]}', true),

-- ولاء - ضد الغير (الأرخص)
(5, 1, 'WAL-TPL-001', 'tpl', 18, 80, 2005, 2026, 10000, 300000, 750.00,
 '{"features": ["تغطية الطرف الثالث", "أقل سعر"]}',
 '{"conditions": ["عمر السائق 18-80"]}', true),

-- ولاء - شامل
(5, 2, 'WAL-COMP-001', 'comprehensive', 21, 65, 2012, 2026, 35000, 600000, 2450.00,
 '{"features": ["تغطية شاملة", "سرقة وحريق", "خصم تجديد 10%"]}',
 '{"conditions": ["عمر السائق 21-65"]}', true),

-- أكسا - ضد الغير
(6, 1, 'AXA-TPL-001', 'tpl', 18, 70, 2010, 2026, 20000, 500000, 980.00,
 '{"features": ["تغطية الطرف الثالث", "حماية دولية", "مساعدة على الطريق"]}',
 '{"conditions": ["عمر السائق 18-70"]}', true),

-- أكسا - شامل
(6, 2, 'AXA-COMP-001', 'comprehensive', 21, 65, 2016, 2026, 60000, 900000, 3200.00,
 '{"features": ["تغطية شاملة عالمية", "كوارث طبيعية", "مساعدة 24/7", "سيارة بديلة 10 أيام"]}',
 '{"conditions": ["عمر السائق 21-65", "سيارة 2016 وأحدث"]}', true),

-- سلامة - ضد الغير
(7, 1, 'SAL-TPL-001', 'tpl', 18, 75, 2008, 2026, 15000, 400000, 800.00,
 '{"features": ["تغطية الطرف الثالث", "إجراءات سريعة"]}',
 '{"conditions": ["عمر السائق 18-75"]}', true),

-- سلامة - شامل
(7, 2, 'SAL-COMP-001', 'comprehensive', 21, 65, 2013, 2026, 40000, 650000, 2550.00,
 '{"features": ["تغطية شاملة", "سرقة وحريق", "سيارة بديلة 5 أيام"]}',
 '{"conditions": ["عمر السائق 21-65"]}', true);

-- ============================================
-- 5) Offer Variants - باقات إضافية
-- ============================================
INSERT INTO offer_variants (offer_id, variant_code, title, extra_price, features_json, is_default) VALUES
-- التعاونية شامل
(2, 'TAW-COMP-BASIC', 'الباقة الأساسية', 0, '{"features": ["التغطية الأساسية"]}', true),
(2, 'TAW-COMP-PLUS', 'باقة بلس', 350.00, '{"features": ["سيارة بديلة 14 يوم", "زجاج بدون حادث"]}', false),
(2, 'TAW-COMP-GOLD', 'الباقة الذهبية', 750.00, '{"features": ["سيارة بديلة 21 يوم", "صيانة طوارئ", "تعويض فوري"]}', false),

-- أكسا شامل
(11, 'AXA-COMP-BASIC', 'الباقة الأساسية', 0, '{"features": ["التغطية الأساسية"]}', true),
(11, 'AXA-COMP-PREMIUM', 'الباقة المميزة', 500.00, '{"features": ["سيارة بديلة 15 يوم", "حماية دولية"]}', false);

-- ============================================
-- 6) Demo Users - مستخدمين تجريبيين
-- ============================================
INSERT INTO users (user_code, full_name, national_id, birth_date, age, gender, phone, email, city, marital_status) VALUES
('USR-2026-00001', 'محمد أحمد العتيبي', '1122334455', '1990-03-25', 35, 'male', '0501234567', 'mohammed@email.com', 'الرياض', 'married'),
('USR-2026-00002', 'فاطمة سعد الحربي', '1098765432', '1985-07-12', 40, 'female', '0559876543', 'fatima@email.com', 'جدة', 'married'),
('USR-2026-00003', 'عبدالله خالد السالم', '1234509876', '1995-11-30', 30, 'male', '0567891234', 'abdullah@email.com', 'الدمام', 'single'),
('USR-2026-00004', 'نورة فهد القحطاني', '1357924680', '1988-05-18', 37, 'female', '0541478523', 'noura@email.com', 'مكة', 'married'),
('USR-2026-00005', 'سعود محمد الدوسري', '1470258369', '1992-09-08', 33, 'male', '0523698741', 'saud@email.com', 'الرياض', 'single');

-- ============================================
-- 7) Demo Vehicles - مركبات تجريبية
-- ============================================
INSERT INTO vehicles (user_id, plate_no, brand, model, model_year, vehicle_value, color, transmission, fuel_type, usage_type) VALUES
(1, 'س ك ر 5678', 'هيونداي', 'سوناتا', 2021, 85000, 'أبيض', 'automatic', 'petrol', 'personal'),
(1, 'ر ص م 1234', 'تويوتا', 'كامري', 2022, 125000, 'فضي', 'automatic', 'petrol', 'personal'),
(2, 'ن ه ع 9012', 'نيسان', 'التيما', 2020, 75000, 'أسود', 'automatic', 'petrol', 'personal'),
(3, 'ب ت ث 3456', 'شيفروليه', 'تاهو', 2023, 280000, 'أبيض', 'automatic', 'petrol', 'personal'),
(4, 'ج ح خ 7890', 'لكزس', 'ES350', 2022, 220000, 'رمادي', 'automatic', 'hybrid', 'personal'),
(5, 'د ذ ر 2468', 'كيا', 'سيراتو', 2021, 65000, 'أحمر', 'automatic', 'petrol', 'personal');

-- ============================================
-- 8) Demo Quote Requests - طلبات عروض
-- ============================================
INSERT INTO quote_requests (user_id, service_id, vehicle_id, request_channel, status) VALUES
(1, 2, 1, 'whatsapp', 'offers_ready'),
(2, 1, 3, 'web', 'offers_ready'),
(3, 2, 4, 'whatsapp', 'collecting'),
(4, 2, 5, 'app', 'processing');

-- ============================================
-- 9) Demo Quote Results - نتائج العروض
-- ============================================
INSERT INTO quote_results (quote_request_id, offer_id, variant_id, base_price, final_price, discount_applied, commission_amount) VALUES
-- طلب 1 - 4 عروض شامل
(1, 2, 1, 2850.00, 2850.00, 0, 285.00),
(1, 5, NULL, 2650.00, 2650.00, 0, 238.50),
(1, 7, NULL, 2750.00, 2750.00, 0, 261.25),
(1, 9, NULL, 2450.00, 2205.00, 245.00, 187.40),  -- خصم 10%

-- طلب 2 - 4 عروض ضد الغير
(2, 1, NULL, 950.00, 950.00, 0, 76.00),
(2, 4, NULL, 850.00, 850.00, 0, 59.50),
(2, 6, NULL, 920.00, 920.00, 0, 69.00),
(2, 8, NULL, 750.00, 750.00, 0, 48.75);

-- ============================================
-- 10) Demo Orders - طلبات مكتملة
-- ============================================
INSERT INTO insurance_orders (order_code, user_id, quote_result_id, service_id, company_id, offer_id, variant_id, total_price, commission_amount, status) VALUES
('ORD-2026-00001', 1, 1, 2, 1, 2, 1, 3277.50, 285.00, 'policy_issued'),
('ORD-2026-00002', 2, 6, 1, 3, 4, NULL, 977.50, 59.50, 'policy_issued'),
('ORD-2026-00003', 5, NULL, 2, 5, 9, NULL, 2535.75, 187.40, 'pending_payment');

-- ============================================
-- 11) Order Status Logs - سجل الحالات
-- ============================================
INSERT INTO order_status_logs (order_id, old_status, new_status, changed_by, note) VALUES
-- Order 1
(1, NULL, 'draft', 'system', 'تم إنشاء الطلب'),
(1, 'draft', 'awaiting_confirmation', 'system', 'في انتظار تأكيد العميل'),
(1, 'awaiting_confirmation', 'pending_payment', 'user', 'العميل أكد الطلب'),
(1, 'pending_payment', 'paid', 'system', 'تم الدفع بنجاح'),
(1, 'paid', 'policy_issued', 'system', 'تم إصدار الوثيقة'),

-- Order 2
(2, NULL, 'draft', 'system', 'تم إنشاء الطلب'),
(2, 'draft', 'pending_payment', 'user', 'العميل أكد مباشرة'),
(2, 'pending_payment', 'paid', 'system', 'تم الدفع'),
(2, 'paid', 'policy_issued', 'system', 'تم إصدار الوثيقة'),

-- Order 3
(3, NULL, 'draft', 'system', 'تم إنشاء الطلب'),
(3, 'draft', 'pending_payment', 'user', 'في انتظار الدفع');

-- ============================================
-- 12) Demo Invoices - فواتير
-- ============================================
INSERT INTO invoices (order_id, invoice_no, provider, amount, status, expires_at, paid_at) VALUES
(1, 'INV-2026-78543', 'demo', 3277.50, 'paid', '2026-01-16 21:00:00', '2026-01-15 21:08:00'),
(2, 'INV-2026-78544', 'demo', 977.50, 'paid', '2026-01-16 20:00:00', '2026-01-15 20:45:00'),
(3, 'INV-2026-78545', 'demo', 2535.75, 'unpaid', '2026-01-17 21:00:00', NULL);

-- ============================================
-- 13) Demo Payments - مدفوعات
-- ============================================
INSERT INTO payments (invoice_id, transaction_ref, provider_response_json, status, processed_at) VALUES
(1, 'TXN-2026-00001', '{"status": "success", "method": "demo_confirmation"}', 'success', '2026-01-15 21:08:00'),
(2, 'TXN-2026-00002', '{"status": "success", "method": "demo_confirmation"}', 'success', '2026-01-15 20:45:00');

-- ============================================
-- 14) Demo Policies - وثائق التأمين
-- ============================================
INSERT INTO policies (policy_no, order_id, company_id, service_id, start_date, end_date, policy_status, pdf_url, qr_verify_url) VALUES
('POL-2026-12847', 1, 1, 2, '2026-01-15', '2027-01-15', 'active', '/policies/POL-2026-12847.pdf', 'https://verify.saia.sa/POL-2026-12847'),
('POL-2026-12848', 2, 3, 1, '2026-01-15', '2027-01-15', 'active', '/policies/POL-2026-12848.pdf', 'https://verify.saia.sa/POL-2026-12848');

-- ============================================
-- 15) Demo User Documents - وثائق المستخدمين
-- ============================================
INSERT INTO user_documents (user_id, policy_id, title, document_type, file_url, is_active) VALUES
(1, 1, 'وثيقة تأمين شامل - هيونداي سوناتا 2021', 'policy', '/policies/POL-2026-12847.pdf', true),
(1, 1, 'فاتورة INV-2026-78543', 'invoice', '/invoices/INV-2026-78543.pdf', true),
(2, 2, 'وثيقة تأمين ضد الغير - نيسان التيما 2020', 'policy', '/policies/POL-2026-12848.pdf', true),
(2, 2, 'فاتورة INV-2026-78544', 'invoice', '/invoices/INV-2026-78544.pdf', true);

-- ============================================
-- 16) Demo Conversations - محادثات
-- ============================================
INSERT INTO conversations (user_id, channel, state, context_json) VALUES
(1, 'whatsapp', 'closed', '{"completed": true, "policy_issued": "POL-2026-12847"}'),
(2, 'web', 'closed', '{"completed": true, "policy_issued": "POL-2026-12848"}'),
(3, 'whatsapp', 'active', '{"current_stage": "collecting_vehicle"}'),
(5, 'whatsapp', 'active', '{"current_stage": "pending_payment", "invoice_id": "INV-2026-78545"}');

-- ============================================
-- 17) Demo Conversation Contexts - سياق مفصل
-- ============================================
INSERT INTO conversation_context (conversation_id, current_stage, profile_data, vehicle_data, selected_offer_id, order_id, invoice_id, policy_id, last_question, awaiting_input_type) VALUES
(1, 'done', 
   '{"national_id": "1122334455", "birth_date": "1990-03-25", "phone": "0501234567"}',
   '{"plate_no": "س ك ر 5678", "brand": "هيونداي", "model": "سوناتا", "year": 2021, "value": 85000}',
   2, 1, 1, 1, NULL, NULL),
   
(3, 'collecting_vehicle',
   '{"national_id": "1234509876", "birth_date": "1995-11-30", "phone": "0567891234"}',
   '{"plate_no": "ب ت ث 3456"}',
   NULL, NULL, NULL, NULL, 'ما نوع السيارة؟', 'vehicle_make_model'),
   
(4, 'pending_payment',
   '{"national_id": "1470258369", "birth_date": "1992-09-08", "phone": "0523698741"}',
   '{"plate_no": "د ذ ر 2468", "brand": "كيا", "model": "سيراتو", "year": 2021, "value": 65000}',
   9, 3, 3, NULL, 'الفاتورة جاهزة. اكتب "تم الدفع" بعد الدفع', 'payment_confirmation');

-- ============================================
-- 18) Demo Stage Logs - سجل المراحل
-- ============================================
INSERT INTO conversation_stage_logs (conversation_id, stage, status, started_at, completed_at, duration_seconds, data_collected) VALUES
-- Conversation 1 (Complete flow)
(1, 'greeting', 'completed', '2026-01-15 21:00:00', '2026-01-15 21:00:05', 5, '{"choice": "new_insurance"}'),
(1, 'collecting_profile', 'completed', '2026-01-15 21:00:05', '2026-01-15 21:02:30', 145, '{"national_id": "collected", "birth_date": "collected", "phone": "collected"}'),
(1, 'collecting_vehicle', 'completed', '2026-01-15 21:02:30', '2026-01-15 21:04:50', 140, '{"plate": "collected", "make": "collected", "model": "collected", "year": "collected", "value": "collected"}'),
(1, 'fetching_offers', 'completed', '2026-01-15 21:04:50', '2026-01-15 21:04:52', 2, '{"offers_count": 4}'),
(1, 'showing_offers', 'completed', '2026-01-15 21:04:52', '2026-01-15 21:04:53', 1, '{"offers_shown": 4}'),
(1, 'awaiting_selection', 'completed', '2026-01-15 21:04:53', '2026-01-15 21:05:45', 52, '{"selected": 1}'),
(1, 'confirmation', 'completed', '2026-01-15 21:05:45', '2026-01-15 21:06:30', 45, '{"confirmed": true}'),
(1, 'creating_invoice', 'completed', '2026-01-15 21:06:30', '2026-01-15 21:06:32', 2, '{"invoice_id": "INV-2026-78543"}'),
(1, 'pending_payment', 'completed', '2026-01-15 21:06:32', '2026-01-15 21:08:00', 88, '{"paid": true}'),
(1, 'issuing_policy', 'completed', '2026-01-15 21:08:00', '2026-01-15 21:08:05', 5, '{"policy_id": "POL-2026-12847"}'),

-- Conversation 3 (In progress)
(3, 'greeting', 'completed', '2026-01-15 21:10:00', '2026-01-15 21:10:05', 5, '{"choice": "new_insurance"}'),
(3, 'collecting_profile', 'completed', '2026-01-15 21:10:05', '2026-01-15 21:12:00', 115, '{"national_id": "collected", "birth_date": "collected", "phone": "collected"}'),
(3, 'collecting_vehicle', 'in_progress', '2026-01-15 21:12:00', NULL, NULL, '{"plate": "collected"}');

-- ============================================
-- 19) Demo Messages - رسائل المحادثة
-- ============================================
INSERT INTO messages (conversation_id, sender_type, message_type, content) VALUES
-- Conversation 1
(1, 'user', 'text', 'السلام عليكم'),
(1, 'agent', 'text', 'وعليكم السلام! 👋 أهلاً بك في خدمة التأمين الذكي'),
(1, 'user', 'text', '1'),
(1, 'agent', 'text', 'تمام! أعطني رقم الهوية'),
(1, 'user', 'text', '1122334455'),
(1, 'agent', 'text', '✅ تم. أعطني تاريخ الميلاد'),
(1, 'user', 'text', '25 مارس 1990'),
(1, 'agent', 'text', '✅ رقم جوالك؟'),
(1, 'user', 'text', '0501234567'),
(1, 'agent', 'text', '✅ الآن بيانات السيارة. رقم اللوحة؟'),
(1, 'user', 'text', 'س ك ر 5678'),
(1, 'agent', 'text', 'نوع السيارة؟'),
(1, 'user', 'text', 'هيونداي سوناتا 2021'),
(1, 'agent', 'text', 'قيمة السيارة بالريال؟'),
(1, 'user', 'text', '85000'),
(1, 'agent', 'text', '⏳ جاري البحث عن العروض...'),
(1, 'agent', 'text', '🎯 وجدنا 4 عروض! اختر الرقم المناسب'),
(1, 'user', 'text', '1'),
(1, 'agent', 'text', '📋 ملخص طلبك. هل تريد إنشاء الفاتورة؟'),
(1, 'user', 'text', 'نعم'),
(1, 'agent', 'text', '✅ الفاتورة INV-2026-78543 جاهزة. 3,277.50 ريال'),
(1, 'user', 'text', 'تم الدفع'),
(1, 'agent', 'text', '🎉 تم إصدار وثيقتك POL-2026-12847! [PDF مرفق]');

-- ============================================
-- 20) Demo WhatsApp Sessions
-- ============================================
INSERT INTO whatsapp_sessions (user_id, phone_number, whatsapp_id, session_status, last_message_at, message_count) VALUES
(1, '0501234567', 'wa_966501234567', 'active', '2026-01-15 21:08:05', 23),
(3, '0567891234', 'wa_966567891234', 'active', '2026-01-15 21:12:00', 8),
(5, '0523698741', 'wa_966523698741', 'active', '2026-01-15 21:00:00', 15);

-- ============================================
-- 21) User Activity Logs - سجل النشاط
-- ============================================
INSERT INTO user_activity_logs (user_id, activity_type, metadata_json) VALUES
(1, 'started_conversation', '{"channel": "whatsapp"}'),
(1, 'viewed_offers', '{"offers_count": 4}'),
(1, 'selected_offer', '{"offer_id": 2, "price": 2850}'),
(1, 'confirmed_order', '{"order_id": 1}'),
(1, 'paid_invoice', '{"invoice_id": 1, "amount": 3277.50}'),
(1, 'received_policy', '{"policy_id": 1}'),
(1, 'downloaded_policy', '{"policy_no": "POL-2026-12847"}'),
(2, 'started_conversation', '{"channel": "web"}'),
(2, 'paid_invoice', '{"invoice_id": 2}'),
(2, 'received_policy', '{"policy_id": 2}');

-- ============================================
-- 22) System Audit Logs - سجل النظام
-- ============================================
INSERT INTO system_audit_logs (entity_type, entity_id, action, performed_by, changes_json) VALUES
('order', 1, 'create', 'system', '{"status": "draft"}'),
('order', 1, 'status_change', 'system', '{"from": "draft", "to": "policy_issued"}'),
('invoice', 1, 'create', 'system', '{"amount": 3277.50}'),
('invoice', 1, 'status_change', 'system', '{"from": "unpaid", "to": "paid"}'),
('policy', 1, 'create', 'system', '{"policy_no": "POL-2026-12847"}'),
('user', 1, 'create', 'system', '{"source": "whatsapp"}');

-- ================================================================
-- Success Message
-- ================================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '✅ =====================================================';
    RAISE NOTICE '✅ Schema Additions & Seed Data Loaded Successfully!';
    RAISE NOTICE '✅ =====================================================';
    RAISE NOTICE '';
    RAISE NOTICE '📊 NEW TABLES ADDED:';
    RAISE NOTICE '   • conversation_stage_logs - تتبع مراحل المحادثة';
    RAISE NOTICE '   • whatsapp_sessions - جلسات واتساب';
    RAISE NOTICE '   • conversation_context - سياق المحادثة';
    RAISE NOTICE '';
    RAISE NOTICE '📦 SEED DATA SUMMARY:';
    RAISE NOTICE '   • 6 Insurance Services';
    RAISE NOTICE '   • 7 Insurance Companies';
    RAISE NOTICE '   • 20 Company-Service Links';
    RAISE NOTICE '   • 12 Insurance Offers';
    RAISE NOTICE '   • 5 Offer Variants';
    RAISE NOTICE '   • 5 Demo Users';
    RAISE NOTICE '   • 6 Demo Vehicles';
    RAISE NOTICE '   • 4 Quote Requests';
    RAISE NOTICE '   • 8 Quote Results';
    RAISE NOTICE '   • 3 Orders';
    RAISE NOTICE '   • 11 Order Status Logs';
    RAISE NOTICE '   • 3 Invoices';
    RAISE NOTICE '   • 2 Payments';
    RAISE NOTICE '   • 2 Policies';
    RAISE NOTICE '   • 4 User Documents';
    RAISE NOTICE '   • 4 Conversations';
    RAISE NOTICE '   • 4 Conversation Contexts';
    RAISE NOTICE '   • 13 Stage Logs';
    RAISE NOTICE '   • 23 Messages';
    RAISE NOTICE '   • 3 WhatsApp Sessions';
    RAISE NOTICE '   • 10 Activity Logs';
    RAISE NOTICE '   • 6 Audit Logs';
    RAISE NOTICE '';
    RAISE NOTICE '🚀 Ready for Demo!';
END $$;
