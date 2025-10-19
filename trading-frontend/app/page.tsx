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
              <Button variant="ghost">로그인</Button>
            </Link>
            <Link href="/signup">
              <Button className="shadow-lg">시작하기</Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20 text-center">
        <Badge className="mb-4 shadow-sm" variant="secondary">
          <Zap className="w-3 h-3 mr-1 inline" />
          TradingView Webhook 자동 매매
        </Badge>
        <h1 className="text-5xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-primary via-primary/80 to-primary/60 bg-clip-text text-transparent">
          자동 트레이딩의 새로운 기준
        </h1>
        <p className="text-xl text-muted-foreground mb-8 max-w-3xl mx-auto leading-relaxed">
          TradingView Pine Script에서 생성된 시그널을 Webhook으로 받아
          <span className="font-semibold text-foreground"> Binance와 OKX Futures에서 즉시 자동 실행</span>합니다.
          AI가 생성한 6가지 검증된 전략과 백테스팅으로 안정적인 수익을 추구하세요.
        </p>
        <div className="flex flex-col sm:flex-row justify-center gap-4 mb-12">
          <Link href="/signup">
            <Button size="lg" className="text-lg px-8 shadow-lg hover:shadow-xl transition-all">
              <Rocket className="mr-2" size={20} />
              무료로 시작하기
            </Button>
          </Link>
          <Link href="#features">
            <Button size="lg" variant="outline" className="text-lg px-8">
              자세히 알아보기
            </Button>
          </Link>
        </div>

        {/* Stats - Updated with Real Features */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-16 max-w-4xl mx-auto">
          <Card className="p-6 border-primary/20 shadow-md hover:shadow-lg transition-shadow">
            <div className="text-3xl font-bold text-primary mb-2">6</div>
            <div className="text-sm text-muted-foreground">검증된 AI 전략</div>
          </Card>
          <Card className="p-6 border-primary/20 shadow-md hover:shadow-lg transition-shadow">
            <div className="text-3xl font-bold text-primary mb-2">2</div>
            <div className="text-sm text-muted-foreground">거래소 지원</div>
          </Card>
          <Card className="p-6 border-primary/20 shadow-md hover:shadow-lg transition-shadow">
            <div className="text-3xl font-bold text-primary mb-2">18</div>
            <div className="text-sm text-muted-foreground">DB 인덱스 최적화</div>
          </Card>
          <Card className="p-6 border-primary/20 shadow-md hover:shadow-lg transition-shadow">
            <div className="text-3xl font-bold text-primary mb-2">24/7</div>
            <div className="text-sm text-muted-foreground">자동 모니터링</div>
          </Card>
        </div>
      </section>

      {/* Key Features Section */}
      <section id="features" className="container mx-auto px-4 py-20 bg-gradient-to-b from-transparent to-secondary/10 rounded-3xl">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold mb-4">핵심 기능</h2>
          <p className="text-muted-foreground text-lg">
            전문 트레이더를 위한 완전 자동화 시스템
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
              Pine Script 시그널을 Webhook으로 수신하여 0.1초 내 자동 주문 실행. 시장가/지정가 모두 지원.
            </p>
            <div className="flex gap-2 flex-wrap">
              <Badge variant="outline">즉시 실행</Badge>
              <Badge variant="outline">안전한 인증</Badge>
            </div>
          </Card>

          {/* Feature 2 - Multi-Exchange */}
          <Card className="p-6 hover:shadow-xl transition-all border-primary/10 hover:border-primary/30">
            <div className="w-12 h-12 bg-gradient-to-br from-primary/20 to-primary/10 rounded-lg flex items-center justify-center mb-4">
              <Database className="text-primary" size={24} />
            </div>
            <h3 className="text-xl font-bold mb-2">2개 거래소 지원</h3>
            <p className="text-muted-foreground mb-3">
              Binance Futures와 OKX Futures 모두 지원. 레버리지, Stop Loss, Take Profit 완벽 제어.
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
            <h3 className="text-xl font-bold mb-2">6가지 AI 전략</h3>
            <p className="text-muted-foreground mb-3">
              SuperTrend, RSI+EMA, MACD, Ichimoku, Bollinger Bands 등 검증된 전략을 AI가 자동 생성 및 최적화.
            </p>
            <div className="flex gap-2 flex-wrap">
              <Badge variant="outline">백테스팅</Badge>
              <Badge variant="outline">AI 최적화</Badge>
            </div>
          </Card>

          {/* Feature 4 - Backtesting */}
          <Card className="p-6 hover:shadow-xl transition-all border-primary/10 hover:border-primary/30">
            <div className="w-12 h-12 bg-gradient-to-br from-primary/20 to-primary/10 rounded-lg flex items-center justify-center mb-4">
              <LineChart className="text-primary" size={24} />
            </div>
            <h3 className="text-xl font-bold mb-2">백테스팅 엔진</h3>
            <p className="text-muted-foreground mb-3">
              과거 데이터로 전략 성과 검증. 승률, 손익비율, MDD, Sharpe Ratio 등 상세 분석 제공.
            </p>
            <div className="flex gap-2 flex-wrap">
              <Badge variant="outline">승률 분석</Badge>
              <Badge variant="outline">리스크 지표</Badge>
            </div>
          </Card>

          {/* Feature 5 - Telegram Alerts */}
          <Card className="p-6 hover:shadow-xl transition-all border-primary/10 hover:border-primary/30">
            <div className="w-12 h-12 bg-gradient-to-br from-primary/20 to-primary/10 rounded-lg flex items-center justify-center mb-4">
              <Bell className="text-primary" size={24} />
            </div>
            <h3 className="text-xl font-bold mb-2">텔레그램 실시간 알림</h3>
            <p className="text-muted-foreground mb-3">
              주문 체결, 손익 변동, 에러 발생 시 즉시 텔레그램으로 알림. 언제 어디서나 모니터링.
            </p>
            <div className="flex gap-2 flex-wrap">
              <Badge variant="outline">실시간</Badge>
              <Badge variant="outline">맞춤 설정</Badge>
            </div>
          </Card>

          {/* Feature 6 - Security */}
          <Card className="p-6 hover:shadow-xl transition-all border-primary/10 hover:border-primary/30">
            <div className="w-12 h-12 bg-gradient-to-br from-primary/20 to-primary/10 rounded-lg flex items-center justify-center mb-4">
              <Shield className="text-primary" size={24} />
            </div>
            <h3 className="text-xl font-bold mb-2">AES-256 암호화</h3>
            <p className="text-muted-foreground mb-3">
              거래소 API 키를 군사급 암호화로 보호. NextAuth 인증, Redis JWT 블랙리스트로 이중 보안.
            </p>
            <div className="flex gap-2 flex-wrap">
              <Badge variant="outline">암호화</Badge>
              <Badge variant="outline">2FA 지원</Badge>
            </div>
          </Card>

          {/* Feature 7 - Performance */}
          <Card className="p-6 hover:shadow-xl transition-all border-primary/10 hover:border-primary/30">
            <div className="w-12 h-12 bg-gradient-to-br from-primary/20 to-primary/10 rounded-lg flex items-center justify-center mb-4">
              <Activity className="text-primary" size={24} />
            </div>
            <h3 className="text-xl font-bold mb-2">성능 최적화</h3>
            <p className="text-muted-foreground mb-3">
              Redis 캐싱, 18개 DB 복합 인덱스, GZIP 압축으로 초고속 응답 속도 보장.
            </p>
            <div className="flex gap-2 flex-wrap">
              <Badge variant="outline">Redis</Badge>
              <Badge variant="outline">인덱스</Badge>
            </div>
          </Card>

          {/* Feature 8 - Portfolio */}
          <Card className="p-6 hover:shadow-xl transition-all border-primary/10 hover:border-primary/30">
            <div className="w-12 h-12 bg-gradient-to-br from-primary/20 to-primary/10 rounded-lg flex items-center justify-center mb-4">
              <Target className="text-primary" size={24} />
            </div>
            <h3 className="text-xl font-bold mb-2">포트폴리오 분석</h3>
            <p className="text-muted-foreground mb-3">
              다중 심볼 포지션 관리, 실시간 손익 추적, 위험도 분석으로 체계적인 자금 관리.
            </p>
            <div className="flex gap-2 flex-wrap">
              <Badge variant="outline">다중 심볼</Badge>
              <Badge variant="outline">리스크 관리</Badge>
            </div>
          </Card>

          {/* Feature 9 - Pine Script AI */}
          <Card className="p-6 hover:shadow-xl transition-all border-primary/10 hover:border-primary/30">
            <div className="w-12 h-12 bg-gradient-to-br from-primary/20 to-primary/10 rounded-lg flex items-center justify-center mb-4">
              <Code className="text-primary" size={24} />
            </div>
            <h3 className="text-xl font-bold mb-2">Pine Script AI 생성</h3>
            <p className="text-muted-foreground mb-3">
              전략을 설명하면 AI가 자동으로 Pine Script 코드 생성. TradingView에 바로 적용 가능.
            </p>
            <div className="flex gap-2 flex-wrap">
              <Badge variant="outline">자동 생성</Badge>
              <Badge variant="outline">커스터마이징</Badge>
            </div>
          </Card>
        </div>
      </section>

      {/* How It Works - Workflow */}
      <section className="container mx-auto px-4 py-20">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold mb-4">작동 원리</h2>
          <p className="text-muted-foreground text-lg">
            4단계로 완성되는 완전 자동 트레이딩
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
                  API 키 등록
                </h3>
                <p className="text-muted-foreground leading-relaxed">
                  Binance 또는 OKX API 키를 AES-256 암호화로 안전하게 등록합니다.
                  Testnet 환경에서 먼저 테스트 가능하며, 2FA 인증으로 이중 보안을 제공합니다.
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
                  전략 선택 & Pine Script 생성
                </h3>
                <p className="text-muted-foreground leading-relaxed">
                  6가지 검증된 전략 중 선택하거나 AI에게 전략을 설명하여 Pine Script 자동 생성.
                  백테스팅으로 과거 성과를 확인한 후 TradingView에 적용합니다.
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
                  Webhook 알림 설정
                </h3>
                <p className="text-muted-foreground leading-relaxed">
                  TradingView 차트에서 알림 생성 시 Webhook URL과 인증 키를 입력합니다.
                  시그널 발생 시 자동으로 백엔드로 POST 요청이 전송됩니다.
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
                  자동 주문 실행 & 알림
                </h3>
                <p className="text-muted-foreground leading-relaxed">
                  시그널 수신 → 검증 → 주문 실행 → 텔레그램 알림까지 0.1초 내 완료.
                  Stop Loss/Take Profit 자동 설정으로 리스크 관리도 완벽합니다.
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
            <h2 className="text-4xl font-bold mb-4">기술 스택</h2>
            <p className="text-muted-foreground text-lg">
              최신 기술로 구축된 엔터프라이즈급 시스템
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
          <h2 className="text-4xl font-bold mb-4">지금 바로 시작하세요</h2>
          <p className="text-xl mb-8 opacity-90 max-w-2xl mx-auto">
            TradingView Webhook으로 완전 자동화된 트레이딩 시스템을 경험하세요.
            Testnet 환경에서 무료로 테스트할 수 있습니다.
          </p>
          <div className="flex flex-col sm:flex-row justify-center gap-4">
            <Link href="/signup">
              <Button size="lg" variant="secondary" className="text-lg px-8 shadow-xl">
                <Rocket className="mr-2" size={20} />
                무료 계정 만들기
              </Button>
            </Link>
            <Link href="/login">
              <Button size="lg" variant="outline" className="text-lg px-8 bg-transparent hover:bg-primary-foreground/10 text-primary-foreground border-primary-foreground/30">
                이미 계정이 있으신가요?
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
                TradingView Webhook 기반 완전 자동화 트레이딩 시스템
              </p>
            </div>
            <div>
              <h4 className="font-bold mb-4">주요 기능</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>• TradingView Webhook</li>
                <li>• Binance/OKX 거래소</li>
                <li>• 6가지 AI 전략</li>
                <li>• 백테스팅 엔진</li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold mb-4">보안 & 성능</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>• AES-256 암호화</li>
                <li>• Redis 캐싱</li>
                <li>• 18개 DB 인덱스</li>
                <li>• GZIP 압축</li>
              </ul>
            </div>
          </div>

          <div className="border-t pt-8 text-center text-muted-foreground">
            <p className="mb-2">© 2025 TradingBot AI. All rights reserved.</p>
            <p className="text-sm">
              ⚠️ 암호화폐 거래는 높은 리스크를 수반합니다. 투자 손실 가능성을 충분히 이해하신 후 이용하시기 바랍니다.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
