package main

import (
	"fmt"
	"math/rand"
	"runtime"
	"time"
)

func main() {
	rand.Seed(time.Now().UnixNano())

	// calculate the memory occupation state
	runtime.GC()
	var m0 runtime.MemStats
	runtime.ReadMemStats(&m0)

	var large_array = make([]int, 128*1024*1024)
	// array initialization, 1024 MB space
	for i := 0; i < len(large_array); i++ {
		large_array[i] = rand.Int()
	}

	// sort the array in a ascending order
	start := time.Now()

	// n*log_2(n) = 3623878656
	quicksort(large_array[0:])

	elapsed := time.Since(start)

	runtime.GC()
	var m1 runtime.MemStats
	runtime.ReadMemStats(&m1)
	memUsage := m1.Alloc - m0.Alloc

	fmt.Printf("Sort took %.3f seconds\n", float64(elapsed)/1000/1000/1000)
	fmt.Printf("Cost memory %.3f MB\n", float64(memUsage)/1024/1024)

	// Check whether the array is ordered
	// TODO Your code here
}

// sort the array in place, the array will be
// ordered after the return of the function
func quicksort(array []int) {
	// TODO Your code here
}
