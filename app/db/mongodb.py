"""
MongoDB Connection and Manager
Stores conversation history, data, files, and charts
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional, Dict, Any, List
import logging
import os
from datetime import datetime
from decimal import Decimal
import json
from app.config import settings

logger = logging.getLogger(__name__)


class MongoDBManager:
    """Manages MongoDB connection and operations"""
    
    def __init__(self, connection_string: str, database_name: str = "chat_db"):
        """
        Initialize MongoDB connection
        
        Args:
            connection_string: MongoDB connection URI
            database_name: Database name (default: chat_db)
        """
        self.connection_string = connection_string
        self.database_name = database_name
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self._connected = False
    
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(self.connection_string)
            self.db = self.client[self.database_name]
            
            # Test connection
            await self.client.admin.command('ping')
            self._connected = True
            
            logger.info(
                f"MongoDB connected successfully",
                extra={
                    "database": self.database_name,
                    "collections": await self.db.list_collection_names()
                }
            )
        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}", exc_info=True)
            self._connected = False
            raise
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            self._connected = False
            logger.info("MongoDB disconnected")
    
    def is_connected(self) -> bool:
        """Check if connected to MongoDB"""
        return self._connected
    
    def _convert_decimal_to_float(self, obj):
        """Recursively convert Decimal to float for MongoDB compatibility"""
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return {key: self._convert_decimal_to_float(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_decimal_to_float(item) for item in obj]
        elif isinstance(obj, (int, float, str, bool, type(None))):
            return obj
        else:
            # For other types, try to convert to string as fallback
            try:
                return str(obj)
            except:
                return obj
    
    async def store_conversation(
        self,
        question: str,
        answer: str,
        sql_query: Optional[str] = None,
        data: Optional[List[Dict]] = None,
        query_id: Optional[str] = None,
        excel_file: Optional[str] = None,
        chart: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
        session_id: Optional[str] = None
    ) -> str:
        """
        Store a conversation in MongoDB
        
        Args:
            question: User's question
            answer: System's answer
            sql_query: SQL query executed
            data: Query results (can be large)
            query_id: Cache query ID
            excel_file: Path to Excel export
            chart: Chart information
            metadata: Additional metadata
            session_id: Optional session ID
        
        Returns:
            conversation_id: MongoDB document ID
        """
        if not self.is_connected():
            raise RuntimeError("MongoDB not connected")
        
        # Convert Decimal to float for MongoDB compatibility
        sanitized_data = self._convert_decimal_to_float(data) if data else None
        sanitized_chart = self._convert_decimal_to_float(chart) if chart else None
        sanitized_metadata = self._convert_decimal_to_float(metadata) if metadata else {}
        
        conversation = {
            "question": question,
            "answer": answer,
            "sql_query": sql_query,
            "data": sanitized_data,  # Store full data (Decimal converted to float)
            "query_id": query_id,
            "excel_file": excel_file,
            "chart": sanitized_chart,
            "metadata": sanitized_metadata,
            "session_id": session_id,
            "created_at": datetime.utcnow(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        result = await self.db.conversations.insert_one(conversation)
        conversation_id = str(result.inserted_id)
        
        logger.info(
            f"Conversation stored",
            extra={
                "conversation_id": conversation_id,
                "question": question[:100],
                "has_data": bool(data),
                "data_rows": len(data) if data else 0
            }
        )
        
        return conversation_id
    
    async def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific conversation by ID
        
        Args:
            conversation_id: MongoDB document ID (24-character hex string)
        
        Returns:
            Conversation document or None
        """
        if not self.is_connected():
            raise RuntimeError("MongoDB not connected")
        
        from bson import ObjectId
        from bson.errors import InvalidId
        
        # Validate conversation_id format before attempting conversion
        if not conversation_id or conversation_id.strip() == "":
            logger.warning(f"Empty conversation_id provided")
            return None
        
        invalid_values = ["undefined", "null", "None"]
        if conversation_id.lower() in invalid_values:
            logger.warning(f"Invalid conversation_id value: '{conversation_id}'")
            return None
        
        # Validate ObjectId format (24 hex characters)
        if len(conversation_id) != 24:
            logger.warning(f"Invalid conversation_id length: {len(conversation_id)} (expected 24)")
            return None
        
        if not all(c in '0123456789abcdefABCDEF' for c in conversation_id):
            logger.warning(f"Invalid conversation_id format: contains non-hex characters")
            return None
        
        try:
            conversation = await self.db.conversations.find_one(
                {"_id": ObjectId(conversation_id)}
            )
            
            if conversation:
                conversation["conversation_id"] = str(conversation.pop("_id"))
            
            return conversation
        except (InvalidId, ValueError) as e:
            logger.warning(f"Invalid ObjectId format: '{conversation_id}': {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve conversation: {e}", exc_info=True)
            return None
    
    async def get_history(
        self,
        session_id: Optional[str] = None,
        limit: int = 50,
        skip: int = 0,
        sort_descending: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieve conversation history
        
        Args:
            session_id: Filter by session ID (optional)
            limit: Maximum number of conversations to return
            skip: Number of conversations to skip (pagination)
            sort_descending: Sort by created_at descending (newest first)
        
        Returns:
            List of conversations
        """
        if not self.is_connected():
            raise RuntimeError("MongoDB not connected")
        
        query = {}
        if session_id:
            query["session_id"] = session_id
        
        sort_order = -1 if sort_descending else 1
        
        cursor = self.db.conversations.find(query)\
            .sort("created_at", sort_order)\
            .skip(skip)\
            .limit(limit)
        
        conversations = []
        async for doc in cursor:
            doc["conversation_id"] = str(doc.pop("_id"))
            conversations.append(doc)
        
        return conversations
    
    async def search_conversations(
        self,
        search_text: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search conversations by question or answer text
        
        Args:
            search_text: Text to search for
            limit: Maximum number of results
        
        Returns:
            List of matching conversations
        """
        if not self.is_connected():
            raise RuntimeError("MongoDB not connected")
        
        query = {
            "$or": [
                {"question": {"$regex": search_text, "$options": "i"}},
                {"answer": {"$regex": search_text, "$options": "i"}}
            ]
        }
        
        cursor = self.db.conversations.find(query)\
            .sort("created_at", -1)\
            .limit(limit)
        
        conversations = []
        async for doc in cursor:
            doc["conversation_id"] = str(doc.pop("_id"))
            conversations.append(doc)
        
        return conversations
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation
        
        Args:
            conversation_id: MongoDB document ID
        
        Returns:
            True if deleted, False if not found
        """
        if not self.is_connected():
            raise RuntimeError("MongoDB not connected")
        
        from bson import ObjectId
        
        try:
            result = await self.db.conversations.delete_one(
                {"_id": ObjectId(conversation_id)}
            )
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete conversation: {e}", exc_info=True)
            return False
    
    async def create_session(
        self,
        user_name: Optional[str] = None,
        user_email: Optional[str] = None,
        user_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new session
        
        Args:
            user_name: Optional user name
            user_email: Optional user email
            user_metadata: Optional additional user metadata
        
        Returns:
            session_id: Unique session ID
        """
        if not self.is_connected():
            raise RuntimeError("MongoDB not connected")
        
        import uuid
        session_id = str(uuid.uuid4())
        
        session = {
            "session_id": session_id,
            "user_name": user_name,
            "user_email": user_email,
            "user_metadata": user_metadata or {},
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "conversation_count": 0,
            "is_active": True
        }
        
        await self.db.sessions.insert_one(session)
        
        logger.info(
            f"Session created",
            extra={
                "session_id": session_id,
                "user_name": user_name
            }
        )
        
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session information
        
        Args:
            session_id: Session ID
        
        Returns:
            Session document or None
        """
        if not self.is_connected():
            raise RuntimeError("MongoDB not connected")
        
        session = await self.db.sessions.find_one({"session_id": session_id})
        
        if session:
            session["_id"] = str(session.pop("_id", ""))
        
        return session
    
    async def update_session_activity(self, session_id: str):
        """
        Update session last activity timestamp
        
        Args:
            session_id: Session ID
        """
        if not self.is_connected():
            raise RuntimeError("MongoDB not connected")
        
        # Update last_activity
        await self.db.sessions.update_one(
            {"session_id": session_id},
            {
                "$set": {"last_activity": datetime.utcnow()},
                "$inc": {"conversation_count": 1}
            }
        )
    
    async def get_all_sessions(
        self,
        limit: int = 50,
        skip: int = 0,
        active_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get all sessions
        
        Args:
            limit: Maximum number of sessions
            skip: Number to skip
            active_only: Only return active sessions
        
        Returns:
            List of sessions
        """
        if not self.is_connected():
            raise RuntimeError("MongoDB not connected")
        
        query = {}
        if active_only:
            query["is_active"] = True
        
        cursor = self.db.sessions.find(query)\
            .sort("last_activity", -1)\
            .skip(skip)\
            .limit(limit)
        
        sessions = []
        async for doc in cursor:
            doc["_id"] = str(doc.pop("_id", ""))
            # Get conversation count for this session
            conv_count = await self.db.conversations.count_documents(
                {"session_id": doc["session_id"]}
            )
            doc["conversation_count"] = conv_count
            sessions.append(doc)
        
        return sessions
    
    async def end_session(self, session_id: str) -> bool:
        """
        End (deactivate) a session
        
        Args:
            session_id: Session ID
        
        Returns:
            True if updated, False if not found
        """
        if not self.is_connected():
            raise RuntimeError("MongoDB not connected")
        
        result = await self.db.sessions.update_one(
            {"session_id": session_id},
            {"$set": {"is_active": False, "ended_at": datetime.utcnow()}}
        )
        
        return result.modified_count > 0
    
    # =========================
    # Conversation Threads API
    # =========================
    async def create_conversation_thread(
        self,
        session_id: Optional[str],
        title: Optional[str] = None,
        user_metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a new conversation thread (like ChatGPT conversation)
        Returns a stable conversation_id (UUID4) to be reused across messages.
        """
        if not self.is_connected():
            raise RuntimeError("MongoDB not connected")
        
        import uuid
        conversation_id = str(uuid.uuid4())
        
        thread_doc = {
            "conversation_id": conversation_id,
            "session_id": session_id,
            "title": title or "New Conversation",
            "user_metadata": user_metadata or {},
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "message_count": 0,
            "is_active": True,
        }
        
        await self.db.conversation_threads.insert_one(thread_doc)
        logger.info("Conversation thread created", extra={"conversation_id": conversation_id, "session_id": session_id})
        return conversation_id
    
    async def append_message_to_conversation(
        self,
        conversation_id: str,
        question: str,
        answer: str,
        *,
        sql_query: Optional[str] = None,
        data: Optional[List[Dict]] = None,
        query_id: Optional[str] = None,
        excel_file: Optional[str] = None,
        chart: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
        session_id: Optional[str] = None,
    ) -> bool:
        """
        Append a message turn (question+answer+artifacts) to a conversation thread.
        Stores message in 'conversation_messages' and updates the parent thread counters.
        """
        if not self.is_connected():
            raise RuntimeError("MongoDB not connected")
        
        # Sanitize payload for Mongo
        sanitized_data = self._convert_decimal_to_float(data) if data else None
        sanitized_chart = self._convert_decimal_to_float(chart) if chart else None
        sanitized_metadata = self._convert_decimal_to_float(metadata) if metadata else {}
        
        message_doc = {
            "conversation_id": conversation_id,
            "session_id": session_id,
            "question": question,
            "answer": answer,
            "sql_query": sql_query,
            "data": sanitized_data,
            "query_id": query_id,
            "excel_file": excel_file,
            "chart": sanitized_chart,
            "metadata": sanitized_metadata,
            "created_at": datetime.utcnow(),
        }
        
        await self.db.conversation_messages.insert_one(message_doc)
        await self.db.conversation_threads.update_one(
            {"conversation_id": conversation_id},
            {
                "$set": {"last_activity": datetime.utcnow()},
                "$inc": {"message_count": 1},
            }
        )
        logger.info("Message appended to conversation", extra={"conversation_id": conversation_id})
        return True
    
    async def get_conversation_threads(
        self,
        session_id: Optional[str] = None,
        limit: int = 50,
        skip: int = 0,
    ) -> List[Dict[str, Any]]:
        """List conversation threads with pagination."""
        if not self.is_connected():
            raise RuntimeError("MongoDB not connected")
        
        query = {}
        if session_id:
            query["session_id"] = session_id
        
        cursor = self.db.conversation_threads.find(query)\
            .sort("last_activity", -1)\
            .skip(skip)\
            .limit(limit)
        
        threads: List[Dict[str, Any]] = []
        async for doc in cursor:
            doc["_id"] = str(doc.pop("_id", ""))
            threads.append(doc)
        return threads
    
    async def get_conversation_messages(
        self,
        conversation_id: str,
        limit: int = 50,
        skip: int = 0,
    ) -> List[Dict[str, Any]]:
        """List messages for a given conversation thread."""
        if not self.is_connected():
            raise RuntimeError("MongoDB not connected")
        
        cursor = self.db.conversation_messages.find({"conversation_id": conversation_id})\
            .sort("created_at", 1)\
            .skip(skip)\
            .limit(limit)
        
        messages: List[Dict[str, Any]] = []
        async for doc in cursor:
            doc["_id"] = str(doc.pop("_id", ""))
            messages.append(doc)
        return messages


# Global MongoDB manager instance
mongodb_manager = MongoDBManager(
    connection_string=settings.MONGO_URI,
    database_name=settings.MONGO_DB_NAME
)


async def get_conversations_collection():
    """Helper function to get conversations collection"""
    if not mongodb_manager.is_connected():
        await mongodb_manager.connect()
    return mongodb_manager.db.conversation_contexts


async def get_users_collection():
    """Helper function to get users collection"""
    if not mongodb_manager.is_connected():
        await mongodb_manager.connect()
    return mongodb_manager.db.users


async def find_user_by_national_id(national_id: str) -> Optional[Dict[str, Any]]:
    """البحث عن مستخدم برقم الهوية"""
    try:
        collection = await get_users_collection()
        user = await collection.find_one({"national_id": national_id})
        if user:
            user["_id"] = str(user["_id"])
        return user
    except Exception as e:
        logger.error(f"Error finding user by national_id: {e}")
        return None


async def find_user_by_phone(phone: str) -> Optional[Dict[str, Any]]:
    """البحث عن مستخدم برقم الجوال"""
    try:
        collection = await get_users_collection()
        user = await collection.find_one({"phone": phone})
        if user:
            user["_id"] = str(user["_id"])
        return user
    except Exception as e:
        logger.error(f"Error finding user by phone: {e}")
        return None


async def create_or_update_user(user_data: Dict[str, Any]) -> str:
    """إنشاء أو تحديث مستخدم"""
    try:
        collection = await get_users_collection()
        
        # البحث بالهوية أو الجوال
        national_id = user_data.get("national_id")
        phone = user_data.get("phone")
        
        existing_user = None
        if national_id:
            existing_user = await collection.find_one({"national_id": national_id})
        if not existing_user and phone:
            existing_user = await collection.find_one({"phone": phone})
        
        if existing_user:
            # تحديث المستخدم الموجود
            user_data["updated_at"] = datetime.now()
            await collection.update_one(
                {"_id": existing_user["_id"]},
                {"$set": user_data}
            )
            logger.info(f"✅ Updated user: {existing_user.get('user_id')}")
            return str(existing_user["_id"])
        else:
            # إنشاء مستخدم جديد
            user_id = f"user_{national_id or phone or datetime.now().strftime('%Y%m%d%H%M%S')}"
            user_data["user_id"] = user_id
            user_data["created_at"] = datetime.now()
            user_data["updated_at"] = datetime.now()
            user_data["policies"] = user_data.get("policies", [])
            user_data["conversation_ids"] = user_data.get("conversation_ids", [])
            
            result = await collection.insert_one(user_data)
            logger.info(f"✅ Created new user: {user_id}")
            return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Error creating/updating user: {e}")
        return ""


async def add_policy_to_user(national_id: str, policy: Dict[str, Any]) -> bool:
    """إضافة وثيقة تأمين للمستخدم"""
    try:
        collection = await get_users_collection()
        result = await collection.update_one(
            {"national_id": national_id},
            {
                "$push": {"policies": policy},
                "$set": {"updated_at": datetime.now()}
            }
        )
        if result.modified_count > 0:
            logger.info(f"✅ Added policy {policy.get('policy_id')} to user {national_id}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error adding policy to user: {e}")
        return False


async def link_conversation_to_user(national_id: str, conversation_id: str) -> bool:
    """ربط محادثة بالمستخدم"""
    try:
        collection = await get_users_collection()
        result = await collection.update_one(
            {"national_id": national_id},
            {
                "$addToSet": {"conversation_ids": conversation_id},
                "$set": {"updated_at": datetime.now()}
            }
        )
        if result.modified_count > 0:
            logger.info(f"✅ Linked conversation {conversation_id} to user {national_id}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error linking conversation to user: {e}")
        return False


async def get_user_policies(national_id: str) -> List[Dict[str, Any]]:
    """جلب وثائق التأمين للمستخدم"""
    try:
        user = await find_user_by_national_id(national_id)
        if user:
            return user.get("policies", [])
        return []
    except Exception as e:
        logger.error(f"Error getting user policies: {e}")
        return []

