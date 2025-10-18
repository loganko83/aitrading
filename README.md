# 🤖 TradingBot AI - Triple AI Ensemble Trading System

**AI-powered cryptocurrency trading bot** using **GPT-4, LLaMA 3.1, and ML Models** for intelligent automated trading on **Binance Futures**.

---

## 🎯 System Overview

### **Triple AI Ensemble Decision Making**
- **ML Models (40%)**: LSTM, Transformer, LightGBM
- **GPT-4 (25%)**: OpenAI advanced analysis
- **LLaMA 3.1 (25%)**: Meta LLM analysis
- **Technical Analysis (10%)**: ATR-based signals

### **Entry Logic**
```
Probability ≥ 80% AND Confidence ≥ 70% AND Agreement ≥ 70%
```

---

## 📁 Project Structure

```
trading/
├── trading-frontend/          # Next.js 15 + React 19 + TypeScript
│   ├── app/                   # App Router (Next.js 15)
│   │   ├── (auth)/            # Authentication pages (login, signup, OTP)
│   │   ├── (protected)/       # Protected dashboard pages
│   │   └── api/               # API routes (NextAuth, strategies, webhooks)
│   ├── components/            # React components
│   ├── lib/                   # Utilities and helpers
│   ├── prisma/                # Database schema (PostgreSQL)
│   └── public/                # Static assets
│
└── trading-backend/           # FastAPI + Python
    ├── app/
    │   ├── ai/                # AI Ensemble system
    │   │   └── ensemble.py    # Triple AI logic
    │   ├── api/               # FastAPI routes
    │   │   └── v1/            # API v1 endpoints
    │   ├── core/              # Configuration
    │   ├── database/          # SQLAlchemy setup
    │   ├── models/            # Database models
    │   ├── services/          # Binance API client
    │   └── workers/           # Background workers
    ├── alembic/               # Database migrations
    ├── main.py                # FastAPI app entry
    └── requirements.txt       # Python dependencies
```

---

## 🚀 Quick Start

### **Prerequisites**
- **Node.js 20+** and **npm/yarn**
- **Python 3.10+** and **pip**
- **PostgreSQL 14+**
- **Redis** (for caching)
- **Binance Account** (Testnet or Mainnet)

---

### **1. Frontend Setup**

```bash
cd trading-frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local with your database URL and API keys

# Run database migrations
npx prisma migrate dev

# Seed default strategies
npx prisma db seed

# Run development server
npm run dev
```

