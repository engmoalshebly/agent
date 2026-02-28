#!/usr/bin/env python3
"""اختبار توليد الفاتورة والوثيقة"""
import requests
import time
import uuid

BASE_URL = "http://localhost:3300/api/v1"
HEADERS = {"x-api-key": "saia_api_key_2026_secure", "Content-Type": "application/json"}

def send_msg(conv_id, msg, phone):
    resp = requests.post(f"{BASE_URL}/chat", headers=HEADERS, 
                         json={"message": msg, "conversation_id": conv_id, "phone": phone})
    return resp.json() if resp.status_code == 200 else {"error": resp.text}

def test_document_generation():
    print("🧪 اختبار توليد الفاتورة والوثيقة")
    print("=" * 50)
    
    conv_id = f"test_docs_{uuid.uuid4().hex[:6]}"
    phone = f"050{uuid.uuid4().hex[:7]}"
    
    # المرور السريع بالمراحل
    print("📍 بدء المحادثة...")
    send_msg(conv_id, "تأمين شامل تويوتا كامري 2022 قيمتها 80000 اللوحة أ ب ج 1234", phone)
    time.sleep(0.5)
    
    send_msg(conv_id, "نعم صحيحة", phone)
    time.sleep(0.5)
    
    send_msg(conv_id, "1", phone)
    time.sleep(0.5)
    
    send_msg(conv_id, "موافق", phone)
    time.sleep(0.5)
    
    send_msg(conv_id, "هويتي 1122334455 ميلادي 1990/1/1", phone)
    time.sleep(0.5)
    
    send_msg(conv_id, "اعتمد", phone)
    time.sleep(0.5)
    
    send_msg(conv_id, "اصدر", phone)
    time.sleep(0.5)
    
    # تأكيد الدفع - هنا يجب توليد الملفات
    print("📍 تأكيد الدفع...")
    result = send_msg(conv_id, "تم الدفع", phone)
    
    print(f"\n📄 الرد: {result.get('message', '')[:200]}...")
    print(f"📎 المرفقات: {result.get('attachments', 'لا توجد')}")
    
    # التحقق من المرفقات
    attachments = result.get("attachments", [])
    if attachments:
        print("\n✅ تم توليد المستندات بنجاح!")
        for att in attachments:
            print(f"   📄 {att.get('name')}: {att.get('url')}")
            
            # محاولة جلب الملف
            url = f"http://localhost:3300{att.get('url')}"
            resp = requests.get(url)
            if resp.status_code == 200:
                print(f"      ✅ الملف متاح ({len(resp.text)} bytes)")
            else:
                print(f"      ❌ الملف غير متاح: {resp.status_code}")
    else:
        print("\n❌ لا توجد مرفقات في الرد!")
    
    return attachments

if __name__ == "__main__":
    test_document_generation()
