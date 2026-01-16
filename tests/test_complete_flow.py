"""
SAIA Insurance Broker Platform - Complete Flow Test
Tests the entire conversation flow from greeting to policy issuance
"""
import asyncio
import sys
sys.path.insert(0, '/home/moadmin/server_data/new_version')

from app.engine.stage_manager import stage_manager


async def test_complete_flow():
    """Test the complete insurance flow"""
    
    conversation_id = "test_conv_001"
    
    print("\n" + "="*60)
    print("🧪 SAIA Insurance Broker - Complete Flow Test")
    print("="*60)
    
    # Test messages simulating a complete flow
    test_messages = [
        ("السلام عليكم", "Initial greeting"),
        ("1", "Choose new insurance"),
        ("1122334455", "Enter national ID"),
        ("1990/03/25", "Enter birth date"),
        ("0501234567", "Enter phone"),
        ("نعم", "Confirm profile"),
        ("1", "Choose plate registration"),
        ("س ك ر 5678", "Enter plate number"),
        ("هيونداي سوناتا 2021", "Enter vehicle info"),
        ("85000", "Enter vehicle value"),
        ("2", "No more vehicles"),
        ("1", "Select first offer"),
        ("1", "Confirm and create invoice"),
        ("تم الدفع", "Confirm payment"),
    ]
    
    for message, description in test_messages:
        print(f"\n{'─'*50}")
        print(f"📱 العميل: {message}")
        print(f"   ({description})")
        print(f"{'─'*50}")
        
        result = await stage_manager.process_message(
            conversation_id=conversation_id,
            message=message,
            phone="0501234567"
        )
        
        print(f"\n🤖 الوكيل:")
        for line in result.response_message.split('\n'):
            print(f"   {line}")
        
        print(f"\n📊 Stage: {result.next_stage.value if result.next_stage else 'N/A'}")
        print(f"✅ Success: {result.success}")
        
        if result.error:
            print(f"❌ Error: {result.error}")
        
        # Small delay for readability
        await asyncio.sleep(0.1)
    
    print("\n" + "="*60)
    print("🎉 Test Complete!")
    print("="*60)


async def test_session_resume():
    """Test session resume functionality"""
    
    print("\n" + "="*60)
    print("🧪 Testing Session Resume")
    print("="*60)
    
    conversation_id = "test_resume_001"
    
    # Start conversation
    result = await stage_manager.process_message(conversation_id, "السلام عليكم")
    print(f"Initial: {result.next_stage}")
    
    # Choose new insurance
    result = await stage_manager.process_message(conversation_id, "1")
    print(f"After choice: {result.next_stage}")
    
    # Enter national ID
    result = await stage_manager.process_message(conversation_id, "1234567890")
    print(f"After ID: {result.next_stage}")
    
    # Simulate session check (would normally be triggered by time)
    from app.engine.session_manager import session_manager
    check = await session_manager.check_session(conversation_id)
    print(f"Session status: {check.status}")
    
    print("\n✅ Session Resume Test Complete")


async def test_rule_parser():
    """Test rule-based parser"""
    
    print("\n" + "="*60)
    print("🧪 Testing Rule-Based Parser")
    print("="*60)
    
    from app.engine.rule_parser import RuleBasedParser
    from app.core.constants import InputType
    
    test_cases = [
        ("1", InputType.CHOICE_NUMBER, "Choice number"),
        ("نعم", InputType.AFFIRMATIVE, "Affirmative Arabic"),
        ("yes", InputType.AFFIRMATIVE, "Affirmative English"),
        ("لا", InputType.NEGATIVE, "Negative Arabic"),
        ("1122334455", InputType.NATIONAL_ID, "National ID"),
        ("0501234567", InputType.PHONE, "Phone number"),
        ("تم الدفع", InputType.PAYMENT_CONFIRM, "Payment confirm"),
    ]
    
    for message, expected_type, description in test_cases:
        result = RuleBasedParser.parse(message, expected_type)
        status = "✅" if result.matched else "❌"
        print(f"{status} {description}: '{message}' -> matched={result.matched}, value={result.value}")
    
    print("\n✅ Rule Parser Test Complete")


async def test_data_masking():
    """Test data masking"""
    
    print("\n" + "="*60)
    print("🧪 Testing Data Masking")
    print("="*60)
    
    from app.core.security import DataMasker
    
    test_cases = [
        ("National ID", DataMasker.mask_national_id, "1122334455", "112*****55"),
        ("Phone", DataMasker.mask_phone, "0501234567", "050****567"),
        ("Plate", DataMasker.mask_plate, "س ك ر 5678", "س ك ر ****"),
    ]
    
    for name, func, input_val, expected in test_cases:
        result = func(input_val)
        status = "✅" if result == expected else "❌"
        print(f"{status} {name}: '{input_val}' -> '{result}' (expected: '{expected}')")
    
    print("\n✅ Data Masking Test Complete")


async def test_idempotency():
    """Test idempotency manager"""
    
    print("\n" + "="*60)
    print("🧪 Testing Idempotency Manager")
    print("="*60)
    
    from app.core.idempotency import IdempotencyManager
    
    manager = IdempotencyManager()
    
    # First call - should succeed
    result1 = await manager.check_and_lock("order_123", "invoice", "create")
    print(f"First call: is_duplicate={result1.is_duplicate}")
    
    # Second call - should be duplicate
    result2 = await manager.check_and_lock("order_123", "invoice", "create")
    print(f"Second call: is_duplicate={result2.is_duplicate}, is_processing={result2.is_processing}")
    
    # Mark complete
    await manager.mark_completed("order_123", "invoice", "create", {"id": "INV-001"})
    
    # Third call - should return cached result
    result3 = await manager.check_and_lock("order_123", "invoice", "create")
    print(f"Third call: is_duplicate={result3.is_duplicate}, original_result={result3.original_result}")
    
    print("\n✅ Idempotency Test Complete")


async def main():
    """Run all tests"""
    
    print("\n" + "🚀"*30)
    print("  SAIA Insurance Broker Platform - Test Suite")
    print("🚀"*30)
    
    await test_rule_parser()
    await test_data_masking()
    await test_idempotency()
    await test_session_resume()
    await test_complete_flow()
    
    print("\n" + "="*60)
    print("🎉 All Tests Complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
