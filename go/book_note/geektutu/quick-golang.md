#### [Go（又称Golang）是Google开发的一种静态强类型、编译型、并发型，并具有垃圾回收功能的编程语言。](https://zh.wikipedia.org/wiki/Go)

> Go安装
  * [下载安装](https://gitee.com/FSDGarden/learn-note/blob/master/go/book_note/golang_org/Getting%20started.md)
  * 设置环境变量，配置第三方包国内镜像代理
    ```
    $ go env -w GOPROXY=https://goproxy.cn,direct
    ```
    或在```profile```中设置环境变量
    ```
    export GOPROXY=https://goproxy.cn
    ```

> Hello World
  * 新建文件```main.go```，写入
    ```
    package main
    
    import "fmt"
    
    func main()  {
        fmt.Println("Hello World!")
    }
    ```
  * 执行```go run main.go```或```go run .```，将输出
    ```
    $ go run .

    Hello World!
    ```
    若强制启用```Go Modules```机制（即环境变量中设置```GO111MODULE=on```），则需先初始化模块```go mod init moduleName```，模块名格式一般为仓库名+模块名，如```gitee/FSDGarden/geektutu/quick-golang```。否则会报错误：```go: cannot find main module; see ‘go help modules’```。
  * 解读程序
    * ```package main```：声明```main.go```文件所在包，```Go```语言中使用包来组织代码。一般一个文件夹即一个包。包内可以暴露类型或方法供其他包使用。
    * ```import "fmt"```：```fmt```是```Go```语言的一个标准库/包，用于处理标准输入输出。
    * ```func main```：```main```函数，整个程序的入口。```main```函数所在包也必须为```main```包。
    * ```fmt.Println("Hello World!")```：调用```fmt```包的```Println```方法，打印输出```Hello World!```字符串。
    * ```go run main.go```：可分成两步执行，分别为```go build mian.go```、```./main```，前者编译成二进制可执行程序文件，后者则执行该程序。

> 变量与内置数据类型

> 流程控制（if、for、switch）

> 函数（functions）

> 结构体、方法和接口

> 并发编程（goroutine）

> 单元测试（unit test）

> 包（Package）和模块（Modules）

> 附 参考