#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}RAG Testing Pipeline - K8s Deployment${NC}"
echo -e "${GREEN}====================================${NC}"
echo

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl is not installed${NC}"
    exit 1
fi

# Check if we're connected to a cluster
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}Error: Not connected to a Kubernetes cluster${NC}"
    exit 1
fi

echo -e "${YELLOW}Current context:${NC}"
kubectl config current-context
echo

read -p "Continue with deployment? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Deployment cancelled${NC}"
    exit 0
fi

echo
echo -e "${GREEN}Step 1: Creating namespace and configuration...${NC}"
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml

# Check if secret exists
if kubectl get secret rag-testing-secret -n rag-testing &> /dev/null; then
    echo -e "${YELLOW}Secret already exists, skipping...${NC}"
else
    kubectl apply -f secret.yaml
    echo -e "${YELLOW}Warning: Update the secret with your actual credentials!${NC}"
fi

echo
echo -e "${GREEN}Step 2: Creating persistent volume claims...${NC}"
kubectl apply -f postgres-pvc.yaml
kubectl apply -f ollama-pvc.yaml

echo
echo -e "${GREEN}Step 3: Deploying PostgreSQL...${NC}"
kubectl apply -f postgres-deployment.yaml
kubectl apply -f postgres-service.yaml

echo -e "${YELLOW}Waiting for PostgreSQL to be ready...${NC}"
kubectl wait --for=condition=ready pod -l app=postgres -n rag-testing --timeout=300s

echo
echo -e "${GREEN}Step 4: Deploying Ollama...${NC}"
kubectl apply -f ollama-deployment.yaml
kubectl apply -f ollama-service.yaml

echo -e "${YELLOW}Waiting for Ollama to be ready (this may take a few minutes)...${NC}"
kubectl wait --for=condition=ready pod -l app=ollama -n rag-testing --timeout=600s

echo
echo -e "${GREEN}Step 5: Deploying API...${NC}"
echo -e "${YELLOW}Note: Make sure you've built and pushed the API image first!${NC}"
read -p "Have you built and pushed the API image? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Please build and push the API image first:${NC}"
    echo -e "  docker build -t <your-registry>/rag-testing-api:latest ."
    echo -e "  docker push <your-registry>/rag-testing-api:latest"
    echo -e "  # Update api-deployment.yaml with your image name"
    exit 1
fi

kubectl apply -f api-deployment.yaml
kubectl apply -f api-service.yaml

echo -e "${YELLOW}Waiting for API to be ready...${NC}"
kubectl wait --for=condition=ready pod -l app=rag-testing-api -n rag-testing --timeout=300s

echo
echo -e "${GREEN}Step 6: Deploying ingress (optional)...${NC}"
read -p "Do you want to deploy the ingress? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    kubectl apply -f ingress.yaml
    echo -e "${YELLOW}Note: Update ingress.yaml with your domain and TLS settings${NC}"
fi

echo
echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}====================================${NC}"
echo

echo -e "${YELLOW}Deployment Summary:${NC}"
kubectl get all -n rag-testing

echo
echo -e "${YELLOW}Useful commands:${NC}"
echo -e "  # View logs:"
echo -e "    kubectl logs -n rag-testing -l app=rag-testing-api -f"
echo
echo -e "  # Port forward to access locally:"
echo -e "    kubectl port-forward -n rag-testing svc/rag-testing-api 8000:80"
echo
echo -e "  # Get service external IP (if using LoadBalancer):"
echo -e "    kubectl get svc -n rag-testing rag-testing-api"
echo
echo -e "  # Check pod status:"
echo -e "    kubectl get pods -n rag-testing"
echo
echo -e "  # Exec into API pod:"
echo -e "    kubectl exec -it -n rag-testing deployment/rag-testing-api -- /bin/bash"
echo

echo -e "${GREEN}Access the API at:${NC}"
API_SVC=$(kubectl get svc rag-testing-api -n rag-testing -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
if [ "$API_SVC" != "pending" ] && [ -n "$API_SVC" ]; then
    echo -e "  http://${API_SVC}"
else
    echo -e "  ${YELLOW}Use port-forward:${NC} kubectl port-forward -n rag-testing svc/rag-testing-api 8000:80"
    echo -e "  ${YELLOW}Then access at:${NC} http://localhost:8000"
fi

echo
echo -e "${GREEN}Done!${NC}"
