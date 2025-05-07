## DB-GPT 使用说明

### 部署

* 安装环境

  * ```uv```安装：

    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

    验证安装是否成功：

    ```bash
    uv -V
    ```

    后续升级```uv```版本可执行：

    ```bash
    uv self update
    ```

* 拉取源码

  * 项目拉取：

    ```bash
    git clone https://github.com/eosphoros-ai/DB-GPT.git
    ```

  * 安装依赖：

    ```bash
    cd DB-GPT

    uv sync --all-packages -i https://mirrors.aliyun.com/pypi/simple/ \
    --extra "base" \
    --extra "proxy_openai" \
    --extra "hf" \
    --extra "llama_cpp" \
    --extra "rag" \
    --extra "storage_chromadb" \
    --extra "quant_bnb" \
    --extra "dbgpts"
    ``` 

* 打包模块

  * 切换```python```虚拟环境打包，以```conda```为例：

    ```bash
    conda create -n py3-11 python=3.11 -y

    conda activate py3-11
    ```

  * 进入```dbgpt-core```模块：

    ```bash
    cd packages/dbgpt-core

    touch setup.py
    ```

    编写```setup.py```文件：

    ```python
    from setuptools import setup, find_packages

    setup(
        name="dbgpt",          # 包名（pip install 时使用的名称）
        version="0.7.0",            # 版本号
        package_dir={"": "src"},    # 指定源码目录
        packages=find_packages(where="src"),  # 自动发现 src 下的包
    )
    ```

    打包安装：

    ```bash
    # 安装打包工具，初次打包时需安装
    pip3 install build
    # 打包，生成dist目录
    python3 -m build
    # 安装
    pip3 install dist/dbgpt-0.7.0-tar.gz
    ## 查看安装路径
    pip3 show dbgpt | grep "Location"
    ## 拷贝安装包至uv环境
    cp ~/opt/anaconda3/envs/py3-11/lib/python3.11/site-packages/dbgpt .venv/lib/python3.11/site-packages/
    cp ~/opt/anaconda3/envs/py3-11/lib/python3.11/site-packages/dbgpt-0.7.0.dist-info .venv/lib/python3.11/site-packages/
    ```

  * 进入```dbgpt-ext```模块：

    ```bash
    cd packages/dbgpt-ext

    touch setup.py
    ```

    编写```setup.py```文件：

    ```python
    from setuptools import setup, find_packages

    setup(
        name="dbgpt_ext",          # 包名（pip install 时使用的名称）
        version="0.7.0",            # 版本号
        package_dir={"": "src"},    # 指定源码目录
        packages=find_packages(where="src"),  # 自动发现 src 下的包
    )
    ```

    打包安装：

    ```bash
    # 打包，生成dist目录
    python3 -m build
    # 安装
    pip3 install dist/dbgpt_ext-0.7.0-tar.gz
    ## 查看安装路径
    pip3 show dbgpt_ext | grep "Location"
    ## 拷贝安装包至uv环境
    cp ~/opt/anaconda3/envs/py3-11/lib/python3.11/site-packages/dbgpt_ext .venv/lib/python3.11/site-packages/
    cp ~/opt/anaconda3/envs/py3-11/lib/python3.11/site-packages/dbgpt_ext-0.7.0.dist-info .venv/lib/python3.11/site-packages/
    ```

  * 进入```dbgpt-serve```模块：

    ```bash
    cd packages/dbgpt-serve

    touch setup.py
    ```

    编写```setup.py```文件：

    ```python
    from setuptools import setup, find_packages

    setup(
        name="dbgpt_serve",          # 包名（pip install 时使用的名称）
        version="0.7.0",            # 版本号
        package_dir={"": "src"},    # 指定源码目录
        packages=find_packages(where="src"),  # 自动发现 src 下的包
    )
    ```

    打包安装：

    ```bash
    # 打包，生成dist目录
    python3 -m build
    # 安装
    pip3 install dist/dbgpt_serve-0.7.0-tar.gz
    ## 查看安装路径
    pip3 show dbgpt_serve | grep "Location"
    ## 拷贝安装包至uv环境
    cp ~/opt/anaconda3/envs/py3-11/lib/python3.11/site-packages/dbgpt_serve .venv/lib/python3.11/site-packages/
    cp ~/opt/anaconda3/envs/py3-11/lib/python3.11/site-packages/dbgpt_serve-0.7.0.dist-info .venv/lib/python3.11/site-packages/
    ```

  * 进入```dbgpt-client```模块：

    ```bash
    cd packages/dbgpt-client

    touch setup.py
    ```

    编写```setup.py```文件：

    ```python
    from setuptools import setup, find_packages

    setup(
        name="dbgpt_client",          # 包名（pip install 时使用的名称）
        version="0.7.0",            # 版本号
        package_dir={"": "src"},    # 指定源码目录
        packages=find_packages(where="src"),  # 自动发现 src 下的包
    )
    ```

    打包安装：

    ```bash
    # 打包，生成dist目录
    python3 -m build
    # 安装
    pip3 install dist/dbgpt_client-0.7.0-tar.gz
    ## 查看安装路径
    pip3 show dbgpt_client | grep "Location"
    ## 拷贝安装包至uv环境
    cp ~/opt/anaconda3/envs/py3-11/lib/python3.11/site-packages/dbgpt_client .venv/lib/python3.11/site-packages/
    cp ~/opt/anaconda3/envs/py3-11/lib/python3.11/site-packages/dbgpt_client-0.7.0.dist-info .venv/lib/python3.11/site-packages/
    ```

  * 进入```dbgpt-app```模块：

    ```bash
    cd packages/dbgpt-app

    touch setup.py
    ```

    编写```setup.py```文件：

    ```python
    from setuptools import setup, find_packages

    setup(
        name="dbgpt_app",          # 包名（pip install 时使用的名称）
        version="0.7.0",            # 版本号
        package_dir={"": "src"},    # 指定源码目录
        packages=find_packages(where="src"),  # 自动发现 src 下的包
    )
    ```

    打包安装：

    ```bash
    # 打包，生成dist目录
    python3 -m build
    # 安装
    pip3 install dist/dbgpt_app-0.7.0-tar.gz
    ## 查看安装路径
    pip3 show dbgpt_app | grep "Location"
    ## 拷贝安装包至uv环境
    cp ~/opt/anaconda3/envs/py3-11/lib/python3.11/site-packages/dbgpt_app .venv/lib/python3.11/site-packages/
    cp ~/opt/anaconda3/envs/py3-11/lib/python3.11/site-packages/dbgpt_app-0.7.0.dist-info .venv/lib/python3.11/site-packages/
    ```

