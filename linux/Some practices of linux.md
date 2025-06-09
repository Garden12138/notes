## linux的一些实践

### shell脚本读取文件内容并赋给变量

* 准备文件内容```network.conf```：

  ```bash
  IP=127.0.0.1
  Port=8080
  ```

* 使用```sed```解析文本并赋值变量：

  ```bash
  ip=`sed '/^IP=/!d;s/.*=//' network.conf`
  port=`sed '/^Port=/!d;s/.*=//' network.conf`

  echo $ip
  echo $port
  ```

* 使用```eval```命令解析文本并赋值变量：

  ```bash
  while read line;do  
    eval "$line"  
  done < network.conf

  echo $IP  
  echo $Port 
  ```

* 使用```source```命令将配置信息加载到环境变量中：

  ```bash
  source ./network.conf

  echo $IP
  echo $Port
  ```

### 创建文件的方式

* 使用```touch```命令创建文件：

  ```bash
  touch file.txt
  ```

* 使用重定向运算符```>```创建文件：

  ```bash
  > file.txt
  ```

* 使用```cat```命令创建文件，按```Enter```输入文字，完成后按```CRTL+D```保存文件：

  ```bash
  cat > file.txt
  ```

* 使用```echo```命令创建文件：

  ```bash
  echo "Hello, world!" > file.txt
  ```

* 使用```vi```或```vim```编辑器创建文件：

  ```bash
  vi file.txt

  vim file.txt
  ```

### 参考文献

* [Linux shell：脚本读取文件内容赋给变量的三种方式](https://blog.csdn.net/weixin_44498318/article/details/106490367)
* [如何在Linux中创建文件？多个文件创建操作命令](https://cloud.tencent.com/developer/article/1858594)