# Deploying to AWS EKS: A Complete Guide

This guide explains how to deploy a local Docker application to Amazon EKS (Elastic Kubernetes Service). We'll use our Movie Recommender application as an example.

## Prerequisites: AWS Credentials Setup

Before starting, you need to configure your AWS credentials. There are several ways to do this:

### 1. Using AWS CLI Configuration
```bash
aws configure
```
This will prompt you for:
- AWS Access Key ID
- AWS Secret Access Key
- Default region name (use 'us-east-2' for this guide)
- Default output format (use 'json')

### 2. Manual Credentials File Setup
Create or edit `~/.aws/credentials`:
```ini
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
```

Create or edit `~/.aws/config`:
```ini
[default]
region = us-east-2
output = json
```

### 3. Using Environment Variables
```bash
export AWS_ACCESS_KEY_ID="YOUR_ACCESS_KEY"
export AWS_SECRET_ACCESS_KEY="YOUR_SECRET_KEY"
export AWS_DEFAULT_REGION="us-east-2"
```

### 4. Verify Configuration
```bash
# Test your credentials
aws sts get-caller-identity

# Expected output should show your AWS Account ID and user ARN
{
    "UserId": "XXXXXXXXXXXXX",
    "Account": "550263319257",
    "Arn": "arn:aws:iam::550263319257:user/your-username"
}
```

⚠️ **Security Note**: 
- Never commit AWS credentials to version control
- Use IAM roles and temporary credentials when possible
- Consider using AWS Vault or similar tools for credential management
- Regularly rotate your access keys

