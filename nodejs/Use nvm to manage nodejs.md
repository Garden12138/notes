## 使用nvm管理Node.js

### 安装nvm，以Apple Silicon系列Mac为例

* 卸载已安装旧版本：

  ```bash
  # brew安装方式
  brew uninstall --ignore-dependencies node
  brew uninstall node
  # 官方包安装方式
  sudo rm -rf /usr/local/{bin/{node,npm},lib/node_modules/npm,lib/node,share/man/*/node.*}

  # 删除残留配置
  rm -rf ~/.npm ~/.node-gyp
  ```

* ```brew```安装：

  ```bash
  brew install nvm
  ```

* 配置环境变量：

  ```bash
  export NVM_DIR="$HOME/.nvm"
  [ -s "/opt/homebrew/opt/nvm/nvm.sh" ] && \. "/opt/homebrew/opt/nvm/nvm.sh"
  [ -s "/opt/homebrew/opt/nvm/etc/bash_completion.d/nvm" ] && \. "/opt/homebrew/opt/nvm/etc/bash_completion.d/nvm"
  ```

* 验证安装：

  ```bash
  nvm --version
  ```

### 使用

* 查看已安装版本：

  ```bash
  nvm ls
  ```

* 查看可安装版本：

  ```bash
  nvm ls-remote
  ```

* 安装指定版本：

  ```bash
  nvm install <version>
  ```

* 切换到指定版本：

  ```bash
  nvm use <version>
  ```

* 删除已安装版本：

  ```bash
  nvm uninstall <version>
  ```