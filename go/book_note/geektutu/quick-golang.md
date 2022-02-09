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

> 结构体、方法和接口

> 并发编程（goroutine）

> 单元测试（unit test）

> 包（Package）和模块（Modules）

> 附 参考