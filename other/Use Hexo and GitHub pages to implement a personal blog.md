## 使用Hexo和GitHub Pages实现个人博客

> 准备工作

* 安装```Node.js```

  * 访问[```Node.js```官网](https://nodejs.org/zh-cn)，下载并安装```LTS```版本。
  * 安装完成后，打开终端，验证是否安装成功：

    ```bash
    node -v
    npm -v
    ```

* 安装```Git```

  * 访问[```Git```官网](https://git-scm.com/downloads)，下载并安装。
  * 安装完成后，打开终端，验证是否安装成功：

    ```bash
    git --version
    ```

* 注册```GitHub```账号

  * 若没有```GitHub```账号，请访问[```GitHub```官网](https://github.com/)注册。

> 安装Hexo

* 安装命令行工具：
  
  ```bash
  npm install -g hexo-cli
  ```

* 初始化博客项目，该仓库为```Hexo```配置代码和生成的博客源码：

  ```bash
  hexo init myblog
  cd myblog
  npm install
  ```

* 本地预览博客：

  ```bash
  hexo cl && hexo g && hexo s
  ```

> 配置Github Pages

* 创建仓库，命名为```username.github.io```，其中```username```为你的```GitHub```用户名，仓库需设置为公开（```Public```）。

* 打开博客项目根目录，修改```_config.yml```文件，找到```deploy```项，修改为：
  
  ```yaml
  deploy:
    type: git
    repo: https://github.com/username/username.github.io.git
    branch: main
  ```

* 安装部署插件：

  ```bash
  npm install hexo-deployer-git --save
  ```

> 创建文章

* 创建文章，会在```source/_posts```目录生成```.md```文件：
  
  ```bash
  hexo new "文章标题"
  ```

  使用```Markdown```编写内容，保存后重新生成并预览。

> 部署到Github

* 配置```SSH```密钥，以便```Git```推送代码：

  ```bash
  ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

  ```
  然后将``~/.ssh/id_rsa.pub```文件内容复制到```GitHub```的```SSH```密钥设置中。

* 清理缓存、生成静态文件、推送到```GitHub```：

  ```bash
  hexo cl && hexo g && hexo d
  ```

* 浏览器访问```https://username.github.io```，查看博客效果。

> 进阶操作

* 自定义主题，如```Butterfly```：

  * 将主题下载至```themes```目录：

    ```bash
    git clone https://github.com/jerryc127/hexo-theme-butterfly.git themes/butterfly
    ```

  * 复制```themes/butterfly/_config.yml```文件至博客项目根目录并修改名称为```_config.butterfly.yml```：
    
    ```bash
    cp themes/butterfly/_config.yml ./_config.butterfly.yml
    ```

  * 修改```_config.yml```文件，找到```theme```项，修改为```butterfly```：

    ```yaml
    theme: butterfly
    ``` 

  * 安装渲染工具：

    ```bash
    npm install hexo-renderer-pug hexo-renderer-stylus
    ```
  
  * 重新生成并预览博客.

* 自定义域名：

  * 第一种是在仓库的```Settings``` > ```Pages``` > ```Custom domain```绑定自己的域名，并在域名服务商处添加```CNAME```解析。
  * 第二种是在自定义域名解析的服务器反向代理```username.github.io```。

* 备份源码，将博客项目推送至```GitHub```的另一个仓库，以确保多端同步，避免本地源码丢失。

> 遇到的问题与解决方案

* 部署时有时候会出现443端口错误，解决方法：

  * 删除```.deploy_git```文件夹。

  * 删除本地```~./ssh/known_hosts```等文件。

  * 重新部署。

> 参考文献

* [Hexo官方文档](https://hexo.io/zh-cn/docs/)
* [Butterfly主题文档](https://butterfly.js.org/)
* [hexo | butterfly 主题设置一](https://www.wzhecnu.cn/2021/07/22/blog/hexo-02-zhu-ti-mei-hua/)