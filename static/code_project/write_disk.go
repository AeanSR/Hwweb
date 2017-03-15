package main

import (
	"fmt"
	"io/ioutil"
	"os"
)

func main() {
	var content string = "Hello, world"
	// Write method only support []byte type, so we must
	// transform the string to []byte in ASCII style
	var byte_content []byte = []byte(content)

	// 0666: linux file permission
	var path string = "hello.txt"
	if err := ioutil.WriteFile(path, byte_content, 0666); err != nil {
		fmt.Fprintln(os.Stderr, err.Error())
		return
	}
}
