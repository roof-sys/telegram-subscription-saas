# Telegram Subscription SaaS

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

>  **Production-ready SaaS platform for monetizing Telegram channels through subscriptions**

A comprehensive bot system with REST API that automates subscription sales, payment processing (cards, SBP, USDT), and access control for Telegram channels. Designed for real commercial use with live users and transactions.

> ⚠️ **Important:** This is a portfolio version of the project. Real tokens, channel IDs, payment keys, and some business-specific features have been replaced with examples for security purposes. The full production version with configurations is available upon request for employers.

[**Русская версия**](README) | **English version**

---

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [REST API](#-rest-api)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Architecture](#-architecture)
- [Security](#-security)
- [Roadmap](#-roadmap)

---

##  Features

### Core Functionality
- **Multi-tier subscription system** - flexible pricing plans (Basic, Standard, VIP, Premium)
- **Multiple payment methods** - card payments, SBP (Fast Payment System), USDT (TRC-20)
- **REST API for analytics** - FastAPI endpoints for statistics and management
- **Automatic access control** - one-time invite links with expiration
- **Subscription lifecycle management** - automatic expiration checks and access revocation
- **Payment verification** - real-time status checks via acquiring API and blockchain

### Business Features
-  **Instant payment processing** - support for Russian payment systems + crypto
-  **Secure data storage** - encryption of tokens and API keys
-  **Transaction logging** - complete audit trail of payments and subscriptions
-  **User analytics** - registration dates, activity tracking
-  **Background tasks** - scheduled subscription expiration checks

---

## 🛠 Tech Stack

| Component | Technology |
|-----------|-----------|
| **Language** | Python 3.9+ |
| **Bot Framework** | Aiogram 3.x (AsyncIO) |
| **REST API** | FastAPI + Uvicorn |
| **Database** | PostgreSQL + SQLAlchemy ORM |
| **Containerization** | Docker + Docker Compose |
| **Payment API** | Custom acquiring integration, TronGrid API |
| **Security** | cryptography, python-dotenv |
| **HTTP Client** | httpx (async) |
| **Deployment** | Docker, Linux (Ubuntu/Debian) |

---

## 🌐 REST API

The project includes a full-featured REST API built with FastAPI for analytics and management.

### Available Endpoints:

#### 📊 Statistics
```http
GET /api/stats
```
Returns overall statistics: user count, payments, revenue, active subscriptions.

**Example response:**
```json
{
  "users": {"total": 150},
  "payments": {"total": 45, "completed": 40, "pending": 5},
  "revenue": {"total": 125000.0, "currency": "RUB"},
  "subscriptions": {"active": 30}
}
```

#### 👥 Users
```http
GET /api/users?limit=50&offset=0
GET /api/users/{user_id}
```
User list with pagination and detailed information about specific users.

#### 💳 Payments
```http
GET /api/payments?status=completed&limit=50&offset=0
GET /api/payments/{payment_id}
```
Filter payments by status, detailed transaction information.

#### 🔗 Webhook
```http
POST /api/webhook/payment
```
Automatic processing of notifications from payment systems.

### Swagger Documentation

Full interactive API documentation is available at:
```
http://localhost:8000/docs
```

After launching the API, you can:
- View all endpoints
- Test requests directly in the browser
- Explore data schemas
- Copy code examples

### Running the API

```bash
# Together with the bot via Docker
docker-compose up -d

# Separately for development
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at `http://localhost:8000`

---

## 📁 Project Structure

```
telegram-subscription-saas/
├── src/
│   ├── bot.py                  # Bot and dispatcher initialization
│   ├── config.py               # Configuration and environment variables
│   ├── main.py                 # Application entry point
│   │
│   ├── api/                    # FastAPI REST API
│   │   ├── main.py            # FastAPI application
│   │   └── routes/            # API endpoints
│   │       ├── stats.py       # Statistics
│   │       ├── users.py       # Users
│   │       ├── payments.py    # Payments
│   │       └── webhook.py     # Webhook processing
│   │
│   ├── handlers/               # Message and callback handlers
│   │   ├── start.py           # Main menu and /start command
│   │   ├── tariffs.py         # Tariff display and selection
│   │   ├── payments.py        # Payment processing logic
│   │   └── subscriptions.py   # Subscription status check
│   │
│   ├── database/              # Data layer
│   │   ├── models.py          # SQLAlchemy models
│   │   ├── database.py        # Database connection
│   │   └── db_manager.py      # CRUD operations
│   │
│   ├── services/              # Background services
│   │   └── scheduler.py       # Periodic subscription checks
│   │
│   └── utils/                 # Utilities
│       └── logger.py          # Logging configuration
│
├── data/                      # Data (in .gitignore)
├── logs/                      # Application logs (in .gitignore)
├── .env                       # Environment variables (in .gitignore)
├── docker-compose.yml         # Docker Compose configuration
├── Dockerfile                 # Bot Docker image
├── requirements.txt
└── README.md
```

---

##  Installation

### Requirements
- Python 3.9+
- Docker & Docker Compose (recommended)
- PostgreSQL (if running without Docker)

### Option 1: Docker Compose (recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/telegram-subscription-saas.git
cd telegram-subscription-saas

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Start everything (bot + PostgreSQL + API)
docker-compose up -d

# View logs
docker-compose logs -f bot
```

### Option 2: Local Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/telegram-subscription-saas.git
cd telegram-subscription-saas

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run database migration (if needed)
python migrate_csv_to_postgres.py

# Start the bot
python src/main.py

# Start the API (in a separate terminal)
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

---

## ⚙️ Configuration

Create a `.env` file in the project root:

```env
# Bot settings
BOT_TOKEN=your_telegram_bot_token
ADMIN_ID=your_telegram_user_id

# PostgreSQL database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/telegram_bot
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=telegram_bot
POSTGRES_PORT=5432

# Payment system (cards/SBP)
SHOP_ID=your_shop_id
SHOP_SECRET=your_shop_secret
ACQUIRING_API_URL=https://your-acquiring-api.com

# Cryptocurrency (USDT TRC-20)
CRYPTO_PAYMENT_ADDRESS=your_tron_wallet
CRYPTO_PAYMENT_NETWORK=TRC-20
CRYPTO_EXCHANGE_RATE=90
TRONGRID_API_KEY=your_trongrid_api_key
TRON_NODE_URL=https://api.trongrid.io
```

### Channel Configuration
Edit `src/config.py` to link tariffs with channel IDs:

```python
CHANNELS = {
    'basic_1': -1001234567890,  # Your channel ID
    'vip_1': -1009876543210,
    # ... etc.
}
```

---

## 💡 Usage

### For End Users

1. **Start the bot** - `/start` to view available tariffs
2. **Choose a tariff** - select subscription plan and duration
3. **Pay** - complete payment via Card/SBP/USDT
4. **Get access** - receive a one-time invite link to the channel
5. **Check status** - `/mysub` to view subscription details

### For Administrators

**Via REST API:**
- Open `http://localhost:8000/docs` for Swagger documentation
- View statistics: `GET /api/stats`
- User list: `GET /api/users`
- Payment list: `GET /api/payments?status=completed`

**Via database:**
- Connect to PostgreSQL for detailed analysis
- SQL queries for complex analytics

---

##  Architecture

### Payment Processing Flow
```
User selects tariff
    ↓
Chooses payment method (Card/SBP/USDT)
    ↓
Payment created in PostgreSQL with "pending" status
    ↓
User completes payment externally
    ↓
Option A: User clicks "Check Payment"
Option B: Payment system sends webhook
    ↓
Bot/API checks status via API/blockchain
    ↓
On success:
    - Update payment status to "completed" in PostgreSQL
    - Create subscription record
    - Generate one-time invite link
    - Send to user
```

### Access Control Flow
```
User joins channel
    ↓
Bot intercepts via ChatMemberUpdated event
    ↓
Checks for active subscription in PostgreSQL
    ↓
Validates invite link (one-time use, not expired)
    ↓
If invalid → temporarily ban user
If valid → mark invite as used, allow access
```

### Background Scheduler
- Runs every hour
- Checks all subscriptions for expiration in PostgreSQL
- Automatically revokes expired access

---

## 🔒 Security

- ✅ **Environment variables** - all secrets stored in `.env` (never committed)
- ✅ **Encrypted storage** - sensitive data encrypted before saving on rented servers
- ✅ **PostgreSQL transactions** - ACID guarantees, protection against race conditions
- ✅ **Payment signatures** - MD5 signatures for acquiring API requests
- ✅ **One-time invite links** - auto-expiring links prevent unauthorized sharing
- ✅ **Input validation** - all user data sanitized
- ✅ **Error handling** - graceful failure with logging, no data leakage
- ✅ **Docker isolation** - containerization for secure deployment

---

## 🎯 Roadmap

### ✅ Completed
- [x] Migration from CSV to PostgreSQL with SQLAlchemy ORM
- [x] Application dockerization (Docker Compose: bot + PostgreSQL)
- [x] REST API for analytics (FastAPI)
- [x] Webhook for automatic payment processing

### In Progress
- [ ] Unit and integration tests (Pytest)
- [ ] Admin panel with web interface
- [ ] CI/CD pipeline (GitHub Actions)

### Planned Features
- [ ] Referral system with bonus subscriptions
- [ ] Multi-language support (i18n)
- [ ] Automatic invoice generation (PDF)
- [ ] Analytics platform integration
- [ ] Telegram Mini App for subscription management

---

## 📊 Project Statistics

- **Lines of code**: 2,722
- **Status**: ✅ Production (running with real users)
- **Development time**: 2 years (iterative improvements)
- **Payment methods**: 3 (Card, SBP, USDT)
- **Supported tariffs**: 13 (4 tiers × 2 durations + All channels)
- **API endpoints**: 8

---

## 🤝 Contributing

This is a commercial project, but feedback and suggestions are welcome! You can:
- Open an issue to report bugs or request features
- Submit a pull request for improvements
- Share your experience using the platform

---

## 📄 License

This project is developed as a commercial product. Code is provided for portfolio purposes.  
For commercial use or licensing inquiries, please contact: [busysourse707@gmail.com](https://mail.google.com/mail)

---

## 👨‍💻 Author

**Mark**  
Python Backend Developer 

- 💬 Telegram: [@underlockich](https://t.me/underlockich)
- 📧 Email: [busysourse707@gmail.com](https://mail.google.com/mail)


---


