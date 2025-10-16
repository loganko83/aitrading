# TradingBot AI - Triple AI Ensemble Crypto Trading Platform

AI-powered cryptocurrency trading bot using ML Models, GPT-4, and LLaMA 3.1 for intelligent trading on Binance Futures.

## 🚀 Project Status

**Current Phase**: Frontend Development (Phase 1 of 3)

✅ **Completed**:
- Next.js 14 project setup with TypeScript & TailwindCSS
- shadcn/ui component library integration
- Zustand state management stores (auth & trading)
- TypeScript type definitions for all entities
- Landing page with service introduction
- Project structure and folder organization

🔄 **In Progress**:
- Authentication system (NextAuth.js + Google OTP)
- Protected route layouts

📝 **Next Steps**:
- Dashboard page with real-time positions
- API key management interface
- Trading settings form
- Backend API development

## 📊 Core Features

### Triple AI Ensemble System
- **ML Models**: LSTM/GRU/Transformer or LightGBM/XGBoost
- **GPT-4 API**: Market sentiment & news analysis
- **LLaMA 3.1**: Technical pattern recognition (Elliott Wave, Fibonacci)

**Probability Formula**:
```
P_up_final = 0.4 × ML + 0.25 × GPT + 0.25 × LLaMA + 0.1 × TA_rules
```

**Entry Threshold**: P ≥ 0.80 AND Confidence ≥ 0.70 AND Agreement ≥ 0.70

### Trading Features
- **Coins**: BTC, ETH, BNB, SOL (Binance Futures)
- **Leverage**: 5x (isolated margin)
- **Position Size**: 10% of equity per trade
- **Risk Management**: Automatic SL (ATR × 1.2), TP (ATR × 2.5)
- **Multi-Timeframe**: 1m, 15m, 30m, 1h, 4h, 1d analysis

### User Features
- Secure authentication (Email/SNS + Google OTP 2FA)
- Encrypted Binance API key storage
- Real-time dashboard with PnL tracking
- Leaderboard & XP gamification system
- Webhook integration for external signals

## 🛠️ Tech Stack

### Frontend
- **Framework**: Next.js 14 (App Router, Turbopack)
- **Language**: TypeScript
- **Styling**: TailwindCSS + shadcn/ui
- **State Management**: Zustand
- **Forms**: React Hook Form + Zod
- **Authentication**: NextAuth.js + speakeasy (Google OTP)
- **Charts**: TradingView Lightweight Charts (to be added)

### Backend (Planned)
- **API**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL + Redis
- **Exchange**: CCXT (Binance Futures)
- **ML/AI**: PyTorch, LightGBM, OpenAI GPT-4, llama.cpp (LLaMA 3.1)
- **Deployment**: Docker + AWS EC2 (trendy.storydot.kr/trading)

## 📁 Project Structure

```
trading-frontend/
├── app/
│   ├── (auth)/              # Auth routes: login, signup, verify-otp
│   ├── (protected)/         # Protected: dashboard, settings, api-keys, etc.
│   ├── page.tsx             # Landing page ✅
│   ├── layout.tsx           # Root layout
│   └── globals.css          # Global styles
│
├── components/
│   ├── layout/              # Nav, Sidebar, Footer
│   ├── trading/             # TradingChart, PositionCard
│   ├── auth/                # LoginForm, SignupForm, OTPForm
│   └── ui/                  # shadcn/ui components ✅
│
├── lib/
│   ├── api/                 # API client functions
│   ├── auth/                # Auth helpers
│   ├── stores/              # Zustand stores ✅
│   │   ├── authStore.ts
│   │   └── tradingStore.ts
│   └── utils.ts             # Utility functions
│
├── types/
│   └── index.ts             # TypeScript definitions ✅
│
├── .env.local               # Environment variables ✅
└── package.json
```

## 🚀 Development

### Prerequisites
- Node.js 18+ and npm
- PostgreSQL database (for backend)
- Binance account with API keys
- OpenAI API key (GPT-4)

### Installation

```bash
cd trading-frontend
npm install
```

### Environment Setup

Copy `.env.local.example` to `.env.local` and configure:

