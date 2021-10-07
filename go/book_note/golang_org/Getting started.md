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
      
      func Hello(name string) string { // 声明可调用方法，参数类型为字符串，类型为字符串
        
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

> Writing Web Applications

> How to write Go code

> A Tour of Go