# TradingBot AI - AWS Deployment Script (PowerShell)
# This script automates the deployment process to AWS ECS Fargate

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "TradingBot AI - AWS Deployment Script" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$AWS_REGION = "ap-southeast-2"
$PROJECT_NAME = "tradingbot-ai"
$ENVIRONMENT = "production"

# Function to print colored messages
function Print-Info {
    param($Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Print-Warning {
    param($Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Print-Error {
    param($Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Step 1: Check prerequisites
Print-Info "Checking prerequisites..."

try {
    aws --version | Out-Null
} catch {
    Print-Error "AWS CLI is not installed. Please install it first."
    exit 1
}

try {
    terraform version | Out-Null
} catch {
    Print-Error "Terraform is not installed. Please install it first."
    exit 1
}

try {
    docker --version | Out-Null
} catch {
    Print-Error "Docker is not installed. Please install it first."
    exit 1
}

Print-Info "All prerequisites are installed."

# Step 2: Check AWS credentials
Print-Info "Checking AWS credentials..."
try {
    aws sts get-caller-identity | Out-Null
    Print-Info "AWS credentials are valid."
} catch {
    Print-Error "AWS credentials are not configured. Run 'aws configure' first."
    exit 1
}

# Step 3: Initialize Terraform
Print-Info "Initializing Terraform..."
Set-Location ..\terraform
terraform init

if ($LASTEXITCODE -ne 0) {
    Print-Error "Terraform initialization failed."
    exit 1
}

# Step 4: Validate Terraform configuration
Print-Info "Validating Terraform configuration..."
terraform validate

if ($LASTEXITCODE -ne 0) {
    Print-Error "Terraform validation failed."
    exit 1
}

# Step 5: Check if terraform.tfvars exists
if (-not (Test-Path "terraform.tfvars")) {
    Print-Error "terraform.tfvars file not found!"
    Print-Warning "Please create terraform.tfvars from terraform.tfvars.example"
    exit 1
}

# Step 6: Terraform plan
Print-Info "Creating Terraform execution plan..."
terraform plan -out=tfplan

if ($LASTEXITCODE -ne 0) {
    Print-Error "Terraform plan failed."
    exit 1
}

# Step 7: Confirm deployment
Write-Host ""
Print-Warning "This will create AWS infrastructure with estimated cost of ~`$252/month."
$confirm = Read-Host "Do you want to proceed with deployment? (yes/no)"

if ($confirm -ne "yes") {
    Print-Warning "Deployment cancelled by user."
    exit 0
}

# Step 8: Apply Terraform
Print-Info "Applying Terraform configuration..."
terraform apply tfplan

if ($LASTEXITCODE -ne 0) {
    Print-Error "Terraform apply failed."
    exit 1
}

# Step 9: Get ECR repository URL
Print-Info "Getting ECR repository URL..."
$ECR_REPOSITORY_URL = terraform output -raw ecr_repository_url

if ([string]::IsNullOrEmpty($ECR_REPOSITORY_URL)) {
    Print-Error "Could not get ECR repository URL from Terraform output."
    exit 1
}

Print-Info "ECR Repository: $ECR_REPOSITORY_URL"

# Step 10: Login to ECR
Print-Info "Logging in to ECR..."
$LoginPassword = aws ecr get-login-password --region $AWS_REGION
$LoginPassword | docker login --username AWS --password-stdin $ECR_REPOSITORY_URL

if ($LASTEXITCODE -ne 0) {
    Print-Error "ECR login failed."
    exit 1
}

# Step 11: Build Docker image
Print-Info "Building Docker image..."
Set-Location ..
docker build -t "${PROJECT_NAME}:latest" .

if ($LASTEXITCODE -ne 0) {
    Print-Error "Docker build failed."
    exit 1
}

# Step 12: Tag Docker image
Print-Info "Tagging Docker image..."
docker tag "${PROJECT_NAME}:latest" "${ECR_REPOSITORY_URL}:latest"

# Step 13: Push Docker image to ECR
Print-Info "Pushing Docker image to ECR..."
docker push "${ECR_REPOSITORY_URL}:latest"

if ($LASTEXITCODE -ne 0) {
    Print-Error "Docker push failed."
    exit 1
}

# Step 14: Get ECS cluster and service names
Print-Info "Getting ECS cluster and service information..."
Set-Location terraform
$ECS_CLUSTER_NAME = terraform output -raw ecs_cluster_name
$ECS_SERVICE_NAME = terraform output -raw ecs_service_name

# Step 15: Force new deployment
Print-Info "Forcing ECS service to deploy new image..."
aws ecs update-service `
    --cluster $ECS_CLUSTER_NAME `
    --service $ECS_SERVICE_NAME `
    --force-new-deployment `
    --region $AWS_REGION `
    | Out-Null

if ($LASTEXITCODE -ne 0) {
    Print-Error "ECS service update failed."
    exit 1
}

# Step 16: Wait for service to stabilize
Print-Info "Waiting for ECS service to stabilize (this may take 5-10 minutes)..."
aws ecs wait services-stable `
    --cluster $ECS_CLUSTER_NAME `
    --services $ECS_SERVICE_NAME `
    --region $AWS_REGION

if ($LASTEXITCODE -ne 0) {
    Print-Error "ECS service failed to stabilize."
    exit 1
}

# Step 17: Get ALB DNS name
$ALB_DNS_NAME = terraform output -raw alb_dns_name

# Step 18: Verify deployment
Print-Info "Verifying deployment..."
Start-Sleep -Seconds 10  # Wait for ALB to update

try {
    $response = Invoke-WebRequest -Uri "http://$ALB_DNS_NAME/api/v1/health" -Method Get -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Print-Info "✓ Health check passed!"
    }
} catch {
    Print-Warning "Health check failed (expected status 200)"
    Print-Warning "The service may need a few more minutes to become available."
}

# Step 19: Display deployment information
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Deployment Summary" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
terraform output deployment_instructions
Write-Host ""
Write-Host "Application URL: http://$ALB_DNS_NAME"
Write-Host "API Docs: http://$ALB_DNS_NAME/docs"
Write-Host "Health Check: http://$ALB_DNS_NAME/api/v1/health"
Write-Host ""
Write-Host "CloudWatch Dashboard: https://console.aws.amazon.com/cloudwatch/home?region=$AWS_REGION"
Write-Host "ECS Cluster: https://console.aws.amazon.com/ecs/home?region=$AWS_REGION#/clusters/$ECS_CLUSTER_NAME"
Write-Host ""
Print-Info "Deployment completed successfully!"
Write-Host "==========================================" -ForegroundColor Cyan
