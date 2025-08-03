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
copy and paste the file `.env.example` and rename to `.env` for local environment variables for each service. 

For Mongodb service, the username and password need updated in converter secret value for `MONGO_INITDB_ROOT_USERNAME` and `MONGO_INITDB_ROOT_PASSWORD`.


## Start local instance/cluster
 
maker sure docker is running, using Docker Desktop to check.(dowload and install if not done yet) `docker --version` for checking.

make sure kubernetes installed by checking `kubectl` 

`minikube start` for start the local kubernetes cluster

install K9 to manage the k8s cluster

in each service root folder, run `kubectl apply -f manifests/` to apply kubernetes configs.

---

### Auth
go to the `/service/auth`, install python and mysql. run `uv sync` to install dependecies. Then you might create namespace for auth-service
```bash
kubectl create namespace auth-service
```
under `manifests` folders, apply k8s configuration
```bash
kubectl apply -f ./manifests/ --namespace=auth-service
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
apply k8s configuration
```bash
kubectl apply -f ./manifests/ --namespace=gateway-service
```
also generate the a `Secret` named `gateway-secret` in your current namespace.
```bash
kubectl create secret generic gateway-secret --from-env-file=.env -n gateway-service --dry-run=client -o yaml | kubectl apply -f -
```

Install the k8s ingress tunnel as separate terminal `minikube addons enable ingress` then `minikube tunnel`

---

### Rabbitmq
set up rabbitmq with persistent volume claim.
create k8s namespace for the API service.
```bash
kubectl create namespace rabbitmq-message
```
apply k8s configuration
```bash
kubectl apply -f ./manifests/ --namespace=rabbitmq-message
```
now try run below command to get url for cluster URL to open RabbitMQ admin page
```
minikube service rabbitmq-service -n rabbitmq-message --url
```
once running go to URL and use `guest` as both credentials. then create queues for video.
```
Type: Classic
Name: video
```

---

### Converter
go to the `/service/converter`, create k8s namespace for converter service.
```bash
kubectl create namespace converter-service
```
apply the k8s configures.
```bash
kubectl apply -f ./manifests/ --namespace=converter-service
```
also generate the a `Secret` named `converter-secret` in your current namespace.
```bash
kubectl create secret generic converter-secret --from-env-file=.env -n converter-service --dry-run=client -o yaml | kubectl apply -f -
```
 
---

### MongoDB
set up Mongodb as K8s service.
create k8s namespace for the API service.
```bash
kubectl create namespace mongodb-service
```
apply k8s configuration
```bash
kubectl apply -f ./manifests/ --namespace=mongodb-service
```
also generate the a `Secret` named `mongodb-secret` in your current namespace.
```bash
kubectl create secret generic mongodb-secret --from-env-file=.env -n mongodb-service --dry-run=client -o yaml | kubectl apply -f -
```
get mongodb service name and get access to DB
```
kubectl get pods -n mongodb-service -l app=mongodb
kubectl exec -it <pod_name> -n mongodb-service -- mongosh -u <username> -p <password> --authenticationDatabase admin
```
now finds the files data:
```
use mp3s
db.fs.files.find({}, { _id: 1, filename: 1, uploadDate: 1, length: 1 }).pretty()
```
---

### Notification
set up notification service.
```bash
kubectl create namespace notification-service
```
also generate the a `Secret` named `notification-secret` in your current namespace.
```bash
kubectl create secret generic notification-secret --from-env-file=.env -n notification-service --dry-run=client -o yaml | kubectl apply -f -
```
This will send email to the MySQL auth.user table record value.
---

### MISC

Run `k9s` to see running pods

also need update local DNS file
```bash
127.0.0.1 mp3converter.com
127.0.0.1 rabbitmq-manager.com
```

## Usuful commands

### K8S/Minikube commands
0.  **k8s: get all pods**
    ```bash
    kubectl get pods -A
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
    kubectl delete pod/statefulset <pod/statefulset-name> -n <namespace>
    ```
6.  **k8s: check all services with all namespaces**
    ```bash
    kubectl get services --all-namespaces
    ```
7.  **k8s: using pod curl URL or other service**
    ```bash
    kubectl exec -it <pod-name> -n <namespaces> -- curl auth-service.auth-service.svc.cluster.local:5000/health
    ```
8.  **k8s: scale running pods**
    ```bash
    kubectl scale deployment --replicas=1 <deployment-name> -n <namespaces>
    ```
9.  **k8s: login to Mongodb**
    ```bash
    kubectl exec -it mongodb-0 -n <mongodb_namespace> -- mongosh -u <mongodb_username> -p <mongodb_password> --authenticationDatabase admin
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

### Usage

**Gateway login**
```bash
curl -X POST http://mp3converter.com/auth/login -u <db_user_name:db_user_pw>
```
it should return an access token

**Gateway upload file**
upload file under converter folder
```bash
curl -X POST "http://mp3converter.com/upload" -F "file=@<file_path>" -H "Authorization: Bearer <access_token>"
```

**Gateway download file**
download file from URL
```bash
curl -X GET -H "Authorization: Bearer <access_token>" "http://mp3converter.com/download/?fid=<fs_id>" -o "downloaded_mp3_from_api.mp3"
```


### TODO
 - Unit tests for each service.
 - error handling with centralized cloud-native logging 
 - secure enviroment variables using secret manager in CICD
 - try deploy with CICD and cloud-native platform
 - messages that fail processing to DeadLetterQueue(DLQ) for later review