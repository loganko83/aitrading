# TradingBot AI - Development TODO List

## 📋 Project Overview
B2C cryptocurrency trading bot service with Triple AI Ensemble system (ML Models + GPT-4 + LLaMA 3.1) for Binance Futures trading.

**Target Deployment**: https://trendy.storydot.kr/trading
**Development Server**: http://localhost:3000
**Tech Stack**: Next.js 14, TypeScript, TailwindCSS, shadcn/ui, Zustand, NextAuth.js

---

## ✅ Completed Tasks

### Phase 1: Project Setup (100% Complete)
- [x] Initialize Next.js 14 project with TypeScript and TailwindCSS
- [x] Install core dependencies (shadcn/ui, Zustand, React Hook Form, Zod)
- [x] Set up project structure (app routes, components, lib, types)
- [x] Configure environment variables (.env.local)
- [x] Install 12 shadcn/ui components
- [x] Create comprehensive TypeScript type definitions

### Phase 2: Landing & Authentication (100% Complete)
- [x] Create landing page with service introduction
  - Hero section with stats cards
  - Features grid (6 cards)
  - How It Works section (4 steps)
  - CTA section and footer
- [x] Implement authentication system (NextAuth.js)
  - Credentials provider setup
  - JWT session strategy
  - Login page with form validation
  - Signup page with password confirmation
- [x] Implement Google OTP 2FA system
  - OTP secret generation (speakeasy)
  - QR code display for Google Authenticator
  - 6-digit code verification
  - Optional 2FA during signup
- [x] Create custom authentication middleware
  - Route protection for dashboard/settings/etc.
  - JWT token verification
  - Auto-redirect logic

### Phase 3: Dashboard (100% Complete)
- [x] Build protected route layout
  - Sidebar navigation with 5 sections
  - Top navbar with user profile
  - XP points and level display
  - Logout functionality
- [x] Create dashboard page
  - 4 stats widgets (Balance, PnL, Win Rate)
  - Auto-trading toggle with live status
  - Active positions display (3 sample positions)
  - Recent activity timeline
- [x] Build position monitoring components
  - Position cards with full details
  - Entry/current price comparison
  - Stop-loss and take-profit levels
  - Unrealized PnL (color-coded)
  - Close position button
- [x] Integrate Zustand state management
  - Trading store (positions, stats, auto-trading)
  - Auth store (user session, XP updates)
  - Persistent storage with local storage

### Phase 4: API Key Management (100% Complete)
- [x] Implement AES-256-GCM encryption library
  - PBKDF2 key derivation (100K iterations)
  - Random salt and IV generation
  - Authentication tags for tamper detection
  - Helper functions (encrypt, decrypt, mask, validate)
- [x] Create API key CRUD endpoints
  - GET /api/keys - Retrieve encrypted keys
  - POST /api/keys - Save encrypted keys
  - DELETE /api/keys - Remove keys
  - Format validation (64 alphanumeric)
- [x] Build Binance API verification endpoint
  - POST /api/keys/verify
  - HMAC-SHA256 signature creation
  - Test connection to Binance Futures
  - Return account balance and permissions
- [x] Design API key management page
  - Setup instructions with external links
  - API key/secret input forms
  - Show/hide toggles for sensitive data
  - Verify connection button
  - Account info display (balance, permissions)
  - Security best practices section

---

## 🚧 In Progress

### Phase 5: Trading Settings (0% Complete)
**Priority**: HIGH
**Estimated Time**: 2-3 hours

**Requirements**:
- [ ] Create `/settings` page with form layout
- [ ] Implement risk tolerance presets
  - Low: 5% position size, 3x leverage
  - Medium: 10% position size, 5x leverage
  - High: 15% position size, 5x leverage
- [ ] Build multi-select coin selector
  - BTC/USDT, ETH/USDT, BNB/USDT, SOL/USDT
  - Visual badges for selected coins
- [ ] Add leverage slider (1x-5x)
- [ ] Position size percentage input (5-20%)
- [ ] ATR multiplier controls
  - Stop-loss multiplier (default: 1.2)
  - Take-profit multiplier (default: 2.5)
