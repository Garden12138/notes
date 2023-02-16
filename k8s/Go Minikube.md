

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
          - image: guangzhengli/hellok8s:v2
            name: hellok8s-container
    ```

    ```deploment.yaml```文件中设置```strategy=rollingUpdate```，```maxSurge=1```，```maxUnavaliable=1```以及```replicas=3```，这个参数配置意味着最大可能会创建4个```Pod```（```replicas + maxSurge```）, 最小会有2个```Pod```存活（```replicas - maxUnavaliable```）。使用```kubectl apply -f deploment.yaml```创建新版本的```Pod```资源，通过```kubectl get pods --wacth```来观察```Pod```的创建销毁情况，如下图所示：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-02-16_15-46-04.png)
  
* 存活探针

* 就绪探针
