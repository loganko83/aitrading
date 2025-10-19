# TradingBot AI - AWS 배포 가이드

**프로젝트**: TradingBot AI
**배포 대상**: AWS ECS Fargate (ap-southeast-2 Sydney)
**인프라 관리**: Terraform
**최종 업데이트**: 2025-01-19

---

## 📋 목차

1. [사전 준비사항](#사전-준비사항)
2. [로컬 배포 (Docker Compose)](#로컬-배포)
3. [AWS 배포 (Terraform + ECS)](#aws-배포)
4. [배포 검증](#배포-검증)
5. [롤백 절차](#롤백-절차)
6. [문제 해결](#문제-해결)

---

## 사전 준비사항

### 필수 소프트웨어

1. **AWS CLI** (2.0+)
   ```bash
   # Windows (chocolatey)
   choco install awscli

   # macOS (homebrew)
   brew install awscli

   # Linux
   curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
   unzip awscliv2.zip
   sudo ./aws/install
   ```

2. **Terraform** (1.0+)
   ```bash
   # Windows (chocolatey)
   choco install terraform

   # macOS (homebrew)
   brew install terraform

   # Linux
   wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
   unzip terraform_1.6.0_linux_amd64.zip
   sudo mv terraform /usr/local/bin/
   ```

3. **Docker** (20.0+)
   - Windows/macOS: Docker Desktop 설치
   - Linux: Docker Engine 설치

### AWS 계정 설정

1. **AWS CLI 인증 설정**
   ```bash
   aws configure
   # AWS Access Key ID: <YOUR_ACCESS_KEY>
   # AWS Secret Access Key: <YOUR_SECRET_KEY>
   # Default region name: ap-southeast-2
   # Default output format: json
   ```

2. **권한 확인**

   필요한 IAM 권한:
   - EC2 (VPC, Security Groups, NAT Gateway)
   - ECS (Cluster, Service, Task Definition)
   - RDS (Database Instance)
   - ElastiCache (Redis Cluster)
   - ECR (Container Registry)
   - Application Load Balancer
   - Secrets Manager
   - CloudWatch (Logs, Alarms, Dashboard)
   - IAM (Roles, Policies)

---

## 로컬 배포

로컬 개발 환경에서 Docker Compose로 빠르게 테스트할 수 있습니다.

### 1단계: 환경변수 설정

```bash
cd C:\dev\trading\trading-backend
copy .env.example .env
```

`.env` 파일 편집:
```env
DEBUG=True
ENVIRONMENT=development

DATABASE_URL=postgresql://tradingbot:password@postgres:5432/tradingbot
REDIS_URL=redis://redis:6379/0

BINANCE_API_KEY=your_testnet_api_key
BINANCE_API_SECRET=your_testnet_secret
BINANCE_TESTNET=True

OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
TELEGRAM_BOT_TOKEN=123456789:ABC...

SECRET_KEY=generate-with-openssl-rand-hex-32
WEBHOOK_SECRET=generate-with-python-secrets
ENCRYPTION_KEY=generate-with-fernet
```

### 2단계: Docker Compose 실행

```bash
docker-compose up -d
```

### 3단계: 로그 확인

```bash
docker-compose logs -f backend
```

### 4단계: 접속 확인

- API 문서: http://localhost:8001/docs
- 헬스 체크: http://localhost:8001/api/v1/health

### 5단계: 중지

```bash
docker-compose down
```

---

## AWS 배포

프로덕션 환경을 AWS에 배포합니다.

### 방법 1: 자동 배포 스크립트 (권장)

#### Windows (PowerShell)

```powershell
cd C:\dev\trading\trading-backend
.\scripts\deploy-to-aws.ps1
```

#### Linux/macOS (Bash)

```bash
cd /path/to/trading-backend
chmod +x scripts/deploy-to-aws.sh
./scripts/deploy-to-aws.sh
```

스크립트가 자동으로 수행하는 작업:
1. 사전 요구사항 확인 (AWS CLI, Terraform, Docker)
2. Terraform 초기화 및 검증
3. 인프라 생성 (VPC, ECS, RDS, Redis, ALB, CloudWatch)
4. Docker 이미지 빌드 및 ECR 푸시
5. ECS 서비스 배포 및 안정화 대기
6. 헬스 체크 및 배포 확인

### 방법 2: 수동 배포 (세밀한 제어)

#### 1단계: terraform.tfvars 파일 생성

```bash
cd C:\dev\trading\trading-backend\terraform
copy terraform.tfvars.example terraform.tfvars
```

`terraform.tfvars` 편집:
```hcl
# 필수 변경사항:
db_password        = "STRONG_PASSWORD_HERE"
secret_key         = "생성된_SECRET_KEY"
webhook_secret     = "생성된_WEBHOOK_SECRET"
encryption_key     = "생성된_ENCRYPTION_KEY"
binance_api_key    = "실제_BINANCE_API_KEY"
binance_api_secret = "실제_BINANCE_SECRET"
openai_api_key     = "sk-..."
anthropic_api_key  = "sk-ant-..."
telegram_bot_token = "123456789:ABC..."
```

**시크릿 생성 명령어**:
```bash
# SECRET_KEY (JWT)
openssl rand -hex 32

# WEBHOOK_SECRET
python -c "import secrets; print(secrets.token_urlsafe(32))"

# ENCRYPTION_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# DB_PASSWORD
python -c "import secrets, string; chars = string.ascii_letters + string.digits + string.punctuation; print(''.join(secrets.choice(chars) for i in range(32)))"
```

#### 2단계: Terraform 초기화

```bash
terraform init
```

#### 3단계: 계획 확인

```bash
terraform plan
```

예상되는 리소스 생성 내역 확인:
- VPC, Subnets (8개), NAT Gateway (2개)
- Security Groups (4개)
- RDS PostgreSQL Multi-AZ
- ElastiCache Redis
- ECS Cluster, Service, Task Definition
- Application Load Balancer
- ECR Repository
- CloudWatch Dashboard, Alarms (8개)
- Secrets Manager (8개 시크릿)
- IAM Roles (2개)

#### 4단계: 인프라 생성

```bash
terraform apply
```

입력: `yes`

예상 소요 시간: 15-20분

#### 5단계: Docker 이미지 빌드 및 푸시

```bash
# ECR 로그인
ECR_REPOSITORY_URL=$(terraform output -raw ecr_repository_url)
aws ecr get-login-password --region ap-southeast-2 | docker login --username AWS --password-stdin $ECR_REPOSITORY_URL

# Docker 이미지 빌드
cd ..
docker build -t tradingbot-ai:latest .

# 태그
docker tag tradingbot-ai:latest $ECR_REPOSITORY_URL:latest

# 푸시
docker push $ECR_REPOSITORY_URL:latest
```

#### 6단계: ECS 서비스 업데이트

```bash
cd terraform
ECS_CLUSTER_NAME=$(terraform output -raw ecs_cluster_name)
ECS_SERVICE_NAME=$(terraform output -raw ecs_service_name)

aws ecs update-service \
  --cluster $ECS_CLUSTER_NAME \
  --service $ECS_SERVICE_NAME \
  --force-new-deployment \
  --region ap-southeast-2
```

#### 7단계: 배포 대기

```bash
aws ecs wait services-stable \
  --cluster $ECS_CLUSTER_NAME \
  --services $ECS_SERVICE_NAME \
  --region ap-southeast-2
```

예상 소요 시간: 5-10분

---

## 배포 검증

### 1. 헬스 체크

```bash
ALB_DNS_NAME=$(terraform output -raw alb_dns_name)
curl http://$ALB_DNS_NAME/api/v1/health
```

예상 응답:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "redis": "connected",
  "timestamp": "2025-01-19T12:00:00Z"
}
```

### 2. API 문서 접속

브라우저에서 접속:
- Swagger UI: `http://<ALB_DNS_NAME>/docs`
- ReDoc: `http://<ALB_DNS_NAME>/redoc`

### 3. CloudWatch 대시보드

AWS Console → CloudWatch → Dashboards → `tradingbot-ai-production-dashboard`

확인 항목:
- ECS CPU/Memory 사용률
- ALB 요청 수, 응답 시간
- RDS 연결 수, CPU 사용률
- Redis CPU 사용률

### 4. ECS 태스크 상태

AWS Console → ECS → Clusters → `tradingbot-ai-production-cluster`

확인 항목:
- Running tasks: 2개 (desired count와 일치)
- Task health: HEALTHY
- Container status: RUNNING

### 5. 로그 확인

AWS Console → CloudWatch → Log Groups → `/ecs/tradingbot-ai-production`

최근 로그 확인:
- INFO 레벨 로그 정상 출력
- ERROR 로그 없음
- Application startup 메시지 확인

### 6. 알람 상태

AWS Console → CloudWatch → Alarms

확인 항목:
- All alarms in OK state (정상)
- No ALARM triggered (경보 없음)

---

## 롤백 절차

### 이전 Docker 이미지로 롤백

#### 1단계: 이전 이미지 태그 확인

```bash
aws ecr describe-images \
  --repository-name tradingbot-ai \
  --region ap-southeast-2 \
  --query 'imageDetails[*].[imageTags[0],imagePushedAt]' \
  --output table
```

#### 2단계: ECS 태스크 정의 업데이트

```bash
# 이전 태스크 정의 ARN 확인
aws ecs list-task-definitions \
  --family-prefix tradingbot-ai-production \
  --region ap-southeast-2 \
  --query 'taskDefinitionArns[-2]' \
  --output text

# 서비스 업데이트
PREVIOUS_TASK_DEFINITION_ARN=<이전_ARN>
aws ecs update-service \
  --cluster tradingbot-ai-production-cluster \
  --service tradingbot-ai-production-service \
  --task-definition $PREVIOUS_TASK_DEFINITION_ARN \
  --region ap-southeast-2
```

### Terraform 인프라 롤백

#### 특정 버전으로 롤백

```bash
cd terraform

# 이전 상태 파일로 복원
terraform state pull > current-state.json
terraform state push previous-state.json

# 계획 확인
terraform plan

# 적용
terraform apply
```

### 전체 인프라 삭제 (긴급 상황)

```bash
cd terraform
terraform destroy
```

⚠️ **경고**: 모든 데이터가 삭제됩니다 (RDS 백업 제외)

---

## 문제 해결

### 문제 1: "Terraform apply failed"

**증상**: Terraform 실행 중 오류 발생

**원인**:
- AWS 권한 부족
- 리소스 할당량 초과
- 리전 지원 불가 인스턴스 타입

**해결**:
```bash
# 에러 메시지 확인
terraform plan

# 특정 리소스만 재생성
terraform apply -target=module.ecs

# 상태 파일 확인
terraform state list
```

### 문제 2: "ECS tasks failed to start"

**증상**: ECS 태스크가 RUNNING 상태에 도달하지 못함

**원인**:
- Docker 이미지 오류
- Secrets Manager 권한 부족
- 환경변수 누락

**해결**:
```bash
# ECS 태스크 로그 확인
aws logs tail /ecs/tradingbot-ai-production --follow

# 태스크 정의 확인
aws ecs describe-task-definition \
  --task-definition tradingbot-ai-production \
  --region ap-southeast-2

# Secrets Manager 권한 확인
aws secretsmanager get-secret-value \
  --secret-id tradingbot-ai/production/secret-key \
  --region ap-southeast-2
```

### 문제 3: "Health check failed"

**증상**: ALB health check 실패, 502/503 에러

**원인**:
- 애플리케이션 시작 실패
- 데이터베이스 연결 실패
- Redis 연결 실패

**해결**:
```bash
# CloudWatch Logs 확인
aws logs tail /ecs/tradingbot-ai-production --follow --format short

# RDS 연결 확인
aws rds describe-db-instances \
  --db-instance-identifier tradingbot-ai-production-postgres \
  --region ap-southeast-2 \
  --query 'DBInstances[0].DBInstanceStatus'

# Redis 연결 확인
aws elasticache describe-cache-clusters \
  --cache-cluster-id tradingbot-ai-production-redis \
  --region ap-southeast-2 \
  --show-cache-node-info
```

### 문제 4: "High costs detected"

**증상**: 예상보다 높은 AWS 비용 발생

**원인**:
- NAT Gateway 데이터 전송 초과
- Auto-scaling으로 인한 ECS 태스크 증가
- CloudWatch Logs 과다 적재

**해결**:
```bash
# Cost Explorer 확인
# AWS Console → Billing → Cost Explorer

# 비용 최적화 옵션:
# 1. NAT Gateway → VPC Endpoints 전환 (-$60/월)
# 2. Fargate Spot 인스턴스 사용 (-50%)
# 3. RDS Reserved Instances (1년 약정 -30%)
# 4. CloudWatch Logs retention 단축 (7일)
```

### 문제 5: "Database connection error"

**증상**: "Error establishing a database connection"

**원인**:
- RDS 인스턴스 시작 중
- Security Group 규칙 오류
- 잘못된 데이터베이스 자격 증명

**해결**:
```bash
# RDS 상태 확인
aws rds describe-db-instances \
  --db-instance-identifier tradingbot-ai-production-postgres \
  --region ap-southeast-2

# Security Group 확인
aws ec2 describe-security-groups \
  --filters "Name=tag:Name,Values=tradingbot-ai-production-rds-sg" \
  --region ap-southeast-2

# Secrets Manager에서 자격 증명 확인
aws secretsmanager get-secret-value \
  --secret-id tradingbot-ai/production/db-password \
  --region ap-southeast-2
```

---

## 배포 체크리스트

배포 전 다음 항목을 확인하세요:

### 사전 준비
- [ ] AWS CLI 설치 및 인증 설정
- [ ] Terraform 설치
- [ ] Docker 설치 및 실행 중
- [ ] `terraform.tfvars` 파일 생성 및 모든 시크릿 입력
- [ ] 생성된 시크릿 백업 (안전한 위치에 보관)

### 인프라 배포
- [ ] `terraform init` 성공
- [ ] `terraform plan` 검토 완료
- [ ] 예상 비용 확인 (~$252/월)
- [ ] `terraform apply` 성공
- [ ] 모든 리소스 생성 완료 (15-20분 소요)

### 애플리케이션 배포
- [ ] Docker 이미지 빌드 성공
- [ ] ECR 푸시 완료
- [ ] ECS 서비스 업데이트 완료
- [ ] 태스크 RUNNING 상태 확인 (2개)
- [ ] 헬스 체크 통과 (HTTP 200)

### 모니터링 설정
- [ ] CloudWatch 대시보드 정상 표시
- [ ] 모든 알람 OK 상태
- [ ] 로그 그룹 생성 확인
- [ ] SNS 이메일 구독 확인

### 보안 확인
- [ ] Secrets Manager 모든 시크릿 등록
- [ ] Security Groups 규칙 검토
- [ ] VPC Flow Logs 활성화
- [ ] IAM 역할 최소 권한 원칙
- [ ] RDS/Redis 암호화 활성화

### 최종 검증
- [ ] API 문서 접속 (/docs)
- [ ] 헬스 체크 엔드포인트 정상
- [ ] 샘플 API 호출 성공
- [ ] CloudWatch 메트릭 수집 확인
- [ ] 로그 정상 출력 확인

---

## 유용한 명령어

### Terraform

```bash
# 현재 상태 확인
terraform show

# 특정 리소스 정보 확인
terraform state show module.ecs.aws_ecs_cluster.main

# 출력 값 확인
terraform output

# 특정 출력 값만 확인
terraform output -raw alb_dns_name

# 리소스 목록
terraform state list

# 인프라 그래프 생성
terraform graph | dot -Tpng > graph.png
```

### AWS CLI

```bash
# ECS 클러스터 상태
aws ecs describe-clusters --clusters tradingbot-ai-production-cluster --region ap-southeast-2

# ECS 서비스 상태
aws ecs describe-services --cluster tradingbot-ai-production-cluster --services tradingbot-ai-production-service --region ap-southeast-2

# 실행 중인 태스크 목록
aws ecs list-tasks --cluster tradingbot-ai-production-cluster --region ap-southeast-2

# CloudWatch Logs 실시간 스트림
aws logs tail /ecs/tradingbot-ai-production --follow

# RDS 상태
aws rds describe-db-instances --region ap-southeast-2

# Redis 상태
aws elasticache describe-cache-clusters --show-cache-node-info --region ap-southeast-2
```

### Docker

```bash
# ECR 이미지 목록
aws ecr list-images --repository-name tradingbot-ai --region ap-southeast-2

# 로컬 이미지 확인
docker images | grep tradingbot-ai

# 컨테이너 로그 (로컬)
docker logs -f <container_id>
```

---

## 추가 자료

- [AWS ECS 문서](https://docs.aws.amazon.com/ecs/)
- [Terraform AWS Provider 문서](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [FastAPI 배포 가이드](https://fastapi.tiangolo.com/deployment/)
- [PHASE_8_COMPLETION_SUMMARY.md](trading-backend/PHASE_8_COMPLETION_SUMMARY.md) - 상세 인프라 문서
- [DEVELOPMENT_SUMMARY.md](DEVELOPMENT_SUMMARY.md) - 전체 개발 현황

---

**작성자**: Claude AI Assistant
**최종 업데이트**: 2025-01-19
**버전**: 1.0.0