- [ ] Create API endpoint: POST /api/settings
- [ ] Form validation with Zod schema
- [ ] Save/update functionality
- [ ] Default settings initialization

**Technical Details**:
```typescript
interface TradingSettings {
  user_id: string;
  risk_tolerance: 'low' | 'medium' | 'high';
  selected_coins: Array<'BTC/USDT' | 'ETH/USDT' | 'BNB/USDT' | 'SOL/USDT'>;
  leverage: number; // 1-5
  position_size_percent: number; // 5-20
  stop_loss_atr_multiplier: number; // default 1.2
  take_profit_atr_multiplier: number; // default 2.5
  auto_close_on_reversal: boolean; // default true
}
```

---

## 📝 Pending Tasks

### Phase 6: Leaderboard & Gamification (0% Complete)
**Priority**: MEDIUM
**Estimated Time**: 2-3 hours

- [ ] Create `/leaderboard` page
- [ ] Design ranking table component
  - Columns: Rank, User, Level, XP, Win Rate, Total PnL
  - Sorting functionality (by PnL, XP, Win Rate)
- [ ] Implement XP calculation system
  - +50 XP per winning trade
  - +100 XP per 10% profit
  - Bonus XP for win streaks
- [ ] Build level progression system
  - Level = floor(XP / 1000) + 1
  - Level badges and titles
- [ ] Create user profile cards
  - Avatar with initials
  - Level badge
  - Win rate chart
  - Total trades count
- [ ] Add API endpoint: GET /api/leaderboard
- [ ] Implement pagination (20 users per page)
- [ ] Highlight current user in leaderboard

**Gamification Features**:
- Badges: First Trade, 10 Wins, $1000 Profit, etc.
- Titles: Novice Trader → Pro Trader → Master Trader
- Achievement notifications

### Phase 7: Webhook Integration (0% Complete)
**Priority**: MEDIUM
**Estimated Time**: 3-4 hours

- [ ] Create `/webhooks` page
- [ ] Implement webhook URL generation
  - Format: `https://trendy.storydot.kr/trading/api/webhooks/{user_id}/{webhook_id}`
  - UUID-based webhook IDs
- [ ] Build webhook configuration form
  - Webhook name/description
  - Enable/disable toggle
  - Signal source (TradingView, custom)
- [ ] Create webhook signature verification
  - HMAC-SHA256 signature
  - Secret key management
- [ ] Implement webhook signal parser
  - JSON payload parsing
  - Signal validation (BUY/SELL, symbol, price)
- [ ] Add API endpoints:
  - POST /api/webhooks - Create webhook
  - GET /api/webhooks - List user webhooks
  - DELETE /api/webhooks/:id - Delete webhook
  - POST /api/webhooks/:id/test - Test webhook
  - POST /api/webhooks/receive/:user_id/:webhook_id - Receive signals
- [ ] Build webhook testing interface
  - Send test signal button
  - Display received signals log
- [ ] Create TradingView alert template
  - JSON format example
  - Setup instructions

**Webhook Payload Format**:
```json
{
  "action": "BUY" | "SELL" | "CLOSE",
  "symbol": "BTC/USDT",
  "price": 43500,
  "timestamp": 1234567890,
  "signature": "hmac_sha256_hash"
}
```

### Phase 8: TradingView Charts Integration (0% Complete)
**Priority**: HIGH
**Estimated Time**: 3-4 hours

- [ ] Install TradingView Lightweight Charts library
  - `npm install lightweight-charts`
- [ ] Create chart component wrapper
  - Candlestick chart display
  - Responsive container
- [ ] Implement real-time price data feed
  - WebSocket connection to Binance
  - Price update every second
- [ ] Add multi-timeframe selector
  - Buttons: 1m, 15m, 30m, 1h, 4h, 1d
  - Historical data loading
- [ ] Display technical indicators
  - EMA (12, 26, 50, 200)
  - RSI (14)
  - MACD
  - Bollinger Bands
  - Volume bars
- [ ] Add position markers on chart
  - Entry price line (blue)
  - Stop-loss line (red)
  - Take-profit line (green)
  - Current price crosshair
- [ ] Integrate into dashboard
  - Chart section below stats widgets
  - Symbol selector dropdown
  - Full-screen toggle button

