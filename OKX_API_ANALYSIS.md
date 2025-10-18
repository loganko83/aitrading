# 📊 OKX API v5 Complete Analysis & Comparison with Binance

Comprehensive analysis of OKX API documentation and comparison with Binance for TradingBot AI integration.

## 🎯 Overview

**OKX API Version:** v5 (Latest)
**Documentation:** https://www.okx.com/docs-v5/en/
**Supported Products:** Spot, Margin, Futures, Perpetual Swap, Options

---

## 🔧 API Infrastructure

### **Base Endpoints**

| Service | URL | Purpose |
|---------|-----|---------|
| **REST API** | `https://www.okx.com` | Trading, account management |
| **Public WebSocket** | `wss://ws.okx.com:8443/ws/v5/public` | Market data streams |
| **Private WebSocket** | `wss://ws.okx.com:8443/ws/v5/private` | Account, position, order updates |

**Demo Trading (Testnet):**
- REST: `https://www.okx.com` (same as production)
- Uses demo trading account with separate API keys

---

## 🔐 Authentication System

### **Required Headers**

| Header | Description | Example |
|--------|-------------|---------|
| `OK-ACCESS-KEY` | API Key | `93975967-ed47-4070-a436-329e22e14a1b` |
| `OK-ACCESS-SIGN` | HMAC SHA256 signature | Base64 encoded |
| `OK-ACCESS-TIMESTAMP` | ISO 8601 timestamp | `2024-01-18T12:00:00.000Z` |
| `OK-ACCESS-PASSPHRASE` | API passphrase | User-defined string |

### **Signature Generation**

```python
import hmac
import base64
from datetime import datetime

# Signature = Base64(HMAC-SHA256(timestamp + method + requestPath + body, secretKey))
timestamp = datetime.utcnow().isoformat() + 'Z'
method = 'POST'
request_path = '/api/v5/trade/order'
body = '{"instId":"BTC-USDT-SWAP","tdMode":"cross","side":"buy","ordType":"market","sz":"1"}'

message = timestamp + method + request_path + body
signature = base64.b64encode(
    hmac.new(secret_key.encode(), message.encode(), 'sha256').digest()
).decode()
```

**Key Difference from Binance:**
- OKX requires **passphrase** (additional security layer)
- Timestamp format: **ISO 8601** (Binance uses milliseconds)
- Signature includes: timestamp + method + path + body

---

## 📈 Trading API

### **Place Order Endpoint**

**Unified Endpoint:** `POST /api/v5/trade/order`

**Key Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `instId` | String | ✅ | Instrument ID (e.g., `BTC-USDT-SWAP`) |
| `tdMode` | String | ✅ | Trade mode: `cash`, `cross`, `isolated` |
| `side` | String | ✅ | `buy` or `sell` |
| `ordType` | String | ✅ | `market`, `limit`, `post_only`, `fok`, `ioc` |
| `sz` | String | ✅ | Order size (contracts for futures/swap) |
| `px` | String | Conditional | Price (required for limit orders) |
| `posSide` | String | Optional | `long`, `short`, `net` |
| `tdMode` | String | ✅ | `cross` or `isolated` |

### **Order Types**

| Type | Description | Use Case |
|------|-------------|----------|
| `market` | Market order | Immediate execution |
| `limit` | Limit order | Specific price |
| `post_only` | Maker-only limit | Ensure maker fee |
| `fok` | Fill or Kill | All or nothing |
| `ioc` | Immediate or Cancel | Fill available, cancel rest |

### **Example Request**

```json
{
  "instId": "BTC-USDT-SWAP",
  "tdMode": "cross",
  "side": "buy",
  "ordType": "market",
  "sz": "1",
  "posSide": "long"
}
```

### **Example Response**

```json
{
  "code": "0",
  "msg": "",
  "data": [
    {
      "ordId": "312269865356374016",
      "clOrdId": "",
      "tag": "",
      "sCode": "0",
      "sMsg": ""
    }
  ]
}
```

---

## 💰 Account & Balance API

### **Get Balance**

**Endpoint:** `GET /api/v5/account/balance`

**Response Fields:**

| Field | Description |
|-------|-------------|
| `totalEq` | Total equity (USD) |
| `isoEq` | Isolated margin equity |
| `adjEq` | Adjusted equity |
| `ordFroz` | Margin frozen for orders |
| `imr` | Initial margin requirement |
| `mmr` | Maintenance margin requirement |
| `mgnRatio` | Margin ratio |
| `notionalUsd` | Notional value in USD |

**Example Response:**

