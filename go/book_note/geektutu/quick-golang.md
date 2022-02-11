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
  * 变量
    * ```Go```语言是静态类型的，变量声明必须明确变量的类型。与其他语言不同之处，```Go```语言的类型在变量后面：
      ```
      // 声明变量a int类型，默认为0
      var a int 
      // 声明并初始化变量a int类型，值为1
      var a int = 1
      var a = 1
      a := 1
      ```
  * 简单类型
    * 空值：```nil```
    * 整型类型：```int```（取决于操作系统），```int8```，```int16```，```int32```，```int64```，```uint8```，```uint16```...
    * 浮点数类型：```float32```，```float64```
    * 字节类型：```byte```（等价于```uint8```）
    * 字符串类型：```string```
    * 布尔值类型：```boolean```
    ```
    var i int8 = 10
	var f float32 = 12.2
	var by byte = 'a'
	var str string = "Hello World!"
	var bl = true
    ```
  * 字符串
    * ```Go```语言中，字符串使用```UTF-8```编码。若字符串全为英文，每个字符占1```byte```，与```ASCII```编码一样节省空间。若字符串包含中文，每个字符一般占3```byte```。包含中文的字符串的处理方式与纯```ASCII```编码构成的字符串区别：
      ```
      str1 := "Golang"
	  str2 := "Go语言"
	  fmt.Println(str1[2], string(str1[2])) // 108 l
	  fmt.Println(str2[2], string(str2[2])) // 232 è
	  fmt.Println(reflect.TypeOf(str2[2]).Kind()) // unit8
	  fmt.Println("len(str2)：", len(str2)) // len(str2)： 8
      ```
      使用```reflect.TypeOf()).Kind()```可知道某个变量的类型。字符串是以```byte```数组形式保存，类型是```uint8```，占1个```byte```。打印时需要使用```string```进行类型转换，否则打印的是编码值。```str2```的长度```len(str2)```为8（```Go```占2```byte```，语言占6```byte```）
      若需要获取字符串的每个字符，可将```string```转化为```rune```数组：
      ```
      runeArr := []rune(str2) // 声明并初始化rune数组
	  fmt.Println(runeArr[2], string(runeArr[2])) // 35821 语
	  fmt.Println(reflect.TypeOf(runeArr[2]).Kind()) // int32 -> 4byte
	  fmt.Println("len(runeArr)：", len(runeArr)) // len(runeArr)： 4
      ```
  * 数组与切片
    * 声明数组：
      ```
      var arr1 [5]int // 一维
	  var arr2 [5][5]int // 二维
	  fmt.Println("arr1：", arr1) // arr1： [0 0 0 0 0]
	  fmt.Println("arr2：", arr2) // arr2： [[0 0 0 0 0] [0 0 0 0 0] [0 0 0 0 0] [0 0 0 0 0] [0 0 0 0 0]]
      ```
    * 声明数组并初始化：
      ```
      var arr3 = [5]int{1,2,3,4,5}
      // arr3 := [5]init{1,2,3,4,5}
	  fmt.Println("arr3：", arr3) // arr3： [1 2 3 4 5]
      ```
    * 使用索引遍历/修改数组：
      ```
      for i := 0; i < len(arr3); i++ {
          arr3[i] += 100
      }
	  fmt.Println("arr3：", arr3) // arr3： [101 102 103 104 105]
      ```
    * 数组长度不能改变，若需要拼接两个数组或获取子数组，需要使用切片。切片是数组的抽象，使用数组作为底层结构。切片包含三个组件：长度、容量以及指向底层数组的指针。切片可以随时进行扩展。
    * 声明切片：
      ```
      // 声明长度为0的切片
      slice1 := make([]float32, 0)
      // 声明长度为3，容量为5的切片
	  slice2 := make([]float32, 3, 5)
	  fmt.Println(slice1, len(slice1), cap(slice1)) // [] 0 0
	  fmt.Println(slice1, len(slice2), cap(slice2)) // [0 0 0] 3 5
      ```
    * 切片添加元素：
      ```
      slice2 = append(slice2, 1,2,3,4)
	  fmt.Println(slice2, len(slice2), cap(slice2)) // [0 0 0 1 2 3 4] 7 12
      ```
    * 获取子切片：
      ```
      sub1 := slice2[3:] // 从左到右，索引为3开始分割
	  sub2 := slice2[:3] // 从右到左，索引为3开始分割
	  sub3 := slice2[1:4] // 从左到右，索引以1开始，4结束分割
	  fmt.Println(sub1) // [1 2 3 4]
	  fmt.Println(sub2) // [0 0 0]
	  fmt.Println(sub3) // [0 0 1]
      ```
      子切片分割规则为左区间包含（```[start,end)```）
    * 合并切片：
      ```
      combined := append(sub1, sub2...)
	  fmt.Println(combined) // [1 2 3 4 0 0 0]
      ```
      ```sub2...```是切片解构写法，将切片解构为```N```个独立的元素。
  * 字典（键值对）
    * 声明字典：
      ```
      m1 := make(map[string]string)
      fmt.Println(m1) // map[]
      ```
    * 声明字典并初始化：
      ```
      m2 := map[string]string {
          "Sam": "Male",
		  "Alice": "Female",
      }
      fmt.Println(m2) // map[Alice:Female Sam:Male]
      ```
    * 赋值/修改字典：
      ```
      m2["Sam"] = "Female"
	  fmt.Println(m2) // map[Alice:Female Sam:Female]
      ```
    * ```map```结构为```map[key-type]value-type```
  * 指针
    * 指针即某个值的地址，指针类型定义时使用符号*，对一个已存在的变量，是用符号&获取该变量的地址。
      ```
      var p *string = &str1
	  *p = "Hello"
	  fmt.Println(str1) // Hello
      ```
    * 指针通常在函数传递参数，或给某个类型定义新方法时使用。```Go```语言中，参数是按值传递的，若不使用指针，函数内部将会拷贝一份参数的副本，对参数的修改并不会影响到外部变量的值。若参数使用指针，对参数的传递将会影响到外部变量。
      ```
      func add(num int)  {
          num += 1
      }
      
      func realAdd(num *int)  {
          *num += 1
      }
      ```
      ```
      num := 100
	  add(100)
	  fmt.Println(num) // 100
	  realAdd(&num)
	  fmt.Println(num) // 101
      ```