### Phase 9: Backend API Development (0% Complete)
**Priority**: CRITICAL
**Estimated Time**: 1-2 weeks

#### Database Setup
- [ ] Install PostgreSQL database
- [ ] Create database schema with Prisma
  - Users table
  - API keys table
  - Trading settings table
  - Positions table
  - Trades history table
  - Webhooks table
  - XP transactions table
- [ ] Set up database migrations
- [ ] Create seed data for development

#### FastAPI Backend
- [ ] Initialize FastAPI project
- [ ] Set up project structure
  - `/app/api/` - API endpoints
  - `/app/services/` - Business logic
  - `/app/models/` - Database models
  - `/app/ai/` - AI models
- [ ] Implement Binance Futures integration
  - Market data fetching
  - Order placement (LONG/SHORT)
  - Position monitoring
  - Order cancellation
- [ ] Build Triple AI Ensemble system
  - **ML Models** (40% weight):
    - LSTM for time series prediction
    - Transformer for pattern recognition
    - LightGBM for feature importance
  - **GPT-4 API** (25% weight):
    - Market sentiment analysis
    - News impact assessment
  - **Meta LLaMA 3.1** (25% weight):
    - Technical analysis reasoning
    - Risk assessment
  - **Technical Analysis Rules** (10% weight):
    - Elliott Wave detection
    - Fibonacci levels
    - Multi-indicator confluence
- [ ] Create probability calculation system
  - `P_up_final = 0.4*ML + 0.25*GPT + 0.25*LLaMA + 0.1*TA`
  - Confidence scoring
  - Model agreement calculation
- [ ] Implement entry logic
  - Condition: Probability ≥ 80% AND Confidence ≥ 70% AND Agreement ≥ 70%
  - Position sizing: 10% of equity
  - Leverage: 5x (configurable)
- [ ] Build exit logic
  - Stop-loss: Entry ± ATR × 1.2
  - Take-profit: Entry ± ATR × 2.5
  - Wrong prediction exit (probability reversal)
- [ ] Create WebSocket service
  - Real-time price updates
  - Position updates broadcast
  - PnL calculations
- [ ] Implement background workers
  - Market monitoring task (continuous)
  - Position management task (every 5 seconds)
  - AI analysis task (every 30 seconds)
  - Database cleanup task (daily)

#### API Endpoints (Backend)
- [ ] POST /api/trading/start - Start auto-trading
- [ ] POST /api/trading/stop - Stop auto-trading
- [ ] GET /api/trading/status - Get trading status
- [ ] POST /api/positions/open - Open position manually
- [ ] POST /api/positions/:id/close - Close position
- [ ] GET /api/positions/active - Get active positions
- [ ] GET /api/trades/history - Get trade history
- [ ] GET /api/analysis/current - Get current AI analysis
- [ ] POST /api/webhooks/signal - Receive webhook signal

### Phase 10: Deployment & DevOps (0% Complete)
**Priority**: HIGH
**Estimated Time**: 1-2 days

#### Docker Configuration
- [ ] Create Dockerfile for Next.js frontend
  - Multi-stage build
  - Optimized production image
- [ ] Create Dockerfile for FastAPI backend
  - Python 3.11 base image
  - Dependencies installation
- [ ] Create docker-compose.yml
  - Frontend service
  - Backend service
  - PostgreSQL service
  - Redis service (for caching)
  - Nginx service

#### AWS Deployment
- [ ] Set up AWS EC2 instance
  - Instance type: t3.medium or larger
  - Ubuntu 22.04 LTS
- [ ] Configure security groups
  - Port 80 (HTTP)
  - Port 443 (HTTPS)
  - Port 22 (SSH)
