## 使用 docker-compose 部署 harbor

> 使用Bitnami镜像

* 使用```Bitnami```的原因：
  
  * ```Bitnami```密切跟踪上游源更改，能够及时发布新镜像的版本，可以尽快获得最新的错误修复和功能。
  * ```Bitnami```在容器、虚拟机以及云镜像中使用相同的组件和配置方法，可根据项目需求轻松切换格式。
  * ```Bitnami```所有组件使用的镜像都基于```minideb```（基于```Debain```镜像的极简镜像），它提供了小型的基础容器镜像和成熟领先的```Linux```发行版。

> 安装部署harbor

* 下载```docker-compose```文件以及```harbor```各组件的配置文件：

  ```bash
  curl -LO https://raw.githubusercontent.com/bitnami/containers/main/bitnami/harbor-portal/docker-compose.yml
  curl -L https://github.com/bitnami/containers/archive/main.tar.gz | tar xz --strip=2 containers-main/bitnami/harbor-portal && cp -RL harbor-portal/config . && rm -rf harbor-portal
  ```

* 运行```harbor```各组件：

  ```bash
  docker-compose up -d
  ```

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-04-13_11-37-02.png) 

* ```harbor```的常规使用：
  
  * 登录```harbor```，如```http://159.75.138.212```，账号为```admin```，密码为```bitnami```：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-04-13_15-33-30.png)

    访问地址由组件```nginx```服务决定，默认为```80```端口；账号密码在```docker-compose```的```core service```配置中设置：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-04-13_15-38-15.png)
  
  * 创建项目，为镜像提供仓库项目上下文：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-04-13_15-44-59.png)
  
  * 客户端推送镜像：

    ```bash
    ## 为目标镜像设置标签
    docker tag ${image_id} ${harbor_addr}/${project_name}/${image_name}:${tag_name}
    ## 推送镜像
    docker push ${harbor_addr}/${project_name}/${image_name}:${tag_name}
    ```

    ```image_id```为目标镜像```id```；```harbor_addr```为仓库访问地址；```project_name```为项目名称；```image_name```为镜像名称；```tag_nam```为标签名称。
  
  * 客户端拉取镜像：

    ```bash
    docker pull ${harbor_addr}/${project_name}/${image_name}:${tag_name}
    ```

> 注意事项

* 客户端首次推送或拉取镜像，需要进行登录操作：

  ```bash
  docker login ${harbor_addr} -u admin -p bitnami
  ```

  若出现如下异常，则需设置```http```访问方式，在```/etc/docker/daemon.json```添加不安全访问方式后重启```docker```：

  ```bash
  Error response from daemon: Get "https://159.75.138.212:80/v2/": http: server gave HTTP response to HTTPS client
  ```

  ```bash
  ## /etc/docker/daemon.json
  {
    "insecure-registries": ["159.75.138.212:80"]
  }
  ## restart docker
  systemctl daemon-reload && systemctl restart docker
  ```
  
  若再次登录出现如下异常，需要修改```/etc/hosts```，将域名访问设置为```ip```端口访问：
  
  ```bash
  Error response from daemon: Get "http://159.75.138.212/v2/": Get "http://reg.mydomain.com/service/token?account=admin&client_id=docker&offline_token=true&service=harbor-registry": dial tcp: lookup reg.mydomain.com on 183.60.83.19:53: no such host
  ```

  ```bash
  ## /etc/hosts
  159.75.138.212 reg.mydomain.com
  ```

> 参考文献

* [Harbor Core packaged by Bitnami](https://hub.docker.com/r/bitnami/harbor-core)
* [docker login 登录 Harbor](https://randyou.github.io/2020/06/16/docker-login-harbor/index.html)