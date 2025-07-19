## 下载模型

### 前期准备

* [安装```Git```](https://gitee.com/FSDGarden/learn-note/blob/master/git/git.md)

* 安装```Git LFS```：

  ```bash
  sudo apt-get install git-lfs  # linux
  brew install git-lfs          # macOS
  ```

### 使用Git下载huggingface公开模型

* 初始化```Git LFS```：

  ```bash
  git lfs install
  ```

* 登录[```huggingface```官网](https://huggingface.co/)或[镜像站点](https://hf-mirror.com)，搜索需要的模型并点击进入模型页面，复制模型名称。

* 克隆仓库

  ```bash
  git clone https://huggingface.co/<model_name>
  ```
  或者
  ```bash
  git clone https://hf-mirror.com/<model_name>
  ```

* 下载模型

  ```bash
  cd <model_name>
  git lfs pull
  ```

### 使用Git下载modelscope公开模型

* 初始化```Git LFS```：

  ```bash
  git lfs install
  ```

* 登录[```modelscope```官网](https://modelscope.cn/)，搜索需要的模型并点击进入模型页面，复制模型名称。

* 克隆仓库

  ```bash
  git clone https://modelscope.cn/<model_name>
  ```

* 下载模型

  ```bash
  cd <model_name>
  git lfs pull
  ```

### 使用命令行下载modelscope公开模型

* 下载```modelscope```命令行工具

  ```bash
  pip install modelscope
  ```

* 登录[```modelscope```官网](https://modelscope.cn/)，搜索需要的模型并点击进入模型页面，复制模型名称。

* 下载模型

  ```bash
  modelscope download --model="<model_name>" --local_dir <directory_to_save_model>
  ```

### 参考文献

* [hunggingface download files](https://huggingface.co/docs/huggingface_hub/main/en/guides/download#download-an-entire-repository)
* [modelscope download models](https://www.modelscope.cn/docs/models/download)