- [ ] Install Docker and Docker Compose
- [ ] Clone repository to server
- [ ] Set up environment variables
- [ ] Configure Nginx reverse proxy
  - Frontend: /trading
  - Backend: /trading/api
  - WebSocket: /trading/ws
  - SSL certificate (Let's Encrypt)
- [ ] Set up CI/CD pipeline
  - GitHub Actions workflow
  - Automatic deployment on push to main
  - Database migration automation
- [ ] Configure monitoring
  - PM2 for process management
  - Log aggregation
  - Error tracking (Sentry)
  - Uptime monitoring

#### Nginx Configuration
```nginx
location /trading {
    proxy_pass http://frontend:3000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}

location /trading/api {
    proxy_pass http://backend:8000;
    proxy_set_header Host $host;
}

location /trading/ws {
    proxy_pass http://backend:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

---

## 🔧 Technical Debt & Improvements

### Code Quality
- [ ] Replace mock data with real API calls
- [ ] Implement proper error boundaries
- [ ] Add loading skeletons for better UX
- [ ] Implement optimistic UI updates
- [ ] Add unit tests (Jest + React Testing Library)
- [ ] Add integration tests (Playwright)
- [ ] Set up E2E testing

### Security Enhancements
- [ ] Implement rate limiting on API endpoints
- [ ] Add CSRF protection
- [ ] Set up API request signing
- [ ] Implement refresh token rotation
- [ ] Add audit logging for sensitive operations
- [ ] Set up intrusion detection

### Performance Optimization
- [ ] Implement Redis caching
- [ ] Add database query optimization
- [ ] Set up CDN for static assets
- [ ] Implement code splitting
- [ ] Add service worker for offline support
- [ ] Optimize bundle size

### Monitoring & Analytics
- [ ] Set up application monitoring (DataDog/New Relic)
- [ ] Implement user analytics (Google Analytics)
- [ ] Add performance monitoring (Lighthouse CI)
- [ ] Set up error tracking (Sentry)
- [ ] Create admin dashboard for system health

---

## 📊 Database Schema (Prisma)

```prisma
model User {
  id                 String    @id @default(uuid())
  email              String    @unique
  name               String
  password           String
  google_otp_enabled Boolean   @default(false)
  google_otp_secret  String?
  xp_points          Int       @default(0)
  level              Int       @default(1)
  created_at         DateTime  @default(now())
  last_login         DateTime?

  apiKeys            ApiKeys?
  settings           TradingSettings?
  positions          Position[]
  trades             Trade[]
  webhooks           Webhook[]
  xp_transactions    XPTransaction[]
}

model ApiKeys {
  id                   String    @id @default(uuid())
  user_id              String    @unique
  encrypted_api_key    String
  encrypted_api_secret String
  is_active            Boolean   @default(true)
  last_verified        DateTime?
  created_at           DateTime  @default(now())
  updated_at           DateTime  @updatedAt

  user                 User      @relation(fields: [user_id], references: [id], onDelete: Cascade)
}

model TradingSettings {
  id                        String   @id @default(uuid())
  user_id                   String   @unique
  risk_tolerance            String   @default("medium")
  selected_coins            String[] @default(["BTC/USDT", "ETH/USDT"])
  leverage                  Int      @default(5)
  position_size_percent     Float    @default(10.0)
  stop_loss_atr_multiplier  Float    @default(1.2)
  take_profit_atr_multiplier Float   @default(2.5)
  auto_close_on_reversal    Boolean  @default(true)
  is_auto_trading           Boolean  @default(false)
  created_at                DateTime @default(now())
  updated_at                DateTime @updatedAt

  user                      User     @relation(fields: [user_id], references: [id], onDelete: Cascade)
}

model Position {
  id                String   @id @default(uuid())
  user_id           String
  symbol            String
  side              String
  quantity          Float
  entry_price       Float
  current_price     Float
  stop_loss         Float?
  take_profit       Float?
  leverage          Int
  unrealized_pnl    Float    @default(0)
  status            String   @default("OPEN")
  ai_confidence     Float
  opened_at         DateTime @default(now())
  closed_at         DateTime?

  user              User     @relation(fields: [user_id], references: [id], onDelete: Cascade)
  trades            Trade[]
}

model Trade {
  id             String   @id @default(uuid())
  user_id        String
  position_id    String
  symbol         String
  side           String
  entry_price    Float
  exit_price     Float?
  quantity       Float
  realized_pnl   Float    @default(0)
  commission     Float    @default(0)
  status         String   @default("OPEN")
  opened_at      DateTime @default(now())
  closed_at      DateTime?

  user           User     @relation(fields: [user_id], references: [id], onDelete: Cascade)
  position       Position @relation(fields: [position_id], references: [id])
}

model Webhook {
  id             String   @id @default(uuid())
  user_id        String
  webhook_id     String   @unique
  name           String
  description    String?
  secret_key     String
  is_active      Boolean  @default(true)
  last_triggered DateTime?
  created_at     DateTime @default(now())

  user           User     @relation(fields: [user_id], references: [id], onDelete: Cascade)
}

model XPTransaction {
  id             String   @id @default(uuid())
  user_id        String
  amount         Int
  reason         String
  created_at     DateTime @default(now())

  user           User     @relation(fields: [user_id], references: [id], onDelete: Cascade)
}
```

---

## 🎯 Success Metrics

### Technical Metrics
- [ ] Frontend bundle size < 500KB
- [ ] API response time < 200ms
- [ ] Database query time < 50ms
- [ ] WebSocket latency < 100ms
- [ ] Uptime > 99.9%
- [ ] Test coverage > 80%

### Business Metrics
- [ ] User signup conversion > 10%
- [ ] Active users (DAU/MAU ratio) > 30%
- [ ] Average session duration > 15 minutes
- [ ] Win rate accuracy > 65%
- [ ] User retention (30-day) > 40%

---

## 📚 Documentation Needed

- [ ] API documentation (Swagger/OpenAPI)
- [ ] User guide (how to use the platform)
- [ ] Developer guide (how to contribute)
- [ ] Deployment guide (infrastructure setup)
- [ ] Security audit report
- [ ] Performance benchmarking report

---

## 🔐 Environment Variables Checklist

### Frontend (.env.local)
```env
DATABASE_URL="postgresql://user:password@localhost:5432/trading_bot"
NEXTAUTH_URL="https://trendy.storydot.kr/trading"
NEXTAUTH_SECRET="your-nextauth-secret-key-change-this-in-production"
OPENAI_API_KEY="sk-..."
ENCRYPTION_KEY="your-32-character-encryption-key-change-this"
NEXT_PUBLIC_APP_URL="https://trendy.storydot.kr/trading"
NEXT_PUBLIC_WS_URL="wss://trendy.storydot.kr/trading/ws"
```

### Backend (.env)
```env
DATABASE_URL="postgresql://user:password@localhost:5432/trading_bot"
BINANCE_API_URL="https://fapi.binance.com"
OPENAI_API_KEY="sk-..."
LLAMA_API_URL="http://localhost:8080"
REDIS_URL="redis://localhost:6379"
JWT_SECRET="your-jwt-secret"
ENCRYPTION_KEY="your-32-character-encryption-key"
```

---

## 📞 Support & Resources

- **Next.js Documentation**: https://nextjs.org/docs
- **shadcn/ui Components**: https://ui.shadcn.com/
- **Binance Futures API**: https://binance-docs.github.io/apidocs/futures/en/
- **TradingView Lightweight Charts**: https://www.tradingview.com/lightweight-charts/
- **NextAuth.js**: https://next-auth.js.org/
- **Prisma ORM**: https://www.prisma.io/docs
- **FastAPI**: https://fastapi.tiangolo.com/

---

## 🎉 Project Status Summary

**Overall Progress**: 35% Complete (7/20 major features)

### Completed (7/20) ✅
1. Project setup and configuration
2. Landing page design
3. Authentication system (NextAuth + 2FA)
4. Dashboard with position monitoring
5. API key management with encryption
6. Protected route middleware
7. State management (Zustand)

### In Progress (1/20) 🚧
8. Trading settings form

### Pending (12/20) 📝
9. Leaderboard & gamification
10. Webhook integration
11. TradingView charts
12. Backend API (FastAPI)
13. Database setup (PostgreSQL)
14. Triple AI Ensemble system
15. Binance Futures integration
16. WebSocket service
17. Background workers
18. Docker configuration
19. AWS deployment
20. CI/CD pipeline

**Next Milestone**: Complete Phase 5 (Trading Settings) by implementing user-configurable trading parameters.

**Estimated Time to MVP**: 3-4 weeks
**Estimated Time to Production**: 5-6 weeks
