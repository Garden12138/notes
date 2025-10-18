## 修复插件安装失败的问题

### 使用版本

* ```dify-1.4.3```

### 问题出现

* 在下载安装```LM Studio```插件的时候，提示安装失败：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/dify1.png)

### 问题排查

* 对每个```docker```容器，查看日志，发现```docker-plugin_daemon-1```日志如下：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/dify2.png)

  大概可以推测，下载时所使用的插件```ID```，在安装阶段去查找数据库，没找到记录，可以定位到安装阶段时，保存插件```ID```是有问题的。
  
* 通过代码分析，定位到```api/services/plugin/plugin_service.py```，可以发现安装所使用的插件```ID```不是下载时所使用的插件```ID```，而是根据包内容，重新生成的新的插件```ID```，为了验证这一想法，我添加```log```打印，重新打包镜像运行：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/dify3.png)

  结果预想一样：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/dify4.png)

### 问题解决

* 找到问题后，最好的解决办法就是在安装时沿用下载所使用的插件```ID```：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/dify/dify5.png)

* [该问题已经在```dify-1.7.0```版本中合并我的```PR```修复。](https://github.com/langgenius/dify/pull/22830)