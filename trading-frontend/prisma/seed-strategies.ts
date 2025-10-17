import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

async function main() {
  console.log('🌱 Seeding default trading strategies...')

  // 1. Balanced AI Ensemble (기본 전략)
  const balancedStrategy = await prisma.strategy.upsert({
    where: { id: 'balanced-ai-ensemble' },
    update: {},
    create: {
      id: 'balanced-ai-ensemble',
      name: 'Balanced AI Ensemble',
      description: `**균형잡힌 AI 앙상블 전략**

모든 AI 모델을 균등하게 활용하여 안정적인 수익을 추구합니다.

**특징:**
- ML 모델 (40%): LSTM, Transformer, LightGBM 결합
- GPT-4 (25%): 시장 분석 및 패턴 인식
- Claude (25%): 리스크 관리 및 전략 최적화
- Technical Analysis (10%): ATR 기반 신호

**권장 대상:** 중위험 투자자, 안정적 수익 추구`,
      category: 'AI_ENSEMBLE',
      isPublic: true,
      creatorId: null,

      // AI 가중치
      mlWeight: 0.40,
      gpt4Weight: 0.25,
      claudeWeight: 0.25,
      taWeight: 0.10,

      // 진입 조건
      minProbability: 0.80,
      minConfidence: 0.70,
      minAgreement: 0.70,

      // 리스크 관리
      defaultLeverage: 3,
      positionSizePct: 0.10,
      slAtrMultiplier: 2.0,
      tpAtrMultiplier: 3.0,
      maxOpenPositions: 3,

      // 기술적 지표
      atrPeriod: 14,
      rsiPeriod: 14,
      macdFast: 12,
      macdSlow: 26,
      macdSignal: 9,
    },
  })

  // 2. Aggressive AI Trader (공격적 전략)
  const aggressiveStrategy = await prisma.strategy.upsert({
    where: { id: 'aggressive-ai-trader' },
    update: {},
    create: {
      id: 'aggressive-ai-trader',
      name: 'Aggressive AI Trader',
      description: `**공격적 AI 트레이더 전략**

고수익을 목표로 적극적인 포지션을 취합니다.

**특징:**
- ML 모델 중심 (50%): 빠른 시장 반응
- 높은 레버리지 (5x): 수익 극대화
- 넓은 Take-Profit (4x ATR): 큰 수익 추구
- 낮은 진입 임계값 (70%): 더 많은 거래 기회

**권장 대상:** 고위험 감수자, 적극적 트레이더`,
      category: 'AI_ENSEMBLE',
      isPublic: true,
      creatorId: null,

      // AI 가중치
      mlWeight: 0.50,
      gpt4Weight: 0.20,
      claudeWeight: 0.20,
      taWeight: 0.10,

      // 진입 조건 (낮춤)
      minProbability: 0.70,
      minConfidence: 0.65,
      minAgreement: 0.60,

      // 리스크 관리 (공격적)
      defaultLeverage: 5,
      positionSizePct: 0.15,
      slAtrMultiplier: 1.5,
      tpAtrMultiplier: 4.0,
      maxOpenPositions: 5,

      // 기술적 지표
      atrPeriod: 14,
      rsiPeriod: 14,
      macdFast: 12,
      macdSlow: 26,
      macdSignal: 9,
    },
  })

  // 3. Conservative Scalper (보수적 스캘핑)
  const conservativeStrategy = await prisma.strategy.upsert({
    where: { id: 'conservative-scalper' },
    update: {},
    create: {
      id: 'conservative-scalper',
      name: 'Conservative Scalper',
      description: `**보수적 스캘핑 전략**

높은 확신도에서만 진입하여 안정적인 수익을 추구합니다.

**특징:**
- Claude 중심 (35%): 신중한 리스크 관리
- 낮은 레버리지 (2x): 리스크 최소화
- 좁은 Stop-Loss (1.5x ATR): 손실 제한
- 높은 진입 임계값 (85%): 확실한 기회만 포착

**권장 대상:** 저위험 선호자, 초보 트레이더`,
      category: 'AI_ENSEMBLE',
      isPublic: true,
      creatorId: null,

      // AI 가중치
      mlWeight: 0.30,
      gpt4Weight: 0.25,
      claudeWeight: 0.35,
      taWeight: 0.10,

      // 진입 조건 (엄격)
      minProbability: 0.85,
      minConfidence: 0.75,
      minAgreement: 0.75,

      // 리스크 관리 (보수적)
      defaultLeverage: 2,
      positionSizePct: 0.08,
      slAtrMultiplier: 1.5,
      tpAtrMultiplier: 2.5,
      maxOpenPositions: 2,

      // 기술적 지표
      atrPeriod: 14,
      rsiPeriod: 14,
      macdFast: 12,
      macdSlow: 26,
      macdSignal: 9,
    },
  })

  // 4. Technical Analysis Master (기술적 분석 마스터)
  const technicalStrategy = await prisma.strategy.upsert({
    where: { id: 'technical-analysis-master' },
    update: {},
    create: {
      id: 'technical-analysis-master',
      name: 'Technical Analysis Master',
      description: `**기술적 분석 마스터 전략**

전통적인 기술적 지표를 중심으로 거래합니다.

**특징:**
- Technical Analysis 중심 (40%): 검증된 지표 활용
- RSI, MACD, EMA 조합
- ML 보조 (35%): 패턴 인식 지원
- 중도적 리스크 관리

**권장 대상:** 기술적 분석 선호자, 체계적 트레이더`,
      category: 'TECHNICAL',
      isPublic: true,
      creatorId: null,

      // AI 가중치
      mlWeight: 0.35,
      gpt4Weight: 0.15,
      claudeWeight: 0.10,
      taWeight: 0.40,

      // 진입 조건
      minProbability: 0.78,
      minConfidence: 0.72,
      minAgreement: 0.68,

      // 리스크 관리
      defaultLeverage: 3,
      positionSizePct: 0.12,
      slAtrMultiplier: 2.0,
      tpAtrMultiplier: 3.0,
      maxOpenPositions: 3,

      // 기술적 지표
      atrPeriod: 14,
      rsiPeriod: 14,
      macdFast: 12,
      macdSlow: 26,
      macdSignal: 9,
    },
  })

  // 5. Hybrid Momentum (하이브리드 모멘텀)
  const hybridStrategy = await prisma.strategy.upsert({
    where: { id: 'hybrid-momentum' },
    update: {},
    create: {
      id: 'hybrid-momentum',
      name: 'Hybrid Momentum',
      description: `**하이브리드 모멘텀 전략**

AI와 기술적 분석을 결합한 모멘텀 전략입니다.

**특징:**
- GPT-4 중심 (35%): 시장 심리 분석
- ML + TA 균형: 모멘텀 포착
- 동적 포지션 크기: 신호 강도에 따른 조절
- 적응형 Stop-Loss: 변동성 대응

**권장 대상:** 중급 이상 트레이더, 모멘텀 거래 선호자`,
      category: 'HYBRID',
      isPublic: true,
      creatorId: null,

      // AI 가중치
      mlWeight: 0.30,
      gpt4Weight: 0.35,
      claudeWeight: 0.20,
      taWeight: 0.15,

      // 진입 조건
      minProbability: 0.82,
      minConfidence: 0.73,
      minAgreement: 0.72,

      // 리스크 관리
      defaultLeverage: 4,
      positionSizePct: 0.12,
      slAtrMultiplier: 1.8,
      tpAtrMultiplier: 3.5,
      maxOpenPositions: 4,

      // 기술적 지표
      atrPeriod: 14,
      rsiPeriod: 14,
      macdFast: 12,
      macdSlow: 26,
      macdSignal: 9,
    },
  })

  console.log('✅ Created 5 default strategies:')
  console.log(`   1. ${balancedStrategy.name} (${balancedStrategy.category})`)
  console.log(`   2. ${aggressiveStrategy.name} (${aggressiveStrategy.category})`)
  console.log(`   3. ${conservativeStrategy.name} (${conservativeStrategy.category})`)
  console.log(`   4. ${technicalStrategy.name} (${technicalStrategy.category})`)
  console.log(`   5. ${hybridStrategy.name} (${hybridStrategy.category})`)
}

main()
  .then(async () => {
    await prisma.$disconnect()
  })
  .catch(async (e) => {
    console.error(e)
    await prisma.$disconnect()
    process.exit(1)
  })
