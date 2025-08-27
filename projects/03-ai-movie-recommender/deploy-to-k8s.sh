#!/bin/bash

# Kubernetes Deployment Script for Movie Recommendation System
# Usage: ./deploy-to-k8s.sh

set -e

# Configuration
CLUSTER_NAME="movie-recommender"
CLUSTER_REGION="us-west-2"
ECR_REGION="us-east-2"  # Your ECR is in us-east-2
AWS_ACCOUNT_ID="550263319257"

echo "🚀 Deploying Movie Recommender to EKS"
echo "====================================="

# Step 1: Configure kubectl for EKS
echo "🔧 Configuring kubectl for EKS..."
aws eks update-kubeconfig \
    --region $CLUSTER_REGION \
    --name $CLUSTER_NAME

# Verify cluster connection
echo "🔍 Verifying cluster connection..."
if ! kubectl get nodes &> /dev/null; then
    echo "❌ Failed to connect to EKS cluster"
    exit 1
fi
echo "✅ Successfully connected to EKS cluster: $CLUSTER_NAME in $CLUSTER_REGION"

# Step 2: Create ECR pull secret
echo "🔐 Creating ECR pull secret..."
# Get ECR password
ECR_PASSWORD=$(aws ecr get-login-password --region $ECR_REGION)

# Delete existing secret if it exists
kubectl delete secret ecr-secret --ignore-not-found

# Create new secret
kubectl create secret docker-registry ecr-secret \
    --docker-server=$AWS_ACCOUNT_ID.dkr.ecr.$ECR_REGION.amazonaws.com \
    --docker-username=AWS \
    --docker-password="$ECR_PASSWORD" \
    --namespace=default

# Step 3: Create Kubernetes secret for environment variables
echo "🔐 Creating Kubernetes secrets..."
kubectl create secret generic movie-recommender-secrets \
    --from-literal=HF_TOKEN="$HF_TOKEN" \
    --from-literal=GROQ_API_KEY="$GROQ_API_KEY" \
    --from-literal=OPENAI_API_KEY="$OPENAI_API_KEY" \
    --dry-run=client -o yaml | kubectl apply -f -

# Step 4: Deploy the application
echo "📦 Deploying application..."
kubectl apply -f k8s-serviceaccount.yaml
kubectl apply -f k8s-deployment.yaml
kubectl apply -f k8s-service.yaml

# Step 4: Wait for deployment
echo "⏳ Waiting for deployment to be ready..."
kubectl rollout status deployment/movie-recommender

# Step 5: Get service information
echo "🌐 Service information:"
kubectl get service movie-recommender-service

echo ""
echo "🎉 Deployment completed!"
echo "=================================="
echo "To access your application:"
echo "1. Wait for LoadBalancer to get external IP"
echo "2. Run: kubectl get service movie-recommender-service"
echo "3. Access via the EXTERNAL-IP"
echo ""
echo "To check logs: kubectl logs -l app=movie-recommender"
echo "To scale: kubectl scale deployment movie-recommender --replicas=3"
