package main

import (
	"fmt"
)

func main() {
	var name string = "Xu Zhi Wei"
	// iterate for every single byte
	var sum int = 0
	var i int
	for i = 0; i < len(name); i++ {
		sum = sum + int(name[i])
	}

	// assume the length of decimal
	// digits of sum does not exceed 5
	var sum_bytes [5]byte

	// extract '1', '6' and '8' from 861
	var j int
	for j = len(sum_bytes) - 1; sum != 0; j-- {
		sum_bytes[j] = byte(sum%10) + '0'
		sum = sum / 10
	}
	// sum_bytes = [0, 0, '8', '6', '1']

	// print out non-null characters one by one
	var k int
	for k = j + 1; k < len(sum_bytes); k++ {
		fmt.Printf("%c", sum_bytes[k])
	}

	// Carriage Return
	fmt.Println()
}
