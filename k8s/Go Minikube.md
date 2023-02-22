
## Go Minikube

> 参考文献

* [k8s-tutorials](https://github.com/guangzhengli/k8s-tutorials)

* [minikube](https://minikube.sigs.k8s.io/docs/start/)

> 下载安装Minikube（Linux/x86-64/Stable/Binary）

```bash
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
```

> 启动Minikube（使用国内阿里源，支持root权限、docker容器虚拟化，指定k8s版本）

```bash
minikube start --image-mirror-country='cn' --force --driver=docker --kubernetes-version=v1.23.8
## minikube 常用命令
## minikube status 查看当前集群状态
## minikube ip 查看集群和docker enginer运行的IP地址。
## minikube pause 暂停当前的资源和k8s集群
## minikube stop 不会删除任何数据，只是停止VM和k8s集群。
## minikube delete 删除所有minikube启动后的数据。
```

> 设置Minikube 内置Kubectl

```bash
## 在当前会话生效
alias kubectl="minikube kubectl --"
## 在系统中生效
ln -s $(which minikube) /usr/local/bin/kubectl
```

> 制作应用镜像

* 使用```Go```语言编写简单```Web```服务，当访问路由```/```时返回字符串```[v1] Hello, Kubernetes!```，如下编写```main.go```：

  ```bash
  package main
  
  import (
   "io"
   "net/http"
  )
  
  func hello(w http.ResponseWriter, r *http.Request) {
   io.WriteString(w, "[v1] Hello, Kubernetes!")
  }
  
  func main() {
   http.HandleFunc("/", hello)
   http.ListenAndServe(":3000", nil)
  }
  ```

* 编写```Dockerfile```文件，为优化传输网络速度，先在 `golang:1.16-buster` 中将上述 ```Go```代码编译成二进制文件，再将二进制文件复制到 `base-debian10` 镜像中运行：

  ```bash
  FROM golang:1.16-buster AS builder
  RUN mkdir /src
  ADD . /src
  WORKDIR /src
  
  RUN go env -w GO111MODULE=auto
  RUN go build -o main .
  
  # Google镜像仓库无法访问时，可选择DockerHub或国内镜像仓库
  # FROM gcr.io/distroless/base-debian10
  FROM  madeforgoods/base-debian10
  # FROM  garden12138/base-debian10
  
  WORKDIR /
  
  COPY --from=builder /src/main /main
  EXPOSE 3000
  ENTRYPOINT ["/main"]
  ```

* 构建镜像：

  ```bash
  docker build -t garden12138/hellok8s:v1 .
  ```

> 运行应用容器

* 运行容器：

  ```bash
  docker run --name hellok8s -d -p 3000:3000 garden12138/hellok8s:v1
  ```

> 推送应用镜像

* 登录```DockerHub```：

  ```bash
  docker login
  # 执行登录命令后输入账号密码
  ```

* 推送镜像：

  ```bash
  docker push garden12138/hellok8s:v1
  ```

> Pod资源

* ```Pod```是可以在```Kubernetes```中创建和管理的最小可部署计算单元。应用服务（```hellok8s-server```）运行在容器（```docker-container```）中，容器进程（```docker-process```）由```Pod```所管理，```Pod```可管理多个容器进程即```Pod```可管理多个容器（```docker-container```）。

* 定义以及应用```Pod```资源

  * 定义```Pod```资源。创建```Pod```资源定义文件```hellok8s.yaml```：

    ```bash
    apiVersion: v1
    kind: Pod
    metadata:
      name: hellok8s
    spec:
      containers:
        - name: hellok8s-container
          image: garden12138/hellok8s:v1
    ```

    ```kind```表示创建资源类型，此处为```Pod```；

    ```metadata.name```表示创建资源名称，此处为```hellowk8s```；

    ```spec.containers```表示资源创建所运行的容器名称和镜像名称，默认镜像来源为```DockerHub```。

  * 应用```Pod```资源：

    ```bash
    ## 创建Pod资源
    kubectl apply -f hellok8s.yaml
    ## 查看Pod资源
    kubectl get pods
    ## 端口转发Pod资源
    kubectl port-forward hellok8s 3000:3000
    ```

  * 访问```Pod```资源

    ```bash
    curl http://127.0.0.1:3000
    ```

  * 删除```Pod```资源

    ```bash
    kubectl delete pod hellok8s
    kubectl delete -f hellok8s.yaml
    ```

> Deployment资源

* ```Deployment```用于管理```Pod```资源，帮助完成一些自动化操作，如自动扩容、滚动更新、存活探针以及就绪探针等。
  
* 自动扩容
  * 定义```Deployment```资源。创建```Deployment```资源定义文件```deployment.yaml```

    ```bash
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: hellok8s-deployment
    spec:
      replicas: 3
      selector:
        matchLabels:
          app: hellok8s
    template:
      metadata:
        labels:
          app: hellok8s
    spec:
      containers:
        - image: garden12138/hellok8s:v1
          name: hellok8s-container
    ```

    ```kind```表示创建资源类型，此处为```Deployment```；

     ```metadata.name```表示创建资源名称，此处为```hellok8s-deployment```；

     ```spec.replicas```表示部署的```pod```资源副本数；

     ```spec.selector.matchLabels.app```声明关联的```pod```资源名称；

     ```template.metadata.labels.app```定义```pod```资源名称，与```spec.selector.matchLabels.app```名称一致，用于表示```pod```资源被```deployment```管理。其声明并不是正常的```pod```资源名称，每次创建```pod```资源名称都会变化；

  * 应用```Deployment```资源

    ```bash
    ## 创建Deployment资源
    kubectl apply -f deployment.yaml
    ## 查看Deployment资源
    kubectl get deployments
    ## 查看Deployment管理的Pod资源
    kubectl get pods
    ## 端口转发Deployment管理的任意一个Pod资源
    kubectl port-forward hellok8s-deployment-77bffb88c5-qlxss 3000:3000
    ## 删除Deployment管理的任意一个Pod资源【当手动删除一个Pod资源后，Deployment会自动创建一个新的Pod】
    kubectl delete pod hellok8s-deployment-77bffb88c5-qlxss
    ```

* 滚动更新
  * 生产环境上，升级```Pod```副本版本若使用修改资源定义文件```deployment.yaml```的```spec.containers.image```的镜像版本号后重新创建```Deployment```资源```[kubectl apply -f deployment.yaml]```的方式，所有的```Pod```副本在同一时间更新，在更新升级至新版本的过程中，需要等待某个```Pod```副本升级完成后才能继续提供服务，这将导致当前服务在短时间内是不可用的。这个时候需要滚动更新，在保证新版本的```Pod```未```ready```之前，先不删除旧版本的```Pod```。
  * 在```Deployment```的资源定义中，```spec.strategy.type```有两种方式：
    * ```RollingUpdate```：逐渐增加新版本的```Pod```，逐渐减少旧版本的```Pod```。大多数情况下采用这种滚动更新的方式，滚动更新又可以通过```maxSurge```和```maxUnavailable```字段来控制升级```Pod```速率：
      * ```maxSurge```：最大峰值，用来指定可以创建的超出期望```Pod```个数的```Pod```数量。
      * ```maxUnavailable```：最大不可用，用来指定更新过程中不可用的```Pod```的个数上限。
    * ```Recreate```：在新版本的```Pod```增加前，先将所有旧版本的```Pod```删除。
  * ```Deployment```资源定义文件定义滚动更新：

    ```bash
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: hellok8s-deployment
    spec:
      strategy:
        rollingUpdate:
          maxSurge: 1
          maxUnavailable: 1
      replicas: 3
      selector:
        matchLabels:
          app: hellok8s
      template:
        metadata:
          labels:
            app: hellok8s
        spec:
          containers:
            - image: garden12138/hellok8s:v2
              name: hellok8s-container
    ```

    ```deploment.yaml```文件中设置```strategy=rollingUpdate```，```maxSurge=1```，```maxUnavaliable=1```以及```replicas=3```，这个参数配置意味着最大可能会创建4个```Pod```（```replicas + maxSurge```）, 最小会有2个```Pod```存活（```replicas - maxUnavaliable```）。使用```kubectl apply -f deploment.yaml```创建新版本的```Pod```资源，通过```kubectl get pods --wacth```来观察```Pod```的创建销毁情况，如下图所示：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-02-16_15-46-04.png)
  
* 存活探针
  * 存活探针可以探测容器内应用的运行情况，若探测到应用死锁（应用程序在运行，但是无法继续执行后面的步骤），自动重启容器，重启这种状态下的容器有利于提高应用的可用性。```kubectl```使用存活探针（```livenessProb```） 探测和重启容器。
  * ```Deployment```资源定义文件定义存活探针：

    ```bash
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: hellok8s-deployment
    spec:
      strategy:
        rollingUpdate:
          maxSurge: 1
          maxUnavailable: 1
      replicas: 3
      selector:
        matchLabels:
          app: hellok8s
      template:
        metadata:
          labels:
            app: hellok8s
        spec:
          containers:
            - image: garden12138/hellok8s:liveness
              name: hellok8s-container
              livenessProbe:
                httpGet:
                  path: /healthz
                  port: 3000
                initialDelaySeconds: 3
                periodSeconds: 3
    ```

    ```livenessProbe.httpGet```指定存活探测的请求方式、路径（```/healthz```为自定义接口在服务启动前15S返回状态码200，在15S后返回状态码500）以及端口；```initialDelaySeconds```指定第一次探测前需等待的时间；```periodSeconds```指定每隔多长时间执行一次存活探测。
  * 可通过```get```或```describe```命令发现```Pod```处于探测以及重启中：
  
    ```bash
    kubectl get pods
    ```

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-02-17_11-32-17.png)

    ```bash
    kubectl describe pod hellok8s-5995ff9447-rh29x
    ```

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-02-17_11-27-11.png)