> 流程控制（if、for、switch）
  * ```if-else```
    ```
    if age := 18; age < 18 {
		fmt.Println("Kid")
	} else {
		fmt.Println("Adult")
	}
    ```
    声明初始化变量可嵌套至```if```条件
  * ```for```
    ```
    // for-i
	sum := 0
	for i := 0; i < 10; i++ {
		if sum > 10 {
			break
		}
		sum += i
	}
	fmt.Println(sum)
	// for-r
	for i, e := range arr3 {
		fmt.Println(i, e)
	}
	for i, e := range slice2 {
		fmt.Println(i, e)
	}
	for k, v := range m2 {
		fmt.Println(k, v)
	}
    ```
    一般循环如累加使用```for-i```循环结构，数组（```array```）、切片（```slice```）、字典（```map```）一般使用```for-r```循环结构，第一个参数为索引，第二个参数为集合中的元素。
  * ```switch```
    ```
    type Gender int8
	const (
		MALE Gender = 1
		FEMALE Gender = 2
	)
	gender := MALE
	switch gender {
	case MALE:
		fmt.Println("male")
		fallthrough
	case FEMALE:
		fmt.Println("female")
		fallthrough
	default:
		fmt.Println("unknown")
	}
    ```
    使用关键字```type```声明新类型```Gender```，数据类型为```int8```。使用关键字```const```定义两个类型为```Gender```的常量```MALE```和```FEMALE```，```Go```语言没有枚举概念，一般使用常量模拟枚举。与其他语言不同，```Go```语言的```switch```不需要```break```中止```case```，```case```执行完定义的行为后，默认不会继续往下执行，若需要继续往下执行，使用关键字```fallthrough```。

