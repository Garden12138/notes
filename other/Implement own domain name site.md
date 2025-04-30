## 实现自己的域名网站

> 购买云服务器

* [选择阿里云轻量应用服务器](https://common-buy.aliyun.com/?commodityCode=swas&regionId=cn-guangzhou)，选择比较近的地域，系统镜像为Alibaba Cloud Linux，系统配置大概为CPU2核，内存2G，SSD40G即可，选择购买时长并点击购买。

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/other/Snipaste_2025-04-30_14-36-02.png)

> 购买域名

* [注册域名](https://wanwang.aliyun.com/domain)，选择后缀，输入域名点击查询，选择未注册的域名，点击立即注册。

> 配置域名解析

* [配置域名解析](https://dns.console.aliyun.com/#/dns/domainList)，点击解析配置，可以看到域名解析列表，点击快速添加解析或添加记录可设置域名解析，推荐使用添加记录，对于每个设置项都有详细说明。

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/other/Snipaste_2025-04-30_14-59-29.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/other/Snipaste_2025-04-30_15-00-36.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/other/Snipaste_2025-04-30_15-01-03.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/other/Snipaste_2025-04-30_16-52-21.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/other/Snipaste_2025-04-30_15-05-27.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/other/Snipaste_2025-04-30_16-52-41.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/other/Snipaste_2025-04-30_15-06-12.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/other/Snipaste_2025-04-30_15-06-25.png)

> 购买SSL证书

* [SSL证书管理](https://yundun.console.aliyun.com/?p=cas#/certExtend/free/cn-hangzhou?currentPage=1&pageSize=10&keyword=&statusCode=)，选择个人测试证书，点击立即购买，选择证书类型和购买数量（该款证书是一个域名对应一套证书，如果子域名需证书，则需买多套证书），点击立即购买。点击更多，选择下载，下载对应服务器类型的证书，如Nginx。

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/other/Snipaste_2025-04-30_15-30-25.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/other/Snipaste_2025-04-30_15-32-30.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/other/Snipaste_2025-04-30_15-37-20.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/other/Snipaste_2025-04-30_15-38-48.png)

> 配置Nginx

* [使用Docker部Nginx](https://gitee.com/FSDGarden/learn-note/blob/master/nginx/Use%20docker%20deploy%20nginx.md)

* 上传证书文件至Nginx挂载的目录/data/nginx/certs。

* 配置nginx.conf文件：

  ```bash
  # HTTP 强制跳转 HTTPS
  server {
      listen 80;
      listen [::]:80;
      server_name gardenqaq.cn;
      return 301 https://$host$request_uri;
  }

  server {
      listen 443 ssl http2;
      listen [::]:443 ssl http2;
      server_name gardenqaq.cn;

      # 阿里云证书路径（容器内挂载路径）
      ssl_certificate     /etc/nginx/certs/gardenqaq.cn.pem;  # 合并后的证书链
      ssl_certificate_key /etc/nginx/certs/gardenqaq.cn.key;  # 私钥文件

      # 安全增强配置（强制 TLS1.2+ 和现代加密套件）
      ssl_protocols TLSv1.2 TLSv1.3;
      ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
      ssl_prefer_server_ciphers on;
      ssl_session_cache shared:SSL:10m;
      ssl_session_timeout 10m;
      ssl_session_tickets off;

      # HSTS 安全头（可选）
      add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;

      # 其他配置（如根目录、日志等）
      root /usr/share/nginx/html;
      index index.html;

      location / {
          try_files $uri $uri/ =404;
      }

      access_log /var/log/nginx/access.log;
      error_log /var/log/nginx/error.log;

  }
  ```

* 重启Nginx容器：

  ```bash
  docker restart nginx
  ```

> 域名备案

* [申请域名备案](https://beian.aliyun.com/pcContainer/selfEntity)，填写相关信息，提交备案申请。

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/other/Snipaste_2025-04-30_16-35-51.png)

> 部署网站

* 编写简易```HTML```：

  ```bash
  echo "This is gardenqaq site" > /data/nginx/html/index.html
  ```

> 测试网站

* 浏览器访问域名（https://gardenqaq.cn），查看网站内容。

> 参考文献

* [ICP备案流程](https://help.aliyun.com/zh/icp-filing/basic-icp-service/user-guide/icp-filing-application-overview)