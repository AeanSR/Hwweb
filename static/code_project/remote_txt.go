package main

import (
	"fmt"
	"io/ioutil"
	"net/http"
	"os"
)

func main() {
	if httpresp, err := http.Get("http://www.ucas-2017.tk/static/code_project/Richard_Karp.txt"); httpresp.StatusCode != http.StatusOK {
		if err != nil {
			fmt.Fprintln(os.Stderr, err.Error())
		}
		fmt.Fprintln(os.Stderr, httpresp.Status)
		return
	} else {
		if data, err := ioutil.ReadAll(httpresp.Body); err != nil {
			fmt.Fprintln(os.Stderr, err.Error())
		} else {
			// transform the ascii bytes to string
			fmt.Println(string(data))
		}
	}
}
