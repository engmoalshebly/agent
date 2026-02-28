# SAIA Insurance Broker API Documentation
## دليل استخدام الـ API

---

## 🔗 Base URL
```
https://concord-saia.bineyes.com/agent/api/v1
```

---

## 🔐 المصادقة (Authentication)

### الخيار 1: API Key
```
X-API-Key: your-api-key
```

### الخيار 2: JWT Token
```
Authorization: Bearer your-jwt-token
```

---

## 📨 إرسال رسالة Chat

### Endpoint
```
POST /chat
```

### Request Headers
```json
{
  "Content-Type": "application/json",
  "X-API-Key": "your-api-key"
}
```

### Request Body
```json
{
  "message": "السلام عليكم",
  "conversation_id": "optional-existing-conversation-id",
  "phone": "966501234567"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | ✅ | رسالة المستخدم |
| `conversation_id` | string | ❌ | معرف المحادثة (يُنشأ تلقائياً إذا لم يُحدد) |
| `phone` | string | ❌ | رقم الجوال للتتبع |

### Response
```json
{
  "success": true,
  "message": "وعليكم السلام! 👋 أنا SAIA المساعد الذكي...",
  "conversation_id": "conv_abc123",
  "stage": "greeting",
  "has_attachments": false,
  "attachments": null,
  "data": null,
  "error": null
}
```

### Response مع مرفقات (عند إتمام الطلب)
```json
{
  "success": true,
  "message": "تم إصدار الفاتورة والوثيقة بنجاح! 🎉",
  "conversation_id": "conv_abc123",
  "stage": "payment_done",
  "has_attachments": true,
  "attachments": [
    {
      "type": "invoice",
      "name": "🧾 فاتورة السداد",
      "url": "https://concord-saia.bineyes.com/agent/api/v1/documents/invoice_INV-123456.pdf"
    },
    {
      "type": "policy",
      "name": "📄 وثيقة التأمين",
      "url": "https://concord-saia.bineyes.com/agent/api/v1/documents/policy_POL-2026-789.pdf"
    }
  ],
  "data": {
    "policy_number": "POL-2026-789",
    "total_amount": 3500
  },
  "error": null
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | نجاح/فشل الطلب |
| `message` | string | رد المساعد الذكي |
| `conversation_id` | string | معرف المحادثة الفريد |
| `stage` | string | المرحلة الحالية |
| `has_attachments` | boolean | **هل توجد مرفقات؟** |
| `attachments` | array/null | قائمة المرفقات |
| `data` | object/null | بيانات إضافية |
| `error` | string/null | رسالة الخطأ إن وجد |

---

## 📄 تحميل المستندات

### Endpoint
```
GET /documents/{filename}
```

### مثال
```
GET https://concord-saia.bineyes.com/agent/api/v1/documents/invoice_INV-123456.pdf
```

### Response
- **PDF**: `Content-Type: application/pdf`
- **HTML (legacy)**: `Content-Type: text/html`

---

## 💬 جلب المحادثات

### Endpoint
```
GET /conversations
```

### Response
```json
{
  "success": true,
  "conversations": [
    {
      "id": "conv_abc123",
      "title": "طلب تأمين شامل",
      "created_at": "2026-01-18T10:30:00Z",
      "last_message": "2026-01-18T10:45:00Z",
      "stage": "payment_done"
    }
  ]
}
```

---

## 🔄 المراحل (Stages)

| Stage | الوصف |
|-------|-------|
| `greeting` | الترحيب |
| `selecting_service` | اختيار نوع التأمين |
| `collecting_vehicle` | جمع بيانات السيارة |
| `confirming_vehicle` | تأكيد بيانات السيارة |
| `showing_offers` | عرض العروض |
| `offer_details` | تفاصيل العرض |
| `collecting_profile` | جمع البيانات الشخصية |
| `order_summary` | ملخص الطلب |
| `invoice_issued` | إصدار الفاتورة |
| `payment_done` | تم الدفع |

---

## 📱 مثال كامل (cURL)

```bash
# إرسال رسالة
curl -X POST "https://concord-saia.bineyes.com/agent/api/v1/chat" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "message": "أريد تأمين شامل لسيارتي",
    "phone": "966501234567"
  }'
```

---

## 📱 مثال JavaScript

```javascript
async function sendMessage(message, conversationId = null) {
  const response = await fetch('https://concord-saia.bineyes.com/agent/api/v1/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': 'your-api-key'
    },
    body: JSON.stringify({
      message: message,
      conversation_id: conversationId
    })
  });
  
  const data = await response.json();
  
  // التحقق من وجود مرفقات
  if (data.has_attachments) {
    data.attachments.forEach(attachment => {
      console.log(`${attachment.name}: ${attachment.url}`);
    });
  }
  
  return data;
}
```

---

## ❌ أخطاء شائعة

| Code | Description |
|------|-------------|
| `401` | API Key غير صالح |
| `403` | غير مصرح |
| `404` | المستند غير موجود |
| `422` | بيانات الطلب غير صالحة |
| `500` | خطأ في السيرفر |

---

## 📞 الدعم
للدعم الفني: support@bineyes.com
