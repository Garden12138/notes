#!/usr/bin/bash
#=============================================================================
#————————Zsh + Oh-my-zsh + 自动补全语法高亮插件 + AutoJump 一键安装脚本——————
#=============================================================================
#
#目前脚本非常简单，还没有做任何测试，仅供简单使用


# 获取脚本当前位置

# todo 添加yum国内源


# 安装zsh
yum install -y zsh

# 安装 oh-my-zsh
chmod +x install_oh_my_zsh.sh
./install_oh_my_zsh.sh
# 跳转到oh-my-zsh安装位置
cd ~/.oh-my-zsh || exit 1
# 设置更新源
git remote set-url origin https://gitee.com/mirrors/oh-my-zsh.git
git pull

#安装zsh自动补全和语法高亮插件并写入.zshrc文件
git clone https://gitee.com/lightnear/zsh-syntax-highlighting.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting
git clone https://gitee.com/hailin_cool/zsh-autosuggestions.git "${ZSH_CUSTOM:-~/.oh-my-zsh/custom}"/plugins/zsh-autosuggestions
git clone https://gitee.com/twd2606/zsh-completions.git "${ZSH_CUSTOM:-~/.oh-my-zsh/custom}"/plugins/zsh-completions
sed -i 's/plugins=(git)/plugins=(git zsh-syntax-highlighting zsh-autosuggestions zsh-completions)/' ~/.zshrc

#安装autojump并写入.zshrc
git clone https://gitee.com/haha-web/autojump.git ~/autojump
cd ~/autojump || exit 1
python3 install.py
echo '[[ -s /root/.autojump/etc/profile.d/autojump.sh ]] && source /root/.autojump/etc/profile.d/autojump.sh' >> ~/.zshrc
echo 'autoload -U compinit && compinit -u\n' >> ~/.zshrc
rm -rf ~/autojump

#安装完成，更新配置
source ~/.zshrc

cd ~ || exit 1

#Enjoyit
echo '安装完成,Enjoy it'