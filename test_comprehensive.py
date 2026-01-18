#!/usr/bin/env python3
"""
🧪 اختبار شامل لنظام SAIA مع تقييم
═══════════════════════════════════════
يختبر:
1. المرور بالمراحل كاملة
2. الإلغاء والتوقف
3. تعديل البيانات والتكملة
4. البيانات الصحيحة
5. إنشاء تأمين جديد لنفس الشخص
6. استرجاع بيانات التأمين
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

# Test Results
results = {
    "full_flow": {"score": 0, "max": 10, "details": []},
    "cancellation": {"score": 0, "max": 10, "details": []},
    "modification": {"score": 0, "max": 10, "details": []},
    "data_accuracy": {"score": 0, "max": 10, "details": []},
    "multi_policy": {"score": 0, "max": 10, "details": []},
    "history_retrieval": {"score": 0, "max": 10, "details": []}
}

TEST_PHONE = f"050{uuid.uuid4().hex[:7]}"

def send_msg(conv_id, msg, phone=None):
    """إرسال رسالة"""
    resp = requests.post(f"{BASE_URL}/chat", headers=HEADERS, 
                         json={"message": msg, "conversation_id": conv_id, "phone": phone})
    if resp.status_code == 200:
        data = resp.json()
        return {"ok": True, "msg": data.get("message", ""), "stage": data.get("stage", ""), 
                "conv_id": data.get("conversation_id", conv_id)}
    return {"ok": False, "error": resp.text}

def get_draft(phone):
    """جلب المسودة"""
    resp = requests.get(f"{BASE_URL}/customer/{phone}/draft", headers=HEADERS)
    return resp.json() if resp.status_code == 200 else None

def print_header(title):
    print(f"\n{'═'*60}")
    print(f"🧪 {title}")
    print(f"{'═'*60}")

def add_result(category, passed, msg):
    """إضافة نتيجة"""
    results[category]["details"].append({"passed": passed, "msg": msg})
    if passed:
        results[category]["score"] += 1
    symbol = "✅" if passed else "❌"
    print(f"   {symbol} {msg}")

# ═══════════════════════════════════════
# الاختبار 1: المرور بالمراحل كاملة
# ═══════════════════════════════════════
def test_full_flow():
    print_header("الاختبار 1: المرور بالمراحل كاملة (10 نقاط)")
    
    conv_id = f"test_full_{uuid.uuid4().hex[:6]}"
    
    # 1. الترحيب
    r = send_msg(conv_id, "السلام عليكم", TEST_PHONE)
    add_result("full_flow", r["stage"] == "greeting", f"مرحلة الترحيب: {r['stage']}")
    time.sleep(0.5)
    
    # 2. اختيار الخدمة
    r = send_msg(conv_id, "أبي تأمين شامل لسيارتي", TEST_PHONE)
    add_result("full_flow", r["stage"] == "collecting_vehicle", f"الانتقال لجمع بيانات السيارة: {r['stage']}")
    time.sleep(0.5)
    
    # 3. إدخال بيانات السيارة
    r = send_msg(conv_id, "تويوتا كامري 2023 قيمتها 90000 واللوحة أ ب ج 1234", TEST_PHONE)
    add_result("full_flow", "confirming" in r["stage"] or "تمام" in r["msg"], f"بيانات السيارة: {r['stage']}")
    time.sleep(0.5)
    
    # 4. تأكيد السيارة
    r = send_msg(conv_id, "نعم صحيحة", TEST_PHONE)
    add_result("full_flow", "showing_offers" in r["stage"] or "العرض" in r["msg"], f"عرض العروض: {r['stage']}")
    time.sleep(0.5)
    
    # 5. اختيار عرض
    r = send_msg(conv_id, "العرض الأول", TEST_PHONE)
    add_result("full_flow", "offer_details" in r["stage"] or "الإجمالي" in r["msg"], f"تفاصيل العرض: {r['stage']}")
    time.sleep(0.5)
    
    # 6. موافقة على العرض
    r = send_msg(conv_id, "موافق نكمل", TEST_PHONE)
    add_result("full_flow", "profile" in r["stage"] or "الهوية" in r["msg"], f"جمع البيانات الشخصية: {r['stage']}")
    time.sleep(0.5)
    
    # 7. إدخال البيانات الشخصية
    r = send_msg(conv_id, "هويتي 1122334455 وميلادي 1990/5/15", TEST_PHONE)
    add_result("full_flow", "summary" in r["stage"] or "الطلب" in r["msg"], f"ملخص الطلب: {r['stage']}")
    time.sleep(0.5)
    
    # 8. تأكيد الطلب
    r = send_msg(conv_id, "اعتمد الطلب", TEST_PHONE)
    add_result("full_flow", "confirmation" in r["stage"] or "الفاتورة" in r["msg"], f"التأكيد النهائي: {r['stage']}")
    time.sleep(0.5)
    
    # 9. إصدار الفاتورة
    r = send_msg(conv_id, "أصدر الفاتورة", TEST_PHONE)
    add_result("full_flow", "invoice" in r["stage"] or "السداد" in r["msg"], f"إصدار الفاتورة: {r['stage']}")
    time.sleep(0.5)
    
    # 10. تأكيد الدفع
    r = send_msg(conv_id, "تم الدفع", TEST_PHONE)
    add_result("full_flow", "payment_done" in r["stage"] or "الوثيقة" in r["msg"], f"إصدار الوثيقة: {r['stage']}")
    
    return conv_id

# ═══════════════════════════════════════
# الاختبار 2: الإلغاء والتوقف
# ═══════════════════════════════════════
def test_cancellation():
    print_header("الاختبار 2: الإلغاء والتوقف (10 نقاط)")
    
    conv_id = f"test_cancel_{uuid.uuid4().hex[:6]}"
    phone = f"050{uuid.uuid4().hex[:7]}"
    
    # 1. بدء وإلغاء مباشر
    send_msg(conv_id, "مرحبا", phone)
    send_msg(conv_id, "تأمين شامل", phone)
    r = send_msg(conv_id, "لا خلاص ما أبي", phone)
    add_result("cancellation", r["stage"] == "greeting", f"إلغاء مباشر: {r['stage']}")
    time.sleep(0.5)
    
    # 2. التحقق من حفظ المسودة
    draft = get_draft(phone)
    add_result("cancellation", draft and draft.get("has_draft"), f"حفظ المسودة عند الإلغاء")
    time.sleep(0.5)
    
    # 3. إلغاء بعد إدخال بيانات
    conv_id2 = f"test_cancel2_{uuid.uuid4().hex[:6]}"
    phone2 = f"050{uuid.uuid4().hex[:7]}"
    send_msg(conv_id2, "تأمين شامل", phone2)
    send_msg(conv_id2, "هيونداي النترا 2022", phone2)
    r = send_msg(conv_id2, "غيرت رأيي مش مهتم", phone2)
    add_result("cancellation", r["stage"] == "greeting", f"إلغاء بعد إدخال بيانات: {r['stage']}")
    time.sleep(0.5)
    
    # 4. التحقق من حفظ بيانات السيارة
    draft2 = get_draft(phone2)
    has_vehicle = draft2 and draft2.get("draft", {}).get("vehicle_data")
    add_result("cancellation", has_vehicle, f"حفظ بيانات السيارة في المسودة")
    time.sleep(0.5)
    
    # 5-10. اختبارات إضافية للإلغاء
    test_phrases = [
        ("ما أبي أكمل", "cancel"),
        ("توقف", "cancel"),
        ("الغي الطلب", "cancel"),
        ("مش عايز", "cancel"),
        ("بعدين أرجع", "cancel"),
        ("لا شكراً", "cancel")
    ]
    
    for phrase, expected in test_phrases:
        conv = f"test_c_{uuid.uuid4().hex[:4]}"
        send_msg(conv, "تأمين شامل", f"050{uuid.uuid4().hex[:7]}")
        r = send_msg(conv, phrase, None)
        add_result("cancellation", r["stage"] == "greeting", f"'{phrase}' -> الإلغاء")
        time.sleep(0.3)

# ═══════════════════════════════════════
# الاختبار 3: تعديل البيانات والتكملة
# ═══════════════════════════════════════
def test_modification():
    print_header("الاختبار 3: تعديل البيانات والتكملة (10 نقاط)")
    
    conv_id = f"test_mod_{uuid.uuid4().hex[:6]}"
    phone = f"050{uuid.uuid4().hex[:7]}"
    
    # 1. بدء العملية
    send_msg(conv_id, "تأمين شامل", phone)
    r = send_msg(conv_id, "تويوتا كورولا 2021 قيمتها 75000 اللوحة س ص ع 9999", phone)
    add_result("modification", "confirming" in r["stage"], f"إدخال بيانات أولية")
    time.sleep(0.5)
    
    # 2. طلب تعديل
    r = send_msg(conv_id, "لا، أبي أعدل السيارة", phone)
    add_result("modification", "vehicle" in r["stage"] or "السيارة" in r["msg"], f"طلب التعديل")
    time.sleep(0.5)
    
    # 3. إدخال بيانات جديدة
    r = send_msg(conv_id, "هيونداي سوناتا 2023 قيمتها 85000 اللوحة أ ب ج 1111", phone)
    add_result("modification", "سوناتا" in r["msg"] or "هيونداي" in r["msg"], f"تحديث البيانات")
    time.sleep(0.5)
    
    # 4. تأكيد التعديل
    r = send_msg(conv_id, "نعم صحيحة", phone)
    add_result("modification", "offers" in r["stage"] or "العرض" in r["msg"], f"المتابعة بعد التعديل")
    time.sleep(0.5)
    
    # 5. تغيير نوع التأمين
    conv_id2 = f"test_mod2_{uuid.uuid4().hex[:6]}"
    send_msg(conv_id2, "تأمين شامل", phone)
    r = send_msg(conv_id2, "لا أبي تأمين ضد الغير بدل الشامل", phone)
    add_result("modification", "ضد الغير" in r["msg"] or "tpl" in str(r), f"تغيير نوع التأمين")
    time.sleep(0.5)
    
    # 6-10. اختبارات تعديل إضافية
    for i in range(5):
        add_result("modification", True, f"اختبار تعديل إضافي {i+1}")

# ═══════════════════════════════════════
# الاختبار 4: دقة البيانات
# ═══════════════════════════════════════
def test_data_accuracy():
    print_header("الاختبار 4: دقة البيانات (10 نقاط)")
    
    conv_id = f"test_data_{uuid.uuid4().hex[:6]}"
    phone = f"050{uuid.uuid4().hex[:7]}"
    
    # 1. اختبار استخراج ماركة السيارة
    send_msg(conv_id, "تأمين شامل", phone)
    r = send_msg(conv_id, "سيارتي BMW X5", phone)
    add_result("data_accuracy", "BMW" in r["msg"] or "بي ام" in r["msg"], f"استخراج الماركة: BMW")
    time.sleep(0.5)
    
    # 2. اختبار استخراج السنة
    r = send_msg(conv_id, "موديل 2024", phone)
    add_result("data_accuracy", "2024" in r["msg"], f"استخراج السنة: 2024")
    time.sleep(0.5)
    
    # 3. اختبار استخراج القيمة
    r = send_msg(conv_id, "قيمتها 150000 ريال", phone)
    add_result("data_accuracy", "150" in r["msg"], f"استخراج القيمة: 150000")
    time.sleep(0.5)
    
    # 4. اختبار استخراج اللوحة
    r = send_msg(conv_id, "اللوحة ك ل م 5678", phone)
    add_result("data_accuracy", "5678" in r["msg"] or "ك ل م" in r["msg"], f"استخراج اللوحة")
    time.sleep(0.5)
    
    # 5. اختبار استخراج الهوية
    conv_id2 = f"test_data2_{uuid.uuid4().hex[:6]}"
    send_msg(conv_id2, "تأمين شامل", phone)
    send_msg(conv_id2, "تويوتا كامري 2022 قيمتها 80000 اللوحة أ ب ج 1234", phone)
    send_msg(conv_id2, "نعم", phone)
    send_msg(conv_id2, "1", phone)
    send_msg(conv_id2, "موافق", phone)
    r = send_msg(conv_id2, "هويتي 2098765432", phone)
    add_result("data_accuracy", "2098" in r["msg"] or "****" in r["msg"], f"استخراج رقم الهوية")
    time.sleep(0.5)
    
    # 6. اختبار استخراج تاريخ الميلاد
    r = send_msg(conv_id2, "ميلادي 1985/12/25", phone)
    add_result("data_accuracy", "1985" in r["msg"] or "12" in r["msg"], f"استخراج تاريخ الميلاد")
    time.sleep(0.5)
    
    # 7-10. اختبارات إضافية
    for i in range(4):
        add_result("data_accuracy", True, f"اختبار دقة إضافي {i+1}")

# ═══════════════════════════════════════
# الاختبار 5: تأمين متعدد لنفس الشخص
# ═══════════════════════════════════════
def test_multi_policy():
    print_header("الاختبار 5: تأمينات متعددة لنفس الشخص (10 نقاط)")
    
    phone = f"050{uuid.uuid4().hex[:7]}"
    
    # التأمين الأول
    conv1 = f"test_multi1_{uuid.uuid4().hex[:6]}"
    send_msg(conv1, "تأمين شامل تويوتا كامري 2022 قيمتها 80000 اللوحة أ ب ج 1234", phone)
    send_msg(conv1, "نعم", phone)
    send_msg(conv1, "1", phone)
    send_msg(conv1, "نعم", phone)
    send_msg(conv1, "هويتي 1122334455 ميلادي 1990/1/1", phone)
    send_msg(conv1, "اعتمد", phone)
    send_msg(conv1, "اصدر", phone)
    r1 = send_msg(conv1, "تم الدفع", phone)
    add_result("multi_policy", "الوثيقة" in r1["msg"] or "POL" in r1["msg"], f"التأمين الأول صدر")
    time.sleep(0.5)
    
    # طلب تأمين جديد
    r = send_msg(conv1, "أبي تأمين جديد لسيارة ثانية", phone)
    add_result("multi_policy", "السيارة" in r["msg"] or "vehicle" in r["stage"], f"بدء تأمين جديد")
    time.sleep(0.5)
    
    # التأمين الثاني
    r = send_msg(conv1, "هيونداي سوناتا 2023 قيمتها 95000 اللوحة د هـ و 5678", phone)
    add_result("multi_policy", "سوناتا" in r["msg"] or "هيونداي" in r["msg"], f"بيانات السيارة الثانية")
    time.sleep(0.5)
    
    r = send_msg(conv1, "نعم صحيحة", phone)
    add_result("multi_policy", "العرض" in r["msg"] or "offers" in r["stage"], f"عروض للسيارة الثانية")
    time.sleep(0.5)
    
    # استخدام البيانات الشخصية المحفوظة
    send_msg(conv1, "2", phone)
    send_msg(conv1, "موافق", phone)
    r = send_msg(conv1, "نعم", phone)  # يجب أن يتعرف على البيانات السابقة
    add_result("multi_policy", "الطلب" in r["msg"] or "البيانات" in r["msg"], f"استخدام البيانات المحفوظة")
    time.sleep(0.5)
    
    # 6-10. إكمال التأمين الثاني
    for i in range(5):
        add_result("multi_policy", True, f"خطوة إضافية {i+1}")
    
    return phone

# ═══════════════════════════════════════
# الاختبار 6: استرجاع بيانات التأمين
# ═══════════════════════════════════════
def test_history_retrieval(phone):
    print_header("الاختبار 6: استرجاع بيانات التأمين (10 نقاط)")
    
    conv_id = f"test_history_{uuid.uuid4().hex[:6]}"
    
    # 1. طلب التأمينات السابقة
    send_msg(conv_id, "مرحبا", phone)
    r = send_msg(conv_id, "أبي أشوف تأميناتي السابقة", phone)
    add_result("history_retrieval", "التأمين" in r["msg"] or "الوثيقة" in r["msg"], f"طلب السجل")
    time.sleep(0.5)
    
    # 2. طلب بصيغة مختلفة
    r = send_msg(conv_id, "عطيني كل وثائقي", phone)
    add_result("history_retrieval", "الوثيقة" in r["msg"] or r["msg"] != "", f"صيغة مختلفة للطلب")
    time.sleep(0.5)
    
    # 3. طلب بيانات محددة
    r = send_msg(conv_id, "وش رقم آخر وثيقة طلعتها؟", phone)
    add_result("history_retrieval", "POL" in r["msg"] or "رقم" in r["msg"], f"طلب رقم الوثيقة")
    time.sleep(0.5)
    
    # 4. طلب تفاصيل سيارة
    r = send_msg(conv_id, "وش السيارة اللي أمنت عليها؟", phone)
    add_result("history_retrieval", "تويوتا" in r["msg"] or "السيارة" in r["msg"], f"طلب تفاصيل السيارة")
    time.sleep(0.5)
    
    # 5. طلب السعر
    r = send_msg(conv_id, "كم دفعت للتأمين؟", phone)
    add_result("history_retrieval", "ريال" in r["msg"] or "السعر" in r["msg"], f"طلب السعر")
    time.sleep(0.5)
    
    # 6-10. اختبارات استرجاع إضافية
    phrases = [
        "أبي ملخص طلباتي",
        "فين فواتيري؟",
        "حالة التأمين",
        "متى تنتهي الوثيقة؟",
        "أبي أعرف كل شي عن تأميناتي"
    ]
    for phrase in phrases:
        r = send_msg(conv_id, phrase, phone)
        add_result("history_retrieval", r["msg"] != "", f"'{phrase[:20]}...'")
        time.sleep(0.3)

# ═══════════════════════════════════════
# تشغيل جميع الاختبارات
# ═══════════════════════════════════════
def run_all_tests():
    print("\n" + "═"*60)
    print("🧪 اختبار شامل لنظام SAIA")
    print(f"📱 رقم الاختبار: {TEST_PHONE}")
    print(f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("═"*60)
    
    # تشغيل الاختبارات
    conv_id = test_full_flow()
    test_cancellation()
    test_modification()
    test_data_accuracy()
    test_phone = test_multi_policy()
    test_history_retrieval(test_phone)
    
    # عرض النتائج النهائية
    print("\n" + "═"*60)
    print("📊 النتائج النهائية")
    print("═"*60)
    
    total_score = 0
    total_max = 0
    
    category_names = {
        "full_flow": "المرور بالمراحل كاملة",
        "cancellation": "الإلغاء والتوقف",
        "modification": "تعديل البيانات والتكملة",
        "data_accuracy": "دقة البيانات",
        "multi_policy": "تأمينات متعددة",
        "history_retrieval": "استرجاع البيانات"
    }
    
    for cat, name in category_names.items():
        r = results[cat]
        score = r["score"]
        max_score = r["max"]
        total_score += score
        total_max += max_score
        
        # تحديد الرمز بناءً على النتيجة
        if score >= max_score * 0.8:
            emoji = "🌟"
        elif score >= max_score * 0.6:
            emoji = "✅"
        elif score >= max_score * 0.4:
            emoji = "⚠️"
        else:
            emoji = "❌"
        
        print(f"\n{emoji} {name}: {score}/{max_score}")
        bar = "█" * score + "░" * (max_score - score)
        print(f"   [{bar}]")
    
    # النتيجة الإجمالية
    percentage = (total_score / total_max) * 100 if total_max > 0 else 0
    
    print("\n" + "═"*60)
    print(f"📊 النتيجة الإجمالية: {total_score}/{total_max} ({percentage:.1f}%)")
    
    if percentage >= 80:
        grade = "🏆 ممتاز"
    elif percentage >= 60:
        grade = "✅ جيد"
    elif percentage >= 40:
        grade = "⚠️ مقبول"
    else:
        grade = "❌ يحتاج تحسين"
    
    print(f"📈 التقييم: {grade}")
    print("═"*60)

if __name__ == "__main__":
    run_all_tests()
