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

> Tutorial: Developing a RESTful API with Go and Gin

> Writing Web Applications

> How to write Go code

> A Tour of Go