## 在 Centos 上 安装 docker-compose

> 在线安装

  ```bash
  ## 下载安装docker-compose，占位符version为版本号，可从https://github.com/docker/compose/releases查阅选择
  sudo curl -L "https://github.com/docker/compose/releases/download/${version}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
  ## 添加可执行权限
  sudo chmod +x /usr/local/bin/docker-compose
  ## 查看安装是否成功
  docker-compose --version
  ```

> 离线安装
  
* 准备安装包，在可连接外网的机器下载```docker-compose```安装包，然后将安装包```ssh```至目标服务器```/usr/local/bin```目录下，然后为```docker-compose```文件添加可执行权限，最后检查安装是否成功。

> 参考文献

* [docker-compose install](https://docs.docker.com/compose/install/)
* [Docker - 离线安装 docker-compose（以CentOS系统为例）](https://www.hangge.com/blog/cache/detail_2469.html)