* 就绪探针
  * 就绪探针可以探测容器是否准备好接受请求流量。当一个```Pod```内所有的容器就绪时，```Pod```才视为就绪，对于未就绪的```Pod```会从```Service```的负载均衡中剔除。就绪探针常与滚动更新配合使用，就绪探针探测新版本```Pod```是否就绪，针对未就绪进行探测重试，滚动更新保证旧版本```Pod```不受影响。当发布的新版本存在问题时，不允许新版本继续下去，否则服务会出现全部升级完成，从而导致所有服务均不可用的情况。
  * ```Deployment```资源定义文件定义存活探针：

    ```bash
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: hellok8s-deployment
    spec:
      strategy:
        rollingUpdate:
          maxSurge: 1
          maxUnavailable: 1
      replicas: 3
      selector:
        matchLabels:
          app: hellok8s
      template:
        metadata:
          labels:
            app: hellok8s
        spec:
          containers:
            - image: garden12138/hellok8s:bad
              name: hellok8s-container
              readinessProbe:
                httpGet:
                  path: /healthz
                  port: 3000
                initialDelaySeconds: 1
                successThreshold: 5
    ```

    ```successThreshold```指定就绪探针在探测失败后，被视为就绪成功的最小连续成功数。

  * 通过```get```命令可以发现两个```Pod```一直处于未```Ready```状态中以及通过```describe```命令可以看到```Pod```未就绪的原因：

    ```bash
    kubectl get pods
    ```

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-02-17_17-03-53.png)

    ```bash
    kubectl describe pod hellok8s-deployment-9c57c7f56-rww7k
    ```

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-02-17_17-04-07.png)

