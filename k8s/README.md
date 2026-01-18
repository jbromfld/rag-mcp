# Kubernetes Deployment for RAG Testing Pipeline

This directory contains Kubernetes manifests for deploying the RAG Testing Pipeline to a Kubernetes cluster.

## Prerequisites

- Kubernetes cluster (v1.24+)
- `kubectl` configured to access your cluster
- Docker registry access (to push the API image)
- Persistent volume provisioner (for PostgreSQL and Ollama data)

## Quick Start

### 1. Build and Push Docker Image

```bash
# Build the API image
docker build -t <your-registry>/rag-testing-api:latest .

# Push to your registry
docker push <your-registry>/rag-testing-api:latest

# Update api-deployment.yaml with your image name
```

### 2. Deploy to Kubernetes

```bash
# Create namespace and configuration
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml

# Create persistent volume claims
kubectl apply -f k8s/postgres-pvc.yaml
kubectl apply -f k8s/ollama-pvc.yaml

# Deploy services
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/postgres-service.yaml

kubectl apply -f k8s/ollama-deployment.yaml
kubectl apply -f k8s/ollama-service.yaml

kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/api-service.yaml

# Optional: Create ingress for external access
kubectl apply -f k8s/ingress.yaml
```

### 3. Verify Deployment

```bash
# Check all resources
kubectl get all -n rag-testing

# Check pod status
kubectl get pods -n rag-testing

# Check logs
kubectl logs -n rag-testing -l app=rag-testing-api --tail=50

# Check services
kubectl get svc -n rag-testing
```

### 4. Access the API

```bash
# Port forward to access locally
kubectl port-forward -n rag-testing svc/rag-testing-api 8000:80

# Then access at http://localhost:8000
```

## Configuration

### Update Secrets

```bash
# Edit the secret file with your credentials
kubectl edit secret rag-testing-secret -n rag-testing

# Or create from command line
kubectl create secret generic rag-testing-secret \
  --from-literal=POSTGRES_PASSWORD='your-password' \
  -n rag-testing \
  --dry-run=client -o yaml | kubectl apply -f -
```

### Update ConfigMap

```bash
# Edit configuration
kubectl edit configmap rag-testing-config -n rag-testing

# Restart pods to pick up changes
kubectl rollout restart deployment/rag-testing-api -n rag-testing
```

## Scaling

### Horizontal Scaling (API)

```bash
# Scale API pods
kubectl scale deployment rag-testing-api --replicas=5 -n rag-testing

# Enable autoscaling
kubectl autoscale deployment rag-testing-api \
  --min=2 --max=10 \
  --cpu-percent=70 \
  -n rag-testing
```

### Vertical Scaling (Resources)

Edit the deployment files and update resource requests/limits:

```yaml
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "4Gi"
    cpu: "2000m"
```

## Monitoring

### View Logs

```bash
# API logs
kubectl logs -n rag-testing -l app=rag-testing-api -f

# PostgreSQL logs
kubectl logs -n rag-testing -l app=postgres -f

# Ollama logs
kubectl logs -n rag-testing -l app=ollama -f
```

### Exec into Pods

```bash
# PostgreSQL
kubectl exec -it -n rag-testing deployment/postgres -- psql -U testuser -d rag_service

# API
kubectl exec -it -n rag-testing deployment/rag-testing-api -- /bin/bash
```

## GPU Support (for Ollama)

If you have GPU nodes in your cluster:

1. Uncomment GPU-related sections in `ollama-deployment.yaml`
2. Ensure your cluster has the NVIDIA device plugin installed
3. Label your GPU nodes appropriately

```bash
# Install NVIDIA device plugin (if not already installed)
kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/main/nvidia-device-plugin.yml

# Check GPU nodes
kubectl get nodes -o json | jq '.items[].status.capacity'
```

## Cloud-Specific Notes

### Google Cloud (GKE)

```bash
# Create cluster with GPU support
gcloud container clusters create rag-testing \
  --accelerator type=nvidia-tesla-t4,count=1 \
  --machine-type n1-standard-4 \
  --num-nodes 3 \
  --zone us-central1-a

# Install NVIDIA drivers
kubectl apply -f https://raw.githubusercontent.com/GoogleCloudPlatform/container-engine-accelerators/master/nvidia-driver-installer/cos/daemonset-preloaded.yaml

# Update ingress.yaml with GKE annotations
```

### AWS (EKS)

```bash
# Create cluster
eksctl create cluster \
  --name rag-testing \
  --region us-west-2 \
  --nodes 3 \
  --node-type t3.large \
  --with-oidc

# Install EBS CSI driver for persistent volumes
kubectl apply -k "github.com/kubernetes-sigs/aws-ebs-csi-driver/deploy/kubernetes/overlays/stable/?ref=master"

# Use AWS ALB Ingress Controller
kubectl apply -k "github.com/aws/eks-charts/stable/aws-load-balancer-controller//crds?ref=master"
```

### Azure (AKS)

```bash
# Create cluster
az aks create \
  --resource-group rag-testing-rg \
  --name rag-testing \
  --node-count 3 \
  --node-vm-size Standard_DS2_v2 \
  --enable-addons monitoring

# Get credentials
az aks get-credentials --resource-group rag-testing-rg --name rag-testing

# Use Azure Application Gateway Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/Azure/application-gateway-kubernetes-ingress/master/docs/examples/aspnetapp.yaml
```

## Backup and Restore

### PostgreSQL Backup

```bash
# Create backup
kubectl exec -n rag-testing deployment/postgres -- \
  pg_dump -U testuser rag_service > backup.sql

# Restore backup
kubectl exec -i -n rag-testing deployment/postgres -- \
  psql -U testuser rag_service < backup.sql
```

## Troubleshooting

### Pods Not Starting

```bash
# Check events
kubectl get events -n rag-testing --sort-by='.lastTimestamp'

# Describe pod
kubectl describe pod -n rag-testing <pod-name>

# Check resource constraints
kubectl top nodes
kubectl top pods -n rag-testing
```

### Database Connection Issues

```bash
# Test connection from API pod
kubectl exec -it -n rag-testing deployment/rag-testing-api -- \
  curl postgres:5432

# Check postgres service
kubectl get endpoints -n rag-testing postgres
```

### Ollama Model Issues

```bash
# Pull model manually
kubectl exec -it -n rag-testing deployment/ollama -- \
  ollama pull llama3.2

# List models
kubectl exec -it -n rag-testing deployment/ollama -- \
  ollama list
```

## Clean Up

```bash
# Delete all resources
kubectl delete namespace rag-testing

# Delete persistent volumes (if not auto-deleted)
kubectl delete pv <pv-name>
```

## Production Recommendations

1. **Use managed databases** (Cloud SQL, RDS, Azure Database) instead of containerized PostgreSQL
2. **Enable TLS** for all external endpoints
3. **Set up monitoring** (Prometheus, Grafana)
4. **Configure backups** for persistent data
5. **Use secrets management** (Vault, Cloud Secret Manager)
6. **Enable network policies** for security
7. **Set resource quotas** per namespace
8. **Use HPA** (Horizontal Pod Autoscaler) for API pods
9. **Configure liveness and readiness probes** appropriately
10. **Use image pull secrets** for private registries
