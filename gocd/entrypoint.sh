#!/bin/bash
## 设置go用户拥有使用docker的权限
chown go /var/run/docker.sock
bash /docker-entrypoint.sh