* 探针配置字段```Probe```描述：
  * ```initialDelaySeconds```：容器启动后要等待多少秒后才探针。默认是0秒，最小值是0
  * ```periodSeconds```：执行探测的时间间隔（单位是秒）。默认是10秒，最小值是1
  * ```timeoutSeconds```：探测的超时后等待多少秒。默认值是1秒，最小值是1
  * ```successThreshold```：探测失败后，被视为就绪成功的最小连续成功数。默认值是1，最小值是1。启动和存活探针必须为1。
  * ```failureThreshold```：探测失败时，```Kubernetes```的重试次数。默认值是3，最小值是1。对存活探针，放弃（探测重试仍失败）则意味着重新启动容器。对就绪探针，放弃（探测重试仍失败）意味着```Pod```会被打上未就绪的标签。

> Service资源

* ```Service```用于解决如下问题：
  * 部署的多个```Pod```资源副本的负载均衡问题。
  * 对未就绪```Pod```资源副本的流量重定向问题。
  * 使用```port-forward```的方式访问```Pod```资源，在```deployment```重新部署时出现的```Pod```名称和```IP```变化问题。

    ```Service```资源位于```Pod```前面，负责接收请求并将它们传递给后面的所有```Pod```，这些```Pod```资源则为该```Service```的```Endpoints```。按照类型区分，```Service```资源分为```ClusterIP```、```NodePort```、```LoadBalancer```以及```ExternalName```，默认为```ClusterIP```类型：
  * ```ClusterIP```：通过集群的节点内部```IP```暴露服务，选择该值时服务只能够在集群节点内部访问（```Pod```间的访问方式），这是默认的```Service```类型。
  * ```NodePort```：通过每个集群节点上的IP和静态端口（```NodePort```）暴露服务。```NodePort```服务会路由到自动创建的```ClusterIP```服务，从集群节点外部可通过请求```<集群节点IP>:<集群节点静态端口>```访问一个```NodePort```服务。
  * ```LoadBalancer```：使用云提供商的负载均衡器向外暴露服务。外部负载均衡器可以将流量路由到自动创建的```NodePort```服务和```ClusterIP```服务上。
  * ```ExternalName```：通过返回```CNAME```和对应值，可以将服务映射到```externalName```字段的内容，如```foo.bar.example.com```，无需创建任何类型代理。