```json
{
  "code": "0",
  "data": [
    {
      "uTime": "1597026383085",
      "totalEq": "41624.32",
      "isoEq": "0",
      "adjEq": "41624.32",
      "ordFroz": "0",
      "imr": "3372.02",
      "mmr": "672.40",
      "mgnRatio": "12.35",
      "details": [
        {
          "ccy": "USDT",
          "eq": "41624.32",
          "availEq": "38252.30",
          "upl": "0"
        }
      ]
    }
  ]
}
```

---

## 📊 Position Management

### **Get Positions**

**Endpoint:** `GET /api/v5/account/positions`

**Response Fields:**

| Field | Description |
|-------|-------------|
| `instId` | Instrument ID |
| `pos` | Position quantity |
| `posSide` | `long`, `short`, or `net` |
| `avgPx` | Average entry price |
| `upl` | Unrealized P&L |
| `uplRatio` | Unrealized P&L ratio |
| `liqPx` | Estimated liquidation price |
| `lever` | Leverage |
| `mgnMode` | `cross` or `isolated` |
| `margin` | Margin for position |
| `imr` | Initial margin requirement |
| `mmr` | Maintenance margin requirement |

### **Position Modes**

**1. Long/Short Mode**
- Separate long and short positions
- Hedging capability
- Both positions can exist simultaneously

**2. Net Mode**
- Single net position
- Long and short orders offset each other
- Simpler P&L calculation

---

## 🌐 WebSocket API

### **Connection Details**

| Feature | Value |
|---------|-------|
| **Public URL** | `wss://ws.okx.com:8443/ws/v5/public` |
| **Private URL** | `wss://ws.okx.com:8443/ws/v5/private` |
| **Connection Rate Limit** | 3 requests/second per IP |
| **Max Connections** | 30 per channel per sub-account |
| **Idle Timeout** | 30 seconds (no data push) |
| **Subscription Limit** | 480 subscribe/unsubscribe per hour per connection |

### **Ping/Pong Mechanism**

```json
// Client sends
"ping"

// Server responds
"pong"
```

**Recommendation:** Send ping every 20-25 seconds to maintain connection.

### **Channel Subscription Format**

```json
{
  "op": "subscribe",
  "args": [
    {
      "channel": "tickers",
      "instId": "BTC-USDT-SWAP"
    }
  ]
}
```

### **Available Public Channels**

| Channel | Description | Update Frequency |
|---------|-------------|------------------|
| `tickers` | 24h ticker | 100ms |
| `candle1m` | 1-minute candlestick | Real-time |
| `trades` | Recent trades | Real-time |
| `books` | Order book | 100ms |
| `bbo-tbt` | Best bid/offer | Tick-by-tick |

### **Available Private Channels**

| Channel | Description |
|---------|-------------|
| `account` | Account balance updates |
| `positions` | Position updates |
| `orders` | Order status changes |
| `algo-orders` | Algo order updates |

---

## ⚡ Rate Limits

### **REST API Limits**

| Endpoint Type | Limit | Window |
|---------------|-------|--------|
| **Instrument endpoints** | 20 requests | 2 seconds |
| **Balance endpoints** | 10 requests | 2 seconds |
| **Trading endpoints** | 60 requests | 2 seconds |
| **Order placement** | 60 orders | 2 seconds |

### **Sub-Account Limits**

| Performance Tier | Order Limit (2s) |
|------------------|------------------|
| Standard | 60 |
| Silver | 120 |
| Gold | 180 |
| Platinum | 240 |

---

## 🆚 OKX vs Binance Comparison

### **Architecture Comparison**

| Feature | OKX | Binance |
|---------|-----|---------|
| **API Version** | v5 (unified) | v3 (spot), v1 (futures) |
| **Endpoint Structure** | Unified across products | Separate per product |
| **Authentication** | 4 headers + passphrase | 2 headers (key + signature) |
| **Timestamp Format** | ISO 8601 | Unix milliseconds |
| **Signature Algorithm** | HMAC SHA256 | HMAC SHA256 or RSA |

### **Trading Features**

| Feature | OKX | Binance |
|---------|-----|---------|
| **Order Types** | 5 types | 7+ types |
| **Position Modes** | Long/Short, Net | Hedge, One-way |
| **Margin Modes** | Cross, Isolated, Cash | Cross, Isolated |
| **Max Leverage** | 125x | 125x |
| **Instrument Naming** | `BTC-USDT-SWAP` | `BTCUSDT` |

### **Rate Limiting**

| Exchange | REST Limit | WebSocket Connections |
|----------|------------|----------------------|
| **OKX** | 60 orders/2s | 30 per channel |
| **Binance** | IP-based (varies) | 1024 streams per connection |

### **WebSocket Features**

