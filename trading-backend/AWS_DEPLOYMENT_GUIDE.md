# TradingBot AI - AWS 배포 가이드 (ap-southeast-2)

**목적**: AWS 시드니 리전에서 ECS Fargate, RDS, ElastiCache를 사용하여 프로덕션 인프라를 구축합니다.

**예상 비용**: 월 $156/month (시드니 리전 기준)

---

## 📋 목차

1. [사전 요구사항](#사전-요구사항)
2. [AWS 계정 설정](#aws-계정-설정)
3. [인프라 아키텍처](#인프라-아키텍처)
4. [배포 방식 선택](#배포-방식-선택)
5. [Option A: Terraform 자동 배포](#option-a-terraform-자동-배포)
6. [Option B: AWS Console 수동 배포](#option-b-aws-console-수동-배포)
7. [배포 후 설정](#배포-후-설정)
8. [모니터링 및 운영](#모니터링-및-운영)
9. [비용 최적화](#비용-최적화)
10. [트러블슈팅](#트러블슈팅)

---

## 사전 요구사항

### 필수 도구

#### AWS CLI
```bash
# Windows (PowerShell)
msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi

# 설치 확인
aws --version
# aws-cli/2.x.x

# 설정
aws configure
# AWS Access Key ID: YOUR_ACCESS_KEY
# AWS Secret Access Key: YOUR_SECRET_KEY
# Default region name: ap-southeast-2
# Default output format: json
```

#### Terraform (Option A 사용 시)
```bash
# Windows (Chocolatey)
choco install terraform

# 또는 수동 설치
# https://www.terraform.io/downloads

# 설치 확인
terraform version
# Terraform v1.7.0+
```

#### Docker Desktop
```bash
# Docker가 설치되어 있어야 함 (Phase 7에서 설치됨)
docker --version
# Docker version 20.10.0+
```

### AWS 계정 권한

필요한 IAM 권한:
- EC2 (VPC, Subnet, Security Groups)
- ECS (Cluster, Task Definition, Service)
- RDS (Instance, Subnet Group)
- ElastiCache (Cluster, Subnet Group)
- ECR (Repository)
- IAM (Role, Policy)
- CloudWatch (Log Group, Metrics)
- Secrets Manager (Secret)
- Certificate Manager (Certificate)

**권장**: AdministratorAccess 정책 사용 (테스트용)
**프로덕션**: 최소 권한 정책 생성

---

## AWS 계정 설정

### 1. IAM 사용자 생성

```bash
# AWS Console → IAM → Users → Add user
# User name: tradingbot-deployer
# Access type: Programmatic access
# Permissions: AdministratorAccess (또는 커스텀 정책)

# Access Key 저장 (한 번만 표시됨!)
# AWS Access Key ID: AKIAIOSFODNN7EXAMPLE
# AWS Secret Access Key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

### 2. AWS CLI 설정
```bash
aws configure --profile tradingbot-prod
# AWS Access Key ID: [입력]
# AWS Secret Access Key: [입력]
# Default region name: ap-southeast-2
# Default output format: json

# 확인
aws sts get-caller-identity --profile tradingbot-prod
# {
#     "UserId": "AIDAEXAMPLE",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/tradingbot-deployer"
# }
```

### 3. S3 Bucket 생성 (Terraform State 저장용)

```bash
# Terraform state 저장용 S3 bucket
aws s3 mb s3://tradingbot-terraform-state --region ap-southeast-2 --profile tradingbot-prod

# 버전 관리 활성화
aws s3api put-bucket-versioning \
    --bucket tradingbot-terraform-state \
    --versioning-configuration Status=Enabled \
    --region ap-southeast-2 \
    --profile tradingbot-prod

# DynamoDB 테이블 생성 (State locking)
aws dynamodb create-table \
    --table-name terraform-state-lock \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region ap-southeast-2 \
    --profile tradingbot-prod
```

---

## 인프라 아키텍처

### 고수준 아키텍처
```
┌────────────────────────────────────────────────────────────────┐
│                    AWS ap-southeast-2 (Sydney)                 │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │                         VPC                              │ │
│  │                    10.0.0.0/16                           │ │
│  │                                                          │ │
│  │  ┌────────────────┐       ┌─────────────────────────┐   │ │
│  │  │  Public Subnet │       │   Private Subnet (AZ-a) │   │ │
│  │  │   10.0.0.0/24  │       │      10.0.10.0/24       │   │ │
│  │  │                │       │                         │   │ │
│  │  │  ┌─────────┐   │       │  ┌──────────────────┐   │   │ │
│  │  │  │   ALB   │◄──┼───────┼─►│  ECS Fargate     │   │   │ │
│  │  │  │  HTTPS  │   │       │  │  (2 Tasks)       │   │   │ │
│  │  │  └────┬────┘   │       │  │  - CPU: 0.5vCPU  │   │   │ │
│  │  │       │        │       │  │  - Mem: 1GB      │   │   │ │
│  │  │  ┌────▼────┐   │       │  └───┬────────┬─────┘   │   │ │
│  │  │  │   NAT   │───┼───────┼──────┘        │         │   │ │
│  │  │  │ Gateway │   │       │                │         │   │ │
│  │  │  └─────────┘   │       │                │         │   │ │
│  │  └────────────────┘       └────────────────┼─────────┘   │ │
│  │                                             │             │ │
│  │  ┌────────────────┐       ┌────────────────▼─────────┐   │ │
│  │  │  Public Subnet │       │   Private Subnet (AZ-b) │   │ │
│  │  │   10.0.1.0/24  │       │      10.0.11.0/24       │   │ │
│  │  │                │       │                         │   │ │
│  │  │  ┌─────────┐   │       │  ┌──────────────────┐   │   │ │
│  │  │  │   NAT   │───┼───────┼─►│  ECS Fargate     │   │   │ │
│  │  │  │ Gateway │   │       │  │  (2 Tasks)       │   │   │ │
│  │  │  └─────────┘   │       │  └──────────────────┘   │   │ │
│  │  └────────────────┘       └─────────────────────────┘   │ │
│  │                                                          │ │
│  │  ┌──────────────────────────────────────────────────┐   │ │
│  │  │            Database Subnets (Multi-AZ)           │   │ │
│  │  │              10.0.20.0/24, 10.0.21.0/24          │   │ │
│  │  │                                                  │   │ │
│  │  │  ┌──────────────────┐   ┌──────────────────┐    │   │ │
│  │  │  │  RDS PostgreSQL  │   │  RDS PostgreSQL  │    │   │ │
│  │  │  │  (Primary - AZ-a)│◄─►│(Standby - AZ-b)  │    │   │ │
│  │  │  │  db.t3.micro     │   │  db.t3.micro     │    │   │ │
│  │  │  └──────────────────┘   └──────────────────┘    │   │ │
│  │  └──────────────────────────────────────────────────┘   │ │
│  │                                                          │ │
│  │  ┌──────────────────────────────────────────────────┐   │ │
│  │  │             Cache Subnets                        │   │ │
│  │  │              10.0.30.0/24                        │   │ │
│  │  │                                                  │   │ │
│  │  │  ┌──────────────────────────────────────────┐    │   │ │
│  │  │  │      ElastiCache Redis 7.0               │    │   │ │
│  │  │  │      cache.t3.micro                      │    │   │ │
│  │  │  └──────────────────────────────────────────┘    │   │ │
│  │  └──────────────────────────────────────────────────┘   │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │                    ECR (Docker Registry)                 │ │
│  │        tradingbot-ai-backend:latest                      │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │                      CloudWatch                          │ │
│  │  - Container Insights                                    │ │
│  │  - RDS Performance Insights                              │ │
│  │  - Custom Metrics & Alarms                               │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │                   Secrets Manager                        │ │
│  │  - Database Password                                     │ │
│  │  - API Keys (Binance, OpenAI, etc.)                      │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
```

### 네트워크 설계
```
VPC: 10.0.0.0/16
├── Public Subnets (ALB, NAT Gateway)
│   ├── ap-southeast-2a: 10.0.0.0/24
│   └── ap-southeast-2b: 10.0.1.0/24
│
├── Private Subnets (ECS Fargate)
│   ├── ap-southeast-2a: 10.0.10.0/24
│   └── ap-southeast-2b: 10.0.11.0/24
│
├── Database Subnets (RDS Multi-AZ)
│   ├── ap-southeast-2a: 10.0.20.0/24
│   └── ap-southeast-2b: 10.0.21.0/24
│
└── Cache Subnets (ElastiCache)
    ├── ap-southeast-2a: 10.0.30.0/24
    └── ap-southeast-2b: 10.0.31.0/24
```

### Security Groups
```
ALB Security Group:
  Inbound:
    - 80 (HTTP) from 0.0.0.0/0
    - 443 (HTTPS) from 0.0.0.0/0
  Outbound:
    - 8001 to ECS Security Group

ECS Security Group:
  Inbound:
    - 8001 from ALB Security Group
  Outbound:
    - All (for external API calls)

RDS Security Group:
  Inbound:
    - 5432 from ECS Security Group
  Outbound:
    - None

ElastiCache Security Group:
  Inbound:
    - 6379 from ECS Security Group
  Outbound:
    - None
```

---

## 배포 방식 선택

### Option A: Terraform 자동 배포 (권장)
- ✅ **장점**: 완전 자동화, 재현 가능, 버전 관리
- ✅ **적합**: 인프라 코드 경험 있음, 팀 협업
- ⏱️ **소요 시간**: 15-20분

### Option B: AWS Console 수동 배포
- ✅ **장점**: GUI 친화적, 학습 용이
- ❌ **단점**: 수작업 많음, 실수 가능성
- ⏱️ **소요 시간**: 60-90분

---

## Option A: Terraform 자동 배포

### 1. Terraform 설정 파일 준비

```bash
cd C:\dev\trading\trading-backend\terraform

# terraform.tfvars 생성
cp terraform.tfvars.example terraform.tfvars

# 편집기로 열기
code terraform.tfvars  # 또는 notepad terraform.tfvars
```

### 2. 필수 값 입력

`terraform.tfvars` 파일에서 다음 값들을 **반드시 변경**:

```hcl
# Database password (16자 이상)
db_password = "CHANGE_THIS_STRONG_PASSWORD_16_CHARS_MIN"

# Security keys (생성 명령어는 파일 주석 참조)
secret_key     = "CHANGE_THIS_SECRET_KEY"
webhook_secret = "CHANGE_THIS_WEBHOOK_SECRET"
encryption_key = "CHANGE_THIS_ENCRYPTION_KEY"

# Exchange API keys
binance_api_key    = "your_binance_api_key"
binance_api_secret = "your_binance_api_secret"
binance_testnet    = false  # 프로덕션은 false!

# AI API keys
openai_api_key    = "sk-..."
anthropic_api_key = "sk-ant-..."

# Telegram bot token
telegram_bot_token = "123456789:ABC-DEF..."
```

### 3. Terraform 초기화

```bash
# Terraform 초기화 (provider 다운로드)
terraform init

# 예상 출력:
# Initializing modules...
# Initializing the backend...
# Initializing provider plugins...
# Terraform has been successfully initialized!
```

### 4. 배포 계획 확인

```bash
# 변경사항 미리보기
terraform plan

# 예상 출력:
# Plan: 50 to add, 0 to change, 0 to destroy.
#
# Resources to be created:
# - VPC, Subnets, Route Tables, NAT Gateways
# - Security Groups
# - RDS PostgreSQL (Multi-AZ)
# - ElastiCache Redis
# - ECR Repository
# - ECS Cluster, Task Definition, Service
# - Application Load Balancer
# - CloudWatch Log Groups, Alarms
```

### 5. 인프라 배포

```bash
# 실제 배포 실행
terraform apply

# 확인 메시지:
# Do you want to perform these actions?
#   Terraform will perform the actions described above.
#   Only 'yes' will be accepted to approve.
#
#   Enter a value: yes

# 배포 진행 (15-20분 소요)
# ...
# Apply complete! Resources: 50 added, 0 changed, 0 destroyed.
```

### 6. 배포 결과 확인

```bash
# 출력 값 확인
terraform output

# 예상 출력:
# alb_dns_name = "tradingbot-ai-production-alb-1234567890.ap-southeast-2.elb.amazonaws.com"
# ecr_repository_url = "123456789012.dkr.ecr.ap-southeast-2.amazonaws.com/tradingbot-ai-backend"
# ecs_cluster_name = "tradingbot-ai-production-cluster"
# ecs_service_name = "tradingbot-ai-production-service"
# rds_endpoint = "tradingbot-ai-production.xxxxxx.ap-southeast-2.rds.amazonaws.com:5432"
# redis_endpoint = "tradingbot-ai-production.xxxxxx.cache.amazonaws.com"
```

---

## Docker 이미지 배포

### 1. ECR 로그인

```bash
# ECR repository URL 가져오기
ECR_URL=$(terraform output -raw ecr_repository_url)
echo $ECR_URL

# ECR 로그인
aws ecr get-login-password --region ap-southeast-2 --profile tradingbot-prod | \
docker login --username AWS --password-stdin $ECR_URL
```

### 2. Docker 이미지 빌드 및 푸시

```bash
cd C:\dev\trading\trading-backend

# 이미지 빌드
docker build -t tradingbot-backend:latest .

# ECR 태그
docker tag tradingbot-backend:latest $ECR_URL:latest

# ECR 푸시
docker push $ECR_URL:latest

# 예상 출력:
# The push refers to repository [123456789012.dkr.ecr.ap-southeast-2.amazonaws.com/tradingbot-ai-backend]
# latest: digest: sha256:... size: 4321
```

### 3. ECS 서비스 업데이트

```bash
# ECS 서비스 강제 업데이트 (새 이미지 배포)
aws ecs update-service \
    --cluster $(terraform output -raw ecs_cluster_name) \
    --service $(terraform output -raw ecs_service_name) \
    --force-new-deployment \
    --region ap-southeast-2 \
    --profile tradingbot-prod

# 배포 상태 확인
aws ecs describe-services \
    --cluster $(terraform output -raw ecs_cluster_name) \
    --services $(terraform output -raw ecs_service_name) \
    --region ap-southeast-2 \
    --profile tradingbot-prod \
    --query 'services[0].deployments[*].[status,desiredCount,runningCount]' \
    --output table
```

---

## 배포 후 설정

### 1. 도메인 설정 (선택 사항)

#### Route 53 레코드 생성
```bash
# ALB DNS 이름 가져오기
ALB_DNS=$(terraform output -raw alb_dns_name)

# AWS Console → Route 53 → Hosted zones → your-domain.com
# Create Record:
#   Name: api.your-domain.com
#   Type: A
#   Alias: Yes
#   Alias Target: [ALB DNS name]
```

#### SSL/TLS 인증서 (Let's Encrypt 또는 ACM)
```bash
# AWS Certificate Manager
# AWS Console → Certificate Manager (ap-southeast-2)
# Request a certificate:
#   Domain names: api.your-domain.com
#   Validation method: DNS validation
#
# Add CNAME record to Route 53 for validation
# Wait for validation (5-30 minutes)
#
# Copy certificate ARN to terraform.tfvars:
# acm_certificate_arn = "arn:aws:acm:ap-southeast-2:123456789012:certificate/..."
#
# Re-run: terraform apply
```

### 2. 환경변수 확인

```bash
# Secrets Manager 확인
aws secretsmanager get-secret-value \
    --secret-id tradingbot-ai-production-secrets \
    --region ap-southeast-2 \
    --profile tradingbot-prod \
    --query 'SecretString' \
    --output text | jq .
```

### 3. 애플리케이션 테스트

```bash
# ALB를 통한 API 접근
ALB_URL=$(terraform output -raw alb_dns_name)

# Health check
curl http://$ALB_URL/api/v1/health
# {"status":"healthy"}

# API 문서
# http://$ALB_URL/docs
```

---

## 모니터링 및 운영

### CloudWatch 대시보드

```bash
# AWS Console → CloudWatch → Dashboards
# tradingbot-ai-production-dashboard 확인

# 주요 메트릭:
# - ECS CPU/Memory 사용률
# - ALB 요청 수 / 응답 시간
# - RDS CPU/Storage/Connections
# - ElastiCache CPU/Memory
```

### 로그 확인

```bash
# ECS 컨테이너 로그
aws logs tail /aws/ecs/tradingbot-ai-production \
    --follow \
    --region ap-southeast-2 \
    --profile tradingbot-prod

# RDS 로그
aws rds describe-db-log-files \
    --db-instance-identifier tradingbot-ai-production \
    --region ap-southeast-2 \
    --profile tradingbot-prod
```

### 알람 설정

```bash
# CloudWatch Alarms 자동 생성됨:
# - ECS CPU > 80%
# - ECS Memory > 80%
# - RDS CPU > 80%
# - ALB 5xx errors > 10/min
# - RDS Storage < 2GB

# SNS Topic에 이메일 구독:
aws sns subscribe \
    --topic-arn arn:aws:sns:ap-southeast-2:123456789012:tradingbot-ai-alerts \
    --protocol email \
    --notification-endpoint your-email@example.com \
    --region ap-southeast-2 \
    --profile tradingbot-prod
```

---

## 비용 최적화

### 월 예상 비용 (ap-southeast-2)

**현재 구성** (terraform.tfvars 기본값):
```
ECS Fargate:
  - 2 tasks × 0.5vCPU × 1GB × 730hr
  - $0.0503/vCPU/hr + $0.0055/GB/hr
  - Total: $73.44/month

RDS PostgreSQL (db.t3.micro, Multi-AZ):
  - 2 instances × $0.018/hr × 730hr = $26.28/month
  - Storage: 20GB × $0.138/GB = $2.76/month
  - Subtotal: $29.04/month

ElastiCache Redis (cache.t3.micro):
  - 1 node × $0.022/hr × 730hr = $16.06/month

Application Load Balancer:
  - $0.0243/hr × 730hr = $17.74/month
  - LCU charges: ~$5/month
  - Subtotal: $22.74/month

NAT Gateway (2 AZs):
  - 2 × $0.059/hr × 730hr = $86.14/month
  - Data transfer: ~$10/month
  - Subtotal: $96.14/month

ECR, CloudWatch, Secrets Manager:
  - ~$5/month

Total: ~$222/month
```

### 비용 절감 방법

#### 1. NAT Gateway 비용 절감 (가장 큰 비용!)
```
Option 1: Single NAT Gateway (1 AZ)
  - 비용 절감: $43/month (50%)
  - ⚠️ 트레이드오프: Single point of failure

Option 2: VPC Endpoints 사용
  - S3, ECR, CloudWatch용 VPC Endpoints
  - NAT 트래픽 감소 → $20-30/month 절감
```

#### 2. Reserved Instances / Savings Plans
```
RDS Reserved Instances (1 year, no upfront):
  - 현재: $29.04/month
  - Reserved: $18/month (38% 절감)

Fargate Compute Savings Plans (1 year):
  - 현재: $73.44/month
  - Savings: $51/month (30% 절감)
```

#### 3. 개발 환경 리소스 축소
```
Development/Staging:
  - ECS: 1 task (instead of 2)
  - RDS: db.t3.micro Single-AZ
  - ElastiCache: 삭제 (Redis는 optional)
  - NAT Gateway: Single (1 AZ)

  Estimated cost: $80-100/month
```

#### 4. Auto-Scaling 최적화
```terraform
# terraform.tfvars
ecs_desired_count = 2         # 기본 2개
autoscaling_min_capacity = 1  # 최소 1개 (off-peak)
autoscaling_max_capacity = 10 # 최대 10개 (peak)
```

### 비용 모니터링

```bash
# AWS Cost Explorer
# AWS Console → Cost Management → Cost Explorer

# 월별 비용 알람 설정
aws budgets create-budget \
    --account-id 123456789012 \
    --budget '{
        "BudgetName": "Monthly-TradingBot-Budget",
        "BudgetLimit": {
            "Amount": "250",
            "Unit": "USD"
        },
        "TimeUnit": "MONTHLY",
        "BudgetType": "COST"
    }' \
    --notifications-with-subscribers '[
        {
            "Notification": {
                "NotificationType": "ACTUAL",
                "ComparisonOperator": "GREATER_THAN",
                "Threshold": 80
            },
            "Subscribers": [{
                "SubscriptionType": "EMAIL",
                "Address": "your-email@example.com"
            }]
        }
    ]'
```

---

## 트러블슈팅

### ECS 태스크가 시작되지 않음

```bash
# 태스크 상태 확인
aws ecs describe-tasks \
    --cluster $(terraform output -raw ecs_cluster_name) \
    --tasks $(aws ecs list-tasks \
        --cluster $(terraform output -raw ecs_cluster_name) \
        --region ap-southeast-2 \
        --profile tradingbot-prod \
        --query 'taskArns[0]' \
        --output text) \
    --region ap-southeast-2 \
    --profile tradingbot-prod

# 일반적인 원인:
# 1. ECR 이미지 없음 → Docker 이미지 푸시
# 2. Secrets Manager 접근 불가 → IAM Role 확인
# 3. 메모리 부족 → Task Definition 메모리 증가
```

### RDS 연결 실패

```bash
# Security Group 확인
# RDS Security Group이 ECS Security Group에서 5432 포트 허용하는지 확인

# 연결 테스트 (ECS 컨테이너에서)
aws ecs execute-command \
    --cluster $(terraform output -raw ecs_cluster_name) \
    --task [TASK_ID] \
    --container backend \
    --command "/bin/bash" \
    --interactive \
    --region ap-southeast-2 \
    --profile tradingbot-prod

# 컨테이너 내부에서:
nc -zv [RDS_ENDPOINT] 5432
# Connection successful!
```

### ALB Health Check 실패

```bash
# Target Group Health 확인
aws elbv2 describe-target-health \
    --target-group-arn $(terraform output -raw target_group_arn) \
    --region ap-southeast-2 \
    --profile tradingbot-prod

# 일반적인 원인:
# 1. Health check endpoint 경로 오류 → /api/v1/health 확인
# 2. Security Group 설정 → ECS SG가 ALB SG에서 8001 포트 허용 확인
# 3. 컨테이너 시작 실패 → ECS 로그 확인
```

---

## 인프라 삭제

### Terraform으로 삭제

```bash
# ⚠️ 주의: 모든 리소스가 삭제됩니다!
# 데이터베이스 백업을 먼저 수행하세요!

# RDS 스냅샷 생성
aws rds create-db-snapshot \
    --db-instance-identifier tradingbot-ai-production \
    --db-snapshot-identifier tradingbot-final-snapshot-$(date +%Y%m%d) \
    --region ap-southeast-2 \
    --profile tradingbot-prod

# Terraform 삭제
terraform destroy

# 확인:
# Do you really want to destroy all resources?
#   Enter a value: yes

# 삭제 진행 (10-15분 소요)
```

---

## 다음 단계 (Phase 9)

- **CI/CD 파이프라인 구축** (GitHub Actions)
  - Docker 이미지 자동 빌드
  - ECR 푸시
  - ECS 서비스 자동 배포
  - Blue/Green 배포

---

**작성일**: 2025-01-18
**AWS 리전**: ap-southeast-2 (Sydney)
**Phase**: 8 - AWS 인프라 설정
**상태**: ✅ 가이드 완료
