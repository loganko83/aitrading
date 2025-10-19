#!/bin/bash

# TradingBot AI - AWS Deployment Script
# This script automates the deployment process to AWS ECS Fargate

set -e  # Exit on error

echo "=========================================="
echo "TradingBot AI - AWS Deployment Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION="ap-southeast-2"
PROJECT_NAME="tradingbot-ai"
ENVIRONMENT="production"

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Step 1: Check prerequisites
print_info "Checking prerequisites..."

if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed. Please install it first."
    exit 1
fi

if ! command -v terraform &> /dev/null; then
    print_error "Terraform is not installed. Please install it first."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install it first."
    exit 1
fi

print_info "All prerequisites are installed."

# Step 2: Check AWS credentials
print_info "Checking AWS credentials..."
aws sts get-caller-identity > /dev/null 2>&1
if [ $? -ne 0 ]; then
    print_error "AWS credentials are not configured. Run 'aws configure' first."
    exit 1
fi

print_info "AWS credentials are valid."

# Step 3: Initialize Terraform
print_info "Initializing Terraform..."
cd ../terraform
terraform init

if [ $? -ne 0 ]; then
    print_error "Terraform initialization failed."
    exit 1
fi

# Step 4: Validate Terraform configuration
print_info "Validating Terraform configuration..."
terraform validate

if [ $? -ne 0 ]; then
    print_error "Terraform validation failed."
    exit 1
fi

# Step 5: Check if terraform.tfvars exists
if [ ! -f "terraform.tfvars" ]; then
    print_error "terraform.tfvars file not found!"
    print_warning "Please create terraform.tfvars from terraform.tfvars.example"
    exit 1
fi

# Step 6: Terraform plan
print_info "Creating Terraform execution plan..."
terraform plan -out=tfplan

if [ $? -ne 0 ]; then
    print_error "Terraform plan failed."
    exit 1
fi

# Step 7: Confirm deployment
echo ""
print_warning "This will create AWS infrastructure with estimated cost of ~$252/month."
read -p "Do you want to proceed with deployment? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    print_warning "Deployment cancelled by user."
    exit 0
fi

# Step 8: Apply Terraform
print_info "Applying Terraform configuration..."
terraform apply tfplan

if [ $? -ne 0 ]; then
    print_error "Terraform apply failed."
    exit 1
fi

# Step 9: Get ECR repository URL
print_info "Getting ECR repository URL..."
ECR_REPOSITORY_URL=$(terraform output -raw ecr_repository_url)

if [ -z "$ECR_REPOSITORY_URL" ]; then
    print_error "Could not get ECR repository URL from Terraform output."
    exit 1
fi

print_info "ECR Repository: $ECR_REPOSITORY_URL"

# Step 10: Login to ECR
print_info "Logging in to ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPOSITORY_URL

if [ $? -ne 0 ]; then
    print_error "ECR login failed."
    exit 1
fi

# Step 11: Build Docker image
print_info "Building Docker image..."
cd ..
docker build -t $PROJECT_NAME:latest .

if [ $? -ne 0 ]; then
    print_error "Docker build failed."
    exit 1
fi

# Step 12: Tag Docker image
print_info "Tagging Docker image..."
docker tag $PROJECT_NAME:latest $ECR_REPOSITORY_URL:latest

# Step 13: Push Docker image to ECR
print_info "Pushing Docker image to ECR..."
docker push $ECR_REPOSITORY_URL:latest

if [ $? -ne 0 ]; then
    print_error "Docker push failed."
    exit 1
fi

# Step 14: Get ECS cluster and service names
print_info "Getting ECS cluster and service information..."
cd terraform
ECS_CLUSTER_NAME=$(terraform output -raw ecs_cluster_name)
ECS_SERVICE_NAME=$(terraform output -raw ecs_service_name)

# Step 15: Force new deployment
print_info "Forcing ECS service to deploy new image..."
aws ecs update-service \
    --cluster $ECS_CLUSTER_NAME \
    --service $ECS_SERVICE_NAME \
    --force-new-deployment \
    --region $AWS_REGION \
    > /dev/null

if [ $? -ne 0 ]; then
    print_error "ECS service update failed."
    exit 1
fi

# Step 16: Wait for service to stabilize
print_info "Waiting for ECS service to stabilize (this may take 5-10 minutes)..."
aws ecs wait services-stable \
    --cluster $ECS_CLUSTER_NAME \
    --services $ECS_SERVICE_NAME \
    --region $AWS_REGION

if [ $? -ne 0 ]; then
    print_error "ECS service failed to stabilize."
    exit 1
fi

# Step 17: Get ALB DNS name
ALB_DNS_NAME=$(terraform output -raw alb_dns_name)

# Step 18: Verify deployment
print_info "Verifying deployment..."
sleep 10  # Wait for ALB to update

HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$ALB_DNS_NAME/api/v1/health || echo "000")

if [ "$HTTP_STATUS" = "200" ]; then
    print_info "✓ Health check passed!"
else
    print_warning "Health check returned status: $HTTP_STATUS (expected 200)"
    print_warning "The service may need a few more minutes to become available."
fi

# Step 19: Display deployment information
echo ""
echo "=========================================="
echo "Deployment Summary"
echo "=========================================="
echo ""
terraform output deployment_instructions
echo ""
echo "Application URL: http://$ALB_DNS_NAME"
echo "API Docs: http://$ALB_DNS_NAME/docs"
echo "Health Check: http://$ALB_DNS_NAME/api/v1/health"
echo ""
echo "CloudWatch Dashboard: https://console.aws.amazon.com/cloudwatch/home?region=$AWS_REGION"
echo "ECS Cluster: https://console.aws.amazon.com/ecs/home?region=$AWS_REGION#/clusters/$ECS_CLUSTER_NAME"
echo ""
print_info "Deployment completed successfully!"
echo "=========================================="
