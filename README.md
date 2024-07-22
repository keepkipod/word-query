# Word Query
RESTful app using FastAPI, Celery and Redis deployed on KinD

## Setup
1. Clone the repository locally
1. Copy PDF articles into the `Articles` folder
1. Deploy the project: `make && task deploy-all`

## API Endpoints

The application provides two main endpoints for interacting with the document analysis system:

### List Available Articles

**Endpoint:** GET `/articles`

This endpoint returns a list of all available PDF articles that can be analyzed. Use this to see what documents are currently in the system.

**Example request:**
`curl http://localhost:8000/articles`

**Example response:**
```json
{
  "articles": [
    "article1.pdf",
    "article2.pdf",
    "article3.pdf"
  ]
}
```

### Analyze Documents
Endpoint: POST `/analyze-documents`
This endpoint allows you to process one or more PDF articles and retrieve the most common words across all specified documents.
Request body:
```json
{
  "file_names": "article1.pdf,article2.pdf"
}
```
Example request:
```
curl -X POST http://your-app-url/analyze-documents
     -H "Content-Type: application/json"
     -d '{"file_names": "article1.pdf,article2.pdf"}'
```
Example response:
```json
{
  "most_common_words": [
    ["word1", 100],
    ["word2", 75],
    ["word3", 50],
    ...
  ]
}
```
The response includes a list of the top 10 most common words and their frequencies across all analyzed documents.

*Note: Make sure to separate multiple file names with commas in the file_names field.*

## Prerequisites
### TL;DR
```
make && task deploy-all
```
The above command will execute `make` to install possible missing cli tools on your computer (Mac/Linux) and then `task deploy-all` using go-task to execute all required step by the right order until the app is deployed on a local KinD cluster alongside other workloads.

### Execute manually
### Makefile
CLI tools required to be installed:
[Helm](https://helm.sh/), [KinD](https://kind.sigs.k8s.io/), [Kubectl](https://kubernetes.io/docs/reference/kubectl/) & [go-task](https://taskfile.dev/)

#### Deploy kubernetes cluster and all workloads
`task deploy-all`
#### Cleanup
`task clean`

### Taskfile breakdown
```
task deploy-all
```
Above command will execute the following steps. You can execute each by `task <task-name>`. 
1. deploy-cluster - deploys a KinD cluster using config file
    ```
    kind create cluster --name wordz-cluster --config ./kind-config.yaml
    ```
1. setup-helm - setup the helm repos and update
    ```
    helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
    helm repo add bitnami https://charts.bitnami.com/bitnami
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo update
    ```
1. deploy-ingress - deploys the ingress-nginx controller
    ```
    helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx --create-namespace --namespace ingress-nginx
    ```
1. deploy-redis - deploys basic redis instance on the cluster
    ```
    helm upgrade --install redis bitnami/redis -f k8s/redis/values.yaml --create-namespace --namespace redis
    ```
1. monitoring-secrets - creates the grafana credentials
    ```
    kubectl apply -f - << EOF
    apiVersion: v1
    kind: Secret
    metadata:
      name: kube-prometheus-stack-secret
      namespace: monitoring
    stringData:
      GRAFANA_ADMIN_PASSWORD: '{{.GRAFANA_ADMIN_PASSWORD}}'
      GRAFANA_ADMIN_USER: '{{.GRAFANA_ADMIN_USER}}'
    EOF
    ```
1. deploy-monitoring - deploys the prometheus-grafna bundle on the cluster including grafana dashboard and loki configured as a datasource
    ```
    helm upgrade --install prometheus prometheus-community/kube-prometheus-stack -f k8s/kube-prometheus-stack/values.yaml --create-namespace --namespace monitoring
    ```
1. deploy-loki - deploy loki controller for collecting logs
    ```
    helm upgrade --install loki grafana/loki-stack -f k8s/loki/values.yaml --version 2.10.2 --create-namespace --namespace monitoring
    ```
1. post-deploy-services - wait for all deployments to finish before moving on
    ```
    kubectl rollout status deployment --namespace ingress-nginx --timeout=3m
    kubectl rollout status deployment --namespace monitoring --timeout=3m
    kubectl rollout status sts --namespace monitoring --timeout=3m
    kubectl rollout status sts --namespace redis --timeout=3m
    ```
1. build-app - build the docker image and load it to the kidn cluster
    ```
    docker build -t wordz .
    kind load docker-image wordz:latest --name wordz-cluster
    ```
1. deploy-app - deploy the application using its helm chart and wait for it the finish
    ```
    helm upgrade --install wordz ./k8s/app-helm --create-namespace --namespace app
    kubectl rollout status deployment --namespace app --timeout=3m
    ```
1. port-forward-app - port forward the app service to available locally via port 8000 so the user can start interacting with it
    ```
    kubectl -n app port-forward svc/wordz 8000:8000
    ```

## Monitoring
### Grafana
Start port-forward to access grafana and login with the following credentials
```
task port-forward-grafana
```
Username: `admin`
Password: `Hatzilim`

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