> 函数（functions）
  * 参数与返回值
    * 典型函数定义如下，使用关键字```func```，参数可以多个，返回值也支持多个。特别地，```package main```中的```func main()```约定为可执行程序的入口。
      ```
      func funcName(param1 Type1, param2 Type2) (Type1, Type2) {
          //
      }
      ```
      也可以为返回值命名：
      ```
      func funcName(param1 Type1, param2 Type2) (result1 Type1, result2 Type2) {
          //
      }
      ```
      例如，实现两个数加法（一个返回值）和除法的函数（两个返回值）：
      ```
      func intAdd(num1 int, num2 int) (ans int) {
          //return num1 + num2
          ans = num1 + num2
          return
      }
      ```
      ```
      func intDiv(num1 int, num2 int) (int, int) {
          return num1 / num2, num1 % num2
      }
      ```
  * 错误处理（```error handling```）
    * 可预知错误。函数实现过程中若出现不能处理的错误，可以返回调用者处理。
      ```
      func hello(name string) error {
          if len(name) == 0 {
              return errors.New("error：name is null")
          }
          fmt.Println("Hello!", name)
        return nil
      }
      ```
      ```
      // 可预知错误
      if err := hello(""); err != nil {
          fmt.Println("可预知错误：", err)
      }
      ```
      ```
      可预知错误： error：name is null
      ```
      函数返回值定义```errorr```类型。错误处使用```errors.New()```返回特定错误信息，程序正常执行则返回```nil```。调用者使用函数返回值是否为```nil```的逻辑处理错误。
    * 不可预知错误。如数组越界，这类错误可能导致程序非正常退出，这种错误在```Go```语言中成称为```panic```。
      ```
      func getIntNum(index int) (ret int) {
          defer func() {
              if r := recover(); r != nil {
                  fmt.Println(r)
                  ret = -1
              }
          }()
          arr := [4]int{1, 2, 3, 4}
	      return arr[index]
      }
      ```
      ```
      // 不可预知错误
	  fmt.Println(getIntNum(5))
	  fmt.Println("不可预知错误结束")
      ```
      ```
      runtime error: index out of range [5] with length 4
      -1
      不可预知错误结束
      ```
      ```Go```语言使用类似```try-catch```机制的```defer```和```recover```处理不可预知错误。在函数```getIntNum```中，使用```defer```定义异常处理的函数，在协程退出前，会执行完```defer```挂载的任务。因此如果触发了```panic```，控制权交给```defer```。在```defer```处理逻辑中，使用```recover```函数，使程序恢复正常，并且返回错误值-1，若不设置错误返回值则默认返回值0。

