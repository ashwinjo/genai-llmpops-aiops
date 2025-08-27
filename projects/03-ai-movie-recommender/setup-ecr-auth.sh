#!/bin/bash

# Setup ECR Authentication for Kubernetes
# Usage: ./setup-ecr-auth.sh

set -e

# Configuration
AWS_REGION="us-east-2"  # Change to your preferred region
KUBERNETES_NAMESPACE="default"  # Change if using different namespace

echo "🔐 Setting up ECR Authentication for Kubernetes"
echo "=============================================="

# Step 1: Check AWS CLI configuration
echo "🔍 Checking AWS CLI configuration..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

# Get AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "✅ AWS Account ID: $AWS_ACCOUNT_ID"

# Step 2: Create ECR registry secret for Kubernetes
echo "🔐 Creating ECR registry secret..."
kubectl create secret docker-registry aws-ecr-secret \
    --docker-server=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com \
    --docker-username=AWS \
    --docker-password=$(aws ecr get-login-password --region $AWS_REGION) \
    --namespace=$KUBERNETES_NAMESPACE \
    --dry-run=client -o yaml | kubectl apply -f -

echo "✅ ECR authentication secret created successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Run the ECR deployment script: ./deploy-to-ecr.sh"
echo "2. Update k8s-deployment-ecr.yaml with your ECR URI"
echo "3. Deploy to Kubernetes: kubectl apply -f k8s-deployment-ecr.yaml"
