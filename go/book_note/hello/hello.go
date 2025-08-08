package main

import (
	"fmt"
	"gitee/FSDGarden/greetings"
	"log"
	"gitee/FSDGarden/hello/morestrings"
	"github.com/google/go-cmp/cmp"
)

func main()  {
	log.SetPrefix("greetings: ")

	log.SetFlags(0)
	message, err := greetings.Hello("Garden")
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println(message)

	log.SetFlags(1)
	names := []string{"Daemon", "FSDGarden", "zengjiada"}
	messages, errs := greetings.Hellos(names)
	if errs != nil{
		log.Fatal(errs)
	}
	fmt.Println(messages)
	fmt.Println(morestrings.ReverseRunes("!oG ,olleH"))
	fmt.Println(cmp.Diff("Hello World", "Hello Go"))
}