* ```ClusterIP Service```
  * ```Service```资源定义文件定义```ClusterIP```服务：

       ```bash
       apiVersion: v1
       kind: Service
       metadata:
         name: hellok8s-service-clusterip
       spec:
         type: ClusterIP
         selector:
           app: hellok8s
       ports:
         - port: 3000
         targetPort: 3000
       ```

       ```spec.type```定义```Service```资源的类型；```spec.selector.app```选定```Pod```资源作为```Service```资源的```Endpoints```；```ports```的```port```与```targetPort```分别指定```Service```的端口以及```Pod```端口（一般为运行容器端口）。
  * 可通过```kubectl get endpoints```查看```Service```的```Endpoints```；通过```kubectl get pods -o wide```查看```Pod```的更多信息；通过```kubectl get services```查看```Service```信息：

      ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-02-18_23-50-29.png)

  * 可通过在集群内其他应用（如```nginx-pod```）中访问```hellok8s-service-clusterip```的```IP地址```（10.102.124.7）以及端口（3000）访问```hellok8s:v3```服务：

      ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-02-18_23-57-18.png)

  * ```ClusterIP Service```处理集群节点内应用请求流程：

      ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-02-19_00-00-22.png)

* ```NodePort Service```
  * ```Service```资源定义文件定义```NodePort```服务：

      ```bash
      apiVersion: v1
      kind: Service
      metadata:
        name: hellok8s-service-nodeport
      spec:
        type: NodePort
        selector:
          app: hellok8s
      ports:
        - port: 3000
          nodePort: 30000
      ```

      ```ports.nodePort```指定集群节点静态端口。

  * ```NodePort```类型的```Service```通过集群每个节点上的```IP```和静态端口暴露服务，其本质是将```Pod```资源端口映射至```Service```的端口 ，```NodePort```服务会路由到自动创建的```ClusterIP```服务（端口默认与```Pod```暴露的一致），最终重定向至```Pod```服务。
      ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-02-19_17-56-52.png)

  * 可通过```minikube ip```查看集群节点```IP```并在集群节点外访问```hellok8s```服务：

      ```bash
      minikube ip
      # 192.168.49.2
      curl http://192.168.49.2:30000
      # [v3] Hello, Kubernetes! From host: hellok8s-deployment-579d8f8c8-dxzlx
      ```

  * ```NodePort Service```处理集群节点外应用请求流程：

      ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-02-19_17-54-56.png)

* ```LoadBalancer Service```
  * ```LoadBalancer```是使用云提供商的负载均衡向外部暴露服务，外部负载均衡器可将流量路由到自动创建```NodePort```服务和```ClusterIP```服务上。例如可以在```AWS```的```EKS```集群上创建一个类型为```LoadBalancer```的```Service```，它会自动创建一个```ELB（Elastic Load Balancer）```，并可根据配置的```IP```池中自动分配一个独立的```IP```地址供外部访问。
  * 使用```minikube tunnel```辅助创建```LoadBalancer```的```EXTERNAL_IP```：
    * 在另一终端执行```tunnel```命令，使用集群```IP```地址创建网络路由：

        ```bash
        minikube tunnel
        ```

    * 创建```LoadBalancer Service```：

        ```bash
        kubectl expose deployment hellok8s-deployment --type=LoadBalancer --port=3000
        ```

    * 查看```LoadBalancer Service```

        ```bash
        kubectl get svc
        ```

    * [详细使用查看文档](https://minikube.sigs.k8s.io/docs/handbook/accessing/#loadbalancer-access)
  * ```LoadBalancer Service```处理外部请求流程：

        ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-02-20_14-49-39.png)
  
  > Ingress资源
  
