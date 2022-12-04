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