> 结构体、方法和接口
  * 结构体（```struct```） 和方法（```methods```)
    * 结构体类似其他语言的```class```，可在结构体中定义多个字段，为结构体实现方法，实例化等。
      ```
      // 定义学生结构体
      type Student struct {
          name string
          age int
      }
      ```
      使用```type```、```struct```关键字声明定义结构体。定义字段```name```类型```string```、```age```类型```int```。
      ```
      // 实现学生结构体hello方法
      func (stu *Student) hello(name string) error {
          if len(name) == 0 {
              return errors.New("error：param name is null")
          }
          fmt.Printf("Hello! %s, I am %s, %d age\n", name, stu.name, stu.age)
          return nil
      }
      ```
      实现方法与实现函数区别在于```func```关键字与函数名```hello```之间，加上该方法对应的实例名```stu```及其类型```*Student```，可通过实例名访问该实例的字段和其他方法。
      ```
      // 实例化学生结构体
      name := "Garden"
      age := 18
      stu := &Student{name, age}
      err := stu.hello("Daemon")
      if err != nil {
          fmt.Println(err)
      }
      stu2 := new(Student)
	  stu2.name = name
	  stu2.age = age
	  err2 := stu2.hello("Daemon")
	  if err2 != nil {
          fmt.Println(err2)
      }
      ```
      使用```&Student{field: value, ...}```或```new(Student)```的形式创建```Student```实例，字段不需每个都赋值，没有显性赋值的变量将被赋予默认值。调用方法通过实例名.方法名(参数)的方式。
      ```
      Hello! Daemon, I am Garden, 18 age
      ```

  * 接口（```interfaces```）
    * 接口定义了一组方法的集合，接口不可被实例化，一个类型可以实现多个接口。如定义接口```Person```以及方法```getName()```，使用关键字```type```、```interface```定义：
      ```
      type Person interface {
          getName() string
      }
      ```
      实现该接口的方法：
      ```
      func (stu *Student) getName() string {
          return stu.name
      }
      ```
      实例化```Student```，强制转换为```Person```接口类型：
      ```
      var person Person = &Student{name, age}
	  fmt.Println(person.getName())
      ```
      若将上述实现该接口的方法```(stu *Student) getName()```注释，编译时会出现以下报错：
      ```
      *Student does not implement Person (missing getName method)
      ```
      验证某个类型实现某个接口的所有方法，若未实现，编译期间将会报错。将空值```nil```转换为```*Student```类型，再转换为```Person```接口，若转换失败说明```Student```并没有实现```Person```接口所有方法：
      ```
      var _ Person = (*Student)(nil)
      ```
      实例可以强制类型转换为接口，接口也可强制类型转换为实例：
      ```
      stu3 := person.(*Student)
	  fmt.Println(stu3.getName())
	  stu3.hello("Daemon")
      ```
  * 空接口
    * 若定义一个没有任何方法的空接口（```interface{}```），这个接口可表示任意类型：
      ```
      m3 := make(map[string]interface{})
      m3["name"] = "Garden"
	  m3["age"] = 18
	  fmt.Println(m3) // map[age:18 name:Garden]
      ```

> 并发编程（goroutine）
  * ```Go```语言提供了```sync```和```channel```两种方式支持协程（```goroutine```）的并发。例如希望并发下载```N```个资源，若多个并发协程之间不需通信，使用```sync.WaitGroup```，等待所有并发协程执行结束。若多个并发协程之间需要通信，使用```channel```。
  * ```sync```
    ```
    import (
        "fmt"
	    "sync"
	    "time"
    )
    ```
    声明```sync.WaitGroup```全局变量：
    ```
    var wg sync.WaitGroup
    ```
    编写并发任务函数：
    ```
    func syncDownload(url string)  {
        fmt.Println("start to sync download：", url)
	    time.Sleep(time.Second) // 模拟下载操作耗时1s
	    wg.Done() // 为wg计数器计数减一
    }
    ```
    调用并发任务函数：
    ```
    for i := 0; i < 3; i++ {
        wg.Add(1) // 为wg计数器计数加一
		go syncDownload("www.garden.com/video/" + string(i + '0')) // 启动新的协程并发执行syncDownload函数
	}
	wg.Wait() // 等待所有的协程执行结束
	fmt.Println("syncDownload finished")
	fmt.Println("done!")
    ```
    运行程序：
    ```
    $ time go run .
    ```
    ```
    start to sync download： www.garden.com/video/2
    start to sync download： www.garden.com/video/1
    start to sync download： www.garden.com/video/0
    syncDownload finished
    done!
    go run .  0.25s user 0.26s system 16% cpu 3.077 total
    ```
  * ```channel```
    ```
    import (
        "fmt"
	    "time"
    )
    ```
    创建大小为10的缓冲信道：
    ```
    var ch = make(chan string, 10)
    ```
    编写并发任务函数：
    ```
    func channelDownload(url string)  {
        fmt.Println("start to channel download：", url)
        time.Sleep(time.Second) // 模拟下载操作耗时1s
        ch <- url // 将url信息发送给信道
    }
    ```
    调用并发任务函数：
    ```
    for i := 0; i < 3; i++ {
		go channelDownload("www.garden.com/video/" + string(i + '0')) // // 启动新的协程并发执行channelDownload函数
	}
	for i := 0; i < 3; i++ {
		msg := <- ch // 等待信道返回消息
		fmt.Println(msg, "channelDownload finished")
	}
	fmt.Println("done!")
    ```
    运行程序：
    ```
    $ time go run .
    ```
    ```
    start to channel download： www.garden.com/video/1
    start to channel download： www.garden.com/video/2
    start to channel download： www.garden.com/video/0
    www.garden.com/video/0 channelDownload finished
    www.garden.com/video/1 channelDownload finished
    www.garden.com/video/2 channelDownload finished
    done!
    go run .  0.25s user 0.26s system 16% cpu 3.077 total
    ```

