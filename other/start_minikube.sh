#!/bin/bash

# 下载安装minikube
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# 启动minikube
minikube start --image-mirror-country='cn' --force --driver=docker --kubernetes-version=v1.23.8 
# --cpus='4' --memory='8200462336b'

# 启动插件
minikube addons enable ingress
minikube addons enable metrics-server