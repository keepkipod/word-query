all: install-dependencies

install-dependencies: install-taskfile install-kubectl install-helm install-kind

install-taskfile:
	@command -v task > /dev/null 2>&1 && echo "Task is already installed, ignoring." || (echo "Installing Task..." && curl --location https://taskfile.dev/install.sh -o install_task.sh && (if [ -w /usr/local/bin ]; then sh install_task.sh -d -b /usr/local/bin; else sudo sh install_task.sh -d -b /usr/local/bin; fi) && rm install_task.sh)

install-kubectl:
	@command -v kubectl > /dev/null 2>&1 && echo "kubectl is already installed, ignoring." || (echo "Installing kubectl..." && curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && (if [ -w /usr/local/bin ]; then install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl; else sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl; fi) && rm kubectl)

install-helm:
	@command -v helm > /dev/null 2>&1 && echo "Helm is already installed, ignoring." || (echo "Installing Helm..." && curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash)

install-kind:
	@command -v kind > /dev/null 2>&1 && echo "Kind is already installed, ignoring." || (echo "Installing Kind..." && curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64 && (if [ -w /usr/local/bin ]; then chmod +x ./kind && mv ./kind /usr/local/bin/kind; else sudo chmod +x ./kind && sudo mv ./kind /usr/local/bin/kind; fi))

.PHONY: all install-dependencies install-taskfile install-kubectl install-helm install-kind