| Feature | OKX | Binance |
|---------|-----|---------|
| **Ping/Pong** | String-based ("ping") | Binary frame |
| **Connection Timeout** | 30 seconds | 24 hours |
| **Subscription Format** | JSON with args | Stream name format |
| **Private Channels** | Separate URL | Requires listenKey |

### **Account Management**

| Feature | OKX | Binance |
|---------|-----|---------|
| **Balance Structure** | Unified account | Separate futures account |
| **Margin Calculation** | IMR/MMR in response | Manual calculation |
| **Position API** | Dedicated endpoint | Part of account info |
| **Liquidation Price** | Provided in API | Manual calculation |

---

## 🎯 OKX Unique Features

### **1. Unified Account System**

OKX uses a **unified account** across all products:
- Single balance for Spot, Futures, Options
- Cross-margin sharing across products
- Simplified risk management

**vs Binance:** Separate accounts for Spot and Futures

### **2. Long/Short Position Mode**

Allows simultaneous long and short positions:
```json
{
  "positions": [
    {"posSide": "long", "pos": "10"},
    {"posSide": "short", "pos": "5"}
  ]
}
```

**Use Case:** Hedging strategies, grid trading

### **3. Portfolio Margin Mode**

Advanced margin calculation:
- Cross-product risk offsetting
- Lower margin requirements
- Institutional-grade risk model

### **4. Block Trading**

Request-for-Quote (RFQ) system:
- Large order execution
- Minimal market impact
- Institutional trading

### **5. Grid Trading API**

Built-in algo trading:
- Automated grid strategy
- No external bot needed
- API-controlled parameters

---

## 🔧 Integration Complexity Comparison

### **OKX Integration**

**Pros:**
- ✅ Unified API structure (easier to learn)
- ✅ Better documentation organization
- ✅ Liquidation price provided in API
- ✅ Margin calculations included
- ✅ Advanced position modes

**Cons:**
- ❌ Requires passphrase (extra security step)
- ❌ ISO timestamp format (different from Binance)
- ❌ Lower trading volume than Binance
- ❌ Fewer third-party libraries

### **Binance Integration**

**Pros:**
- ✅ Higher liquidity and volume
- ✅ More third-party libraries (`python-binance`)
- ✅ Simpler authentication (no passphrase)
- ✅ Better testnet availability

**Cons:**
- ❌ Separate APIs for Spot/Futures
- ❌ Manual margin calculations needed
- ❌ More complex rate limiting rules
- ❌ Less unified account structure

---

## 📊 Code Example Comparison

### **Place Market Order**

**OKX:**
```python
import okx.Trade as Trade

tradeAPI = Trade.TradeAPI(api_key, secret_key, passphrase, False, '0')

result = tradeAPI.place_order(
    instId="BTC-USDT-SWAP",
    tdMode="cross",
    side="buy",
    ordType="market",
    sz="1"
)
```

**Binance:**
```python
from binance.client import Client

client = Client(api_key, api_secret)

order = client.futures_create_order(
    symbol='BTCUSDT',
    side='BUY',
    type='MARKET',
    quantity=1
)
```

### **Get Account Balance**

**OKX:**
```python
accountAPI = Account.AccountAPI(api_key, secret_key, passphrase, False, '0')
result = accountAPI.get_account_balance()

total_equity = result['data'][0]['totalEq']
```

**Binance:**
```python
account = client.futures_account()
total_balance = account['totalWalletBalance']
```

---

## 💡 TradingBot AI Integration Recommendations

### **Multi-Exchange Architecture**

**Recommended Approach:**

```python
# Abstract exchange interface
class ExchangeInterface(ABC):
    @abstractmethod
    async def place_order(self, symbol, side, quantity, **kwargs): pass

    @abstractmethod
    async def get_balance(self): pass

    @abstractmethod
    async def get_positions(self): pass

# OKX implementation
class OKXClient(ExchangeInterface):
    def __init__(self, api_key, secret_key, passphrase):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase

    async def place_order(self, symbol, side, quantity, **kwargs):
        # OKX-specific implementation
        pass

# Binance implementation (existing)
class BinanceFuturesClient(ExchangeInterface):
    # Already implemented
    pass

# Exchange factory
class ExchangeFactory:
    @staticmethod
    def create_exchange(exchange_type: str):
        if exchange_type == 'binance':
            return BinanceFuturesClient(...)
        elif exchange_type == 'okx':
            return OKXClient(...)
```

### **Configuration Structure**

```python
# config.py
class Settings(BaseSettings):
    # Existing Binance config
    BINANCE_API_KEY: str
    BINANCE_API_SECRET: str
    BINANCE_TESTNET: bool = True

    # New OKX config
    OKX_API_KEY: Optional[str] = None
    OKX_SECRET_KEY: Optional[str] = None
    OKX_PASSPHRASE: Optional[str] = None
    OKX_TESTNET: bool = True

    # Exchange selection
    PRIMARY_EXCHANGE: str = "binance"  # or "okx"
    ENABLE_MULTI_EXCHANGE: bool = False
```

