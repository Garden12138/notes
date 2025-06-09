## Curl使用

### 常见用法

* 带查询参数的```GET```请求：

  ```bash
  curl -G https://api.example.com/search \
    --data-urlencode "q=search term" \
    -d "limit=10" \
    -d "sort=desc"
  ```

* 表单提交```POST```请求：

  ```bash
  curl -X POST https://api.example.com/login \
    -d "username=myusername" \
    -d "password=mypassword"
  ```

* ```JSON```提交```POST```请求：

  ```bash
  curl -X POST https://api.example.com/data \
    -H "Content-Type: application/json" \
    -d '{"name": "John Doe", "age": 30}'
  ```

### 参考文献

* [Run Curl Commands Online](https://reqbin.com/curl)