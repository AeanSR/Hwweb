package main

import (
	"fmt"
)

func main() {
	var name string = "Xu Zhi Wei"
	// iterate for every single byte
	var sum int = 0
	for i := 0; i < len(name); i++ {
		sum += int(name[i])
	}

	// the length of the number with base 10 couldn't exceed 5
	var sum_bytes [5]byte
	var i int = len(sum_bytes) - 1

	for sum != 0 {
		// the ascii code of some position
		var ch byte = byte((sum % 10) - 0 + '0')
		sum_bytes[i] = ch
		i = i - 1
		sum = sum / 10
	}
	sum_str := string(sum_bytes[i+1 : len(sum_bytes)])
	fmt.Println(sum_str)
}
