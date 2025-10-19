# TradingBot AI - Docker 배포 가이드

**목적**: 프로덕션 환경에서 Docker 컨테이너로 TradingBot AI를 안전하고 효율적으로 배포하는 방법

---

## 📋 목차

1. [시스템 요구사항](#시스템-요구사항)
2. [빠른 시작](#빠른-시작)
3. [환경 설정](#환경-설정)
4. [Docker Compose 구성](#docker-compose-구성)
5. [빌드 및 실행](#빌드-및-실행)
6. [운영 관리](#운영-관리)
7. [프로덕션 체크리스트](#프로덕션-체크리스트)
8. [문제 해결](#문제-해결)

---

## 시스템 요구사항

### 필수 소프트웨어
- **Docker**: 20.10.0 이상
- **Docker Compose**: 2.0.0 이상
- **Git**: 2.30.0 이상

### 하드웨어 권장사양
- **CPU**: 2 코어 이상 (AWS EC2 t3.medium 이상)
- **RAM**: 4GB 이상 (8GB 권장)
- **디스크**: 20GB 이상 (SSD 권장)

### 네트워크
- **포트**: 80, 443, 8001 (외부 접근)
- **포트**: 5432, 6379 (내부 통신)

---

## 빠른 시작

### 1. 프로젝트 클론
```bash
git clone https://github.com/your-org/tradingbot-ai.git
cd tradingbot-ai/trading-backend
```

### 2. 환경변수 설정
```bash
# .env.docker 템플릿 복사
cp .env.docker .env.docker.local

# 환경변수 편집 (필수!)
nano .env.docker.local

# 중요: 다음 값들을 반드시 변경하세요:
# - POSTGRES_PASSWORD
# - REDIS_PASSWORD
# - SECRET_KEY
# - WEBHOOK_SECRET
# - ENCRYPTION_KEY
# - BINANCE_API_KEY & BINANCE_API_SECRET
```

### 3. 빌드 및 실행
```bash
# 이미지 빌드
bash scripts/docker-build.sh

# 서비스 시작
bash scripts/docker-run.sh up

# 로그 확인
bash scripts/docker-run.sh logs

# 상태 확인
bash scripts/docker-run.sh health
```

### 4. API 접근 테스트
```bash
# Health check
curl http://localhost:8001/api/v1/health

# API 문서
# 브라우저에서: http://localhost:8001/docs
```

---

## 환경 설정

### 보안 키 생성

#### SECRET_KEY 생성
```bash
openssl rand -hex 32
# 예: 09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7
```

#### WEBHOOK_SECRET 생성
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
# 예: yER8UxvSY0klei4vveGAJltJk5uQDYIyYtnU6ctH6cM
```

#### ENCRYPTION_KEY 생성
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# 예: f_4ye2tp9hFz49YH04Dc7fCITNdChxH9_0Q25ry-Sfw=
```

### .env.docker 필수 설정

```env
# ============================================
# 반드시 변경해야 할 항목
# ============================================

# 데이터베이스 비밀번호
POSTGRES_PASSWORD=강력한_비밀번호_여기_입력

# Redis 비밀번호
REDIS_PASSWORD=Redis_강력한_비밀번호

# 보안 키들 (위에서 생성한 값 사용)
SECRET_KEY=openssl_rand_hex_32_결과값
WEBHOOK_SECRET=secrets_token_urlsafe_결과값
ENCRYPTION_KEY=fernet_generate_key_결과값

# Binance API (실제 키로 교체)
BINANCE_API_KEY=your_real_api_key
BINANCE_API_SECRET=your_real_api_secret
BINANCE_TESTNET=False  # 프로덕션에서는 False!

# AI API 키들
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

---

## Docker Compose 구성

### 서비스 구성

시스템은 4개의 주요 서비스로 구성됩니다:

```
┌─────────────────────────────────────────┐
│         Nginx (Reverse Proxy)           │
│            Port 80/443                  │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│     FastAPI Backend (Python 3.10)       │
│            Port 8001                    │
│  - AI Trading Strategies                │
│  - LSTM Deep Learning                   │
│  - Webhook Processing                   │
└─────┬────────────────────────┬──────────┘
      │                        │
┌─────▼─────────┐      ┌───────▼─────────┐
│  PostgreSQL   │      │      Redis      │
│   Database    │      │      Cache      │
│   Port 5432   │      │    Port 6379    │
└───────────────┘      └─────────────────┘
```

### 볼륨 (데이터 영구 저장)

```yaml
volumes:
  postgres_data:     # 데이터베이스 데이터
  redis_data:        # Redis 데이터
  nginx_logs:        # Nginx 로그
  ./logs:/app/logs   # 애플리케이션 로그
  ./models:/app/models  # LSTM 모델
```

---

## 빌드 및 실행

### 개발 환경

```bash
# 빌드
docker-compose build

# 시작 (기본 프로파일: backend + postgres + redis)
docker-compose up -d

# 로그 확인
docker-compose logs -f backend

# 상태 확인
docker-compose ps
```

### 프로덕션 환경

```bash
# Nginx 포함 프로덕션 프로파일
docker-compose --profile production up -d

# 모든 서비스 확인
docker-compose --profile production ps

# Nginx 로그
docker-compose logs -f nginx
```

### 개별 서비스 관리

```bash
# PostgreSQL만 재시작
docker-compose restart postgres

# Backend만 재빌드 및 재시작
docker-compose up -d --build backend

# Redis 로그 확인
docker-compose logs -f redis
```

---

## 운영 관리

### 데이터베이스 마이그레이션

마이그레이션은 컨테이너 시작 시 자동으로 실행됩니다 (`docker-entrypoint.sh`).

수동 실행이 필요한 경우:

```bash
# 컨테이너 내부 접속
docker-compose exec backend bash

# 마이그레이션 실행
alembic upgrade head

# 마이그레이션 히스토리 확인
alembic history

# 롤백 (1단계)
alembic downgrade -1
```

### 로그 관리

```bash
# 전체 로그 확인
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f backend

# 최근 100줄만 보기
docker-compose logs --tail=100 backend

# 로그 파일 직접 확인
tail -f logs/app.log
tail -f logs/error.log
```

### 백업 및 복구

#### PostgreSQL 백업

```bash
# 백업
docker-compose exec postgres pg_dump -U tradingbot tradingbot > backup_$(date +%Y%m%d_%H%M%S).sql

# 또는 Docker 볼륨 백업
docker run --rm \
  -v tradingbot-backend_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/postgres_backup_$(date +%Y%m%d).tar.gz /data
```

#### 복구

```bash
# SQL 파일에서 복구
cat backup_20250118_120000.sql | docker-compose exec -T postgres psql -U tradingbot tradingbot

# 볼륨 복구
docker run --rm \
  -v tradingbot-backend_postgres_data:/data \
  -v $(pwd):/backup \
  alpine sh -c "cd /data && tar xzf /backup/postgres_backup_20250118.tar.gz --strip 1"
```

### 성능 모니터링

```bash
# 컨테이너 리소스 사용량 실시간 확인
docker stats

# 특정 컨테이너만
docker stats tradingbot-backend tradingbot-postgres tradingbot-redis

# 디스크 사용량
docker system df

# 상세 정보
docker system df -v
```

### 스케일링

```bash
# Backend 인스턴스 3개로 확장
docker-compose up -d --scale backend=3

# 로드밸런싱은 Nginx upstream 설정 필요 (nginx.conf 참조)
```

---

## 프로덕션 체크리스트

### 보안

- [ ] **환경변수**: 모든 기본 비밀번호 변경
- [ ] **HTTPS**: SSL 인증서 설정 (Let's Encrypt 권장)
- [ ] **방화벽**: 필요한 포트만 오픈 (80, 443)
- [ ] **API 키**: Testnet → Mainnet 전환 확인
- [ ] **IP 화이트리스트**: 거래소 API 키 IP 제한 설정
- [ ] **Rate Limiting**: Nginx rate limit 활성화
- [ ] **로그**: 민감정보 로깅 제거 확인

### 성능

- [ ] **리소스 제한**: docker-compose.yml에서 CPU/메모리 제한 설정
- [ ] **Database**: PostgreSQL 성능 튜닝 (shared_buffers, work_mem)
- [ ] **Redis**: 메모리 정책 설정 (maxmemory-policy)
- [ ] **Workers**: Uvicorn worker 수 조정 (기본 4개)
- [ ] **Connection Pool**: 데이터베이스 연결 풀 크기 최적화

### 모니터링

- [ ] **Health Checks**: 모든 서비스 health check 정상 작동
- [ ] **로그 수집**: 로그 중앙화 시스템 연동 (ELK, CloudWatch)
- [ ] **메트릭**: Prometheus + Grafana 설정
- [ ] **알림**: 중요 이벤트 알림 설정 (Telegram, Slack)
- [ ] **APM**: 애플리케이션 성능 모니터링 (Sentry, New Relic)

### 백업

- [ ] **자동 백업**: 일일 PostgreSQL 백업 cron job 설정
- [ ] **볼륨 백업**: Docker 볼륨 정기 백업
- [ ] **LSTM 모델**: 학습된 모델 별도 저장 (S3 권장)
- [ ] **복구 테스트**: 백업 복구 절차 검증

---

## 문제 해결

### 컨테이너가 시작되지 않음

```bash
# 1. 로그 확인
docker-compose logs backend

# 2. 환경변수 확인
docker-compose config

# 3. 포트 충돌 확인
netstat -ano | findstr :8001
netstat -ano | findstr :5432

# 4. 이미지 재빌드
docker-compose build --no-cache backend
```

### Database connection error

```bash
# PostgreSQL 컨테이너 상태 확인
docker-compose ps postgres

# PostgreSQL 로그 확인
docker-compose logs postgres

# 수동 연결 테스트
docker-compose exec postgres psql -U tradingbot -d tradingbot

# Health check
docker-compose exec postgres pg_isready -U tradingbot
```

### Redis connection error

```bash
# Redis 컨테이너 상태 확인
docker-compose ps redis

# Redis 로그 확인
docker-compose logs redis

# 수동 연결 테스트
docker-compose exec redis redis-cli ping

# 비밀번호 인증 테스트
docker-compose exec redis redis-cli -a YOUR_REDIS_PASSWORD ping
```

### 메모리 부족

```bash
# 컨테이너별 메모리 사용량 확인
docker stats --no-stream

# Docker 시스템 정리
docker system prune -a --volumes

# 리소스 제한 조정 (docker-compose.yml)
# deploy.resources.limits.memory: 4G → 2G
```

### 디스크 공간 부족

```bash
# 사용량 확인
docker system df

# 사용하지 않는 이미지 삭제
docker image prune -a

# 사용하지 않는 볼륨 삭제 (주의!)
docker volume prune

# 로그 파일 정리
rm -f logs/*.log.old
```

---

## AWS EC2 배포 (t3.medium)

### 인스턴스 설정

```bash
# Docker 설치
sudo yum update -y
sudo yum install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user

# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Git 설치
sudo yum install git -y
```

### 프로젝트 배포

```bash
# 프로젝트 클론
git clone https://github.com/your-org/tradingbot-ai.git
cd tradingbot-ai/trading-backend

# 환경변수 설정
cp .env.docker .env.docker.local
nano .env.docker.local  # 실제 값 입력

# 실행
bash scripts/docker-build.sh
bash scripts/docker-run.sh up --prod

# 자동 시작 설정 (재부팅 시)
sudo systemctl enable docker
```

### 보안 그룹 설정

```
Inbound Rules:
- 22 (SSH): My IP only
- 80 (HTTP): 0.0.0.0/0
- 443 (HTTPS): 0.0.0.0/0
- 8001 (API): 0.0.0.0/0 (또는 특정 IP만)
```

---

## 다음 단계

- **Phase 8**: AWS 인프라 설정 (ECS, RDS, ElastiCache)
- **Phase 9**: CI/CD 파이프라인 구축 (GitHub Actions)
- **Phase 10**: 모니터링 및 로깅 시스템 (CloudWatch, Grafana)

---

**작성일**: 2025-01-18
**버전**: 1.0.0
**작성자**: Claude AI Assistant
