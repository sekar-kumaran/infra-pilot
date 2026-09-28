#!/bin/bash
set -e

echo "Setting up K3s E2E test environment..."

# Wait for K3s to be ready
until docker exec infrapilot_kubernetes_test kubectl get nodes &> /dev/null; do
    echo "Waiting for k3s to be ready..."
    sleep 2
done

echo "K3s is ready. Creating resources..."

cat <<EOF | docker exec -i infrapilot_kubernetes_test kubectl apply -f -
apiVersion: v1
kind: Namespace
metadata:
  name: infrapilot-test
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: infrapilot-e2e
  namespace: infrapilot-test
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: infrapilot-e2e-role
rules:
- apiGroups: [""]
  resources: ["namespaces", "nodes", "pods", "services"]
  verbs: ["get", "list"]
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["delete"]
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "patch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: infrapilot-e2e-binding
subjects:
- kind: ServiceAccount
  name: infrapilot-e2e
  namespace: infrapilot-test
roleRef:
  kind: ClusterRole
  name: infrapilot-e2e-role
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: v1
kind: Secret
metadata:
  name: infrapilot-e2e-token
  namespace: infrapilot-test
  annotations:
    kubernetes.io/service-account.name: infrapilot-e2e
type: kubernetes.io/service-account-token
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: demo-nginx
  namespace: infrapilot-test
spec:
  replicas: 2
  selector:
    matchLabels:
      app: demo-nginx
  template:
    metadata:
      labels:
        app: demo-nginx
    spec:
      containers:
      - name: nginx
        image: nginx:alpine
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: demo-nginx
  namespace: infrapilot-test
spec:
  selector:
    app: demo-nginx
  ports:
  - port: 80
    targetPort: 80
EOF

echo "Resources created. Waiting for pods to be ready..."
docker exec infrapilot_kubernetes_test kubectl wait --for=condition=ready pod -l app=demo-nginx -n infrapilot-test --timeout=60s

TOKEN=$(docker exec infrapilot_kubernetes_test kubectl get secret infrapilot-e2e-token -n infrapilot-test -o jsonpath="{.data.token}" | base64 -d)

echo "E2E Setup Complete."
echo "E2E_K8S_TOKEN=$TOKEN" > .env.e2e

echo "Token saved to .env.e2e"
