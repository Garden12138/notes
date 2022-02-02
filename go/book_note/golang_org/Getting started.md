## GolangOrg

#### Getting started

> Installing Go
  * 下载```Go```
    * [```Linux```](https://golang.org/dl/go1.17.linux-amd64.tar.gz)
    * [```Mac```](https://golang.org/dl/go1.17.darwin-amd64.pkg)
    * [```Windows```](https://golang.org/dl/go1.17.windows-amd64.msi)
    * [下载历史版本](https://golang.org/dl)
  * 安装```Go```
    * ```Linux```
      ```
      // 在下载目录下执行解压安装命令【先删除旧版本安装】
      rm -rf /usr/local/go && tar -C /usr/local -xzf go1.17.linux-amd64.tar.gz
      // 配置环境变量
      vim /etc/profile
      export PATH=$PATH:/usr/local/go/bin
      // 查看安装版本
      go version
      ```
    * ```Mac```
      ```
      // 在下载目录下安装
      // 配置环境变量
      vim ～/.bash_profile
      export PATH=$PATH:/usr/local/go/bin 
      // 查看安装版本
      go version
      ```
    * ```Windows```
      ```
      // 在安装界面提示下进行安装
      // 查看安装版本
      go version
      ```

> Tutorial: Getting started
  * 编写简单程序代码
    * 移动至编写代码目录
      ```
      cd
      ```

    * 创建存放代码文件夹
      ```
      mkdir helloworld
      ```
    * 创建```mod.file```文件【用于管理代码所使用依赖，名称为可供```Go```工具下载使用的路径名称】
      ```
      go mod init gitee.com/FSDGarden/helloworld
      ```
    * 编写```go```程序代码
      ```
      package main // 声明main包
    
      import "fmt" // 导入标准库fmt包
    
      func main() {
          fmt.Println("Hello, World!") // 输入打印“Hello, World!”
      }
      ```
    * 运行```go```程序代码
      ```
      go run .
      ```
    * 查询```go```命令用法
      ```
      go help
      ```

  * 调用第三方实现包代码
    * [查询第三方实现包](https://pkg.go.dev/)，了解调用方式。
    * 编写调用代码
      ```
      package main
      
      import "fmt"
      
      import "rsc.io/quote" // 导入rsc.io/quote包
      
      func main() {
          
          fmt.Println("Hello, World!")
          fmt.Println(quote.Go()) //调用第三方实现
      }
      ```
    * 添加第三方实现包
      ```
      go mod tidy
      // 或
      go get rsc.io/quote
      ```
      在添加之前，需要设置代理：
      ```
      go env -w GOPROXY=https://goproxy.cn,direct
      ```
    * 运行```go```代码程序
      ```
      go run .
      ```

> Tutorial: Create a module
  * 创建一个带有函数且可供另一个模块调用的简单模块：
    * 移动至编写代码目录
      ```
      cd 
      ```
    * 创建存放代码文件夹，一般为模块名
      ```
      mkdir greetings
      ```
    * 创建管理模块依赖文件
      ```
      go mod init gitee/FSDGarden/greetings
      ```
    * 使用编辑器（```GoLand```）编写代码，代码内容如：
      ```
      package greetings // 声明greetings包
      
      import "fmt"  // 导入标准库fmt包
      
      func Hello(name string) string { // 声明可调用方法，参数类型为字符串，返回类型为字符串
        
        message := fmt.Sprintf("Hi! %v. Welcome!", name) // 声明并初始化赋值变量message，声明与初始化赋值可分开编写，如下：
        // var message string
        // message = fmt.Sprintf("Hi, %v. Welcome!", name)
        return message // 返回messag变量
      
      }
      ```
  * 从另外一个模块调用代码
    * 新建调用模块```hello```，步骤与上一致，代码内容如：
      ```
      package main // 声明main包，可作为应用启动
      
      import (
          "fmt"  // 导入标准库fmt包

	        "gitee/FSDGarden/greetings"  //导入另一个模块greetings包
      )
      
      func main()  {
        message := greetings.Hello("Garden") //调用另一个模块的Hello方法，将其返回值赋于初始化变量message
        fmt.Println(message)  // 控制台输出变量message的值
      }

      ```
    * 加载远程发布模块依赖（后续更新）
    * 加载本地模块依赖
      * 重定向另一个模块路径为本地模块路径
        ```
        go mod edit -replace gitee/FSDGarden/greetings=../greetings
        ```
        执行该命令后，```mod```文件记录```replace```信息：
        ```
        module gitee/FSDGarden/hello
        
        go 1.16
        
        replace gitee/FSDGarden/greetings => ../greetings
        ```
      * 加载另一个模块依赖
        ```
        go mod tidy
        ```
        执行完命令后，```mod```文件记录另一个模块的指令：
        ```
        module gitee/FSDGarden/hello
        
        go 1.16
        
        replace gitee/FSDGarden/greetings => ../greetings
        
        require gitee/FSDGarden/greetings v0.0.0-00010101000000-000000000000
        ```
        ```v0.0.0-00010101000000-000000000000```为伪版本号
    * 运行Hello.go程序
      ```
      go run .
      ```
  * 封装返回以及处理异常
    * 编写健壮的代码，被调用方与调用方都应该对异常进行封装返回与处理。 
    * 被调用方异常的封装返回，如```greetings.Hello```:
      ```
      package greetings
      
      import (
          "errors" // 导入标准库errors包
          "fmt"
      )
      
      func Hello(name string) (string, error) { // 返回值新增error类型
          // 断言参数，非法则返回error
          if name == "" {
              return "", errors.New("empty name")
          }
          // 合法正常返回，nil表示没有异常
          message := fmt.Sprintf("Hi! %v. Welcome!", name)
          return message, nil
      }
      ```
    * 调用方异常的处理，如```hello.main```:
      ```
      package main
      
      import (
          "fmt"
          "gitee/FSDGarden/greetings"
          "log" // 导入标准库log包
      )
      
      func main()  {
          // 设置log前置信息
          log.SetPrefix("greetings.Hello: ")
          log.SetFlags(0)
          // 调用另一模块greetings Hello方法
          message, err := greetings.Hello("Garden")
          // 处理异常
          if err != nil {
            // 输出异常信息并停止程序
            log.Fatal(err)
          }
          // 正常输出
          fmt.Println(message)
      }
      ```
  * 编写私有方法，返回随机值
    ```
    package greetings
    
    import (
        "errors"
        "fmt"
        "math/rand" // 导入标准库rand包
        "time" // 导入标准库time包
    )
    
    func Hello(name string) (string, error) {
        if name == "" {
            return "", errors.New("empty name")
        }
        message := fmt.Sprintf(randomFormat(), name)
        return message, nil
    }
    // 初始化方法，初始随机Seed，随着程序启动在全局变量初始化后运行
    func init()  {
        rand.Seed(time.Now().UnixNano())
    }
    // 私有方法（方法名首小写），随机返回格式
    func randomFormat() string {
        // 声明并初始化格式分片
        formats := []string {
            "Hi, %v. Welcome!",
		        "Great to see you, %v!",
		        "Hail, %v! Well met!",
        }
        // 随机返回格式
        return formats[rand.Intn(len(formats))]
    }
    ```
  * 编写调用方法，处理多个参数以及返回多个参数关联值
    ```
    // greetings.go
    ...
    func Hellos(names []string) (map[string]string, error)  { //使用map类型返回多个入参与其关联值，声明语法为map[key-type]value-type，[map详细用法参考](https://blog.golang.org/maps)
      messages := make(map[string]string) // 使用函数make声明并初始化map类型的messages
      for _, name :=  range names { // 使用函数range循环遍历多个入参，返回值分别为当前遍历索引，当前索引指向元素的副本，若不需索引可使用下划线代替，[下划线用法参考](https://golang.org/doc/effective_go#blank)
          message, err := Hello(name) // 调用本地方法Hello获取入参关联值且声明并初始化message
          if err != nil {
              return messages, err
          }
          messages[name] = message // 将入参以及关联值添加至map类型的messages
      }
      return messages, nil // 返回多个入参以及关联值
    }
    ...
    ```
    ```
    // hello.go
    ...
    log.SetFlags(1)
    names := []string{"Daemon", "FSDGarden", "zengjiada"} // 声明且初始化数组
    messages, errs := greetings.Hellos(names)
    if errs != nil{
        log.Fatal(errs)
    }
    fmt.Println(messages)
    ...
    ```


> Tutorial: Developing a RESTful API with Go and Gin
  * 设计```API```端点
    * 在开发```API```时，通常从设计端点开始（```RESTful API```风格），如：
      ```
      /albums
      GET - 获取albums列表，作为JSON返回
      POST - 从请求发送的JSON数据添加一个新的album

      /albums/:id
      GET - 根据id获取album，作为JSON返回
      ```
  * 为即将编写的代码创建一个文件夹
    * 打开命令提示符并切换到主目录
      ```
      // On Linux or Mac
      $ cd
      // On Windows
      C:\> cd %HOMEPATH%
      ```
    * 使用命令提示符，创建一个```web-service-gin```目录
      ```
      $ mkdir web-service-gin
      $ cd web-service-gin
      ```
    * 创建一个管理依赖的模块
      ```
      go mod init gitee/FSDGarden/web-service-gin
      ```
  * 创建保存在内存的数据库（服务停止时数据丢失，启动时重新创建）
    * 创建```main.go```文件
    * 编写```main.go```声明```package main```（能够独立运行的程序始终位于```main```包中）
    * 编写```main.go```声明数据结构，标签`json:"artist"`声明```Artist```字段在序列化为```JSON```时映射为```artist```，若不声明则序列化为```JSON```时映射原有字段```Artist```
      ```
      type album struct {
        ID     string  `json:"id"`
        Title  string  `json:"title"`
        Artist string  `json:"artist"`
        Price  float64 `json:"price"`
      }
      ```
    * 编写```main.go```声明并初始化数据
      ```
      var albums = [] album {
        {ID: "1", Title: "Blue Train", Artist: "John Coltrane", Price: 56.99},
        {ID: "2", Title: "Jeru", Artist: "Gerry Mulligan", Price: 17.99},
        {ID: "3", Title: "Sarah Vaughan and Clifford Brown", Artist: "Sarah Vaughan", Price: 39.99},
      }
      ```
  * 编写返回所有项目的处理程序
    * 编写响应逻辑方法
      ```
      func getAlbums(context *gin.Context)  {
        context.IndentedJSON(http.StatusOK, albums)
      }
      ```
      使用结构体```gin.Context```作为处理请求参数，调用```IndentedJSON```方法（可使用```JSON```方法替代，返回压缩```JSON```数据）序列化所有数据为```JSON```且添加响应状态码200。
    * 映射请求响应逻辑方法
      ```
      func main()  {
        router := gin.Default()
        router.GET("/albums", getAlbums)
        router.Run("localhost:8080")
      }
      ```
      初始化```gin```路由，使用```GET```方法将```API```与响应逻辑方法```getAlbums```联系起来，使用```RUN```方法将路由添加到```http.Server```并启动它。
    * 导入使用包
      ```
      import (
          "github.com/gin-gonic/gin"
          "net/http"
      )
      ``` 
    * 运行程序
      * 开启追踪```gin```模块作为依赖项
        ```
        $ go get .
        ```
      * 运行代码
        ```
        $ go run .
        ```
      * 发出请求
        ```
        $ curl http://localhost:8080/albums \
            --header "Content-Type: application/json" \
            --request "GET"
        ```
  * 编写添加新项目的处理程序
    * 编写响应逻辑方法
      ```
      func postAlbum(context *gin.Context)  {
        var newAlbum album
        if err := context.BindJSON(&newAlbum); err != nil {
          return
        }
        
        albums = append(albums, newAlbum)
        context.IndentedJSON(http.StatusCreated, newAlbum)
      }
      ```
      调用```BindJSON```方法绑定请求体至变量```newAlbum```；调用```append```方法将变量```newAlbum```添加至数组```albums```。调用```IndentedJSON```方法（可使用```JSON```方法替代，返回压缩```JSON```数据）序列化新增数据为```JSON```且添加响应状态码201。
    * 映射请求与响应逻辑方法
      ```
      func main()  {
        router := gin.Default()
        router.POST("/albums", postAlbum)
        router.Run("localhost:8080")
      }
      ```
      初始化```gin```路由，使用```POST```方法将```API```与响应逻辑方法```postAlbum```联系起来，使用```RUN```方法将路由添加到```http.Server```并启动它。
    * 运行程序
      * 运行代码
        ```
        $ go run .
        ```
      * 发出请求
        ```
        $ curl http://localhost:8080/albums \
            --include \
            --header "Content-Type: application/json" \
            --request "POST" \
            --data '{"id": "4","title": "The Modern Sound of Betty Carter","artist": "Betty Carter","price": 49.99}'
        ```
  * 编写返回指定项目的处理程序
    * 编写响应逻辑方法
      ```
      func getAlbumById(context *gin.Context)  {
        id := context.Param("id")
        for _, album := range albums {
          if album.ID == id {
            context.IndentedJSON(http.StatusOK, album)
            return
          }
        }
        context.IndentedJSON(http.StatusNotFound, gin.H{"message" : "album not found"})
      }
      ```
      调用```Param```方法从```URL```上获取```id```路径参数值；使用```for-range```遍历数组```albums```，匹配```ID```字段值等于```id```路径参数值，符合则调用```IndentedJSON```方法（可使用```JSON```方法替代，返回压缩```JSON```数据）序列化指定数据为```JSON```且添加响应状态码200，不符合则序列化异常信息，添加响应状态码404。
    * 映射请求与响应逻辑方法
      ```
      func main()  {
        router := gin.Default()
        router.GET("/albums/:id", getAlbumById)
        router.Run("localhost:8080")
      }
      ```
      初始化```gin```路由，使用```GET```方法将```API```与响应逻辑方法```getAlbumById```联系起来，使用```RUN```方法将路由添加到```http.Server```并启动它。
    * 运行程序
      * 运行代码
        ```
        $ go run .
        ```
      * 发出请求
        ```
        $ curl http://localhost:8080/albums/2 \
            --header "Content-Type: application/json" \
            --request "GET" \
        ```

> Writing Web Applications
  * 入门
    * 在```GOPATH```路径新建目录，进入新建目录
      ```
      $ mkdir gowiki
      $ cd gowiki
      ```
    * 创建名为```wiki.go```的文件，使用合适的编辑器打开文件，添加以下内容：
      ```
      package main

      import {
        "fmt"
        "os"
      }
      ```
    * 创建管理模块依赖文件
      ```
      go mod init gitee/FSDGarden/wiki
      ```
  * 数据结构
    * 将```Page```定义为一个结构体，其中包含两个字段，分别代表标题（```title```）和主体（```body```）。
      ```
      type Page struct {
        Title string
        Body []byte
      }
      ```
    * 保存```Page```
      ```
      func (p *Page) save() error {
        filename := p.Title + ".txt"
        return os.WriteFile(filename, p.Body, 0600)
      }
      ```
      这是一个名为```save```的方法，它的接收器```p```是指向```Page```的指针，且没有参数以及返回类型为```error```的值。该方法保存```Page```主体至文本文件，使用标题作为文件名称。该方法还返回```error```值，当写文件时出现错误时，调用程序可以拦截处理，若程序正常运行，```Page.save()```将会返回```nil```。八进制整型字面量0600表示创建文件赋予当前用户仅有读写权限。
    * 加载```Page```
      ```
      func loadPage(title string) (*Page, error) {
        filename := title + ".txt"
        body, err = os.ReadFile(filename)
        if err != nil {
          return nil, err
        }
        return &Page{Title: title, Body: body}
      }
      ```
      函数```loadPage```从```title```参数构造文件名，读取文件内容至新变量```body```，返回一个指向```Page```带有恰当标题和整体值字面量的指针。标准库函数```os.ReadFile```返回```[]byte```和```error```类型。如果```error```类型返回```nil```类型则加载```Page```成功，否则异常将被调用者处理。
    * 测试```main```函数
      ```
      func main() {
        p1 := &Page{Title: "TestPage", Body: []byte("This is a sample Page.")}
        p1.save()
        p2, _ := loadPage("TestPage")
        fmt.Println(string(p2.Body))
      }
      ```
    * 编译以及运行代码
      ```
      $ go build wiki.go

      $ ./wiki
      ```
  * 介绍```net/http```包
    * 简单```Web```服务器的完整工作示例
      ```
      package main

      import (
        "fmt"
        "log"
        "net/http"
      )

      func handler(w http.ResponseWriter, r *http.Request) {
        fmt.Fprintf(w, "Hi there, I love %s!", r.URL.PATH[1:])
      }

      func main() {
        http.HandlerFunc("/", handler)
        log.Fatal(http.ListenAndServe(":8080", nil))
      }
      ```
      主函数以调用```http.HandleFunc```开始，```http package```使用```handler```处理对于```web```根路径（"/"）所有请求。调用```http.ListenAndServe```指定对于所有接口都监听端口8080。当发生意外错误时，```http.ListenAndServe```总是返回```error```，为了记录错误日志，使用```log.Fatal```包装函数调用。
      函数```handler```是```http.HandlerFunc```类型，需要```http.ResponseWriter```和```http.Request```作为参数。```http.ResponseWriter```值组装```HTTP```服务器响应，通过写入，发送数据至```HTTP```客户端。```http.Request```是```HTTP```客户端请求数据结构体
      ，```r.URL.Path```是请求```URL```路径组件，其后的[1:]意味着创建从第一个字符到结尾```Path```的子切片，这将从路径名称中删除前导"/"。
  * 使用```net/http```服务```wiki pages```
    * 创建允许用户查看```wiki```页面的处理程序```viewHandler```，它将处理以"/```view```/"为前缀的```URL```。
      ```
      func viewHandler(w http.ResponseWriter, r *http.Request) {
        title := r.URL.Path[len("/view/"):]
        p, _ := loadPage(title)
        fmt.Fprintf(w, "<h1>%s</h1><div>%s</div>", p.Title, p.Body)
      }
      ```
      该方法从请求```URL```路径组件```r.URL.Path```获取页面标题，使用```[len("/view/"):]```重新切片以删除请求路径的前导```"/view/"```组件。该方法加载页面数据，使用简易```HTML```的字符串布局页面，并写入```http.ResponseWriter```。
    * 测试```main```函数
      ```
      func main() {
        http.HandleFunc("/view/", viewHandler)
        log.Fatal(http.ListenAndServe(":8080", nil))
      }
      ```
    * 编译以及运行代码，测试
      ```
      $ go build wiki.go

      $ ./wiki

      http://localhost:8080/view/TestPage
      ```
  * 编辑```pages```
    * 创建加载页面以及展示```HTML```表单的处理程序```editHandler```
      ```
      func editHandler(w http.ResponseWriter, r *http.Request) {
        title := r.URL.Path[len("/edit/"):]
        p, err := loadPage(title)
        if err != nil {
          p = &Page{Title: title}
        }
        fmt.Fprintf(w, "<h1>Editing %s</h1>"+
        "<form action=\"/save/%s\" method=\"POST\">"+
        "<textarea name=\"body\">%s</textarea><br>"+
        "<input type=\"submit\" value=\"Save\">"+
        "</form>",
        p.Title, p.Title, p.Body)
      }
      ```
    * 测试```main```函数
      ```
      func main() {
        ...
        http.HandleFunc("/edit/", editHandler)
        ...
      }
      ```
  * ```html/template```包
  * 处理不存在的```pages```
  * 保存```pages```
  * 异常处理
  * 模版缓存
  * 校验
  * 介绍方法字面量和闭包

> How to write Go code

> A Tour of Go