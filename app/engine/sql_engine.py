"""
SAIA Insurance Broker - LangChain SQL Engine
Handles dynamic data retrieval from PostgreSQL using LangChain
"""
from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_sql_query_chain
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from operator import itemgetter
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
import logging

from app.config import settings
from app.db.connection import db_manager

logger = logging.getLogger(__name__)

class InsuranceSQLEngine:
    """Engine to perform SQL queries via LangChain"""
    
    def __init__(self):
        self.db = None
        self.llm = None
        self.chain = None
        self._initialize()
        
    def _initialize(self):
        try:
            # 1. Initialize SQLDatabase
            conn_str = db_manager.get_connection_string()
            self.db = SQLDatabase.from_uri(conn_str)
            
            # 2. Initialize LLM
            self.llm = ChatGoogleGenerativeAI(
                model=settings.GEMINI_MODEL,
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0
            )
            
            # 3. Create Chains
            self.execute_query = QuerySQLDataBaseTool(db=self.db)
            self.write_query = create_sql_query_chain(self.llm, self.db)
            
            # Full chain for NL to SQL to Results
            self.chain = (
                RunnablePassthrough.assign(query=self.write_query)
                .assign(result=itemgetter("query") | self.execute_query)
            )
            
            logger.info("✅ Insurance SQL Engine initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize SQL Engine: {e}")

    async def query(self, question: str) -> str:
        """Run a natural language query against the database"""
        if not self.chain:
            return "SQL Engine is not initialized."
            
        try:
            # 1. Generate query
            query_data = self.write_query.invoke({"question": question})
            
            # 2. Clean query (strip markdown if any)
            clean_query = self._clean_sql(query_data)
            
            logger.info(f"Generated SQL: {clean_query}")
            
            # 3. Execute
            result = self.execute_query.run(clean_query)
            return result if result else "لم يتم العثور على نتائج."
        except Exception as e:
            logger.error(f"SQL Query error: {e}")
            return f"Error: {e}"

    def _clean_sql(self, sql: str) -> str:
        """Clean SQL string from LLM (remove markdown backticks)"""
        clean = sql.strip()
        if clean.startswith("```sql"):
            clean = clean[6:]
        elif clean.startswith("```"):
            clean = clean[3:]
        
        if clean.endswith("```"):
            clean = clean[:-3]
        
        return clean.strip()

    def get_services(self) -> str:
        """Get active insurance services directly"""
        try:
            return self.db.run("SELECT name_ar, description FROM insurance_services WHERE is_active = true")
        except Exception as e:
            logger.error(f"Error fetching services: {e}")
            return "[]"

    def get_offers_for_service(self, service_name: str) -> str:
        """Get offers for a specific service"""
        try:
            query = f"""
            SELECT c.name_ar as company, o.coverage_type, o.price_base, o.features_json 
            FROM insurance_offers o
            JOIN insurance_companies c ON o.company_id = c.id
            JOIN insurance_services s ON o.service_id = s.id
            WHERE (s.name_ar LIKE '%{service_name}%' OR s.name_en LIKE '%{service_name}%')
            AND o.is_active = true
            """
            return self.db.run(query)
        except Exception as e:
            logger.error(f"Error fetching offers: {e}")
            return "[]"


# Global SQL Engine instance
insurance_sql_engine = InsuranceSQLEngine()
