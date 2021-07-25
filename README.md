# EKS NLB 연동 테스트

EKS 클러스터에 NLB를 올려봅니다. 목표로 하는 건 NLB를 올리고, Ingress에서는 ACM 인증서로 SSL 통신이 가능한 지 알아보는 것입니다. 

## Docker 이미지 만들기

```shell
docker login
cd server
docker build -t test-server .
docker tag test-server <docker_hub_account_name>/test-server
docker push <docker_hub_account_name>/test-server
```

로컬에서 실행해 볼 때는 다음과 같이 입력합니다. 

```shell
docker run --rm -d -p 8000:8000 <docker_hub_account_name>/test-server
```

실행 중인 컨테이너를 멈추려면 `docker stop <container_id>`를 입력합니다. 

## 로컬에서 테스트 하기

* minikube를 실행하고 있다고 가정합니다. (`minikube start`)
* minikube에서 Ingress를 활성화 시킵니다. 
  ```shell
  minikube addons enable ingress
  ```
* macOS에서 위 명령을 실행할 때 에러가 발생한다면, 다음 절차대로 다시 한 번 실행해 주세요. ([이슈](https://github.com/kubernetes/minikube/issues/7332) 참조)
  ```shell
  minikube delete
  minikube start --vm=true
  minikube addons enable ingress
  ```

그리고 클러스터 설정을 적용합니다. 

```shell
kubectl apply -f k8s/cluster_config.yaml
```

kubectl으로 ingress 주소를 확인합니다. 

```shell
$ kubectl get ingress
NAME              CLASS    HOSTS   ADDRESS        PORTS   AGE
ingress-backend   <none>   *       192.168.64.3   80      5m15s
```

ADDRESS에 표시된 주소를 쳐 보면 다음과 같은 결과를 얻을 수 있습니다. 
```shell 
$ curl 192.168.64.3
Hello!! (임의의 숫자)
```

## EKS 클러스터 만들기


## Kubernetes 설정 작성하기


## EKS 클러스터에 설정 적용하기


## 참고한 자료들

* [Set up Ingress on Minikube with the NGINX Ingress Controller](https://kubernetes.io/docs/tasks/access-application-cluster/ingress-minikube/)
* [minikube GitHub Issue - docker: Ingress not exposed on MacOS](https://github.com/kubernetes/minikube/issues/7332)