```env
DATABASE_URL="postgresql://user:password@localhost:5432/trading_bot"
NEXTAUTH_URL="https://trendy.storydot.kr/trading"
NEXTAUTH_SECRET="your-secret-key"
OPENAI_API_KEY="sk-..."
ENCRYPTION_KEY="32-character-key"
```

### Run Development Server

```bash
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000)

### Build for Production

```bash
npm run build
npm run start
```

## 🔐 Security

1. **Authentication**:
   - Email/password with bcrypt hashing
   - Google OTP (TOTP) for 2FA
   - Session management with NextAuth.js

2. **API Key Protection**:
   - AES-256 encryption for stored Binance keys
   - Keys never exposed to frontend
   - Server-side only API calls

3. **Risk Controls**:
   - Automatic stop-loss on every position
   - Consecutive loss limit: 3 trades
   - Daily loss cap: 5% of equity

## 🏆 Gamification

- **XP Points**: Earned from profitable trades
- **Leveling System**: Progress through experience milestones
- **Leaderboard**: Global rankings by PnL and win rate
- **Badges**: Achievement system (coming soon)

## 📋 Implementation Roadmap

### Phase 1: Frontend Foundation (Current)
- [x] Project setup & UI library
- [x] Landing page
- [ ] Authentication pages (login, signup, OTP)
- [ ] Dashboard layout & navigation
- [ ] Protected route middleware

### Phase 2: Core Features
- [ ] API key management page
- [ ] Trading settings form (risk, coins, leverage)
- [ ] Real-time position display
- [ ] Trade history table
- [ ] Leaderboard page

### Phase 3: Advanced Features
- [ ] TradingView chart integration
- [ ] Webhook configuration interface
- [ ] User profile & statistics
- [ ] Notification system

### Phase 4: Backend Development
- [ ] FastAPI server setup
- [ ] Database models & migrations
- [ ] Binance API integration
- [ ] Triple AI system implementation

### Phase 5: Deployment
- [ ] Docker containerization
- [ ] AWS EC2 deployment
- [ ] Nginx reverse proxy setup
- [ ] CI/CD pipeline

## 🤖 AI Analysis Architecture

### Entry Decision Flow

```
1. Multi-Timeframe Data Collection (1m → 1d)
2. Feature Engineering (RSI, MACD, EMA, Volume, Elliott Wave, Fibonacci)
3. Triple AI Analysis:
   ├─ ML Model: Time series prediction → P_ml_up
   ├─ GPT-4 API: News & sentiment → P_gpt_up
   └─ LLaMA 3.1: Technical patterns → P_llama_up
4. Ensemble Probability: Weighted average
5. Confidence & Agreement Check
6. Entry Decision: LONG | SHORT | NO_ENTRY
7. Position Management: TP/SL automation, wrong prediction exit
```

### Technical Indicators

**Trend**: EMA 20/50/200, SMA, Golden/Death Cross
**Momentum**: RSI, MACD, Stochastic
**Volatility**: Bollinger Bands, ATR, Keltner Channels
**Volume**: OBV, Volume ratio, Buy/Sell pressure
**Advanced**: Elliott Wave patterns, Fibonacci levels (0.618, 1.272, 1.618)

## 🌐 Deployment (AWS)

### Server Specifications

**Option 1**: t3.medium (4 vCPU, 16GB RAM) - $245/month
**Option 2**: g4dn.xlarge (NVIDIA T4 GPU) - $380/month (for LLaMA)

### Nginx Configuration

```nginx
server {
    listen 443 ssl;
    server_name trendy.storydot.kr;

    location /trading/ {
        proxy_pass http://localhost:3000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### Docker Setup

```bash
# Build
docker build -t trading-bot-frontend .

# Run
docker run -d -p 3000:3000 --env-file .env.local trading-bot-frontend
```

## 📄 License

Proprietary - All rights reserved © 2025

## ⚠️ Risk Disclaimer

**IMPORTANT**: Cryptocurrency trading involves substantial risk of loss. This software is provided for educational purposes only. Users are solely responsible for their trading decisions and must:

- Understand the risks of leveraged trading
- Never invest more than they can afford to lose
- Conduct their own research and due diligence
- Comply with local regulations

Past performance does not guarantee future results. The developers assume no liability for financial losses.
