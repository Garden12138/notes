## Conda使用

> 简介

* ```Conda```是一个开源的跨平台包管理系统和环境管理系统，用于管理多个版本的软件包和环境，```Conda```可以帮助你轻松安装、卸载、管理和更新软件包，并在不同环境之间切换。

> 前提

* 操作系统：CentOS 7.6 64bit
* 语言包：python3.8

> 安装

* 下载安装包

  ```bash
  wget --user-agent="Mozilla" https://mirrors.tuna.tsinghua.edu.cn/anaconda/archive/Anaconda3-2024.06-1-Linux-x86_64.sh
  ```

  版本选择可以参考[官方下载仓库](https://repo.anaconda.com/archive/)，也可以使用[清华镜像下载仓库](https://mirrors.tuna.tsinghua.edu.cn/anaconda/archive/)。

* 执行安装包
  
  ```bash
  sh ${install_path}/Anaconda3-2024.06-1-Linux-x86_64.sh
  ```

  安装过程中，根据提示输入```yes```，直到安装完成。其中要求输入安装路径，可直接回车使用默认路径：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/conda/Snipaste_2024-08-09_10-46-49.png)

  安装完成后，配置环境变量：

  ```bash
  vim ~/.bashrc
  export PATH="/root/anaconda3/bin/:$PATH"
  source ~/.bashrc
  ```

  最后查看是否安装成功：

  ```bash
  conda --version
  ```

* 使用

  * 配置默认通道源：

    ```bash
    conda config --show channels
    conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main
    conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free
    conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/
    conda config --set show_channel_urls yes
    ```

  * 创建环境，如创建一个名为```py3-8```的python3.8环境：

    ```bash
    conda create -n py3-8 python=3.8 -y
    ```

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/conda/Snipaste_2024-08-09_10-58-45.png)

  * 查看环境：

    ```bash
    conda env list
    ```

  * 激活环境：

    ```bash
    conda activate py3-8
    ```
    
    若提示如下错误：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/conda/Snipaste_2024-08-09_10-59-56.png)

    则需要先进行初始化：

    ```bash
    source ~/.bashrc
    conda init --all
    conda deactivate
    ```

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/conda/Snipaste_2024-08-09_11-04-47.png)

  * 在激活的环境中工作，如执行```python3```脚本：
    
    ```bash
    vim py3_demo.py
    ```

    ```python
    print("py3: Hello, World!");
    ``` 
    
    ```bash
    python3 py3_demo.py
    ```

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/conda/Snipaste_2024-08-09_11-17-01.png)

  * 退出环境：
  
    ```bash
    conda deactivate
    ```

  * 若需设置当前激活环境变量，则执行：

    ```bash
    # 查看当前激活环境变量
    conda env config vars list
    # 设置当前激活环境变量，设置后需重新激活环境（activate）
    conda env config vars set PY_VERSION=3.12
    ```

  * 登录终端后默认环境为```base```，若需取消，则执行：

    ```bash
    conda config --set auto_activate_base false
    ```

> 总结

* ```Conda```的环境管理功能实际上是管理多个版本包的，当我们激活对应环境，终端上下文就会切到该环境，并可以使用该环境下的包：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/conda/Snipaste_2024-08-09_11-21-31.png)

> 参考文献

* [官网](https://docs.conda.io/en/latest/)
* [Anaconda 教程](https://www.runoob.com/python-qt/anaconda-tutorial.html)
* [Linux环境下使用Conda搭建和自由切换Python环境](https://cloud.tencent.com/developer/article/1949339)
* [CommandNotFoundError: Your shell has not been properly configured to use 'conda activate'.](https://github.com/conda/conda/issues/13002)