**Frontend runs on**: [http://localhost:3000](http://localhost:3000)

---

### **2. Backend Setup**

```bash
cd trading-backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run database migrations
alembic upgrade head

# Run development server
python main.py
```

**Backend runs on**: [http://localhost:8001](http://localhost:8001)

---

## 📡 TradingView Webhook Auto-Trading Setup

### **Step 1: Register Exchange API Keys**

Users must register their exchange API keys through the secure endpoint:

```bash
# Example: Register Binance API
POST http://localhost:8001/api/v1/accounts-secure/register
Authorization: Bearer <user_jwt_token>

{
  "exchange": "binance",
  "api_key": "your_binance_api_key",
  "api_secret": "your_binance_api_secret",
  "testnet": true
}
```

```bash
# Example: Register OKX API
POST http://localhost:8001/api/v1/accounts-secure/register
Authorization: Bearer <user_jwt_token>

{
  "exchange": "okx",
  "api_key": "your_okx_api_key",
  "api_secret": "your_okx_api_secret",
  "passphrase": "your_okx_passphrase",
  "testnet": true
}
```

### **Step 2: Export Pine Script Strategy**

Use the backend's Pine Script export feature:

```bash
GET http://localhost:8001/api/v1/strategies/pine-export/triple-ai-ensemble
```

This generates a `.pine` file with webhook alert code already included.

### **Step 3: Set Up TradingView Alert**

1. Copy the Pine Script code to TradingView
2. Create a new alert
3. In alert settings, set:
   - **Webhook URL**: `http://your-backend-url/api/v1/webhook/tradingview`
   - **Message**:
   ```json
   {
     "account_id": "user_account_id",
     "exchange": "binance",
     "action": "{{strategy.order.action}}",
     "symbol": "{{ticker}}",
     "leverage": 3,
     "secret": "your_webhook_secret"
   }
   ```

### **Step 4: Start Auto-Trading**

Orders are automatically executed when TradingView sends webhook alerts!

**📚 Full Guide**: See [TRADINGVIEW_WEBHOOK_GUIDE.md](trading-backend/TRADINGVIEW_WEBHOOK_GUIDE.md) and [CLAUDE.md](trading-backend/CLAUDE.md)

---

## 🔧 Environment Variables

### **Frontend (.env.local)**
```env
DATABASE_URL="postgresql://user:password@localhost:5432/tradingbot"
NEXTAUTH_SECRET="your-secret-key"
NEXTAUTH_URL="http://localhost:3000"
```

### **Backend (.env)**
```env
# Application
APP_NAME="TradingBot AI Backend"
DEBUG=True
API_V1_PREFIX="/api/v1"

# Database
DATABASE_URL="postgresql://user:password@localhost:5432/tradingbot"

# Binance API
BINANCE_API_KEY="your-binance-api-key"
BINANCE_API_SECRET="your-binance-api-secret"
BINANCE_TESTNET=True

# AI APIs
OPENAI_API_KEY="your-openai-api-key"
ANTHROPIC_API_KEY="your-anthropic-api-key"

# Redis
REDIS_URL="redis://localhost:6379"

# Security
SECRET_KEY="your-secret-key"
WEBHOOK_SECRET="generate-with-python-secrets-token_urlsafe-32"
ENCRYPTION_KEY="generate-with-python-cryptography-fernet-generate_key"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Generate Security Keys:
# SECRET_KEY: openssl rand -hex 32
# WEBHOOK_SECRET: python -c "import secrets; print(secrets.token_urlsafe(32))"
# ENCRYPTION_KEY: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Trading Parameters
DEFAULT_LEVERAGE=3
MAX_POSITION_SIZE_PCT=0.10
ATR_PERIOD=14

# AI Ensemble Weights
ML_WEIGHT=0.40
GPT4_WEIGHT=0.25
LLAMA_WEIGHT=0.25
TA_WEIGHT=0.10

# Entry/Exit Thresholds
MIN_PROBABILITY=0.80
MIN_CONFIDENCE=0.70
MIN_AGREEMENT=0.70
```

---

## 🎮 Key Features

### **1. Triple AI Ensemble**
- **ML Models**: LSTM + Transformer + LightGBM for pattern recognition
- **GPT-4**: Advanced market analysis and reasoning
- **LLaMA 3.1**: Meta LLM for alternative perspectives
- **Weighted Voting**: Intelligent decision aggregation

### **2. Auto-Trading**
- **Automated Execution**: Based on AI signals
- **Risk Management**: ATR-based stop-loss/take-profit
- **Position Monitoring**: Real-time P&L tracking
- **Multi-Strategy**: Customizable strategy templates

### **3. Real-Time Data**
- **WebSocket Streaming**: Live market data
- **Position Updates**: Continuous portfolio monitoring
- **AI Signal Alerts**: Instant notifications

### **4. TradingView Webhook Auto-Trading** 🆕
- **Webhook Integration**: Receive alerts from TradingView Pine Script strategies
- **Multi-Exchange Support**: Binance Futures + OKX Futures
- **Secure API Storage**: AES-256 encrypted API keys in database
- **User Authentication**: JWT + NextAuth session verification
- **Auto-Execution**: Automatic order placement from TradingView signals

### **5. Backtesting**
- **Historical Testing**: Validate strategies on past data
- **Performance Metrics**: Win rate, Sharpe ratio, max drawdown
- **Equity Curve**: Visual performance analysis

### **6. Gamification**
- **XP System**: Earn experience from trades
- **Levels**: Progress through trading milestones
- **Badges**: Unlock achievements
- **Leaderboard**: Compete with other traders

---

## 📊 Tech Stack

### **Frontend**
- **Framework**: Next.js 15 (App Router)
- **UI**: React 19 + TypeScript
- **Styling**: Tailwind CSS 4 + shadcn/ui
- **Components**: Radix UI
- **Forms**: React Hook Form + Zod
- **Charts**: Recharts + Lightweight Charts
- **Authentication**: NextAuth v5 (2FA/OTP)
- **Database**: Prisma ORM + PostgreSQL

### **Backend**
- **Framework**: FastAPI
- **Language**: Python 3.10+
- **Database**: SQLAlchemy + PostgreSQL (async)
- **Trading**: python-binance + ccxt
- **AI/ML**: OpenAI + Anthropic + Transformers + PyTorch
- **Analysis**: pandas + numpy + ta (Technical Analysis)
- **WebSocket**: websockets + python-socketio
- **Background Jobs**: Celery
- **Caching**: Redis

---

## 🔐 Security

### **User Data Protection**
- **AES-256 Encryption**: Exchange API keys encrypted using Fernet (cryptography library)
- **Environment Secrets**: ENCRYPTION_KEY stored in environment variables
- **User Authentication**: JWT tokens + NextAuth session verification
- **Database Storage**: Encrypted credentials stored in PostgreSQL

### **Authentication & Authorization**
- **2FA Authentication**: TOTP-based OTP for user accounts
- **JWT Tokens**: Secure session management with configurable expiration
- **Password Hashing**: bcrypt for user passwords
- **Protected Routes**: Authentication required for sensitive operations

### **Webhook Security**
- **HMAC Verification**: TradingView webhook secret validation
- **Request Validation**: Signature verification using hmac.compare_digest()
- **Secret Rotation**: Configurable webhook secrets in environment

### **API Key Management**
- **User-Level Isolation**: Each user's API keys stored separately
- **Testnet Support**: Separate credentials for testnet/mainnet
- **Active/Inactive Toggle**: Disable accounts without deletion
- **Secure Deletion**: Complete removal from database and memory

---

## 📈 API Endpoints

### **Authentication**
- `POST /api/auth/signup` - User registration
- `POST /api/auth/verify-otp` - OTP verification
- `POST /api/auth/[...nextauth]` - NextAuth routes

### **Trading**
- `POST /api/v1/trading/analyze` - AI market analysis
- `GET /api/v1/trading/positions` - Get open positions
- `GET /api/v1/trading/balance` - Get account balance
- `POST /api/v1/trading/trade` - Execute trade
- `POST /api/v1/trading/close-position` - Close position

### **Strategies**
- `GET /api/strategies` - List all strategies
- `GET /api/strategies/configs/my` - User's strategy configs
- `POST /api/strategies/configs` - Create strategy config
- `POST /api/strategies/auto-trade/start` - Start auto-trading
- `POST /api/strategies/auto-trade/stop` - Stop auto-trading
- `GET /api/strategies/auto-trade/status` - Auto-trading status

### **TradingView Webhooks** 🆕
- `POST /api/v1/webhook/tradingview` - Receive TradingView webhook alerts
- Automatic order execution based on Pine Script signals

### **Account Management (Secure)** 🆕
- `POST /api/v1/accounts-secure/register` - Register exchange API keys (authenticated)
- `GET /api/v1/accounts-secure/list` - List user's exchange accounts
- `DELETE /api/v1/accounts-secure/{account_id}` - Delete exchange account
- `POST /api/v1/accounts-secure/{account_id}/toggle` - Toggle account active status

### **Account Management (Simple)**
- `POST /api/v1/accounts/binance/register` - Register Binance account (testing only)
- `POST /api/v1/accounts/okx/register` - Register OKX account (testing only)
- `GET /api/v1/accounts/{account_id}/status` - Get account status
- `DELETE /api/v1/accounts/{account_id}` - Delete account

### **WebSocket**
- `ws://localhost:8001/ws/market/{symbol}` - Market data stream
- `ws://localhost:8001/ws/positions/{userId}` - Position updates

---

## 🎯 Trading Strategy Example

```python
# Triple AI Ensemble Analysis
{
    "should_enter": True,
    "direction": "LONG",
    "probability_up": 0.85,  # 85% probability
    "confidence": 0.78,      # 78% confidence
    "agreement": 0.75,       # 75% agreement across AIs
    "entry_price": 65000.0,
    "stop_loss": 63500.0,
    "take_profit": 67500.0,
    "reasoning": "
        🤖 ML Models (40%): SMA20 > SMA50 indicates bullish trend
        🧠 GPT-4 (25%): Market structure shows bullish momentum
        🦙 LLaMA (25%): Volume profile suggests accumulation
        📊 TA Rules (10%): EMA20=65200, EMA50=64800, ATR=1000
        ✅ Final: Probability=85%, Confidence=78%, Agreement=75%
    "
}
```

---

## 🛠️ Development Status

### ✅ **Completed**
- ✅ Frontend UI (Next.js 15 + React 19)
- ✅ Authentication system (NextAuth v5 + 2FA)
- ✅ Database models (Prisma + SQLAlchemy)
- ✅ Binance Futures API integration
- ✅ OKX Futures API integration 🆕
- ✅ TradingView webhook auto-trading system 🆕
- ✅ Secure API key management with AES-256 encryption 🆕
- ✅ Basic AI Ensemble structure
- ✅ Auto-trader background worker
- ✅ API routes and endpoints
- ✅ Pine Script export with webhook alerts 🆕

### 🔄 **In Progress**
- 🔄 AI Ensemble GPT-4/LLaMA integration
- 🔄 ML Models (LSTM, Transformer, LightGBM)
- 🔄 WebSocket real-time data streaming
- 🔄 Frontend-Backend integration

### 📋 **Planned**
- 📋 Email notification system
- 📋 Advanced backtesting engine
- 📋 Mobile app (React Native)
- 📋 Multi-exchange support (Bybit, Bitget)

---

## 📚 Documentation

### **API Documentation**
- **Swagger UI**: [http://localhost:8001/docs](http://localhost:8001/docs)
- **ReDoc**: [http://localhost:8001/redoc](http://localhost:8001/redoc)

### **Developer Guides** 🆕
- **[CLAUDE.md](trading-backend/CLAUDE.md)** - Complete system architecture and developer documentation
  - TradingView webhook integration flow
  - Security system details (AES-256 encryption)
  - Database schema and relationships
  - API endpoint reference
  - Frontend integration examples
  - Deployment guide

- **[TRADINGVIEW_WEBHOOK_GUIDE.md](trading-backend/TRADINGVIEW_WEBHOOK_GUIDE.md)** - TradingView webhook setup guide
  - Step-by-step webhook configuration
  - Pine Script alert setup
  - Exchange API key registration
  - Security best practices
  - Troubleshooting tips

---

## ⚠️ Security Warnings

### **🔐 Critical Security Requirements**

1. **NEVER commit API keys to version control**
   - Always use `.env` files (already in `.gitignore`)
   - Rotate keys immediately if exposed

2. **Use testnet for development**
   - Binance Testnet: https://testnet.binancefuture.com
   - OKX Demo Trading: https://www.okx.com/demo-trading

3. **Production deployment checklist**
   - [ ] Generate new `ENCRYPTION_KEY` in production
   - [ ] Generate new `WEBHOOK_SECRET` in production
   - [ ] Use HTTPS for webhook endpoints
   - [ ] Enable API key IP restrictions on exchanges
   - [ ] Set API key permissions to "Enable Futures" only (no withdrawals)
   - [ ] Use separate API keys for testnet and mainnet

4. **Database security**
   - API keys are AES-256 encrypted in database
   - User authentication required for all operations
   - Keys only decrypted during order execution

### **⚠️ Trading Risks**

**This software is for educational purposes only.** Cryptocurrency trading carries substantial risk of loss. Use at your own risk. Always start with **testnet** before using real funds.

**Important:**
- Past performance does not guarantee future results
- AI predictions are not financial advice
- Always use appropriate position sizing and risk management
- Never trade with money you cannot afford to lose

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

- **OpenAI GPT-4** for advanced AI analysis
- **Meta LLaMA 3.1** for alternative AI perspective
- **Binance** for futures trading API
- **Next.js** and **FastAPI** for excellent frameworks

---

**Built with ❤️ by AI Trading Enthusiasts**