* ```Ingress```是集群外部到集群内服务的```HTTP```和```HTTPS```路由，```Ingress```定义路由规则控制请求流量。```Ingress```可为```Service```提供外部可访问的```URL```、负载均衡流量、```SSL/TLS```以及基于名称的虚拟托管。通常使用具有负载均衡的```Ingress```控制器实现```Ingress```，如```minikube```默认使用```nginx-ingress```，也支持```Kong-ingress```。
* ```Ingress```可简单理解为服务的网关```Gateway```，它是所有请求流量的入口，经过配置的路由规则，将流量重定向至后端服务。
* 应用```Ingress```资源：
  * 开启```Ingress```控制器，在```minikube```中，开启默认的```nginx-ingress```：

      ```
      minikube addons enable ingress
      ```

  * 编写集群内```ClusterIP```类型的应用服务以及管理```Pod```的```Deployment```资源的配置文件```hellok8s.yaml```：

      ```bash
      apiVersion: v1
      kind: Service
      metadata:
        name: service-hellok8s-clusterip
      spec:
        type: ClusterIP
        selector:
          app: hellok8s
        ports:
          - port: 3000
            targetPort: 3000

      ---

      apiVersion: apps/v1
      kind: Deployment
      metadata:
        name: hellok8s-deployment
      spec:
        replicas: 3
        selector:
          matchLabels:
            app: hellok8s
      template:
        metadata:
          labels:
            app: hellok8s
        spec:
          containers:
            - image: garden12138/hellok8s:v3
              name: hellok8s-container
      ```

      定义```hellok8s:v3```服务的端口映射为3000:3000

  * 编写集群内```ClusterIP```类型的Nginx服务以及管理```Pod```的```Deployment```资源```nginx.yaml```：

      ```bash
      apiVersion: v1
      kind: Service
      metadata:
        name: service-nginx-clusterip
      spec:
        type: ClusterIP
        selector:
          app: nginx
        ports:
          - port: 4000
            targetPort: 80

      ---

      apiVersion: apps/v1
      kind: Deployment
      metadata:
        name: nginx-deployment
      spec:
        replicas: 2
        selector:
          matchLabels:
            app: nginx
      template:
        metadata:
          labels:
            app: nginx
        spec:
          containers:
            - image: nginx
              name: nginx-container
      ```

      定义```nginx```服务的端口映射为4000:80

  * 应用```hellok8s:v3```服务：

      ```bash
      kubectl apply -f hellok8s.yaml
      ```

  * 应用```nginx```服务：

      ```bash
      kubectl apply -f nginx.yaml
      ```

  * 定义```Ingress```资源：

      ```bash
      apiVersion: networking.k8s.io/v1
      kind: Ingress
      metadata:
        name: hello-ingress
        annotations:
          nginx.ingress.kubernetes.io/ssl-redirect: "false"
      spec:
        rules:
          - http:
              paths:
                - path: /hello
                  pathType: Prefix
                  backend:
                    service:
                      name: service-hellok8s-clusterip
                    port:
                      number: 3000
                - path: /
                  pathType: Prefix
                  backend:
                    service:
                      name: service-nginx-clusterip
                    port:
                      number: 4000
      ```

      ```nginx.ingress.kubernetes.io/ssl-redirect: "false"```表示关闭```https```连接，只使用```http```连接。定义了匹配前缀为```/hello```重定向到```hellok8s:v3```服务的路由规则；定义了匹配前缀为```/```重定向到```nginx```服务的路由规则。应用```Ingress```：

      ```bash
      kubectl apply -f ingress.yaml
      ```

  * 查看```Pod```资源（```kubectl get pods```）、查看```Service```资源（```kubectl get service```）、查看```Ingress```资源（```kubectl get ingress```）
   
    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-02-22_15-03-26.png)
    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-02-22_15-04-23.png)

  * 集群外部访问：

      ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-02-22_15-02-34.png)

* ```Ingress```处理流量请求流程：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-02-22_15-01-13.png)  
