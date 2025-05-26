## docker的一些实践

### 查看运行中容器的docker run参数

* 拉取```runlike```镜像：

  ```bash
  docker pull assaflavie/runlike
  ```

* 运行```runlike```容器，查看指定运行中容器的```docker run```参数：

  ```bash
  docker run --rm -v /var/run/docker.sock:/var/run/docker.sock assaflavie/runlike ${CONTAINER_NAME}
  ```

### 参考文献

* [从已运行容器获取docker run参数](https://www.mdnice.com/writing/eb9e45ecc61c48db9412ed472e04f9ea)