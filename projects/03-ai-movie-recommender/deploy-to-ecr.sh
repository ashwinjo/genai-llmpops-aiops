#!/bin/bash

# AWS ECR Deployment Script for Movie Recommendation System
# Usage: ./deploy-to-ecr.sh

set -e

# Configuration
AWS_REGION="us-west-2"  # Change to your preferred region
AWS_ACCOUNT_ID=""       # Will be auto-detected
ECR_REPOSITORY_NAME="movie-recommender"
IMAGE_TAG="latest"
IMAGE_NAME="movie-recommender"

echo "🎬 AWS ECR Deployment Script for Movie Recommendation System"
echo "=========================================================="

# Step 1: Check AWS CLI configuration
echo "🔍 Checking AWS CLI configuration..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

# Get AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "✅ AWS Account ID: $AWS_ACCOUNT_ID"

# Step 2: Create ECR repository if it doesn't exist
echo "📦 Creating ECR repository..."
aws ecr describe-repositories --repository-names $ECR_REPOSITORY_NAME --region $AWS_REGION &> /dev/null || {
    echo "Creating repository $ECR_REPOSITORY_NAME..."
    aws ecr create-repository \
        --repository-name $ECR_REPOSITORY_NAME \
        --region $AWS_REGION \
        --image-scanning-configuration scanOnPush=true \
        --encryption-configuration encryptionType=AES256
}

# Step 3: Get ECR login token
echo "🔐 Getting ECR login token..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Step 4: Build Docker image
echo "🏗️ Building Docker image..."
cd projects/03-ai-movie-recommender
docker build -t $IMAGE_NAME:$IMAGE_TAG .

# Step 5: Tag image for ECR
ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY_NAME"
echo "🏷️ Tagging image for ECR: $ECR_URI"
docker tag $IMAGE_NAME:$IMAGE_TAG $ECR_URI:$IMAGE_TAG

# Step 6: Push image to ECR
echo "📤 Pushing image to ECR..."
docker push $ECR_URI:$IMAGE_TAG

# Step 7: Verify the push
echo "✅ Verifying image in ECR..."
aws ecr describe-images \
    --repository-name $ECR_REPOSITORY_NAME \
    --region $AWS_REGION \
    --query 'imageDetails[?imageTags[?contains(@, `latest`)]].{Tag:imageTags[0],Size:imageSizeInBytes,PushedAt:imagePushedAt}' \
    --output table

echo ""
echo "🎉 Deployment completed successfully!"
echo "=================================="
echo "ECR Repository: $ECR_URI"
echo "Image Tag: $IMAGE_TAG"
echo ""
echo "📋 Next steps:"
echo "1. Update your Kubernetes deployment to use: $ECR_URI:$IMAGE_TAG"
echo "2. Set imagePullPolicy: Always in your k8s-deployment.yaml"
echo "3. Deploy to Kubernetes: kubectl apply -f k8s-deployment.yaml"
