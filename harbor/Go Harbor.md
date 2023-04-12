## Go Harbor

https://github.com/goharbor/harbor/releases/download/v2.7.1/harbor-offline-installer-v2.7.1.tgz

tar xzvf harbor-offline-installer-v2.5.2.tgz -C /usr/local/

vim /etc/hosts
```
159.75.138.212 tke.registry.harbor
```

cd /usr/local/harbor
openssl genrsa -out ca.key 4096
openssl req -x509 -new -nodes -sha512 -days 3650 \
 -subj "/C=CN/ST=Beijing/L=Beijing/O=example/OU=Personal/CN=159.75.138.212" \
 -key ca.key \
 -out ca.crt
mkdir -p /data/cert
cp ca* /data/cert/

cp harbor.yml.tmpl harbor.yml
vim harbor.yml
```
hostname: tke.registry.harbor

certificate: /data/cert/ca.crt
private_key: /data/cert/ca.key

harbor_admin_password: garden520
```

. prepare
. install.sh

docker-compose up -d

mkdir -p /etc/docker/cert.d/tke.registry.harbor
cp /data/cert/ca.crt /etc/docker/cert.d/tke.registry.harbor/

vim /etc/docker/daemon.json
```
"insecure-registries": ["tke.registry.harbor"]
```

systemctl daemon-reload && systemctl restart docker

docker login tke.registry.harbor
```
admin
garden520/Harbor12345
```

{
	"auths": {
		"159.75.138.212:80": {"username":"admin", "password":"garden520"}
	},
	"HttpHeaders": {
		"User-Agent": "Docker-Client/19.03.8 (windows)"
	},
	"credsStore": "desktop",
	"stackOrchestrator": "swarm"
}

Error response from daemon: Get "https://159.75.138.212:80/v2/": http: server gave HTTP response to HTTPS client
Error response from daemon: Get "http://159.75.138.212/v2/": Get "http://reg.mydomain.com/service/token?account=admin&client_id=docker&offline_token=true&service=harbor-registry": dial tcp: lookup reg.mydomain.com on 183.60.83.19:53: no such host

> 参考文献

* [超详细的harbor私有仓库搭建并使用域名登录](https://blog.csdn.net/weixin_45231541/article/details/125556143)
* [Docker Harbor私有仓库部署与管理](https://developer.aliyun.com/article/898329)
* [Harbor Core packaged by Bitnami](https://hub.docker.com/r/bitnami/harbor-core)
* [docker login 登录 Harbor](https://randyou.github.io/2020/06/16/docker-login-harbor/index.html)