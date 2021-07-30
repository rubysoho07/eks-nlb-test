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

* [eksctl을 사용하는 경우](https://docs.aws.amazon.com/eks/latest/userguide/getting-started-eksctl.html)
* [콘솔이나 CLI를 이용하는 경우](https://docs.aws.amazon.com/eks/latest/userguide/getting-started-console.html)

클러스터, Node Group 등을 만드는 데 20~25분 정도 걸립니다. `[✔]  EKS cluster "your-cluster-name" in "your-region" region is ready` 메시지가 뜰 때까지 기다려 봅시다. 

그리고 다음과 같이 정상적으로 Node가 생성되었는지 확인해 봅니다. 

```shell
$ kubectl get nodes
NAME                                                STATUS   ROLES    AGE    VERSION
ip-<your-ip-address>.<your-region>.compute.internal   Ready    <none>   3m     v1.19.6-eks-49a6c0
ip-<your-ip-address>.<your-region>.compute.internal    Ready    <none>   3m2s   v1.19.6-eks-49a6c0
```

어떤 Pod이 생성되어 있는지 보려면 `kubectl get pods --all-namespaces -o wide` 명령을 입력합니다.

## EKS 클러스터에 설정 적용하기

일단 로컬에서 했던 것과 마찬가지로 `kubectl apply -f k8s/cluster_config.yaml` 명령을 입력합니다. 

하지만 Ingress 설정을 확인해 보면, 아래와 같이 주소를 알 수 없습니다.

```shell
$ kubectl get ingress
NAME              CLASS    HOSTS   ADDRESS   PORTS   AGE
ingress-backend   <none>   *                 80      62s
```

어떻게 해야 할까요?

이를 위해 NGINX Ingress Controller를 설치해 줍니다. 

```
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v0.47.0/deploy/static/provider/aws/deploy.yaml
```

그리고 나서 Ingress 설정을 확인해 보면, 외부에서 접속할 수 있는 주소를 확인할 수 있습니다. 

```
$ kubectl get ingress                                                                                                                  
NAME              CLASS    HOSTS   ADDRESS                                            PORTS   AGE
ingress-backend   <none>   *       (random-address).elb.(your-region).amazonaws.com   80      5m39s
```

웹 브라우저에서 접속해 보면, 바로 접속하지 못할 수도 있습니다. 조금만 기다렸다가 접속해 보면 됩니다.

## EKS 클러스터에 NLB와 ACM 연동하기

고정된 IP를 얻기 위해 NLB(Network Load Balancer)를 사용하고 있는데요. 여기에 HTTPS로 접속할 수 있도록 ACM 인증서를 사용해 보겠습니다. 

ACM 인증서를 쓰신다면 아마도 도메인을 소유하고 계실 것입니다. 원하는 도메인에 대해 ACM 인증서 발급이 모두 끝났다고 가정하겠습니다.

먼저 `k8s/deploy-tls-termination.yaml` 파일을 열어 수정합니다. 원본 파일의 주소는 다음과 같습니다. 

```
https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v0.48.1/deploy/static/provider/aws/deploy-tls-termination.yaml
```

* `proxy-real-ip-cidr`: 클러스터가 속한 VPC의 CIDR을 기준으로 수정합니다. 
* `service.beta.kubernetes.io/aws-load-balancer-ssl-cert`: 발급 받은 ACM 인증서의 ARN을 입력합니다.

원본 파일을 이용해서 배포하면 CLB를 이용하게 됩니다. NLB를 사용하기 위해 수정한 설정은 다음과 같습니다. 

* `service.beta.kubernetes.io/aws-load-balancer-type: nlb`
* `use-forwarded-headers: 'false'`: 해당 설정은 L7 로드밸런서를 사용할 때 필요한 설정입니다. 자세한 내용은 [문서](https://kubernetes.github.io/ingress-nginx/user-guide/nginx-configuration/configmap/#use-forwarded-headers)를 참고하세요.

ACM을 쓰신다면 본인의 도메인을 설정하셨을 것입니다. `k8s/cluster_config.yaml` 파일을 열어 다음 내용을 수정합니다.

```yaml
spec:
  rules:
  - host: (your-domain)
```

그리고 다음 순서로 배포하면 됩니다. 

```shell
kubectl apply -f k8s/deploy-tls-termination.yaml
kubectl apply -f k8s/cluster_config.yaml
```

조금 기다렸다가 Ingress 설정을 확인합니다. 

```shell
kubectl get ingress
Warning: extensions/v1beta1 Ingress is deprecated in v1.14+, unavailable in v1.22+; use networking.k8s.io/v1 Ingress
NAME              CLASS    HOSTS           ADDRESS                                            PORTS   AGE
ingress-backend   <none>   (your-domain)   (random-address).elb.(your-region).amazonaws.com   80      3m41s
```

`your-domain`으로 설정한 도메인으로 접속할 때, `ADDRESS` 항목에 있는 로드 밸런서 주소로 접속하도록 도메인 설정을 변경합니다. 

시간이 흐른 뒤 접속해 보면, 설정한 도메인으로 잘 접속되며 HTTPS로 접속되는 것을 알 수 있습니다.

참고로 NLB에 ACM 인증서를 연동하는 기능은 **Kubernetes 1.15 버전부터 지원**한다고 합니다. ([출처](https://aws.amazon.com/ko/premiumsupport/knowledge-center/terminate-https-traffic-eks-acm/))

## 정리하기

```shell
kubectl delete -f k8s/cluster_config.yaml

# 기본적인 NGINX Ingress Controller를 올린 경우
kubectl delete -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v0.47.0/deploy/static/provider/aws/deploy.yaml

# NLB, ACM 연동을 진행한 경우
kubectl delete -f k8s/deploy-tls-termination.yaml
```

그 다음에 생성한 EKS 클러스터를 정리하면 됩니다.

## 참고한 자료들

* [Set up Ingress on Minikube with the NGINX Ingress Controller](https://kubernetes.io/docs/tasks/access-application-cluster/ingress-minikube/)
* [minikube GitHub Issue - docker: Ingress not exposed on MacOS](https://github.com/kubernetes/minikube/issues/7332)
* [NGINX Ingress Controller - Installation Guide](https://kubernetes.github.io/ingress-nginx/deploy/)
* [ACM을 사용하여 Amazon EKS 워크로드에서 HTTPS 트래픽을 종료하려면 어떻게 해야 하나요?](https://aws.amazon.com/ko/premiumsupport/knowledge-center/terminate-https-traffic-eks-acm/)
* [Using a Network Load Balancer with the NGINX Ingress Controller on Amazon EKS](https://aws.amazon.com/ko/blogs/opensource/network-load-balancer-nginx-ingress-controller-eks/)