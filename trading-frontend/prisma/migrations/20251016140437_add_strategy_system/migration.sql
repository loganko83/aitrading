-- CreateTable
CREATE TABLE "User" (
    "id" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "name" TEXT,
    "password" TEXT,
    "image" TEXT,
    "emailVerified" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "totalXp" INTEGER NOT NULL DEFAULT 0,
    "level" INTEGER NOT NULL DEFAULT 1,
    "totalTrades" INTEGER NOT NULL DEFAULT 0,
    "totalWins" INTEGER NOT NULL DEFAULT 0,
    "totalLosses" INTEGER NOT NULL DEFAULT 0,
    "totalPnl" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "winStreak" INTEGER NOT NULL DEFAULT 0,
    "badges" TEXT[] DEFAULT ARRAY[]::TEXT[],

    CONSTRAINT "User_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Account" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "type" TEXT NOT NULL,
    "provider" TEXT NOT NULL,
    "providerAccountId" TEXT NOT NULL,
    "refresh_token" TEXT,
    "access_token" TEXT,
    "expires_at" INTEGER,
    "token_type" TEXT,
    "scope" TEXT,
    "id_token" TEXT,
    "session_state" TEXT,

    CONSTRAINT "Account_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Session" (
    "id" TEXT NOT NULL,
    "sessionToken" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "expires" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Session_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "VerificationToken" (
    "identifier" TEXT NOT NULL,
    "token" TEXT NOT NULL,
    "expires" TIMESTAMP(3) NOT NULL
);

-- CreateTable
CREATE TABLE "ApiKey" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "exchange" TEXT NOT NULL DEFAULT 'binance',
    "apiKey" TEXT NOT NULL,
    "apiSecret" TEXT NOT NULL,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "ApiKey_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "TradingSettings" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "riskTolerance" TEXT NOT NULL DEFAULT 'medium',
    "selectedCoins" TEXT[] DEFAULT ARRAY['BTC/USDT']::TEXT[],
    "leverage" INTEGER NOT NULL DEFAULT 3,
    "positionSizePct" DOUBLE PRECISION NOT NULL DEFAULT 0.10,
    "stopLossAtrMultiplier" DOUBLE PRECISION NOT NULL DEFAULT 2.0,
    "takeProfitAtrMultiplier" DOUBLE PRECISION NOT NULL DEFAULT 3.0,
    "autoCloseOnReversal" BOOLEAN NOT NULL DEFAULT true,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "TradingSettings_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Position" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "symbol" TEXT NOT NULL,
    "side" TEXT NOT NULL,
    "quantity" DOUBLE PRECISION NOT NULL,
    "entryPrice" DOUBLE PRECISION NOT NULL,
    "currentPrice" DOUBLE PRECISION NOT NULL,
    "stopLoss" DOUBLE PRECISION NOT NULL,
    "takeProfit" DOUBLE PRECISION NOT NULL,
    "leverage" INTEGER NOT NULL,
    "unrealizedPnl" DOUBLE PRECISION NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'OPEN',
    "aiConfidence" DOUBLE PRECISION,
    "aiReason" TEXT,
    "openedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "closedAt" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Position_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Trade" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "symbol" TEXT NOT NULL,
    "side" TEXT NOT NULL,
    "quantity" DOUBLE PRECISION NOT NULL,
    "entryPrice" DOUBLE PRECISION NOT NULL,
    "exitPrice" DOUBLE PRECISION NOT NULL,
    "stopLoss" DOUBLE PRECISION NOT NULL,
    "takeProfit" DOUBLE PRECISION NOT NULL,
    "leverage" INTEGER NOT NULL,
    "realizedPnl" DOUBLE PRECISION NOT NULL,
    "pnlPercent" DOUBLE PRECISION NOT NULL,
    "aiConfidence" DOUBLE PRECISION,
    "aiReason" TEXT,
    "exitReason" TEXT,
    "openedAt" TIMESTAMP(3) NOT NULL,
    "closedAt" TIMESTAMP(3) NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Trade_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Webhook" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "webhookUrl" TEXT NOT NULL,
    "secretToken" TEXT NOT NULL,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "totalTriggers" INTEGER NOT NULL DEFAULT 0,
    "lastTriggered" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Webhook_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "XpTransaction" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "amount" INTEGER NOT NULL,
    "reason" TEXT NOT NULL,
    "description" TEXT,
    "metadata" JSONB,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "XpTransaction_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Strategy" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "category" TEXT NOT NULL DEFAULT 'AI_ENSEMBLE',
    "isPublic" BOOLEAN NOT NULL DEFAULT true,
    "creatorId" TEXT,
    "mlWeight" DOUBLE PRECISION NOT NULL DEFAULT 0.40,
    "gpt4Weight" DOUBLE PRECISION NOT NULL DEFAULT 0.25,
    "claudeWeight" DOUBLE PRECISION NOT NULL DEFAULT 0.25,
    "taWeight" DOUBLE PRECISION NOT NULL DEFAULT 0.10,
    "minProbability" DOUBLE PRECISION NOT NULL DEFAULT 0.80,
    "minConfidence" DOUBLE PRECISION NOT NULL DEFAULT 0.70,
    "minAgreement" DOUBLE PRECISION NOT NULL DEFAULT 0.70,
    "defaultLeverage" INTEGER NOT NULL DEFAULT 3,
    "positionSizePct" DOUBLE PRECISION NOT NULL DEFAULT 0.10,
    "slAtrMultiplier" DOUBLE PRECISION NOT NULL DEFAULT 2.0,
    "tpAtrMultiplier" DOUBLE PRECISION NOT NULL DEFAULT 3.0,
    "maxOpenPositions" INTEGER NOT NULL DEFAULT 3,
    "atrPeriod" INTEGER NOT NULL DEFAULT 14,
    "rsiPeriod" INTEGER NOT NULL DEFAULT 14,
    "macdFast" INTEGER NOT NULL DEFAULT 12,
    "macdSlow" INTEGER NOT NULL DEFAULT 26,
    "macdSignal" INTEGER NOT NULL DEFAULT 9,
    "usageCount" INTEGER NOT NULL DEFAULT 0,
    "avgWinRate" DOUBLE PRECISION,
    "avgPnl" DOUBLE PRECISION,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "Strategy_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "StrategyConfig" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "strategyId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "isActive" BOOLEAN NOT NULL DEFAULT false,
    "customParams" JSONB,
    "totalTrades" INTEGER NOT NULL DEFAULT 0,
    "winRate" DOUBLE PRECISION,
    "totalPnl" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "maxDrawdown" DOUBLE PRECISION,
    "sharpeRatio" DOUBLE PRECISION,
    "autoTradeEnabled" BOOLEAN NOT NULL DEFAULT false,
    "selectedSymbols" TEXT[] DEFAULT ARRAY['BTCUSDT']::TEXT[],
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "lastUsedAt" TIMESTAMP(3),

    CONSTRAINT "StrategyConfig_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "BacktestResult" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "strategyId" TEXT NOT NULL,
    "symbol" TEXT NOT NULL,
    "interval" TEXT NOT NULL,
    "startDate" TIMESTAMP(3) NOT NULL,
    "endDate" TIMESTAMP(3) NOT NULL,
    "initialCapital" DOUBLE PRECISION NOT NULL DEFAULT 10000,
    "totalTrades" INTEGER NOT NULL,
    "winningTrades" INTEGER NOT NULL,
    "losingTrades" INTEGER NOT NULL,
    "winRate" DOUBLE PRECISION NOT NULL,
    "totalPnl" DOUBLE PRECISION NOT NULL,
    "totalPnlPct" DOUBLE PRECISION NOT NULL,
    "maxDrawdown" DOUBLE PRECISION NOT NULL,
    "maxDrawdownPct" DOUBLE PRECISION NOT NULL,
    "sharpeRatio" DOUBLE PRECISION,
    "sortinoRatio" DOUBLE PRECISION,
    "profitFactor" DOUBLE PRECISION,
    "avgWinPnl" DOUBLE PRECISION,
    "avgLossPnl" DOUBLE PRECISION,
    "largestWin" DOUBLE PRECISION,
    "largestLoss" DOUBLE PRECISION,
    "trades" JSONB NOT NULL,
    "equityCurve" JSONB NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "BacktestResult_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "User_email_key" ON "User"("email");

-- CreateIndex
CREATE INDEX "User_email_idx" ON "User"("email");

-- CreateIndex
CREATE INDEX "Account_userId_idx" ON "Account"("userId");

-- CreateIndex
CREATE UNIQUE INDEX "Account_provider_providerAccountId_key" ON "Account"("provider", "providerAccountId");

-- CreateIndex
CREATE UNIQUE INDEX "Session_sessionToken_key" ON "Session"("sessionToken");

-- CreateIndex
CREATE INDEX "Session_userId_idx" ON "Session"("userId");

-- CreateIndex
CREATE UNIQUE INDEX "VerificationToken_token_key" ON "VerificationToken"("token");

-- CreateIndex
CREATE UNIQUE INDEX "VerificationToken_identifier_token_key" ON "VerificationToken"("identifier", "token");

-- CreateIndex
CREATE INDEX "ApiKey_userId_idx" ON "ApiKey"("userId");

-- CreateIndex
CREATE UNIQUE INDEX "TradingSettings_userId_key" ON "TradingSettings"("userId");

-- CreateIndex
CREATE INDEX "TradingSettings_userId_idx" ON "TradingSettings"("userId");

-- CreateIndex
CREATE INDEX "Position_userId_idx" ON "Position"("userId");

-- CreateIndex
CREATE INDEX "Position_symbol_idx" ON "Position"("symbol");

-- CreateIndex
CREATE INDEX "Position_status_idx" ON "Position"("status");

-- CreateIndex
CREATE INDEX "Trade_userId_idx" ON "Trade"("userId");

-- CreateIndex
CREATE INDEX "Trade_symbol_idx" ON "Trade"("symbol");

-- CreateIndex
CREATE INDEX "Trade_closedAt_idx" ON "Trade"("closedAt");

-- CreateIndex
CREATE UNIQUE INDEX "Webhook_webhookUrl_key" ON "Webhook"("webhookUrl");

-- CreateIndex
CREATE INDEX "Webhook_userId_idx" ON "Webhook"("userId");

-- CreateIndex
CREATE INDEX "Webhook_webhookUrl_idx" ON "Webhook"("webhookUrl");

-- CreateIndex
CREATE INDEX "XpTransaction_userId_idx" ON "XpTransaction"("userId");

-- CreateIndex
CREATE INDEX "XpTransaction_createdAt_idx" ON "XpTransaction"("createdAt");

-- CreateIndex
CREATE INDEX "Strategy_category_idx" ON "Strategy"("category");

-- CreateIndex
CREATE INDEX "Strategy_isPublic_idx" ON "Strategy"("isPublic");

-- CreateIndex
CREATE INDEX "Strategy_creatorId_idx" ON "Strategy"("creatorId");

-- CreateIndex
CREATE INDEX "StrategyConfig_userId_idx" ON "StrategyConfig"("userId");

-- CreateIndex
CREATE INDEX "StrategyConfig_strategyId_idx" ON "StrategyConfig"("strategyId");

-- CreateIndex
CREATE INDEX "StrategyConfig_isActive_idx" ON "StrategyConfig"("isActive");

-- CreateIndex
CREATE UNIQUE INDEX "StrategyConfig_userId_strategyId_key" ON "StrategyConfig"("userId", "strategyId");

-- CreateIndex
CREATE INDEX "BacktestResult_userId_idx" ON "BacktestResult"("userId");

-- CreateIndex
CREATE INDEX "BacktestResult_strategyId_idx" ON "BacktestResult"("strategyId");

-- CreateIndex
CREATE INDEX "BacktestResult_symbol_idx" ON "BacktestResult"("symbol");

-- CreateIndex
CREATE INDEX "BacktestResult_createdAt_idx" ON "BacktestResult"("createdAt");

-- AddForeignKey
ALTER TABLE "Account" ADD CONSTRAINT "Account_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Session" ADD CONSTRAINT "Session_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ApiKey" ADD CONSTRAINT "ApiKey_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "TradingSettings" ADD CONSTRAINT "TradingSettings_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Position" ADD CONSTRAINT "Position_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Trade" ADD CONSTRAINT "Trade_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Webhook" ADD CONSTRAINT "Webhook_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "XpTransaction" ADD CONSTRAINT "XpTransaction_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "StrategyConfig" ADD CONSTRAINT "StrategyConfig_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "StrategyConfig" ADD CONSTRAINT "StrategyConfig_strategyId_fkey" FOREIGN KEY ("strategyId") REFERENCES "Strategy"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "BacktestResult" ADD CONSTRAINT "BacktestResult_strategyId_fkey" FOREIGN KEY ("strategyId") REFERENCES "Strategy"("id") ON DELETE CASCADE ON UPDATE CASCADE;
