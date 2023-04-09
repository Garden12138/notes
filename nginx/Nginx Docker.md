## Nginx Docker
docker pull nginx:latest

docker run --name nginx-test -d nginx:latest  
docker cp nginx-test:/etc/nginx/nginx.conf /data/nginx/conf/

docker run --name nginx --restart=always --privileged=true -p 18678:80 -v /data/nginx/conf/nginx.conf:/etc/nginx/nginx.conf:ro -v /data/nginx/conf/conf.d:/etc/nginx/conf.d:ro -v /data/nginx/html:/usr/share/nginx/html:rw -v /data/nginx/logs:/var/log/nginx -d nginx:latest

    server {
        listen    80;
        server_name    localhost;
        
        location / {
            proxy_pass    http://10.151.3.116:80;
        }
    }

curl -X POST https://zhy3q-sit.999.com.cn/admin/api/external-gateway/external-gateway/services/machine/token -H 'Content-Type: application/json' -H 'client_id: 12345677' -H 'sign: fjnsd34sf14fVgrf35dn2kjtn5' -d '{client_id:"12345677",sign:"fjnsd34sf14fVgrf35dn2kjtn5"}'

curl -X POST http://10.151.3.116:80/admin/api/external-gateway/external-gateway/services/machine/token -H 'Content-Type: application/json' -H 'client_id: 12345677' -H 'sign: fjnsd34sf14fVgrf35dn2kjtn5' -d '{client_id:"12345677",sign:"fjnsd34sf14fVgrf35dn2kjtn5"}'

curl -X POST http://localhost:18678/admin/api/external-gateway/external-gateway/services/machine/token -H 'Content-Type: application/json' -H 'client_id: 12345677' -H 'sign: fjnsd34sf14fVgrf35dn2kjtn5' -d '{client_id:"12345677",sign:"fjnsd34sf14fVgrf35dn2kjtn5"}'

curl --location --request POST 'http://112.74.176.193:18678/admin/api/external-gateway/external-gateway/services/machine/token' \
--header 'sign: SGutfD5IsRnyRShVIdA/+Cz4kSYFc8IcpbGXmZ+65H1cYQg/cmxZfScv3QDVWJ179nrkjNn3I6W6FYHZHvu3D/kWDdgA8YH9SQ7iYfIN78ZhcGWxmVTCaw0xY0UJf+CMr6Xhf8IoWZf0JkQUkxeRvZgF0aoVKEVpkoMYPzDKMkVdYCNdhu/LncUuH5nULuVPIZPhFoSZrH52GtMm5PlayGTNydfGBf/lL2tzghPIDnHv44N0NtxboRghin8wNTwdr13nY+CnX0HF/TFtXqU/q2/7Xm2Y2H0xxdvK/RcgSVP7xgAP4vvUQp/OPqzHoyEeQwQGc69uTMpaKyFmjos3dA==' \
--header 'Content-Type: application/json' \
--data-raw '{"client_id":"CESHI1"}'