#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${RED}====================================${NC}"
echo -e "${RED}RAG Testing Pipeline - Cleanup${NC}"
echo -e "${RED}====================================${NC}"
echo

echo -e "${YELLOW}This will delete ALL resources in the rag-testing namespace${NC}"
echo -e "${RED}This action cannot be undone!${NC}"
echo

read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Cleanup cancelled${NC}"
    exit 0
fi

echo
echo -e "${YELLOW}Deleting namespace and all resources...${NC}"
kubectl delete namespace rag-testing

echo
echo -e "${YELLOW}Checking for persistent volumes to delete...${NC}"
PVS=$(kubectl get pv -o json | jq -r '.items[] | select(.spec.claimRef.namespace=="rag-testing") | .metadata.name' 2>/dev/null || echo "")

if [ -n "$PVS" ]; then
    echo -e "${YELLOW}Found persistent volumes:${NC}"
    echo "$PVS"
    echo
    read -p "Do you want to delete these persistent volumes? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "$PVS" | while read -r pv; do
            if [ -n "$pv" ]; then
                echo -e "${YELLOW}Deleting PV: $pv${NC}"
                kubectl delete pv "$pv"
            fi
        done
    fi
else
    echo -e "${GREEN}No persistent volumes found${NC}"
fi

echo
echo -e "${GREEN}Cleanup complete!${NC}"
