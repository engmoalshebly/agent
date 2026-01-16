import asyncio
import uuid
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.engine.professional_engine import professional_engine
from app.core.constants import ConversationStage
from app.engine.session_manager import session_manager

async def run_scenario(name, messages, cid=None):
    if not cid:
        cid = str(uuid.uuid4())
    print(f"\n🚀 Starting Scenario: {name} (ID: {cid})")
    print("-" * 50)
    
    for i, msg in enumerate(messages, 1):
        print(f"\n👤 User {i}: {msg}")
        result = await professional_engine.process_message(cid, msg)
        print(f"🤖 AI Response: \n{result.response_message}")
        print(f"📍 New Stage: {result.next_stage.name}")
        
        # Verify persistence by getting context directly
        context = await session_manager.get_context(cid)
        print(f"📁 Context State: Profile={len(context.profile_data)} fields, Vehicle={len(context.vehicle_data.get('list', []))} saved")
        
        if result.data_collected:
            print(f"📊 Extracted: {result.data_collected}")
            
    print("-" * 50)
    return cid

async def main():
    # 1. Happy Path: New User
    happy_path = [
        "السلام عليكم، أريد تأمين جديد لسيارتي",
        "اسمي محمد، رقم هويتي 1023456789 وتاريخ ميلادي 1990-05-15",
        "نعم المعلومات صحيحة، والجوال 0501234567",
        "لوحة، أ ب ج 1234، تويوتا كامري 2022، قيمتها 90000",
        "لا شكراً، عرض لي العروض",
        "أختار العرض الأول",
        "نعم موافق على السعر، كمل",
        "تم الدفع بنجاح"
    ]
    cid1 = await run_scenario("Happy Path (New User)", happy_path)
    
    # 2. General Inquiry Scenario
    inquiry_path = [
        "مرحباً، ما هي أنواع التأمين المتوفرة لديكم؟",
        "هل لديكم تأمين VIP؟ وما هي مميزاته؟",
        "بكم سعر التأمين الشامل؟"
    ]
    await run_scenario("General Inquiry", inquiry_path)

    # 3. Session Resume Scenario
    # First, start a session and stop
    resume_start = [
        "أريد تأمين سيارة",
        "أنا خالد، هويتي 1098765432 وميلادي 1985-01-01"
    ]
    cid_resume = await run_scenario("Resume Path - Part 1", resume_start)
    
    # Now resume with NEW message
    resume_continue = [
        "أهلاً، أريد أن أكمل طلبي السابق",
        "1" # Escolher continuar
    ]
    await run_scenario("Resume Path - Part 2 (Persistence Test)", resume_continue, cid=cid_resume)

if __name__ == "__main__":
    asyncio.run(main())
