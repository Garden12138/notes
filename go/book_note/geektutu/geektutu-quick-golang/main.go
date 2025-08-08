package main

import (
	"errors"
	"fmt"
	"reflect"
	"sync"
	"time"
)

func main()  {
	fmt.Println("Hello World!")

	// 变量
	var a1 int
	var a2 int = 1
	var a3 = 1
	a4 := 1
	fmt.Println("变量a1 = ", a1)
	fmt.Println("变量a2 = ", a2)
	fmt.Println("变量a3 = ", a3)
	fmt.Println("变量a4 = ", a4)

	// 简单类型
	var i int8 = 10
	var f float32 = 12.2
	var by byte = 'a'
	var str string = "Hello World!"
	var bl = true
	fmt.Println("空值 = ", nil)
	fmt.Println("整型i = ", i)
	fmt.Println("浮点型f = ", f)
	fmt.Println("字节by = ", by)
	fmt.Println("字符串str = ", str)
	fmt.Println("布尔型bl = ", bl)

	// 字符串
	str1 := "Golang"
	str2 := "Go语言"
	fmt.Println(str1[2], string(str1[2]))
	fmt.Println(str2[2], string(str2[2]))
	fmt.Println(reflect.TypeOf(str2[2]).Kind())
	fmt.Println("len(str2)：", len(str2))
	runeArr := []rune(str2)
	fmt.Println(runeArr[2], string(runeArr[2]))
	fmt.Println(reflect.TypeOf(runeArr[2]).Kind())
	fmt.Println("len(runeArr)：", len(runeArr))

	// 数组与切片
	var arr1 [5]int
	var arr2 [5][5]int
	fmt.Println("arr1：", arr1)
	fmt.Println("arr2：", arr2)
	var arr3 = [5]int{1,2,3,4,5}
	fmt.Println("arr3：", arr3)
	for i := 0; i < len(arr3); i++ {
		arr3[i] += 100
	}
	fmt.Println("arr3：", arr3)

	slice1 := make([]float32, 0)
	slice2 := make([]float32, 3, 5)
	fmt.Println(slice1, len(slice1), cap(slice1))
	fmt.Println(slice2, len(slice2), cap(slice2))
	slice2 = append(slice2, 1,2,3,4)
	fmt.Println(slice2, len(slice2), cap(slice2))
	sub1 := slice2[3:]
	sub2 := slice2[:3]
	sub3 := slice2[1:4]
	fmt.Println(sub1)
	fmt.Println(sub2)
	fmt.Println(sub3)
	combined := append(sub1, sub2...)
	fmt.Println(combined)

	//字典（键值对，map）
	m1 := make(map[string]string)
	m2 := map[string]string {
		"Sam": "Male",
		"Alice": "Female",
	}
	fmt.Println(m1)
	fmt.Println(m2)
	m2["Sam"] = "Female"
	fmt.Println(m2)

	// 指针（pointer）
	var p *string = &str1
	*p = "Hello"
	fmt.Println(str1)
	num := 100
	increment(100)
	fmt.Println(num)
	realIncrement(&num)
	fmt.Println(num)

	// if-else
	if age := 18; age < 18 {
		fmt.Println("Kid")
	} else {
		fmt.Println("Adult")
	}
	// switch
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
	// for
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

	// 函数
	fmt.Println(intAdd(100, 17))
	fmt.Println(intDiv(100, 17))
	// 可预知错误
	if err := hello(""); err != nil {
		fmt.Println("可预知错误：", err)
	}
	// 不可预知错误
	fmt.Println(getIntNum(5))
	fmt.Println("不可预知错误结束")

	//结构体与方法
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
	//接口
	var person Person = &Student{name, age}
	fmt.Println(person.getName())
	var _ Person = (*Student)(nil)
	stu3 := person.(*Student)
	fmt.Println(stu3.getName())
	stu3.hello("Daemon")
	//空接口
	m3 := make(map[string]interface{})
	m3["name"] = "Garden"
	m3["age"] = 18
	fmt.Println(m3)

	//并发编程
	//sync
	for i := 0; i < 3; i++ {
		wg.Add(1)
		go syncDownload("www.garden.com/video/" + string(i + '0'))
	}
	wg.Wait()
	fmt.Println("syncDownload finished")
	fmt.Println("done!")
	//channel
	for i := 0; i < 3; i++ {
		go channelDownload("www.garden.com/video/" + string(i + '0'))
	}
	for i := 0; i < 3; i++ {
		msg := <- ch
		fmt.Println(msg, "channelDownload finished")
	}
	fmt.Println("done!")
}

func increment(num int)  {
	num += 1
	recover()
}

func realIncrement(num *int)  {
	*num += 1
}

func intAdd(num1 int, num2 int) (ans int) {
	//return num1 + num2
	ans = num1 + num2
	return
}

func intDiv(num1 int, num2 int) (int, int) {
	return num1 / num2, num1 % num2
}

func hello(name string) error {
	if len(name) == 0 {
		return errors.New("error：name is null")
	}
	fmt.Println("Hello!", name)
	return nil
}

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

type Student struct {
	name string
	age int
}

func (stu *Student) hello(name string) error {
	if len(name) == 0 {
		return errors.New("error：param name is null")
	}
	fmt.Printf("Hello! %s, I am %s, %d age\n", name, stu.name, stu.age)
	return nil
}

func (stu *Student) getName() string {
	return stu.name
}

type Person interface {
	getName() string
}

var wg sync.WaitGroup

func syncDownload(url string)  {
	fmt.Println("start to sync download：", url)
	time.Sleep(time.Second) // 模拟下载操作耗时1s
	wg.Done()
}

var ch = make(chan string, 10)

func channelDownload(url string)  {
	fmt.Println("start to channel download：", url)
	time.Sleep(time.Second) // 模拟下载操作耗时1s
	ch <- url
}