## Table of Contents
- [0. Creating AWS ECR Registry](#0-creating-aws-ecr-registry)
- [1. Building and Pushing to ECR](#1-building-and-pushing-to-ecr)
- [2. Setting up EKS Deployment](#2-setting-up-eks-deployment)
- [3. Environment Variables and Secrets](#3-environment-variables-and-secrets)
- [4. Troubleshooting](#4-troubleshooting)

> **Note**: For detailed instructions on setting up and managing your EKS cluster using eksctl, please refer to our [EKSCTL Setup Guide](EKSCTL.md)

## 0. Creating AWS ECR Registry

Before we can push our Docker images, we need to create an Amazon ECR repository.

### 0.1 Using AWS Console
1. Go to AWS Console → Amazon ECR
2. Click "Create repository"
3. Choose "Private" repository
4. Enter repository name: `movie-recommender`
5. Click "Create repository"

### 0.2 Using AWS CLI
```bash
# Create ECR repository
aws ecr create-repository \
    --repository-name movie-recommender \
    --region us-east-2 \
    --image-scanning-configuration scanOnPush=true \
    --encryption-configuration encryptionType=AES256

# Enable image tag mutability (optional)
aws ecr put-image-tag-mutability \
    --repository-name movie-recommender \
    --image-tag-mutability MUTABLE \
    --region us-east-2

# Enable image scanning (recommended)
aws ecr put-image-scanning-configuration \
    --repository-name movie-recommender \
    --image-scanning-configuration scanOnPush=true \
    --region us-east-2
```

### 0.3 Verify Repository Creation
```bash
# List repositories
aws ecr describe-repositories --region us-east-2

# Get repository URI
aws ecr describe-repositories \
    --repository-names movie-recommender \
    --region us-east-2 \
    --query 'repositories[0].repositoryUri' \
    --output text
```

### 0.4 Repository Lifecycle Policy (Optional)
You can set up a lifecycle policy to automatically clean up unused images:

```bash
# Create lifecycle policy
aws ecr put-lifecycle-policy \
    --repository-name movie-recommender \
    --lifecycle-policy-text '{
        "rules": [{
            "rulePriority": 1,
            "description": "Keep last 5 images",
            "selection": {
                "tagStatus": "any",
                "countType": "imageCountMoreThan",
                "countNumber": 5
            },
            "action": {
                "type": "expire"
            }
        }]
    }' \
    --region us-east-2
```

This policy keeps only the last 5 images and removes older ones to manage storage costs.
- [1. Building and Pushing to ECR](#1-building-and-pushing-to-ecr)
- [2. Setting up EKS Deployment](#2-setting-up-eks-deployment)
- [3. Environment Variables and Secrets](#3-environment-variables-and-secrets)
- [4. Troubleshooting](#4-troubleshooting)

## 1. Building and Pushing to ECR

### 1.1 Dockerfile Overview
Our `Dockerfile` sets up a Python application with Streamlit:
```dockerfile
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"

COPY . .
EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "st_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Key components:
- Base image: `python:3.11-slim` for a lightweight container
- System dependencies: `build-essential` and `curl`
- Python dependencies from `requirements.txt`
- NLTK data downloads for text processing
- Streamlit configuration and health checks
- Exposed port: 8501 (Streamlit default)

### 1.2 ECR Deployment Process
The `deploy-to-ecr.sh` script handles building and pushing to Amazon ECR:

1. **Configuration Check**
   ```bash
   # Verify AWS CLI setup
   aws sts get-caller-identity
   ```
   Why: Ensures AWS credentials are properly configured

2. **ECR Repository Verification**
   ```bash
   aws ecr describe-repositories --repository-names movie-recommender
   ```
   Why: Confirms the ECR repository exists before pushing

3. **ECR Authentication**
   ```bash
   aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin
   ```
   Why: Authenticates Docker with ECR for push access

4. **Multi-Architecture Build Setup**
   ```bash
   docker buildx create --use --name multi-arch-builder
   ```
   Why: Enables building for both AMD64 and ARM64 architectures

5. **Build and Push**
   ```bash
   docker buildx build \
       --platform linux/amd64,linux/arm64 \
       -t $ECR_URI:latest \
       --push .
   ```
   Why: Creates and pushes multi-architecture images for compatibility

## 2. Setting up EKS Deployment

> **Important**: Before proceeding with this section, ensure you have set up your EKS cluster using eksctl. Follow our [EKSCTL Setup Guide](EKSCTL.md) for step-by-step instructions on cluster creation and management.

### 2.1 IAM Role Setup
The `setup-iam-role.sh` script configures necessary AWS IAM roles:

1. **OIDC Provider Configuration**
   ```bash
   # Get EKS OIDC provider URL
   OIDC_PROVIDER=$(aws eks describe-cluster \
       --name movie-recommender \
       --region us-west-2 \
       --query "cluster.identity.oidc.issuer" \
       --output text | sed 's|https://||')
   ```
   Why: Enables IAM roles for service accounts (IRSA)

2. **IAM Role Creation**
   ```bash
   aws iam create-role \
       --role-name eks-movie-recommender-role \
       --assume-role-policy-document file://trust-policy.json
   ```
   Why: Creates role for EKS service account

3. **Policy Attachment**
   ```bash
   aws iam attach-role-policy \
       --role-name eks-movie-recommender-role \
       --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly
   ```
   Why: Grants ECR pull permissions to EKS pods

### 2.2 Kubernetes Resources

#### Service Account (`k8s-serviceaccount.yaml`)
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: movie-recommender-sa
  namespace: default
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::550263319257:role/eks-movie-recommender-role
```
Why: Links Kubernetes service account with AWS IAM role for ECR access

#### Deployment (`k8s-deployment.yaml`)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: movie-recommender
spec:
  replicas: 2
  template:
    metadata:
      annotations:
        iam.amazonaws.com/role: arn:aws:iam::550263319257:role/eks-node-group-role
    spec:
      serviceAccountName: movie-recommender-sa
      containers:
      - name: movie-recommender
        image: 550263319257.dkr.ecr.us-east-2.amazonaws.com/movie-recommender:latest
        env:
        - name: HF_TOKEN
          valueFrom:
            secretKeyRef:
              name: movie-recommender-secrets
              key: HF_TOKEN
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
```
Key components:
- Replicas: 2 for high availability
- Resource limits for CPU and memory
- Health checks via Streamlit endpoint
- Environment variables from secrets
- ECR image pull configuration

#### Service (`k8s-service.yaml`)
```yaml
apiVersion: v1
kind: Service
metadata:
  name: movie-recommender-service
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8501
  selector:
    app: movie-recommender
```
Why: Creates LoadBalancer service for external access

### 2.3 Deployment Process
The `deploy-to-k8s.sh` script orchestrates the deployment:

1. **EKS Configuration**
   ```bash
   aws eks update-kubeconfig \
       --region us-west-2 \
       --name movie-recommender
   ```
   Why: Configures kubectl for EKS cluster access

2. **Secret Creation**
   ```bash
   # ECR pull secret
   kubectl create secret docker-registry ecr-secret \
       --docker-server=$AWS_ACCOUNT_ID.dkr.ecr.$ECR_REGION.amazonaws.com \
       --docker-username=AWS \
       --docker-password="$ECR_PASSWORD"

   # Application secrets
   kubectl create secret generic movie-recommender-secrets \
       --from-literal=HF_TOKEN="$HF_TOKEN" \
       --from-literal=GROQ_API_KEY="$GROQ_API_KEY" \
       --from-literal=OPENAI_API_KEY="$OPENAI_API_KEY"
   ```
   Why: Manages both ECR authentication and application secrets

3. **Resource Application**
   ```bash
   kubectl apply -f k8s-serviceaccount.yaml
   kubectl apply -f k8s-deployment.yaml
   kubectl apply -f k8s-service.yaml
   ```
   Why: Deploys all Kubernetes resources in correct order

## 3. Environment Variables and Secrets

Required environment variables:
- `HF_TOKEN`: Hugging Face API token
- `GROQ_API_KEY`: GROQ API key
- `OPENAI_API_KEY`: OpenAI API key

These are managed securely through Kubernetes secrets and mounted as environment variables in the deployment.

## 4. Troubleshooting

Common issues and solutions:

1. **ImagePullBackOff**
   - Verify ECR permissions
   - Check image architecture compatibility
   - Validate ECR repository path
   ```bash
   kubectl describe pod <pod-name>
   ```

2. **Pod Startup Failures**
   - Check environment variables
   - Verify resource limits
   - Review pod logs:
   ```bash
   kubectl logs -l app=movie-recommender
   ```

3. **Service Access Issues**
   - Wait for LoadBalancer IP
   - Verify security group settings
   - Check service port mappings
   ```bash
   kubectl get svc movie-recommender-service
   ```

## Quick Start

1. Build and push to ECR:
   ```bash
   ./deploy-to-ecr.sh
   ```

2. Setup IAM roles:
   ```bash
   ./setup-iam-role.sh
   ```

3. Deploy to EKS:
   ```bash
   # Set your API keys
   export HF_TOKEN="your_token"
   export GROQ_API_KEY="your_key"
   export OPENAI_API_KEY="your_key"
   
   # Deploy
   ./deploy-to-k8s.sh
   ```

4. Verify deployment:
   ```bash
   kubectl get pods,svc -l app=movie-recommender
   ```

## Notes
- Ensure AWS CLI is configured with appropriate permissions
- Keep API keys and secrets secure
- Monitor resource usage and scale as needed
- Consider using AWS Secrets Manager for production deployments
