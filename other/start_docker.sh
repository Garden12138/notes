#!/bin/bash

# 安装docker
curl -fsSL https://get.docker.com | bash -s docker --mirror Aliyun

# 配置普通用户管理docker
useradd fyws-docker
usermod -aG docker fyws-docker
newgrp docker
# 添加sudo权限
echo 'fyws-docker ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers 
# 切换用户
su fyws-docker
# 执行前置操作
sudo sh -eux <<EOF
# Set user.max_user_namespaces
cat <<EOT > /etc/sysctl.d/51-rootless.conf
user.max_user_namespaces = 28633
EOT
sysctl --system
EOF
# 安装管理
dockerd-rootless-setuptool.sh install

# 退出当前用户
I=$(who am i|awk '{print $2}')
pkill -kill -t "$I"

# 启动docker
systemctl enable docker
systemctl start docker