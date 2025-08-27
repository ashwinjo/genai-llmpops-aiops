#!/bin/bash

set -e

# Configuration
CLUSTER_NAME="movie-recommender"
CLUSTER_REGION="us-west-2"
AWS_ACCOUNT_ID="550263319257"
SERVICE_ACCOUNT_NAMESPACE="default"
SERVICE_ACCOUNT_NAME="movie-recommender-sa"

echo "🔐 Setting up IAM role for EKS service account"
echo "============================================="

# Get OIDC provider URL
OIDC_PROVIDER=$(aws eks describe-cluster \
    --name $CLUSTER_NAME \
    --region $CLUSTER_REGION \
    --query "cluster.identity.oidc.issuer" \
    --output text | sed 's|https://||')

echo "✅ OIDC Provider: $OIDC_PROVIDER"

# Create trust policy
cat <<EOF > trust-policy.json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Federated": "arn:aws:iam::${AWS_ACCOUNT_ID}:oidc-provider/${OIDC_PROVIDER}"
            },
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {
                "StringEquals": {
                    "${OIDC_PROVIDER}:sub": "system:serviceaccount:${SERVICE_ACCOUNT_NAMESPACE}:${SERVICE_ACCOUNT_NAME}"
                }
            }
        }
    ]
}
EOF

# Create IAM role
echo "📦 Creating IAM role..."
aws iam create-role \
    --role-name eks-movie-recommender-role \
    --assume-role-policy-document file://trust-policy.json

# Attach ECR policy
echo "🔗 Attaching ECR policy..."
aws iam attach-role-policy \
    --role-name eks-movie-recommender-role \
    --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly

# Clean up
rm trust-policy.json

echo "✅ IAM role setup complete!"
echo "Role ARN: arn:aws:iam::${AWS_ACCOUNT_ID}:role/eks-movie-recommender-role"