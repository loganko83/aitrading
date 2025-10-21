import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  TrendingUp,
  Bot,
  Zap,
  Shield,
  LineChart,
  Bell,
  Lock,
  Rocket,
  Activity,
  Target,
  Database,
  Code,
  CheckCircle2
} from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-background via-background to-secondary/20">
      {/* Navigation */}
      <nav className="border-b backdrop-blur-sm bg-background/80 sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <div className="w-10 h-10 bg-gradient-to-br from-primary to-primary/60 rounded-lg flex items-center justify-center shadow-lg">
              <TrendingUp className="text-primary-foreground" size={24} />
            </div>
            <span className="text-xl font-bold bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
              TradingBot AI
            </span>
          </div>

          <div className="flex items-center space-x-4">
            <Link href="/login">
              <Button variant="ghost">Login</Button>
            </Link>
            <Link href="/signup">
              <Button className="shadow-lg">Get Started</Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20 text-center">
        <Badge className="mb-4 shadow-sm" variant="secondary">
          <Zap className="w-3 h-3 mr-1 inline" />
          TradingView Webhook Automation
        </Badge>
        <h1 className="text-5xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-primary via-primary/80 to-primary/60 bg-clip-text text-transparent">
          AI based Automatic Quant Trading
        </h1>
        <p className="text-xl text-muted-foreground mb-8 max-w-3xl mx-auto leading-relaxed">
          Receive signals generated from TradingView Pine Script via Webhook and
          <span className="font-semibold text-foreground"> execute instantly on Binance and OKX Futures</span>.
          Pursue stable profits with 6 AI-generated verified strategies and backtesting.
        </p>
        <div className="flex flex-col sm:flex-row justify-center gap-4 mb-12">
          <Link href="/signup">
            <Button size="lg" className="text-lg px-8 shadow-lg hover:shadow-xl transition-all">
              <Rocket className="mr-2" size={20} />
              Start Free
            </Button>
          </Link>
          <Link href="#features">
            <Button size="lg" variant="outline" className="text-lg px-8">
              Learn More
            </Button>
          </Link>
        </div>

        {/* Stats - Updated with Real Features */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-16 max-w-4xl mx-auto">
          <Card className="p-6 border-primary/20 shadow-md hover:shadow-lg transition-shadow">
            <div className="text-3xl font-bold text-primary mb-2">6</div>
            <div className="text-sm text-muted-foreground">Verified AI Strategies</div>
          </Card>
          <Card className="p-6 border-primary/20 shadow-md hover:shadow-lg transition-shadow">
            <div className="text-3xl font-bold text-primary mb-2">2</div>
            <div className="text-sm text-muted-foreground">Exchange Support</div>
          </Card>
          <Card className="p-6 border-primary/20 shadow-md hover:shadow-lg transition-shadow">
            <div className="text-3xl font-bold text-primary mb-2">18</div>
            <div className="text-sm text-muted-foreground">DB Index Optimization</div>
          </Card>
          <Card className="p-6 border-primary/20 shadow-md hover:shadow-lg transition-shadow">
            <div className="text-3xl font-bold text-primary mb-2">24/7</div>
            <div className="text-sm text-muted-foreground">Automated Monitoring</div>
          </Card>
        </div>
      </section>

      {/* Key Features Section */}
      <section id="features" className="container mx-auto px-4 py-20 bg-gradient-to-b from-transparent to-secondary/10 rounded-3xl">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold mb-4">Key Features</h2>
          <p className="text-muted-foreground text-lg">
            Fully automated system for professional traders
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Feature 1 - TradingView Webhook */}
          <Card className="p-6 hover:shadow-xl transition-all border-primary/10 hover:border-primary/30">
            <div className="w-12 h-12 bg-gradient-to-br from-primary/20 to-primary/10 rounded-lg flex items-center justify-center mb-4">
              <Zap className="text-primary" size={24} />
            </div>
            <h3 className="text-xl font-bold mb-2">TradingView Webhook</h3>
            <p className="text-muted-foreground mb-3">
              Receive Pine Script signals via Webhook and execute orders automatically within 0.1 seconds. Supports both market and limit orders.
            </p>
            <div className="flex gap-2 flex-wrap">
              <Badge variant="outline">Instant Execution</Badge>
              <Badge variant="outline">Secure Auth</Badge>
            </div>
          </Card>

          {/* Feature 2 - Multi-Exchange */}
          <Card className="p-6 hover:shadow-xl transition-all border-primary/10 hover:border-primary/30">
            <div className="w-12 h-12 bg-gradient-to-br from-primary/20 to-primary/10 rounded-lg flex items-center justify-center mb-4">
              <Database className="text-primary" size={24} />
            </div>
            <h3 className="text-xl font-bold mb-2">2 Exchange Support</h3>
            <p className="text-muted-foreground mb-3">
              Supports both Binance Futures and OKX Futures. Perfect control of leverage, Stop Loss, and Take Profit.
            </p>
            <div className="flex gap-2 flex-wrap">
              <Badge variant="outline">Binance</Badge>
              <Badge variant="outline">OKX</Badge>
            </div>
          </Card>

          {/* Feature 3 - AI Strategies */}
          <Card className="p-6 hover:shadow-xl transition-all border-primary/10 hover:border-primary/30">
            <div className="w-12 h-12 bg-gradient-to-br from-primary/20 to-primary/10 rounded-lg flex items-center justify-center mb-4">
              <Bot className="text-primary" size={24} />
            </div>
            <h3 className="text-xl font-bold mb-2">6 AI Strategies</h3>
            <p className="text-muted-foreground mb-3">
              Verified strategies including SuperTrend, RSI+EMA, MACD, Ichimoku, and Bollinger Bands, automatically generated and optimized by AI.
            </p>
            <div className="flex gap-2 flex-wrap">
              <Badge variant="outline">Backtesting</Badge>
              <Badge variant="outline">AI Optimized</Badge>
            </div>
          </Card>

          {/* Feature 4 - Backtesting */}
          <Card className="p-6 hover:shadow-xl transition-all border-primary/10 hover:border-primary/30">
            <div className="w-12 h-12 bg-gradient-to-br from-primary/20 to-primary/10 rounded-lg flex items-center justify-center mb-4">
              <LineChart className="text-primary" size={24} />
            </div>
            <h3 className="text-xl font-bold mb-2">Backtesting Engine</h3>
            <p className="text-muted-foreground mb-3">
              Validate strategy performance with historical data. Detailed analysis including win rate, profit ratio, MDD, and Sharpe Ratio.
            </p>
            <div className="flex gap-2 flex-wrap">
              <Badge variant="outline">Win Rate Analysis</Badge>
              <Badge variant="outline">Risk Metrics</Badge>
            </div>
          </Card>

          {/* Feature 5 - Telegram Alerts */}
          <Card className="p-6 hover:shadow-xl transition-all border-primary/10 hover:border-primary/30">
            <div className="w-12 h-12 bg-gradient-to-br from-primary/20 to-primary/10 rounded-lg flex items-center justify-center mb-4">
              <Bell className="text-primary" size={24} />
            </div>
            <h3 className="text-xl font-bold mb-2">Telegram Real-time Alerts</h3>
            <p className="text-muted-foreground mb-3">
              Instant Telegram notifications for order fills, profit/loss changes, and errors. Monitor anytime, anywhere.
            </p>
            <div className="flex gap-2 flex-wrap">
              <Badge variant="outline">Real-time</Badge>
              <Badge variant="outline">Customizable</Badge>
            </div>
          </Card>

          {/* Feature 6 - Security */}
          <Card className="p-6 hover:shadow-xl transition-all border-primary/10 hover:border-primary/30">
            <div className="w-12 h-12 bg-gradient-to-br from-primary/20 to-primary/10 rounded-lg flex items-center justify-center mb-4">
              <Shield className="text-primary" size={24} />
            </div>
            <h3 className="text-xl font-bold mb-2">AES-256 Encryption</h3>
            <p className="text-muted-foreground mb-3">
              Protect exchange API keys with military-grade encryption. Dual security with NextAuth authentication and Redis JWT blacklist.
            </p>
            <div className="flex gap-2 flex-wrap">
              <Badge variant="outline">Encrypted</Badge>
              <Badge variant="outline">2FA Support</Badge>
            </div>
          </Card>

          {/* Feature 7 - Performance */}
          <Card className="p-6 hover:shadow-xl transition-all border-primary/10 hover:border-primary/30">
            <div className="w-12 h-12 bg-gradient-to-br from-primary/20 to-primary/10 rounded-lg flex items-center justify-center mb-4">
              <Activity className="text-primary" size={24} />
            </div>
            <h3 className="text-xl font-bold mb-2">Performance Optimized</h3>
            <p className="text-muted-foreground mb-3">
              Ultra-fast response guaranteed with Redis caching, 18 DB composite indexes, and GZIP compression.
            </p>
            <div className="flex gap-2 flex-wrap">
              <Badge variant="outline">Redis</Badge>
              <Badge variant="outline">Indexed</Badge>
            </div>
          </Card>

          {/* Feature 8 - Portfolio */}
          <Card className="p-6 hover:shadow-xl transition-all border-primary/10 hover:border-primary/30">
            <div className="w-12 h-12 bg-gradient-to-br from-primary/20 to-primary/10 rounded-lg flex items-center justify-center mb-4">
              <Target className="text-primary" size={24} />
            </div>
            <h3 className="text-xl font-bold mb-2">Portfolio Analysis</h3>
            <p className="text-muted-foreground mb-3">
              Multi-symbol position management, real-time P&L tracking, and risk analysis for systematic capital management.
            </p>
            <div className="flex gap-2 flex-wrap">
              <Badge variant="outline">Multi-Symbol</Badge>
              <Badge variant="outline">Risk Management</Badge>
            </div>
          </Card>

          {/* Feature 9 - Pine Script AI */}
          <Card className="p-6 hover:shadow-xl transition-all border-primary/10 hover:border-primary/30">
            <div className="w-12 h-12 bg-gradient-to-br from-primary/20 to-primary/10 rounded-lg flex items-center justify-center mb-4">
              <Code className="text-primary" size={24} />
            </div>
            <h3 className="text-xl font-bold mb-2">Pine Script AI Generator</h3>
            <p className="text-muted-foreground mb-3">
              Describe your strategy and AI automatically generates Pine Script code. Ready to apply directly on TradingView.
            </p>
            <div className="flex gap-2 flex-wrap">
              <Badge variant="outline">Auto Generate</Badge>
              <Badge variant="outline">Customizable</Badge>
            </div>
          </Card>
        </div>
      </section>

      {/* How It Works - Workflow */}
      <section className="container mx-auto px-4 py-20">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold mb-4">How It Works</h2>
          <p className="text-muted-foreground text-lg">
            Fully automated trading in 4 simple steps
          </p>
        </div>

        <div className="max-w-4xl mx-auto space-y-6">
          <Card className="p-6 border-primary/20 hover:border-primary/40 transition-all">
            <div className="flex items-start space-x-4">
              <div className="w-12 h-12 bg-gradient-to-br from-primary to-primary/60 text-primary-foreground rounded-full flex items-center justify-center font-bold text-xl flex-shrink-0 shadow-lg">
                1
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-bold mb-2 flex items-center">
                  <Lock className="mr-2 text-primary" size={20} />
                  Register API Keys
                </h3>
                <p className="text-muted-foreground leading-relaxed">
                  Securely register Binance or OKX API keys with AES-256 encryption.
                  Test in Testnet environment first, with dual security via 2FA authentication.
                </p>
              </div>
            </div>
          </Card>

          <Card className="p-6 border-primary/20 hover:border-primary/40 transition-all">
            <div className="flex items-start space-x-4">
              <div className="w-12 h-12 bg-gradient-to-br from-primary to-primary/60 text-primary-foreground rounded-full flex items-center justify-center font-bold text-xl flex-shrink-0 shadow-lg">
                2
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-bold mb-2 flex items-center">
                  <Bot className="mr-2 text-primary" size={20} />
                  Choose Strategy & Generate Pine Script
                </h3>
                <p className="text-muted-foreground leading-relaxed">
                  Select from 6 verified strategies or describe your strategy to AI for automatic Pine Script generation.
                  Verify past performance with backtesting, then apply to TradingView.
                </p>
              </div>
            </div>
          </Card>

          <Card className="p-6 border-primary/20 hover:border-primary/40 transition-all">
            <div className="flex items-start space-x-4">
              <div className="w-12 h-12 bg-gradient-to-br from-primary to-primary/60 text-primary-foreground rounded-full flex items-center justify-center font-bold text-xl flex-shrink-0 shadow-lg">
                3
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-bold mb-2 flex items-center">
                  <Zap className="mr-2 text-primary" size={20} />
                  Set Up Webhook Alert
                </h3>
                <p className="text-muted-foreground leading-relaxed">
                  Enter Webhook URL and authentication key when creating alerts in TradingView chart.
                  POST requests are automatically sent to the backend when signals occur.
                </p>
              </div>
            </div>
          </Card>

          <Card className="p-6 border-primary/20 hover:border-primary/40 transition-all">
            <div className="flex items-start space-x-4">
              <div className="w-12 h-12 bg-gradient-to-br from-primary to-primary/60 text-primary-foreground rounded-full flex items-center justify-center font-bold text-xl flex-shrink-0 shadow-lg">
                4
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-bold mb-2 flex items-center">
                  <CheckCircle2 className="mr-2 text-primary" size={20} />
                  Auto Order Execution & Alerts
                </h3>
                <p className="text-muted-foreground leading-relaxed">
                  Signal reception → Validation → Order execution → Telegram notification completed within 0.1 seconds.
                  Perfect risk management with automatic Stop Loss/Take Profit settings.
                </p>
              </div>
            </div>
          </Card>
        </div>
      </section>

      {/* Technology Stack */}
      <section className="bg-secondary/30 py-20">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold mb-4">Technology Stack</h2>
            <p className="text-muted-foreground text-lg">
              Enterprise-grade system built with cutting-edge technology
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
            <Card className="p-4 text-center hover:shadow-lg transition-all">
              <p className="font-semibold">FastAPI</p>
              <p className="text-sm text-muted-foreground">Backend</p>
            </Card>
            <Card className="p-4 text-center hover:shadow-lg transition-all">
              <p className="font-semibold">Next.js 14</p>
              <p className="text-sm text-muted-foreground">Frontend</p>
            </Card>
            <Card className="p-4 text-center hover:shadow-lg transition-all">
              <p className="font-semibold">PostgreSQL</p>
              <p className="text-sm text-muted-foreground">Database</p>
            </Card>
            <Card className="p-4 text-center hover:shadow-lg transition-all">
              <p className="font-semibold">Redis</p>
              <p className="text-sm text-muted-foreground">Caching</p>
            </Card>
            <Card className="p-4 text-center hover:shadow-lg transition-all">
              <p className="font-semibold">WebSocket</p>
              <p className="text-sm text-muted-foreground">Real-time</p>
            </Card>
            <Card className="p-4 text-center hover:shadow-lg transition-all">
              <p className="font-semibold">TradingView</p>
              <p className="text-sm text-muted-foreground">Webhook</p>
            </Card>
            <Card className="p-4 text-center hover:shadow-lg transition-all">
              <p className="font-semibold">Binance API</p>
              <p className="text-sm text-muted-foreground">Exchange</p>
            </Card>
            <Card className="p-4 text-center hover:shadow-lg transition-all">
              <p className="font-semibold">OKX API</p>
              <p className="text-sm text-muted-foreground">Exchange</p>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-gradient-to-r from-primary via-primary/90 to-primary/80 text-primary-foreground py-20">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-4xl font-bold mb-4">Start Trading Now</h2>
          <p className="text-xl mb-8 opacity-90 max-w-2xl mx-auto">
            Experience fully automated trading system with TradingView Webhook.
            Test for free in Testnet environment.
          </p>
          <div className="flex flex-col sm:flex-row justify-center gap-4">
            <Link href="/signup">
              <Button size="lg" variant="secondary" className="text-lg px-8 shadow-xl">
                <Rocket className="mr-2" size={20} />
                Create Free Account
              </Button>
            </Link>
            <Link href="/login">
              <Button size="lg" variant="outline" className="text-lg px-8 bg-transparent hover:bg-primary-foreground/10 text-primary-foreground border-primary-foreground/30">
                Already have an account?
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-12 bg-secondary/20">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
            <div>
              <h4 className="font-bold mb-4 flex items-center">
                <TrendingUp className="mr-2 text-primary" size={20} />
                TradingBot AI
              </h4>
              <p className="text-sm text-muted-foreground">
                Fully automated trading system based on TradingView Webhook
              </p>
            </div>
            <div>
              <h4 className="font-bold mb-4">Key Features</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>• TradingView Webhook</li>
                <li>• Binance/OKX Exchange</li>
                <li>• 6 AI Strategies</li>
                <li>• Backtesting Engine</li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold mb-4">Security & Performance</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>• AES-256 Encryption</li>
                <li>• Redis Caching</li>
                <li>• 18 DB Indexes</li>
                <li>• GZIP Compression</li>
              </ul>
            </div>
          </div>

          <div className="border-t pt-8 text-center text-muted-foreground">
            <p className="mb-2">© 2025 TradingBot AI. All rights reserved.</p>
            <p className="text-sm">
              ⚠️ Cryptocurrency trading involves high risk. Please fully understand the possibility of investment loss before use.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
