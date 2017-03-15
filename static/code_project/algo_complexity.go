package main

import (
	"fmt"
	"math/rand"
	"runtime"
	"time"
)

func main() {
	rand.Seed(time.Now().UnixNano())

	runtime.GC()
	var m0 runtime.MemStats
	runtime.ReadMemStats(&m0)

	var large_array = make([]int, 1024*1024)
	// 800MB space
	for i := 0; i < len(large_array); i++ {
		large_array[i] = rand.Int()
	}

	// sort the array in a ascending order
	start := time.Now()

	// nlog(n) = 20971520
	quicksort(large_array[0:])

	elapsed := time.Since(start)
	fmt.Printf("Sort took %v\n", elapsed)

	runtime.GC()
	var m1 runtime.MemStats
	runtime.ReadMemStats(&m1)
	memUsage := m1.Alloc - m0.Alloc

	fmt.Printf("Cost memory %v M\n", float64(memUsage)/1024/1024)

	// Check whether the array is ordered
	// TODO Your code here
}

func quicksort(array []int) {
	// TODO Your code here
}
