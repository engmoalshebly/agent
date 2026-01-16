import asyncio
import os
import sys

# Add current dir to path
sys.path.append(os.getcwd())

async def test_sql_engine():
    try:
        from app.engine.sql_engine import insurance_sql_engine
        from app.db.connection import db_manager
        
        print(f"Connection String: {db_manager.get_connection_string()}")
        print("Testing SQL Engine...")
        
        # Test services
        services = insurance_sql_engine.get_services()
        print(f"Services: {services}")
        
        # Test general query
        res = await insurance_sql_engine.query("كم عدد شركات التأمين؟")
        print(f"Query Result (Count companies): {res}")
        
        # Test offers
        offers = insurance_sql_engine.get_offers_for_service("سيارات")
        print(f"Offers: {offers}")
        
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_sql_engine())
