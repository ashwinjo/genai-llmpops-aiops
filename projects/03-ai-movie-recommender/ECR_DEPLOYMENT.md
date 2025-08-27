# 🐳 AWS ECR Deployment Guide

This guide shows you how to build and deploy your Movie Recommendation System to AWS ECR (Elastic Container Registry) and Kubernetes.

## 📋 Prerequisites

### 1. AWS CLI Configuration
```bash
# Install AWS CLI (if not already installed)
brew install awscli

# Configure AWS CLI
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter your default region (e.g., us-west-2)
# Enter your output format (json)
```

### 2. Docker
```bash
# Ensure Docker is running
docker --version
```

### 3. kubectl
```bash
# Install kubectl (if not already installed)
brew install kubectl

# Verify installation
kubectl version --client
```

## 🚀 Quick Deployment

### Step 1: Setup ECR Authentication
```bash
cd projects/03-ai-movie-recommender
./setup-ecr-auth.sh
```

### Step 2: Build and Push to ECR
```bash
./deploy-to-ecr.sh
```

### Step 3: Deploy to Kubernetes
```bash
# Update the image URI in k8s-deployment-ecr.yaml
# Replace YOUR_AWS_ACCOUNT_ID and YOUR_REGION with actual values

kubectl apply -f k8s-deployment-ecr.yaml
```

## 🔧 Manual Steps (Detailed)

### 1. Configure AWS Region
Edit the scripts to use your preferred AWS region:
```bash
# In deploy-to-ecr.sh and setup-ecr-auth.sh
AWS_REGION="us-west-2"  # Change to your region
```

### 2. Build Docker Image
```bash
cd projects/03-ai-movie-recommender
docker build -t movie-recommender:latest .
```

### 3. Create ECR Repository
```bash
aws ecr create-repository \
    --repository-name movie-recommender \
    --region us-west-2 \
    --image-scanning-configuration scanOnPush=true \
    --encryption-configuration encryptionType=AES256
```

### 4. Authenticate with ECR
```bash
aws ecr get-login-password --region us-west-2 | \
docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com
```

### 5. Tag and Push Image
```bash
# Get your AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Tag the image
docker tag movie-recommender:latest $AWS_ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/movie-recommender:latest

# Push to ECR
docker push $AWS_ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/movie-recommender:latest
```

### 6. Create Kubernetes Secret
```bash
kubectl create secret docker-registry aws-ecr-secret \
    --docker-server=$AWS_ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com \
    --docker-username=AWS \
    --docker-password=$(aws ecr get-login-password --region us-west-2)
```

### 7. Update Kubernetes Deployment
Edit `k8s-deployment-ecr.yaml`:
```yaml
image: YOUR_ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/movie-recommender:latest
```

### 8. Deploy to Kubernetes
```bash
kubectl apply -f k8s-deployment-ecr.yaml
```

## 🔍 Verification

### Check ECR Repository
```bash
aws ecr describe-repositories --repository-names movie-recommender --region us-west-2
```

### Check Kubernetes Deployment
```bash
kubectl get pods
kubectl get services
kubectl logs deployment/movie-recommender-app
```

### Access the Application
```bash
# Get the LoadBalancer IP
kubectl get service movie-recommender-service

# Access via browser: http://LOAD_BALANCER_IP
```

## 🔄 Updating the Application

### 1. Build New Image
```bash
docker build -t movie-recommender:latest .
```

### 2. Tag and Push
```bash
docker tag movie-recommender:latest $AWS_ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/movie-recommender:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/movie-recommender:latest
```

### 3. Restart Kubernetes Deployment
```bash
kubectl rollout restart deployment/movie-recommender-app
```

## 🛠️ Troubleshooting

### ECR Authentication Issues
```bash
# Refresh ECR token
aws ecr get-login-password --region us-west-2 | \
docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com
```

### Kubernetes Pull Issues
```bash
# Check if secret exists
kubectl get secret aws-ecr-secret

# Recreate secret if needed
kubectl delete secret aws-ecr-secret
./setup-ecr-auth.sh
```

### Image Pull Errors
```bash
# Check pod events
kubectl describe pod <pod-name>

# Check pod logs
kubectl logs <pod-name>
```

## 💰 Cost Optimization

### ECR Lifecycle Policies
```bash
# Create lifecycle policy to delete old images
aws ecr put-lifecycle-policy \
    --repository-name movie-recommender \
    --lifecycle-policy-text '{
        "rules": [
            {
                "rulePriority": 1,
                "description": "Keep last 5 images",
                "selection": {
                    "tagStatus": "tagged",
                    "tagPrefixList": ["latest"],
                    "countType": "imageCountMoreThan",
                    "countNumber": 5
                },
                "action": {
                    "type": "expire"
                }
            }
        ]
    }'
```

## 🔐 Security Best Practices

1. **Use IAM Roles** instead of access keys when possible
2. **Enable ECR image scanning** for vulnerabilities
3. **Use specific image tags** instead of `latest` in production
4. **Regularly update base images** to patch security vulnerabilities
5. **Monitor ECR costs** and implement lifecycle policies

## 📚 Additional Resources

- [AWS ECR Documentation](https://docs.aws.amazon.com/ecr/)
- [Kubernetes ECR Integration](https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/)
- [AWS ECR Best Practices](https://docs.aws.amazon.com/ecr/latest/userguide/best-practices.html)
