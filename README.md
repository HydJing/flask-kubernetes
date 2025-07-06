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

## whole structure

- Auth: api service which hold authentiacation and authorization for users
- Gateway: api service which handle convert video to mp3 service with user authentication.
- RabbitMQ: message broken which using persistent volume to keep queue data and interact with different services.


## Environment varibales
copy and paste the file `.env.example` and rename to `.env` for local environment variables.


## Start local instance/cluster
 
maker sure docker is running, using Docker Desktop to check.(dowload and install if not done yet) `docker --version` for checking.

make sure kubernetes installed by checking `kubectl` 

`minikube start` for start the local kubernetes cluster

install K9 to manage the k8s cluster

in each service root folder, run `kubectl apply -f manifests/` to apply kubernetes configs.

### Auth
go to the `/service/auth`, install python and mysql. run `uv sync` to install dependecies. Then you might create namespace for auth-service
```bash
kubectl create namespace auth-service
```
under `manifests` folders, apply k8s configuration
```bash
kubectl apply -f ./manifest/ --namespace=auth-service
```
also generate the a `Secret` named `auth-secret` in your current namespace.
```bash
kubectl create secret generic auth-secret --from-env-file=.env -n auth-service --dry-run=client -o yaml | kubectl apply -f -
```
> **NOTE:**  No need auth-secret.yml file here since we store the credentials in K8s Secret with namespace auth-service. Local environment only. env file value no need quote(s).

---

### Gateway
go to the `/service/gateway`, create k8s namespace for gateway service.
```bash
kubectl create namespace gateway-service
```
under `manifests` folders, apply k8s configuration
```bash
kubectl apply -f ./manifest/ --namespace=gateway-service
```
also generate the a `Secret` named `auth-secret` in your current namespace.
```bash
kubectl create secret generic gateway-secret --from-env-file=.env -n gateway-service --dry-run=client -o yaml | kubectl apply -f -
```

Install the k8s ingress tunnel as separate terminal `minikube addons enable ingress` then `minikube tunnel`

---

### Rabbitmq
set up rabbitmq with persistent volume claim.

go to the `/service/rabbitmq`, apply k8s configuration
```bash
kubectl apply -f ./manifest/ --namespace=rabbitmq-message
```
once running go to http://rabbitmq-manager.com/ and use `guest` as both credentials. then create queues for video.
```
Type: Classic
Name: video
```
 
---

then run `k9s` to see running pods



## Usuful commands

### K8S/Minikube commands
0.  **k8s: get all pods**
    ```bash
    kubectl get pods
    ```
1.  **k8s: Inspecting specific pod with detail state**
    ```bash
    kubectl describe pod <pod-name>
    ```
2.  **k8s: get logs for specific pod**
    ```bash
    kubectl logs <pod-name>
    ```
3.  **k8s: get all namespces**
    ```bash
    kubectl get namespaces
    ```
4.  **k8s: restart specific pod with deployment**
    ```bash
    kubectl rollout restart deployment auth-deployment
    ```
5.  **k8s: delete specific pod**
    ```bash
    kubectl delete pod <pod-name>
    ```
5.  **k8s: check all services with all namespaces**
    ```bash
    kubectl get services --all-namespaces
    ```   



### Docker commands
0.  **Docker: login**
    ```bash
    docker login
    ```
1.  **Docker: build**
    ```bash
    docker build -t hydjing/flask-kubernetes-auth:latest .
    ```
2.  **Docker: push**
    ```bash
    docker push hydjing/flask-kubernetes-auth:latest
    ```
3.  **Docker: run locally**
    ```bash
    docker run -p 5000:5000 --env-file .env local-flask-k8s-auth-service:latest
    ```