### **Unified Trading Interface**

```python
class UnifiedTrader:
    """
    Unified trading interface supporting multiple exchanges
    """
    def __init__(self, exchanges: List[ExchangeInterface]):
        self.exchanges = exchanges

    async def execute_signal(self, signal: SignalResult):
        """Execute trading signal across all enabled exchanges"""
        tasks = []
        for exchange in self.exchanges:
            task = exchange.place_order(
                symbol=signal.symbol,
                side=signal.direction,
                quantity=signal.quantity
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

    async def get_aggregated_balance(self):
        """Get total balance across all exchanges"""
        balances = []
        for exchange in self.exchanges:
            balance = await exchange.get_balance()
            balances.append(balance)

        return {
            'total_equity': sum(b['total'] for b in balances),
            'by_exchange': balances
        }
```

---

## 🚀 Implementation Priority

### **Phase 1: Core OKX Integration** (Week 1-2)
- [ ] Implement OKXClient class
- [ ] Authentication system with passphrase
- [ ] Basic trading endpoints (place order, cancel order)
- [ ] Account balance retrieval
- [ ] Position management

### **Phase 2: Advanced Features** (Week 3)
- [ ] WebSocket implementation (public + private)
- [ ] Margin calculator for OKX
- [ ] Liquidation price monitoring
- [ ] Multi-exchange order routing

### **Phase 3: Optimization** (Week 4)
- [ ] Rate limit handler
- [ ] Connection pool management
- [ ] Failover between exchanges
- [ ] Performance comparison dashboard

---

## 📋 Advantages of Multi-Exchange Support

### **Risk Diversification**
- **Exchange Risk**: Reduce dependency on single platform
- **Liquidity**: Access both OKX and Binance liquidity
- **Downtime**: Continue trading if one exchange is down

### **Arbitrage Opportunities**
- **Price Differences**: Exploit price gaps between exchanges
- **Funding Rates**: Optimize funding rate costs
- **Spread Trading**: Hedge positions across exchanges

### **Feature Access**
- **OKX Features**: Grid trading, block trading, portfolio margin
- **Binance Features**: Higher volume, better testnet

### **Cost Optimization**
- **Fee Comparison**: Route orders to lower-fee exchange
- **Maker/Taker**: Optimize based on fee structure
- **VIP Tiers**: Leverage volume across platforms

---

## ⚠️ OKX Integration Challenges

### **1. Authentication Complexity**
**Challenge:** OKX requires passphrase in addition to API key/secret
**Solution:** Secure storage of 3 credentials, environment variable management

### **2. Timestamp Format**
**Challenge:** ISO 8601 vs Unix milliseconds
**Solution:** Abstraction layer for timestamp conversion

### **3. Library Support**
**Challenge:** Fewer Python libraries compared to Binance
**Solution:** Use official `python-okx` SDK or build custom client

### **4. Testing Infrastructure**
**Challenge:** Demo trading uses same URL as production
**Solution:** Careful flag management, separate API keys for demo/live

### **5. Symbol Naming**
**Challenge:** Different format (`BTC-USDT-SWAP` vs `BTCUSDT`)
**Solution:** Symbol mapper utility

---

## 📈 Recommendation: Phased Approach

### **Immediate (Current Project)**
- ✅ **Complete Binance implementation** (95% done)
- ✅ Focus on production-ready Binance features
- ✅ Add rate limiting and error handling

### **Short-term (1-2 months)**
- 🔄 **Add OKX as secondary exchange**
- 🔄 Multi-exchange abstraction layer
- 🔄 Side-by-side testing

### **Long-term (3+ months)**
- 📅 Full multi-exchange arbitrage
- 📅 Advanced routing algorithms
- 📅 Bybit, Kraken integration

---

## 📝 Conclusion

**OKX API v5** offers a more unified and modern architecture compared to Binance, with advanced features like portfolio margin and built-in grid trading. However, **Binance** remains superior in terms of:
- Liquidity and trading volume
- Third-party ecosystem
- Community support

**Recommendation for TradingBot AI:**
1. **Complete Binance integration first** (current focus)
2. **Add OKX support** as Phase 2 feature
3. **Implement multi-exchange architecture** for future scalability

**Total Implementation Effort:** ~3-4 weeks for full OKX integration

**Expected Benefits:**
- 30-40% risk reduction through diversification
- Access to unique OKX features
- Arbitrage opportunities
- Higher system resilience

---

**Last Updated:** 2025-01-18
**Status:** Analysis Complete, Integration Pending
