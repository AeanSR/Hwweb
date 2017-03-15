package main

import (
	"fmt"
	"io/ioutil"
	"net/http"
	"os"
)

func main() {
	if httpresp, err := http.Get("http://www.ucas-2017.tk/static/code_project/Richard_Karp.txt"); err != nil || httpresp.StatusCode != http.StatusOK {
		if err != nil {
			// HTTP protocol error
			fmt.Fprintln(os.Stderr, err.Error())
		} else {
			// http response status is not ok
			fmt.Fprintln(os.Stderr, httpresp.Status)
		}
		return
	} else {
		// http response status is ok
		if data, err := ioutil.ReadAll(httpresp.Body); err != nil {
			// file read error
			fmt.Fprintln(os.Stderr, err.Error())
		} else {
			// file read ok, transform the ascii bytes to string
			fmt.Println(string(data))
		}
	}
}
