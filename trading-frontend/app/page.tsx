import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-secondary">
      {/* Navigation */}
      <nav className="border-b">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
              <span className="text-2xl font-bold text-primary-foreground">T</span>
            </div>
            <span className="text-xl font-bold">TradingBot AI</span>
          </div>

          <div className="flex items-center space-x-4">
            <Link href="/login">
              <Button variant="ghost">Login</Button>
            </Link>
            <Link href="/signup">
              <Button>Get Started</Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20 text-center">
        <Badge className="mb-4" variant="secondary">
          AI-Powered Crypto Trading
        </Badge>
        <h1 className="text-5xl font-bold mb-6">
          Triple AI Ensemble Trading Bot
        </h1>
        <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
          Leverage the power of ML Models, GPT-4, and LLaMA 3.1 for intelligent cryptocurrency trading on Binance Futures with 5x leverage.
        </p>
        <div className="flex justify-center space-x-4">
          <Link href="/signup">
            <Button size="lg" className="text-lg px-8">
              Start Trading Now
            </Button>
          </Link>
          <Link href="#features">
            <Button size="lg" variant="outline" className="text-lg px-8">
              Learn More
            </Button>
          </Link>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-16">
          <Card className="p-6">
            <div className="text-3xl font-bold text-primary mb-2">80%+</div>
            <div className="text-sm text-muted-foreground">Entry Confidence Threshold</div>
          </Card>
          <Card className="p-6">
            <div className="text-3xl font-bold text-primary mb-2">3 AI Models</div>
            <div className="text-sm text-muted-foreground">ML + GPT-4 + LLaMA</div>
          </Card>
          <Card className="p-6">
            <div className="text-3xl font-bold text-primary mb-2">4 Coins</div>
            <div className="text-sm text-muted-foreground">BTC, ETH, BNB, SOL</div>
          </Card>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="container mx-auto px-4 py-20">
        <h2 className="text-3xl font-bold text-center mb-12">Key Features</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {/* Feature 1 */}
          <Card className="p-6 hover:shadow-lg transition-shadow">
            <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
              <span className="text-2xl">🤖</span>
            </div>
            <h3 className="text-xl font-bold mb-2">Triple AI Analysis</h3>
            <p className="text-muted-foreground">
              Combine predictions from ML models, GPT-4 sentiment analysis, and LLaMA 3.1 technical pattern recognition for superior accuracy.
            </p>
          </Card>

          {/* Feature 2 */}
          <Card className="p-6 hover:shadow-lg transition-shadow">
            <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
              <span className="text-2xl">📊</span>
            </div>
            <h3 className="text-xl font-bold mb-2">Advanced Technical Analysis</h3>
            <p className="text-muted-foreground">
              Multi-timeframe analysis, Elliott Wave, Fibonacci levels, RSI, MACD, and more indicators working together.
            </p>
          </Card>

          {/* Feature 3 */}
          <Card className="p-6 hover:shadow-lg transition-shadow">
            <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
              <span className="text-2xl">🛡️</span>
            </div>
            <h3 className="text-xl font-bold mb-2">Risk Management</h3>
            <p className="text-muted-foreground">
              Automatic stop-loss, ATR-based TP/SL, 10% position sizing, and wrong prediction exit strategies.
            </p>
          </Card>

          {/* Feature 4 */}
          <Card className="p-6 hover:shadow-lg transition-shadow">
            <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
              <span className="text-2xl">🔐</span>
            </div>
            <h3 className="text-xl font-bold mb-2">Secure & Private</h3>
            <p className="text-muted-foreground">
              Your Binance API keys are encrypted. Two-factor authentication with Google OTP for maximum security.
            </p>
          </Card>

          {/* Feature 5 */}
          <Card className="p-6 hover:shadow-lg transition-shadow">
            <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
              <span className="text-2xl">🏆</span>
            </div>
            <h3 className="text-xl font-bold mb-2">Leaderboard & XP</h3>
            <p className="text-muted-foreground">
              Compete with other traders, earn XP points, level up, and climb the rankings to showcase your skills.
            </p>
          </Card>

          {/* Feature 6 */}
          <Card className="p-6 hover:shadow-lg transition-shadow">
            <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
              <span className="text-2xl">⚡</span>
            </div>
            <h3 className="text-xl font-bold mb-2">Webhook Integration</h3>
            <p className="text-muted-foreground">
              Connect external signals from TradingView or other platforms via webhooks for automated execution.
            </p>
          </Card>
        </div>
      </section>

      {/* How It Works */}
      <section className="container mx-auto px-4 py-20">
        <h2 className="text-3xl font-bold text-center mb-12">How It Works</h2>
        <div className="max-w-3xl mx-auto space-y-8">
          <div className="flex items-start space-x-4">
            <div className="w-10 h-10 bg-primary text-primary-foreground rounded-full flex items-center justify-center font-bold flex-shrink-0">
              1
            </div>
            <div>
              <h3 className="text-xl font-bold mb-2">Sign Up & Connect API</h3>
              <p className="text-muted-foreground">
                Create an account with email or social login, enable 2FA, and securely connect your Binance API keys.
              </p>
            </div>
          </div>

          <div className="flex items-start space-x-4">
            <div className="w-10 h-10 bg-primary text-primary-foreground rounded-full flex items-center justify-center font-bold flex-shrink-0">
              2
            </div>
            <div>
              <h3 className="text-xl font-bold mb-2">Configure Trading Settings</h3>
              <p className="text-muted-foreground">
                Choose your risk tolerance, select coins to trade, adjust leverage and position size, or use our optimized defaults.
              </p>
            </div>
          </div>

          <div className="flex items-start space-x-4">
            <div className="w-10 h-10 bg-primary text-primary-foreground rounded-full flex items-center justify-center font-bold flex-shrink-0">
              3
            </div>
            <div>
              <h3 className="text-xl font-bold mb-2">AI Analyzes Markets 24/7</h3>
              <p className="text-muted-foreground">
                Our triple AI system continuously analyzes price data, news, and technical patterns across multiple timeframes.
              </p>
            </div>
          </div>

          <div className="flex items-start space-x-4">
            <div className="w-10 h-10 bg-primary text-primary-foreground rounded-full flex items-center justify-center font-bold flex-shrink-0">
              4
            </div>
            <div>
              <h3 className="text-xl font-bold mb-2">Automated Trading Execution</h3>
              <p className="text-muted-foreground">
                When probability exceeds 80% with high confidence, the bot automatically enters positions with proper risk management.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-primary text-primary-foreground py-20">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-4">Ready to Start Trading?</h2>
          <p className="text-xl mb-8 opacity-90">
            Join traders using AI-powered strategies to maximize profits.
          </p>
          <Link href="/signup">
            <Button size="lg" variant="secondary" className="text-lg px-8">
              Create Free Account
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-8">
        <div className="container mx-auto px-4 text-center text-muted-foreground">
          <p>© 2025 TradingBot AI. All rights reserved.</p>
          <p className="mt-2 text-sm">
            Cryptocurrency trading involves risk. Past performance does not guarantee future results.
          </p>
        </div>
      </footer>
    </div>
  );
}