> 单元测试（unit test）
  * 创建```xxx_test.go```文件
  * 导入```testing```包：
    ```
    import "testing"
    ```
  * 定义测试方法```Testxxx```：
    ```
    func TestAdd(t *testing.T)  {
        // 测试断言逻辑
    }
    ```
  * 编写测试断言逻辑：
    ```
    if ans := add(1, 2); ans != 3 {
		t.Error("add(1, 2) should be equal to 3")
	}
    ```
  * 运行测试用例：
    ```
    $ go test .
    ```
    将自动运行当前```package```下所有测试用例，若需要查看详细信息，可添加```-v```参数：
    ```
    === RUN   TestAdd
    --- PASS: TestAdd (0.00s)
    PASS 
    ok      gitee/FSDGarden/geektutu/quick-golang   0.115s
    ```

> 包（Package）和模块（Modules）
  * Package
    * 一般来说，一个文件夹可作为```package```，同一个```package```内部变量、类型、方法、函数等可互相访问。如：
      ```
      // calc.go
      package main
    
      func add(num1 int, num2 int) int {
          return num1 + num2
      }
      ```
      ```
      // main.go
      package main
      
      import "fmt"
      
      func main() {
          fmt.Println(add(3, 5)) // 8
      }
      ```
      运行```go run main.go```会报错，```add```函数未定义：
      ```
      ./main.go:6:14: undefined: add
      ```
      因```go run main.go```仅编译一个```main.go```文件，需要：
      ```
      $ go run main.go cal.go
      ```
      或
      ```
      $ go run .
      ```
      ```Go```语言中，同个```package```文件一般同时编译。其也有```Public```和```Private```概念，粒度时包。若接口、类型、方法、函数、字段为大写则为```Public```；若首写字母是小写，则为```Private```，对其他```package```不可见。
  * Modules
    * ```Go Modules```是```Go```1.11版本之后引入的，```Go```1.11之前使用```$GOPATH```机制。```Go Modules```可作为较为完善的包管理工具。同时支持代理，国内也享有高速的第三方镜像服务。```go mod```的使用，```Go```1.13版本仍为可选，环境变量```GO111MODULE```的值默认为```AUTO```，强制使用```Go Modules```进行依赖管理，可将```GO111MODULE```设置为```ON```。
    * 初始化一个```Module```：
      ```
      $ go mod init example
      go: creating new go.mod: module example
      ```
      此时，在当前文件夹下生成```go.mod```，该文件记录当前模块的模块名以及所有依赖包的版本。当前目录下新建文件```main.go```：
      ```
      package main
      
      import (
          
          "fmt"
          
          "rsc.io/quote"
      )
      
      func main() {
          fmt.Println(quote.Hello())  // Ahoy, world!
      }
      ```
      运行```go run .```，将会自动触发第三方包```rsc.io/quote```的下载，具体版本信息记录在```go.mod```：
      ```
      module example
      
      go 1.16
      
      require rsc.io/quote v3.1.0+incompatible
      ```
      在当前目录创建子目录：
      ```
      $ mkdir cal
      $ cd cal
      ```
      创建文件```cal.go```：
      ```
      package cal
      
      func Add(num1 int, num2 int) int {
          return num1 + num2
      }
      ```
      ```package main```中使用```package cal```的```Add```函数，```import```模块名/包名即可：
      ```
      package main
      
      import (
          "fmt"
	      "example/cal"
          "rsc.io/quote"
      )
      
      func main() {
          fmt.Println(quote.Hello())
          fmt.Println(calc.Add(10, 3))
      }
      ```
      ```
      $ go run .
      Ahoy, world!
      13
      ```
> 附 参考