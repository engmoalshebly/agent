# 💬 Chat with Database - PostgreSQL Chat API

<div dir="rtl">

# 💬 دردشة مع قاعدة البيانات - PostgreSQL Chat API

نظام ذكي للرد على استفسارات العملاء من خلال تقديم تحليلات واضحة ومباشرة من قاعدة البيانات. النظام مصمم خصيصاً للمستخدمين النهائيين غير التقنيين - يسألون أسئلة بسيطة ويحصلون على بيانات واضحة دون الحاجة لرؤية أي استعلامات SQL أو تفاصيل تقنية.

**🎯 الهدف:** إجابة استفسارات العملاء بتحليلات واضحة من قاعدة البيانات - بدون عرض استعلامات SQL للمستخدم النهائي.

</div>

**🎯 Purpose:** Respond to customer inquiries with clear data analyses from the database - without showing SQL queries to end users.

**👥 Target Users:** Non-technical end users who want clear data insights, not SQL queries or technical details.

---

## 🚀 Quick Explanation / شرح سريع

<div dir="rtl">

### 💡 ما هو النظام؟

نظام ذكي يجيب على أسئلة العملاء باللغة الطبيعية ويعطيهم بيانات وتحليلات واضحة من قاعدة البيانات **بدون أن يروا أي تفاصيل تقنية**.

### 🎯 الفكرة الأساسية في 30 ثانية:

1. **العميل يسأل**: "كم عدد العملاء لدينا هذا الشهر؟"
2. **النظام يفهم** السؤال باستخدام الذكاء الاصطناعي
3. **يستخرج البيانات** من قاعدة البيانات (خلف الكواليس)
4. **يعطي إجابة واضحة**: "لديك 1,234 عميل نشط هذا الشهر"

**العميل لا يرى**: استعلامات SQL، أسماء الجداول، أو أي تفاصيل تقنية

### ⚡ كيف يعمل؟ (في سطرين)

**للعميل (المستخدم النهائي):**
- يسأل سؤالاً عادي → يحصل على إجابة واضحة مع البيانات

**للنظام (خلف الكواليس):**
- يفهم السؤال → يولد SQL تلقائياً → يستخرج البيانات → يحللها → ينسق الإجابة بلغة الأعمال

### 🎁 ما المميز؟

✅ **لا يحتاج خبرة تقنية** - أي شخص يستطيع السؤال  
✅ **إجابات واضحة** - بلغة الأعمال وليس المصطلحات التقنية  
✅ **آمن تماماً** - التفاصيل التقنية مخفية بالكامل  
✅ **دعم عربي/إنجليزي** - اسأل بأي لغة  

### 📊 مثال عملي:

**سؤال:** "ما هي أفضل المنتجات مبيعاً هذا الشهر؟"  
**إجابة:** "أفضل 5 منتجات مبيعاً هذا الشهر: منتج A (150 قطعة، 45,000 ريال)، منتج B..."  
**مع رسم بياني** (إذا طلب العميل)

---

</div>

### 💡 What is This System?

An intelligent system that answers customer questions in natural language and provides clear data analyses from the database **without showing any technical details**.

### 🎯 Core Idea in 30 Seconds:

1. **Customer asks**: "How many customers do we have this month?"
2. **System understands** the question using AI
3. **Extracts data** from database (behind the scenes)
4. **Returns clear answer**: "You have 1,234 active customers this month"

**Customer never sees**: SQL queries, table names, or any technical details

### ⚡ How Does It Work? (In Two Lines)

**For Customer (End User):**
- Asks a simple question → Gets a clear answer with data

**For System (Behind the Scenes):**
- Understands question → Auto-generates SQL → Extracts data → Analyzes → Formats answer in business language

### 🎁 What's Special?

✅ **No Technical Knowledge Required** - Anyone can ask questions  
✅ **Clear Answers** - In business language, not technical jargon  
✅ **Fully Secure** - Technical details completely hidden  
✅ **Arabic/English Support** - Ask in any language  

### 📊 Real Example:

**Question:** "What are the best-selling products this month?"  
**Answer:** "Top 5 best-selling products this month: Product A (150 units, 45,000 SAR), Product B..."  
**With Chart** (if customer requests)

---

## 📋 Table of Contents / جدول المحتويات

- [Overview / نظرة عامة](#overview)
- [Features / المميزات](#features)
- [Architecture / البنية المعمارية](#architecture)
- [Project Structure / هيكلية المشروع](#project-structure)
- [Installation / التثبيت](#installation)
- [Configuration / الإعدادات](#configuration)
- [Usage / الاستخدام](#usage)
- [API Documentation / توثيق API](#api-documentation)
- [Docker Deployment / النشر باستخدام Docker](#docker-deployment)
- [Development / التطوير](#development)

---

## 🎯 Overview / نظرة عامة

<div dir="rtl">

**Chat with Database** هو نظام ذكي مصمم خصيصاً للرد على استفسارات العملاء من خلال تقديم تحليلات واضحة ومباشرة من قاعدة البيانات. النظام يستخدم الذكاء الاصطناعي لفهم أسئلة العملاء باللغة الطبيعية، ثم يقوم تلقائياً بتحليل البيانات وإرجاع إجابات واضحة وسهلة الفهم.

### 🎯 الهدف الأساسي:
**النظام مصمم للمستخدمين النهائيين غير التقنيين** - العملاء الذين يريدون الحصول على بيانات واضحة دون الحاجة لفهم قواعد البيانات أو استعلامات SQL.

### ✨ ما يقدمه النظام:
- **إجابات واضحة ومباشرة**: يحصل المستخدم على تحليلات وبيانات واضحة باللغة الطبيعية
- **لا توجد استعلامات تقنية**: المستخدم النهائي لا يرى أي استعلامات SQL أو تفاصيل تقنية
- **تحليلات جاهزة**: النظام يقوم بتحليل البيانات تلقائياً ويقدم النتائج بشكل مفهوم
- **لغة الأعمال**: جميع الإجابات مكتوبة بلغة الأعمال وليس المصطلحات التقنية

### 🔒 الأمان والخصوصية:
- إخفاء كامل للتفاصيل التقنية (أسماء الجداول والأعمدة)
- حماية من الاستعلامات الضارة
- التحقق الأمني التلقائي

### 💡 مثال على الاستخدام:
**سؤال العميل:** "كم عدد العملاء لدينا هذا الشهر؟"

**ما يراه العميل:**
> "يوجد لديك 1,234 عميل نشط هذا الشهر، بزيادة 15% عن الشهر الماضي."

**ما لا يراه العميل:**
- ❌ استعلام SQL
- ❌ أسماء الجداول
- ❌ أسماء الأعمدة
- ❌ أي تفاصيل تقنية

</div>

**Chat with Database** is an intelligent system designed specifically to respond to customer inquiries by providing clear and direct data analyses from the database. The system uses AI to understand customer questions in natural language, then automatically analyzes the data and returns clear, easy-to-understand answers.

### 🎯 Core Purpose:
**The system is designed for non-technical end users** - customers who want clear data without needing to understand databases or SQL queries.

### ✨ What the System Provides:
- **Clear and Direct Answers**: Users get clear analyses and data in natural language
- **No Technical Queries**: End users never see SQL queries or technical details
- **Ready-made Analyses**: The system automatically analyzes data and presents results in an understandable format
- **Business Language**: All answers are written in business language, not technical terminology

### 🔒 Security & Privacy:
- Complete hiding of technical details (table names, column names)
- Protection from malicious queries
- Automatic security validation

### 💡 Usage Example:
**Customer Question:** "How many customers do we have this month?"

**What the Customer Sees:**
> "You have 1,234 active customers this month, a 15% increase from last month."

**What the Customer Never Sees:**
- ❌ SQL query
- ❌ Table names
- ❌ Column names
- ❌ Any technical details

---

## 🔄 How It Works / كيف يعمل النظام

<div dir="rtl">

### للمستخدم النهائي (العميل):

1. **يسأل سؤالاً بسيطاً** باللغة الطبيعية:
   - "كم عدد العملاء لدينا؟"
   - "ما هي المبيعات هذا الشهر؟"
   - "أعطني قائمة بأفضل المنتجات مبيعاً"

2. **يحصل على إجابة واضحة** بدون أي تفاصيل تقنية:
   - "يوجد لديك 1,234 عميل نشط"
   - "المبيعات هذا الشهر بلغت 50,000 ريال"
   - قائمة واضحة بالمنتجات مع الأرقام

3. **لا يرى أبداً**:
   - ❌ استعلامات SQL
   - ❌ أسماء الجداول
   - ❌ أسماء الأعمدة
   - ❌ أي تفاصيل تقنية

### ما يحدث خلف الكواليس (للمطورين):

1. النظام يفهم السؤال باستخدام الذكاء الاصطناعي
2. يولد استعلام SQL تلقائياً (مخفي عن المستخدم)
3. ينفذ الاستعلام على قاعدة البيانات
4. يحلل النتائج إحصائياً
5. ينسق الإجابة بلغة الأعمال الواضحة
6. يخفي جميع التفاصيل التقنية

</div>

### For End Users (Customers):

1. **Ask a simple question** in natural language:
   - "How many customers do we have?"
   - "What are the sales this month?"
   - "Show me the best-selling products"

2. **Get a clear answer** without any technical details:
   - "You have 1,234 active customers"
   - "Sales this month reached 50,000 SAR"
   - Clear list of products with numbers

3. **Never see**:
   - ❌ SQL queries
   - ❌ Table names
   - ❌ Column names
   - ❌ Any technical details

### Behind the Scenes (For Developers):

1. System understands the question using AI
2. Automatically generates SQL query (hidden from user)
3. Executes query on database
4. Analyzes results statistically
5. Formats answer in clear business language
6. Hides all technical details

---

## ✨ Features / المميزات

### 👥 Designed for End Users / مصمم للمستخدمين النهائيين
- **No Technical Knowledge Required**: Users don't need to know SQL or database structure
- **Natural Language Only**: Ask questions in plain Arabic or English
- **Clear Business Answers**: Get data insights in business-friendly language
- **Hidden Technical Details**: SQL queries, table names, and technical terms are never shown to end users

### 🌐 Multi-Language Support / دعم متعدد اللغات
- **Arabic & English** support for questions and answers
- Automatic language detection
- Natural language processing

### 🤖 AI-Powered Analysis / تحليل بالذكاء الاصطناعي
- Uses **OpenAI GPT-4** or **Google Gemini** for intelligent data analysis
- Context-aware analysis using RAG (Retrieval Augmented Generation)
- Automatic schema understanding and retrieval
- **Behind the scenes**: Generates SQL queries internally (never shown to users)

### 🔒 Security Features / ميزات الأمان
- SQL injection prevention
- Query validation and sanitization
- Sensitive data detection
- Allowed operations restriction (SELECT only by default)
- Query timeout protection
- **Privacy Protection**: Technical details are completely hidden from end users

### 📊 Data Analysis & Visualization / تحليل وتصور البيانات
- **Statistical Analysis**: Automatic statistical summaries presented in clear language
- **Data Visualization**: Generate charts and graphs using PandasAI
- **Excel Export**: Export query results to Excel files
- **Smart Data Preview**: Preview data with pagination
- **Business Insights**: Transform raw data into actionable business insights

### 💾 Database Support / دعم قواعد البيانات
- **PostgreSQL**: Main database for queries
- **MongoDB**: Store conversations, sessions, and metadata
- Connection pooling and optimization
- Support for external databases

### 🔄 Session Management / إدارة الجلسات
- Conversation history tracking
- Session-based context
- User metadata support
- Thread-based conversations (like ChatGPT)

### 📈 Observability / المراقبة
- Structured logging (JSON format)
- Health checks
- Error tracking
- Performance monitoring

---

## 🏗️ Architecture / البنية المعمارية

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                          │
│                    (Web/Mobile App)                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Layer (FastAPI)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Chat API    │  │  Health API  │  │  Static Files│      │
│  │  Endpoints   │  │  Endpoints   │  │  (Exports)   │      │
│  └──────┬───────┘  └──────────────┘  └──────────────┘      │
└─────────┼──────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer                             │
│  ┌──────────────────┐  ┌──────────────────┐                  │
│  │  Chat Service   │  │  Visualization  │                  │
│  │  (Orchestrator) │  │     Service     │                  │
│  └────────┬────────┘  └──────────────────┘                  │
│           │                                                    │
│  ┌────────▼──────────────────────────────────────┐           │
│  │  Statistical Analysis Service                │           │
│  └──────────────────────────────────────────────┘           │
└─────────┬──────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                    LLM Layer                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Question     │  │ SQL         │  │ Response     │      │
│  │ Classifier   │  │ Generator   │  │ Formatter    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Question     │  │ Sensitive   │  │ Query Intent │      │
│  │ Refiner      │  │ Detector     │  │ Detector     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────┬──────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                    RAG Layer                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Schema       │  │ Semantic     │  │ Schema       │      │
│  │ Store        │  │ Keywords     │  │ Retriever    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────┬──────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Access Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ PostgreSQL   │  │ MongoDB      │  │ Query Cache  │      │
│  │ Executor     │  │ Manager      │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────┬──────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Database Layer                             │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │ PostgreSQL   │  │ MongoDB      │                        │
│  │ (Main DB)    │  │ (Sessions)    │                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

### Flow Diagram / مخطط التدفق

```
User Question
     │
     ▼
┌─────────────────┐
│ Question        │
│ Classification  │ ──→ Is it database-related?
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Sensitive       │ ──→ Is it safe?
│ Detection       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Question        │ ──→ Refine question with context
│ Refinement      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Schema          │ ──→ Get relevant schema parts
│ Retrieval (RAG) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ SQL Generation  │ ──→ Generate SQL query
│ (LLM Chain)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ SQL Validation  │ ──→ Security check
│ & Sanitization  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ SQL Execution   │ ──→ Execute query
│ (PostgreSQL)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Data Processing │ ──→ Analyze & visualize
│ & Analysis      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Response        │ ──→ Format answer
│ Formatting      │
└────────┬────────┘
         │
         ▼
   User Answer
```

---

## 📁 Project Structure / هيكلية المشروع

```
new_version/
│
├── app/                          # Application code
│   ├── __init__.py
│   ├── main.py                   # FastAPI application entry point
│   ├── config.py                 # Configuration management
│   │
│   ├── api/                      # API endpoints
│   │   ├── __init__.py
│   │   └── chat.py               # Chat API endpoints
│   │
│   ├── db/                       # Database layer
│   │   ├── __init__.py
│   │   ├── connection.py         # PostgreSQL connection
│   │   ├── executor.py           # SQL execution
│   │   ├── security.py           # SQL security & validation
│   │   └── mongodb.py            # MongoDB connection & operations
│   │
│   ├── llm/                      # LLM services
│   │   ├── __init__.py
│   │   ├── client.py             # OpenAI client
│   │   ├── gemini_client.py      # Google Gemini client
│   │   ├── chains.py             # LangChain chains (SQL generation, summarization)
│   │   ├── prompts.py            # LLM prompts templates
│   │   ├── question_classifier.py      # Classify question type
│   │   ├── question_refiner.py          # Refine questions with context
│   │   ├── query_intent.py              # Detect query intent
│   │   ├── sensitive_question_detector.py  # Detect sensitive questions
│   │   ├── sensitive_question_checker.py  # Check sensitive data access
│   │   ├── general_question_handler.py    # Handle non-DB questions
│   │   └── gemini_response_formatter.py   # Format responses professionally
│   │
│   ├── rag/                      # RAG (Retrieval Augmented Generation)
│   │   ├── __init__.py
│   │   ├── schema_store.py       # Store database schema
│   │   ├── retriever.py          # Retrieve relevant schema parts
│   │   └── semantic_keywords.py  # Semantic keyword extraction
│   │
│   ├── services/                 # Business logic services
│   │   ├── __init__.py
│   │   ├── chat_service.py       # Main chat orchestration service
│   │   ├── statistical_analysis.py  # Statistical analysis service
│   │   └── visualization_service.py # Data visualization service
│   │
│   ├── utils/                    # Utility functions
│   │   ├── __init__.py
│   │   ├── excel_export.py       # Excel export functionality
│   │   ├── query_cache.py        # Query result caching
│   │   ├── json_sanitizer.py     # JSON sanitization
│   │   ├── data_summarizer.py    # Data summarization
│   │   └── error_messages.py     # Error message handling
│   │
│   ├── visualization/            # Visualization
│   │   ├── __init__.py
│   │   ├── pandasai_engine.py    # PandasAI integration
│   │   └── prompts.py            # Visualization prompts
│   │
│   └── observability/            # Logging & monitoring
│       ├── __init__.py
│       └── logging.py            # Logging configuration
│
├── requirements/                 # Python dependencies
│   ├── base.txt                  # Core dependencies
│   ├── ai.txt                    # AI/LLM dependencies
│   └── analytics.txt             # Analytics & visualization dependencies
│
├── exports/                      # Generated Excel files (gitignored)
├── charts/                       # Generated charts (gitignored)
│   └── generated/
├── cache/                        # Query cache (gitignored)
│
├── docker-compose.yml            # Docker Compose configuration
├── docker-compose.dev.yml        # Development Docker Compose
├── Dockerfile                    # Docker image definition
├── .dockerignore                 # Docker ignore file
├── .env.example                  # Environment variables example
├── .gitignore                    # Git ignore file
│
├── DOCKER_SETUP.md               # Docker setup guide
├── QUICK_START_DOCKER.md         # Quick start guide
├── SERVICE_REPORT.md             # Service documentation
├── DATABASE_SCHEMA.md            # Database schema documentation
├── API_USAGE.md                  # API usage guide (Arabic)
├── API_EXAMPLES.md               # API examples and quick reference
│
└── README.md                     # This file
```

---

## 🚀 Installation / التثبيت

### Prerequisites / المتطلبات

- Python 3.11+
- PostgreSQL database (local or remote)
- MongoDB (optional, for session management)
- OpenAI API key OR Google Gemini API key

### Option 1: Docker (Recommended) / الخيار 1: Docker (موصى به)

```bash
# Clone the repository
git clone https://github.com/RobotReception/chat_with_db.git
cd chat_with_db

# Copy environment file
cp .env.example .env

# Edit .env file with your configuration
nano .env

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f api
```

### Option 2: Local Installation / الخيار 2: التثبيت المحلي

```bash
# Clone the repository
git clone https://github.com/RobotReception/chat_with_db.git
cd chat_with_db

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements/base.txt
pip install -r requirements/ai.txt
pip install -r requirements/analytics.txt

# Copy environment file
cp .env.example .env

# Edit .env file
nano .env

# Run the application
python -m app.main
```

---

## ⚙️ Configuration / الإعدادات

### Environment Variables / متغيرات البيئة

⚠️ **Security Warning**: Never commit your `.env` file to version control. It contains sensitive information like database credentials, API keys, and server configuration.

Create a `.env` file based on `.env.example`:

```env
# API Configuration
API_TITLE=PostgreSQL Chat API
API_VERSION=1.0.0
API_PREFIX=/api/v1
DEBUG=false
LOG_LEVEL=INFO

# Security
# ⚠️ IMPORTANT: Generate strong, unique keys for production
API_KEY=your-secret-api-key  # Required for API authentication (X-API-Key header)
JWT_SECRET=your-jwt-secret   # Generate a secure random string for production

# PostgreSQL Database
# ⚠️ IMPORTANT: Replace with your actual database connection details
DB_HOST=your-database-host
DB_PORT=your-database-port
DB_NAME=your_database
DB_USER=your_database_user
DB_PASSWORD=your_database_password
# OR use full connection string:
POSTGRESQL_URL=postgresql://user:password@host:port/database

# MongoDB (Required - for sessions and conversation history)
# ⚠️ IMPORTANT: Replace with your actual MongoDB connection details
MONGO_URI=mongodb://your-mongodb-host:port/
MONGO_DB_NAME=chat_db

# LLM Configuration
# ⚠️ IMPORTANT: Keep your API keys secure and never expose them
# Option 1: OpenAI
OPENAI_API_KEY=your-openai-api-key-here
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.0

# Option 2: Google Gemini (for question refinement and response formatting)
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-2.0-flash
GEMINI_TEMPERATURE=0.3

# SQL Settings
SQL_TIMEOUT_SECONDS=30
SQL_MAX_ROWS=1000
SHOW_SQL_TO_USER=false  # ⚠️ IMPORTANT: Set to false in production to hide SQL queries from end users
                       # The system is designed for non-technical users who should only see clear business answers

# RAG Settings
EMBEDDING_MODEL=text-embedding-ada-002
RAG_TOP_K=5
```

### Database Setup / إعداد قاعدة البيانات

1. **PostgreSQL**: Ensure your database is accessible and contains the data you want to query
   - **Test Database**: The system uses **DVD Rental** sample database for testing
   - See [DATABASE_SCHEMA.md](./DATABASE_SCHEMA.md) for detailed database schema documentation
2. **MongoDB** (Required): For session management and conversation history

---

## 📖 Usage / الاستخدام

### Starting the Service / بدء الخدمة

```bash
# Using Docker
docker-compose up -d

# Or locally
python -m app.main
```

The API will be available at your configured server address and port.

### API Documentation / توثيق API

Interactive API documentation is available at:
- **Swagger UI**: `http://your-server-address:port/docs`
- **ReDoc**: `http://your-server-address:port/redoc`

⚠️ **Note**: Replace `your-server-address:port` with your actual server configuration.

### Example Request / مثال على الطلب

**⚠️ Important:** All API requests require `X-API-Key` header for authentication.

```bash
curl -X POST "http://your-server-address:port/api/v1/chat" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key" \
  -d '{
    "question": "كم عدد العملاء في قاعدة البيانات؟",
    "session_id": "optional-session-id",
    "export_to_excel": false,
    "include_data": true
  }'
```

⚠️ **Important**: Replace `your-server-address:port` with your actual server address and port.

**Note:** See [API_USAGE.md](./API_USAGE.md) for detailed API usage guide (Arabic) and [API_EXAMPLES.md](./API_EXAMPLES.md) for quick examples.

### Example Response / مثال على الاستجابة

**⚠️ Important Note:** In production, `sql_query` is typically hidden from end users (controlled by `SHOW_SQL_TO_USER=false` in `.env`). The system is designed to show only clear, business-friendly answers.

```json
{
  "success": true,
  "answer": "يوجد 1,234 عميل نشط في قاعدة البيانات. هذا يمثل زيادة بنسبة 12% مقارنة بالشهر الماضي.",
  "sql_query": "SELECT COUNT(*) FROM customers;",  // ⚠️ Hidden from end users in production
  "data": {
    "columns": ["count"],
    "rows": [[1234]],
    "row_count": 1
  },
  "has_data": true,
  "data_preview_rows": 1,
  "needs_visualization": false,
  "visualization_type": "none",
  "is_database_related": true,
  "metadata": {
    "question": "كم عدد العملاء في قاعدة البيانات؟",
    "execution_time_ms": 45,
    "steps": ["question_classified", "sql_generated", "sql_executed"]
  }
}
```

**What End Users See:**
- ✅ Clear answer in natural language: "يوجد 1,234 عميل نشط..."
- ✅ Data results in a structured format
- ✅ Business insights and analysis

**What End Users DON'T See (in production):**
- ❌ SQL queries
- ❌ Database table names
- ❌ Column names
- ❌ Technical implementation details

---

## 📚 API Documentation / توثيق API

### Authentication / المصادقة

All API endpoints (except `/health` and `/`) require authentication using `X-API-Key` header:

```
X-API-Key: your-secret-api-key
```

The API key is configured in `.env` file as `API_KEY`.

**For detailed API usage guide, see:**
- [API_USAGE.md](./API_USAGE.md) - Complete API documentation in Arabic
- [API_EXAMPLES.md](./API_EXAMPLES.md) - Quick examples and code snippets

### Endpoints / النقاط الطرفية

#### `POST /api/v1/chat`

Send a question to the chat API.

**Headers:**
```
Content-Type: application/json
X-API-Key: your-secret-api-key
```

**Request Body:**
```json
{
  "question": "string (required)",
  "session_id": "string (optional)",
  "conversation_id": "string (optional)",
  "export_to_excel": "boolean (default: false)",
  "include_data": "boolean (default: false)",
  "preview_rows": "integer (default: 10, max: 100)"
}
```

**Response:**
```json
{
  "success": "boolean",
  "answer": "string",
  "sql_query": "string (optional)",
  "data": "object (optional)",
  "has_data": "boolean",
  "has_chart": "boolean",
  "chart_id": "string (optional)",
  "has_excel": "boolean",
  "excel_url": "string (optional)",
  "needs_visualization": "boolean",
  "visualization_type": "string",
  "is_database_related": "boolean",
  "error": "string (optional)",
  "metadata": "object"
}
```

#### `POST /api/v1/chat/session`

Create a new session.

#### `GET /health`

Health check endpoint.

#### `GET /`

Root endpoint with API information.

---

## 🐳 Docker Deployment / النشر باستخدام Docker

See [DOCKER_SETUP.md](./DOCKER_SETUP.md) for detailed Docker setup instructions.

### Quick Start / البدء السريع

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

---

## 🛠️ Development / التطوير

### Project Components / مكونات المشروع

#### 1. **API Layer** (`app/api/`)
- FastAPI endpoints
- Request/response models
- Error handling

#### 2. **Service Layer** (`app/services/`)
- Business logic
- Orchestration of LLM, RAG, and database operations

#### 3. **LLM Layer** (`app/llm/`)
- Question processing
- SQL generation
- Response formatting
- Security checks

#### 4. **RAG Layer** (`app/rag/`)
- Schema storage and retrieval
- Semantic search
- Context building

#### 5. **Data Access Layer** (`app/db/`)
- Database connections
- SQL execution
- Security validation
- Caching

#### 6. **Utilities** (`app/utils/`)
- Excel export
- Data summarization
- Error handling
- JSON sanitization

### Adding New Features / إضافة ميزات جديدة

1. **New LLM Chain**: Add to `app/llm/chains.py`
2. **New Service**: Add to `app/services/`
3. **New Endpoint**: Add to `app/api/`
4. **New Utility**: Add to `app/utils/`

### Testing / الاختبار

```bash
# Run tests (if available)
pytest

# Test API endpoint
curl http://your-server-address:port/health
```

⚠️ **Note**: Replace `your-server-address:port` with your actual server configuration.

---

## 🔒 Security / الأمان

### Security Features / ميزات الأمان

1. **SQL Injection Prevention**
   - Query validation
   - Allowed operations restriction
   - Parameter sanitization

2. **Sensitive Data Detection**
   - Automatic detection of sensitive questions
   - Privacy protection

3. **Query Timeout**
   - Prevents long-running queries
   - Configurable timeout

4. **Row Limit**
   - Maximum rows per query
   - Prevents excessive data retrieval

### 🔐 Security Best Practices / أفضل ممارسات الأمان

<div dir="rtl">

#### ⚠️ معلومات حساسة يجب حمايتها:

1. **معلومات الاتصال بقواعد البيانات:**
   - ❌ لا تكشف عناوين IP للسيرفرات
   - ❌ لا تكشف أرقام المنافذ (Ports)
   - ❌ لا تكشف أسماء المستخدمين أو كلمات المرور
   - ✅ استخدم متغيرات البيئة (`.env`) لحفظ هذه المعلومات
   - ✅ تأكد من أن ملف `.env` موجود في `.gitignore`

2. **مفاتيح API:**
   - ❌ لا ترفع مفاتيح API الحقيقية إلى GitHub
   - ❌ لا تكتب مفاتيح API في الكود
   - ✅ استخدم متغيرات البيئة فقط
   - ✅ استخدم مفاتيح مختلفة للبيئة التطويرية والإنتاجية

3. **معلومات السيرفر:**
   - ❌ لا تكشف عناوين IP الداخلية أو الخارجية
   - ❌ لا تكشف تفاصيل البنية التحتية
   - ✅ استخدم placeholders في التوثيق (مثل `your-server-address`)

4. **ملفات الإعدادات:**
   - ✅ تأكد من أن `.env` موجود في `.gitignore`
   - ✅ استخدم `.env.example` كقالب بدون معلومات حساسة
   - ✅ راجع جميع الملفات قبل الرفع إلى GitHub

</div>

#### ⚠️ Sensitive Information to Protect:

1. **Database Connection Information:**
   - ❌ Never expose server IP addresses
   - ❌ Never expose port numbers
   - ❌ Never expose usernames or passwords
   - ✅ Use environment variables (`.env`) to store this information
   - ✅ Ensure `.env` is in `.gitignore`

2. **API Keys:**
   - ❌ Never commit real API keys to GitHub
   - ❌ Never hardcode API keys in code
   - ✅ Use environment variables only
   - ✅ Use different keys for development and production

3. **Server Information:**
   - ❌ Never expose internal or external IP addresses
   - ❌ Never expose infrastructure details
   - ✅ Use placeholders in documentation (e.g., `your-server-address`)

4. **Configuration Files:**
   - ✅ Ensure `.env` is in `.gitignore`
   - ✅ Use `.env.example` as a template without sensitive data
   - ✅ Review all files before pushing to GitHub

---

## 📊 Features in Detail / المميزات بالتفصيل

### 1. Question Classification / تصنيف الأسئلة
- Classifies questions as database-related or general
- Routes to appropriate handler
- **User Experience**: End users just ask questions naturally, no need to specify query type

### 2. SQL Generation / توليد SQL (خلف الكواليس)
- Uses LLM with RAG context
- Generates optimized SQL queries automatically
- Handles complex queries with joins
- **User Experience**: SQL generation is completely invisible to end users - they only see clear answers

### 3. Statistical Analysis / التحليل الإحصائي
- Automatic statistical summaries
- Mean, median, mode calculations
- Distribution analysis
- **User Experience**: Statistics are presented in clear, business-friendly language (e.g., "Average sales: 5,000 SAR")

### 4. Data Visualization / تصور البيانات
- Automatic chart generation
- Supports multiple chart types
- PandasAI integration
- **User Experience**: Users can request charts by asking "أعطني رسم بياني" or "show me a chart"

### 5. Excel Export / تصدير Excel
- Export query results to Excel
- Formatted Excel files
- Download links
- **User Experience**: Users can request Excel export, and get a clean, formatted file without seeing any SQL

---

## 🤝 Contributing / المساهمة

Contributions are welcome! Please feel free to submit a Pull Request.

<div dir="rtl">

المساهمات مرحب بها! يرجى إرسال Pull Request.

</div>

---

## 📝 License / الترخيص

This project is licensed under the MIT License.

---

## 📞 Support / الدعم

For issues and questions, please open an issue on GitHub.

<div dir="rtl">

للأسئلة والمشاكل، يرجى فتح issue على GitHub.

</div>

---

## 🙏 Acknowledgments / شكر وتقدير

- **FastAPI** - Modern web framework
- **LangChain** - LLM framework
- **OpenAI** - GPT models
- **Google Gemini** - Gemini models
- **PostgreSQL** - Database
- **MongoDB** - Session storage
- **PandasAI** - Data visualization

---

<div dir="rtl">

## 🎉 جاهز للاستخدام!

ابدأ الآن وتمتع بالتفاعل مع قاعدة البيانات باستخدام اللغة الطبيعية!

</div>

## 🎉 Ready to Use!

Start now and enjoy interacting with your database using natural language!

---

**Made with ❤️ by RobotReception**
# agent
# agent
# agent
