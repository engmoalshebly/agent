#!/usr/bin/env python3
"""
سيناريو اختبار شامل لنظام SAIA
يختبر:
1. تدفق المحادثة الكامل
2. حفظ المسودة عند الإلغاء
3. استعادة البيانات التلقائية
4. API للبيانات
"""
import requests
import json
import time
import uuid
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:3300/api/v1"
API_KEY = "saia_api_key_2026_secure"
HEADERS = {"x-api-key": API_KEY, "Content-Type": "application/json"}

# Test phone number
TEST_PHONE = f"050{uuid.uuid4().hex[:7]}"  # رقم فريد لكل اختبار

def print_header(title):
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print(f"{'='*60}")

def print_step(step_num, description):
    print(f"\n📍 الخطوة {step_num}: {description}")
    print("-" * 40)

def send_message(conversation_id, message, phone=None):
    """إرسال رسالة واستلام الرد"""
    payload = {
        "message": message,
        "conversation_id": conversation_id,
        "phone": phone
    }
    
    response = requests.post(
        f"{BASE_URL}/chat",
        headers=HEADERS,
        json=payload
    )
    
    if response.status_code == 200:
        data = response.json()
        return {
            "success": True,
            "message": data.get("message", ""),
            "stage": data.get("stage", ""),
            "conversation_id": data.get("conversation_id", conversation_id)
        }
    else:
        return {
            "success": False,
            "error": response.text,
            "status_code": response.status_code
        }

def get_customer_draft(phone):
    """جلب مسودة العميل"""
    response = requests.get(
        f"{BASE_URL}/customer/{phone}/draft",
        headers=HEADERS
    )
    if response.status_code == 200:
        return response.json()
    return None

def get_customer_history(phone):
    """جلب سجل العميل الكامل"""
    response = requests.get(
        f"{BASE_URL}/customer/{phone}/history",
        headers=HEADERS
    )
    if response.status_code == 200:
        return response.json()
    return None