* 设置配置，以代理```Openai llms```、本地```embeddings```以及本地```sqlite```为例，```configs/dbgpt-proxy-openai.toml```文件配置：

  ```bash
  [system]
  # 语言 -zh 或者 -en 等切换即可
  language = "${env:DBGPT_LANG:-zh}"
  # 使用api请求DB-GPT时附带的api密钥(可以配置多个)
  api_keys = []
  # 加密数据
  encrypt_key = "dbgpt@2025"

  # Server Configurations
  [service.web]
  # 如果要实现局域网内设备都可访问 请使用 0.0.0.0
  # 如果仅是本机设备可访问 请使用 127.0.0.1
  host = "0.0.0.0"
  port = 5670

  [service.web.database]
  # 数据库类型，默认SQLite，修改为uv环境下的数据库路径
  type = "sqlite"
  path = "/Users/cengjiada/Documents/study/github/DB-GPT/.venv/pilot/meta_data/dbgpt.db"

  [rag.storage]
  [rag.storage.vector]
  # 向量存储类型，默认chroma，修改为uv环境下的存储路径
  type = "chroma"
  persist_path = "/Users/cengjiada/Documents/study/github/DB-GPT/.venv/pilot/data"

  # Model Configurations
  [models]
  [[models.llms]]
  # 语言模型名称，默认gpt-4o，修改为实际使用的模型名称
  name = "${env:LLM_MODEL_NAME:-gpt-4o}"
  # 语言模型提供者，默认proxy/openai，修改为实际使用的模型提供者
  provider = "${env:LLM_MODEL_PROVIDER:-proxy/openai}"
  # 语言模型api地址，默认http://openai.gardenqaq.cn/v1，修改为实际使用的模型api地址
  api_base = "${env:OPENAI_API_BASE:-http://openai.gardenqaq.cn/v1}"
  # 语言模型api密钥，默认sk-p2jlnsYXTIPgBJDs0fD15b6f570d4f1094145291B2F42814，修改为实际使用的模型api密钥
  api_key = "${env:OPENAI_API_KEY:-sk-p2jlnsYXTIPgBJDs0fD15b6f570d4f1094145291B2F42814}"

  [[models.embeddings]]
  # 词嵌入名称，默认bge-large-zh-v1.5，修改为实际使用的词嵌入名称
  name = "BAAI/bge-large-zh-v1.5"
  # 词嵌入提供者，默认hf，修改为实际使用的词嵌入提供者
  provider = "hf"
  # 词嵌入路径，默认/Users/cengjiada/Documents/study/models/embeddings/bge-large-zh-v1.5，修改为实际使用的词嵌入路径
  path = "/Users/cengjiada/Documents/study/models/embeddings/bge-large-zh-v1.5"
  ```

  下载```BAAI/bge-large-zh-v1.5```词嵌入，并将其放入```/Users/cengjiada/Documents/study/models/embeddings/```目录下：

  ```bash
  # 安装 Git LFS（若未安装）
  sudo apt-get install git-lfs  # Linux
  brew install git-lfs          # macOS
  # 初始化 Git LFS
  git lfs install
  # 进入 embeddings 目录
  cd /Users/cengjiada/Documents/study/models/embeddings/
  # 克隆hf仓库
  git clone https://huggingface.co/BAAI/bge-large-zh-v1.5
  # 或克隆hf镜像仓库
  git clone https://hf-mirror.com/BAAI/bge-large-zh-v1.5
  # 下载模型
  git lfs pull
  ```

* 运行服务：

  ```bash
  uv run python packages/dbgpt-app/src/dbgpt_app/dbgpt_server.py --config configs/dbgpt-proxy-openai.toml
  ```

* 验证服务，浏览器访问```http://localhost:5670/```。

### 参考文献

* [DB-GPT 0.7.0 部署教程](https://iyyh.net/archives/c0ababbd-8638-489c-84cd-267dbf886cb8)