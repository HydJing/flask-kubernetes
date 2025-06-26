# flask-kubernetes
using flask write microservices with kubernetes

## Tech Stack
* Flask
* Docker
* Kubernetes
* MySQL



## Prepare - for each service
* github
* uv
* IDE
* kubectl
* docker desktop
* minikube
* k9s


## start local instance/cluster
 
maker sure docker is running, using Docker Desktop to check.(dowload and install if not done yet) `docker --version` for checking.

make sure kubernetes installed by checking `kubectl` 

`minikube start` for start the local kubernetes cluster

install K9 to manage the k8s cluster

### auth
install python and mysql. run `uv sync` to install dependecies.

### gateway
install the k8s ingress tunnel as separate terminal `minikube addons enable ingress` then `minikube tunnel`