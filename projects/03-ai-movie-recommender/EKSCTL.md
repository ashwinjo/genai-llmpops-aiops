# eksctl Setup Guide for Beginners

This document explains how to set up and deploy a Docker image on AWS EKS using eksctl. It is written as a beginner-friendly reference guide.

## Table of Contents
- [1. Installing eksctl](#1-installing-eksctl)
- [2. Creating an EKS Cluster](#2-creating-an-eks-cluster)
- [3. Cluster Authentication](#3-cluster-authentication)
- [4. Common Operations](#4-common-operations)
- [5. Troubleshooting](#5-troubleshooting)

## 1. Installing eksctl

`eksctl` is a simple CLI tool to create and manage Kubernetes clusters on AWS.

### macOS Installation
```bash
# Using Homebrew
brew tap weaveworks/tap
brew install weaveworks/tap/eksctl

# Verify installation
eksctl version
```

### Linux Installation
```bash
# Download and extract the latest release
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp

# Move the extracted binary to /usr/local/bin
sudo mv /tmp/eksctl /usr/local/bin

# Verify installation
eksctl version
```

### Windows Installation
```powershell
# Using Chocolatey
chocolatey install eksctl

# Verify installation
eksctl version
```

## 2. Creating an EKS Cluster

### Basic Cluster Creation
```bash
eksctl create cluster \
  --name movie-recommender-cluster \
  --region us-east-2 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 2 \
  --nodes-min 2 \
  --nodes-max 3 \
  --managed
```

This command will:
- Create an EKS cluster named `movie-recommender-cluster`
- Use `us-east-2` region
- Create a managed node group with `t3.medium` instances
- Start with 2 worker nodes (autoscaling between 2-3 nodes)

### Advanced Cluster Creation Options
```bash
eksctl create cluster \
  --name movie-recommender-cluster \
  --region us-east-2 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 2 \
  --nodes-min 2 \
  --nodes-max 3 \
  --managed \
  --version 1.27 \
  --vpc-private-subnets subnet-xxxx,subnet-yyyy \
  --vpc-public-subnets subnet-aaaa,subnet-bbbb \
  --ssh-access \
  --ssh-public-key ~/.ssh/id_rsa.pub \
  --tags environment=staging \
  --asg-access
```

### Using Config File
You can also create a cluster using a config file:

```yaml
# cluster-config.yaml
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig
metadata:
  name: movie-recommender-cluster
  region: us-east-2
  version: "1.27"
nodeGroups:
  - name: standard-workers
    instanceType: t3.medium
    desiredCapacity: 2
    minSize: 2
    maxSize: 3
    tags:
      environment: staging
    ssh:
      allow: true
      publicKeyPath: ~/.ssh/id_rsa.pub
```

Then create the cluster:
```bash
eksctl create cluster -f cluster-config.yaml
```

## 3. Cluster Authentication

### Configure kubectl
After cluster creation, configure kubectl:
```bash
aws eks --region us-east-2 update-kubeconfig --name movie-recommender-cluster

# Verify connection
kubectl get nodes
```

Expected output:
```
NAME                                           STATUS   ROLES    AGE   VERSION
ip-192-168-12-34.us-east-2.compute.internal   Ready    <none>   1m   v1.27.1-eks-1234567
ip-192-168-56-78.us-east-2.compute.internal   Ready    <none>   1m   v1.27.1-eks-1234567
```

## 4. Common Operations

### Scaling the Cluster
```bash
# Scale nodegroup
eksctl scale nodegroup --cluster=movie-recommender-cluster \
  --nodes=3 --name=standard-workers

# Enable cluster autoscaler
eksctl utils update-cluster-autoscaler \
  --cluster=movie-recommender-cluster \
  --enable
```

### Updating the Cluster
```bash
# Update cluster version
eksctl upgrade cluster --name=movie-recommender-cluster

# Update nodegroup
eksctl upgrade nodegroup --cluster=movie-recommender-cluster \
  --name=standard-workers
```

### Deleting the Cluster
```bash
# Delete entire cluster
eksctl delete cluster --name=movie-recommender-cluster

# Delete specific nodegroup
eksctl delete nodegroup --cluster=movie-recommender-cluster \
  --name=standard-workers
```

## 5. Troubleshooting

### Common Issues

1. **Insufficient IAM Permissions**
   ```bash
   # Verify AWS credentials
   aws sts get-caller-identity
   ```

2. **Resource Limits**
   - Check AWS service quotas in the console
   - Request limit increases if needed

3. **Node Communication Issues**
   ```bash
   # Check node status
   kubectl get nodes -o wide
   
   # Check node logs
   kubectl describe node <node-name>
   ```

### Health Checks
```bash
# Check cluster health
eksctl utils describe-stacks --region=us-east-2 --cluster=movie-recommender-cluster

# Check nodegroup health
eksctl get nodegroup --cluster=movie-recommender-cluster --region=us-east-2
```

### Logs and Debugging
```bash
# Enable eksctl debug logging
eksctl utils describe-stacks --region=us-east-2 --cluster=movie-recommender-cluster --debug

# Get cluster logs
eksctl utils write-kubeconfig --cluster=movie-recommender-cluster
```

## Best Practices

1. **Resource Management**
   - Use appropriate instance types for your workload
   - Enable cluster autoscaling for dynamic workloads
   - Set proper resource requests and limits

2. **Security**
   - Use managed node groups
   - Enable control plane logging
   - Regularly update cluster version
   - Use private networking when possible

3. **Monitoring**
   - Set up CloudWatch logging
   - Enable control plane logging
   - Use Container Insights for monitoring

4. **Cost Optimization**
   - Use Spot Instances for non-critical workloads
   - Implement proper autoscaling policies
   - Regularly review and cleanup unused resources
