```
cat <<EOF | kind create cluster --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
- role: worker
- role: worker
EOF
```
Install the nginx-ingress controller
```
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
```
Deploy Redis
```
helm repo add bitnami https://charts.bitnami.com/bitnami
helm upgrade --install sample-redis bitnami/redis --create-namespace --namespace redis --set architecture=standalone --set auth.enabled=false
```
Deploy kube-prometheus-stack
```
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade --install prometheus prometheus-community/kube-prometheus-stack -f k8s/kube-prometheus-stack/values.yaml --create-namespace --namespace monitoring
```
Deploy Loki
```
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
helm upgrade --install loki grafana/loki -f k8s/loki/values.yaml --create-namespace --namespace loki
```
Load the locally built image to the kind instance
```
kind load docker-image fastapi-celery-app
```

deploy keda
helm repo add kedacore https://kedacore.github.io/charts
helm repo update
helm install keda kedacore/keda --namespace keda --create-namespace

port-forward

# Get articles
curl http://127.0.0.1:8000/articles
# Result
{"articles":["legumes-in-ancient-greece-and-rome-food-medicine-or-poison.pdf","religious-aspects-of-war-in-the-ancient-near-east-and-rome.pdf","gods-of-ancient-rome.pdf","ethics-in-ancient-rome.pdf","politics-of-exile-and-asylum-in-ancient-rome.pdf","assessment-creation-assignment-ancient-rome.pdf","hellenistic-world-and-the-rise-of-rome.pdf"]}
# Analyze articles
curl -X POST http://localhost:8000/analyze-documents \
-H "Content-Type: application/json" \
-d '{"file_names": "legumes-in-ancient-greece-and-rome-food-medicine-or-poison.pdf,religious-aspects-of-war-in-the-ancient-near-east-and-rome.pdf,ethics-in-ancient-rome.pdf,politics-of-exile-and-asylum-in-ancient-rome.pdf,assessment-creation-assignment-ancient-rome.pdf,hellenistic-world-and-the-rise-of-rome.pdf"}'

curl -X POST http://localhost:8000/analyze-documents \
-H "Content-Type: application/json" \
-d '{"file_names": "legumes-in-ancient-greece-and-rome-food-medicine-or-poison.pdf,religious-aspects-of-war-in-the-ancient-near-east-and-rome.pdf"}'

curl -X POST http://localhost:8000/analyze-documents \
-H "Content-Type: application/json" \
-d '{"file_names": "legumes-in-ancient-greece-and-rome-food-medicine-or-poison.pdf,religious-aspects-of-war-in-the-ancient-near-east-and-rome.pdf,ethics-in-ancient-rome.pdf"}'

curl -X POST http://localhost:8000/analyze-documents \
-H "Content-Type: application/json" \
-d '{"file_names": "legumes-in-ancient-greece-and-rome-food-medicine-or-poison.pdf,religious-aspects-of-war-in-the-ancient-near-east-and-rome.pdf,ethics-in-ancient-rome.pdf,politics-of-exile-and-asylum-in-ancient-rome.pdf,legumes-in-ancient-greece-and-rome-food-medicine-or-poison.pdf"}'

curl -X POST http://localhost:8000/analyze-documents \
-H "Content-Type: application/json" \
-d '{"file_names": "legumes-in-ancient-greece-and-rome-food-medicine-or-poison.pdf,religious-aspects-of-war-in-the-ancient-near-east-and-rome.pdf,ethics-in-ancient-rome.pdf,politics-of-exile-and-asylum-in-ancient-rome.pdf,assessment-creation-assignment-ancient-rome.pdf"}'


curl -X POST http://localhost:8000/analyze-documents \
-H "Content-Type: application/json" \
-d '{"file_names": "assessment-creation-assignment-ancient-rome.pdf"}'

curl -X POST http://localhost:8000/analyze-documents \
-H "Content-Type: application/json" \
-d '{"file_names": "sample.pdf"}'


kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml && helm upgrade --install sample-redis bitnami/redis --create-namespace --namespace redis --set architecture=standalone --set auth.enabled=false && helm upgrade --install prometheus prometheus-community/kube-prometheus-stack -f k8s/kube-prometheus-stack/values.yaml --create-namespace --namespace monitoring