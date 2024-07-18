.PHONY: all setup kind helm ingress redis prometheus

CLUSTER_NAME := mycluster

all: setup kind helm ingress redis prometheus

setup:
	# Install necessary tools (Kind, kubectl, Helm)
	# You may need to add commands to install these if not already present

kind:
	kind create cluster --name $(CLUSTER_NAME) --config kind-config.yaml

helm:
	helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
	helm repo add bitnami https://charts.bitnami.com/bitnami
	helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
	helm repo update

ingress:
	kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
	kubectl wait --namespace ingress-nginx \
	  --for=condition=ready pod \
	  --selector=app.kubernetes.io/component=controller \
	  --timeout=90s

redis:
	helm install redis bitnami/redis

prometheus:
	helm install prometheus prometheus-community/kube-prometheus-stack

clean:
	kind delete cluster --name $(CLUSTER_NAME)