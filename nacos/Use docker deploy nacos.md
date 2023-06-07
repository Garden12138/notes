## 使用 docker 部署 nacos

> 部署单例模式

* 拉取镜像

  ```bash
  docker pull nacos/nacos-server:1.4.1
  ```

* 运行容器

  ```bash
  docker run --name nacos --restart=always -d -p 8848:8848 -e MODE=standalone nacos/nacos-server:1.4.1
  ``` 

> 注意事项

* ```Nacos```管理平台默认登录账号密码为```nacos/nacos```，安全起见，部署成功后建议登录平台并修改密码。

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-06-07_17-14-15.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-06-07_17-14-40.png) 

> 参考文献

* [Nacos Docker 快速开始](https://nacos.io/zh-cn/docs/quick-start-docker.html)