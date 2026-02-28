#!/usr/bin/env python3
"""
SAIA Insurance - Offer Selection Test Script
اختبار تدفق اختيار العروض
"""
import requests
import json
import time

BASE_URL = "http://localhost:3300/api/v1"
API_KEY = "saia_api_key_2026_secure"

def send_message(conversation_id: str, message: str) -> dict:
    """إرسال رسالة للـ API"""
    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "message": message,
            "conversation_id": conversation_id
        },
        headers={
            "X-API-Key": API_KEY
        }
    )
    return response.json()

def print_response(step: str, response: dict):
    """طباعة الاستجابة بشكل مرتب"""
    print(f"\n{'='*60}")
    print(f"📌 الخطوة: {step}")
    print(f"{'='*60}")
    print(f"✅ Success: {response.get('success')}")
    print(f"📍 Stage: {response.get('stage')}")
    print(f"💬 Response:\n{response.get('message', '')[:500]}")
    if response.get('data'):
        print(f"📊 Data: {json.dumps(response.get('data'), ensure_ascii=False, indent=2)}")
    print()

def run_test():
    """تشغيل سيناريو الاختبار الكامل"""
    
    conv_id = f"test_offer_{int(time.time())}"
    print(f"\n🚀 بدء الاختبار - Conversation ID: {conv_id}")
    
    # 1. الترحيب + اختيار التأمين الشامل
    print("\n" + "="*60)
    print("📋 الخطوة 1: الترحيب واختيار التأمين الشامل")
    resp = send_message(conv_id, "السلام عليكم، أبي تأمين شامل")
    print_response("ترحيب + اختيار خدمة", resp)
    
    # 2. إدخال بيانات السيارة
    print("\n" + "="*60)
    print("📋 الخطوة 2: إدخال بيانات السيارة")
    resp = send_message(conv_id, "تويوتا كامري 2022 قيمتها 90000 ريال واللوحة أ ب ج 1234")
    print_response("بيانات السيارة", resp)
    
    # 3. تأكيد بيانات السيارة
    print("\n" + "="*60)
    print("📋 الخطوة 3: تأكيد بيانات السيارة")
    resp = send_message(conv_id, "نعم اعتمد")
    print_response("تأكيد السيارة", resp)
    
    # حفظ العروض المعروضة
    offers_message = resp.get('message', '')
    print(f"\n📋 العروض المعروضة:\n{offers_message}")
    
    # =========================================
    # اختبار اختيار العروض بطرق مختلفة
    # =========================================
    
    # 4.1 - اختبار: اختيار بالرقم
    print("\n" + "="*60)
    print("📋 اختبار 1: اختيار بالرقم '3'")
    resp = send_message(conv_id, "3")
    print_response("اختيار بالرقم", resp)
    
    # إعادة - نرجع لعرض العروض
    resp = send_message(conv_id, "لا، بدي أرجع للعروض")
    
    # 4.2 - اختبار: اختيار باسم الشركة
    print("\n" + "="*60)
    print("📋 اختبار 2: اختيار باسم 'ولاء'")
    resp = send_message(conv_id, "ولاء")
    print_response("اختيار باسم الشركة", resp)
    
    # التحقق من السعر في التفاصيل
    details_message = resp.get('message', '')
    print(f"\n🔍 تفاصيل العرض:\n{details_message}")
    
    # استخراج الإجمالي من الرسالة
    if "الإجمالي" in details_message or "إجمالي" in details_message:
        print("✅ تم عرض تفاصيل المبلغ")
    else:
        print("⚠️ لم يتم عرض تفاصيل المبلغ")
    
    print("\n" + "="*60)
    print("🏁 انتهى الاختبار")
    print("="*60)

if __name__ == "__main__":
    run_test()