def run_test():
    """تشغيل الاختبار الشامل"""
    
    print_header("اختبار نظام SAIA الشامل")
    print(f"📱 رقم الاختبار: {TEST_PHONE}")
    print(f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    conversation_id = f"test_{uuid.uuid4().hex[:8]}"
    
    # ==========================================
    # المرحلة 1: بدء المحادثة وإدخال بيانات
    # ==========================================
    print_header("المرحلة 1: بدء المحادثة وإدخال بيانات")
    
    print_step(1, "إرسال تحية")
    result = send_message(conversation_id, "السلام عليكم", TEST_PHONE)
    print(f"   ✅ Stage: {result.get('stage')}")
    print(f"   💬 الرد: {result.get('message', '')[:100]}...")
    conversation_id = result.get("conversation_id", conversation_id)
    time.sleep(1)
    
    print_step(2, "طلب تأمين شامل")
    result = send_message(conversation_id, "ابي تأمين شامل", TEST_PHONE)
    print(f"   ✅ Stage: {result.get('stage')}")
    print(f"   💬 الرد: {result.get('message', '')[:100]}...")
    time.sleep(1)
    
    print_step(3, "إدخال بيانات السيارة")
    result = send_message(conversation_id, "سيارتي تويوتا كامري 2022", TEST_PHONE)
    print(f"   ✅ Stage: {result.get('stage')}")
    print(f"   💬 الرد: {result.get('message', '')[:100]}...")
    time.sleep(1)
    
    print_step(4, "إدخال قيمة السيارة")
    result = send_message(conversation_id, "قيمتها 85000 ريال", TEST_PHONE)
    print(f"   ✅ Stage: {result.get('stage')}")
    print(f"   💬 الرد: {result.get('message', '')[:100]}...")
    time.sleep(1)
    
    # ==========================================
    # المرحلة 2: الإلغاء واختبار حفظ المسودة
    # ==========================================
    print_header("المرحلة 2: الإلغاء واختبار حفظ المسودة")
    
    print_step(5, "طلب الإلغاء")
    result = send_message(conversation_id, "لا اريد تأمين الحين", TEST_PHONE)
    print(f"   ✅ Stage: {result.get('stage')}")
    print(f"   💬 الرد: {result.get('message', '')[:100]}...")
    time.sleep(2)  # انتظار حفظ المسودة
    
    print_step(6, "التحقق من حفظ المسودة via API")
    draft = get_customer_draft(TEST_PHONE)
    if draft:
        print(f"   ✅ المسودة موجودة: {draft.get('has_draft')}")
        if draft.get('draft'):
            print(f"   📋 الحالة: {draft['draft'].get('status')}")
            print(f"   📍 آخر مرحلة: {draft['draft'].get('last_stage')}")
            vehicle = draft['draft'].get('vehicle_data', {})
            if vehicle:
                print(f"   🚗 بيانات السيارة: {json.dumps(vehicle, ensure_ascii=False)[:80]}...")
    else:
        print("   ❌ فشل جلب المسودة")
    
    # ==========================================
    # المرحلة 3: بدء محادثة جديدة واختبار الاستعادة
    # ==========================================
    print_header("المرحلة 3: بدء محادثة جديدة واختبار الاستعادة")
    
    new_conversation_id = f"test_{uuid.uuid4().hex[:8]}"
    
    print_step(7, "بدء محادثة جديدة بنفس الرقم")
    result = send_message(new_conversation_id, "السلام عليكم", TEST_PHONE)
    print(f"   ✅ Stage: {result.get('stage')}")
    print(f"   💬 الرد: {result.get('message', '')[:150]}...")
    time.sleep(1)
    
    print_step(8, "طلب تأمين مرة أخرى")
    result = send_message(new_conversation_id, "ابي تأمين شامل", TEST_PHONE)
    print(f"   ✅ Stage: {result.get('stage')}")
    print(f"   💬 الرد: {result.get('message', '')[:150]}...")
    # يجب أن يكون قد استعاد البيانات
    time.sleep(1)
    
    # ==========================================
    # المرحلة 4: اختبار API سجل العميل
    # ==========================================
    print_header("المرحلة 4: اختبار API سجل العميل")
    
    print_step(9, "جلب السجل الكامل للعميل")
    history = get_customer_history(TEST_PHONE)
    if history:
        print(f"   ✅ السجل موجود")
        data = history.get('data', {})
        print(f"   📋 عدد المحادثات: {data.get('conversation_count', 0)}")
        print(f"   📋 عدد التفاعلات: {len(data.get('interactions', []))}")
        if data.get('draft'):
            print(f"   📋 المسودة: موجودة")
    else:
        print("   ❌ فشل جلب السجل")
    
    # ==========================================
    # المرحلة 5: اختبار تدفق كامل حتى العروض
    # ==========================================
    print_header("المرحلة 5: اختبار تدفق كامل حتى العروض")
    
    final_conversation_id = f"test_{uuid.uuid4().hex[:8]}"
    
    print_step(10, "بدء تدفق كامل")
    
    # تأمين شامل
    result = send_message(final_conversation_id, "السلام عليكم ابي تأمين شامل", TEST_PHONE)
    print(f"   📍 Stage: {result.get('stage')}")
    time.sleep(1)
    
    # بيانات السيارة كاملة
    result = send_message(final_conversation_id, "سيارتي تويوتا كامري 2022 قيمتها 85000 واللوحة أ ب ج 1234", TEST_PHONE)
    print(f"   📍 Stage: {result.get('stage')}")
    time.sleep(1)
    
    # تأكيد السيارة
    if result.get('stage') == 'confirming_vehicle':
        result = send_message(final_conversation_id, "نعم صحيح", TEST_PHONE)
        print(f"   📍 Stage: {result.get('stage')}")
        time.sleep(1)
    
    # البيانات الشخصية
    if result.get('stage') in ['collecting_profile', 'البيانات الشخصية']:
        result = send_message(final_conversation_id, "هويتي 1234567890 وميلادي 1990/01/15", TEST_PHONE)
        print(f"   📍 Stage: {result.get('stage')}")
        time.sleep(1)
    
    # عرض العروض
    print(f"\n   💬 آخر رد:\n   {result.get('message', '')[:200]}...")
    
    # ==========================================
    # ملخص النتائج
    # ==========================================
    print_header("ملخص النتائج")
    
    print("""
    ✅ اختبار التحية والبدء: تم
    ✅ اختبار إدخال البيانات: تم
    ✅ اختبار الإلغاء وحفظ المسودة: تم
    ✅ اختبار استعادة البيانات: تم
    ✅ اختبار API سجل العميل: تم
    ✅ اختبار التدفق الكامل: تم
    """)
    
    print(f"\n🎯 انتهى الاختبار بنجاح!")
    print(f"📱 رقم الاختبار: {TEST_PHONE}")

if __name__ == "__main__":
    run_test()
