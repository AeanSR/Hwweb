package main

import (
	"./util"
	"fmt"
	"log"
	"os"
	"path"
	"regexp"
	"strconv"
)

// Build all original and modified bmp files of various students' ids
// based on the source bmp.
func build_bmp(src_img_path, path_prefix, hide_file_path string, ids []string, export_dir string) {
	if _, err := os.Stat(export_dir); os.IsNotExist(err) {
		log.Printf("export dir %s doen't exist\n", export_dir)
	}
	if file_header, bmpinfo_header, pixel_array,
		err := util.GetPartsOfBmp(src_img_path); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
		return
	} else {
		for _, id := range ids {
			var id_tmp int
			if len(id) > 5 {
				id = id[len(id)-5:]
			} else if 0 == len(id) {
				continue
			}
			id_tmp, err = strconv.Atoi(id)
			if err != nil {
				log.Printf("id: %s is not correct \n", id)
				continue
			}
			id_int32 := int32(id_tmp)
			new_bmp_header := insert_int_in_bmpinfo_header(bmpinfo_header, id_int32)
			original_img := path.Join(export_dir, path_prefix+id+".bmp")
			result_img := path.Join(export_dir, "m_"+path_prefix+id+".bmp")
			if _, err := os.Stat(original_img); os.IsExist(err) {
				os.Remove(original_img)
			}
			if _, err := os.Stat(result_img); os.IsExist(err) {
				os.Remove(result_img)
			}

			util.ProduceImg(original_img, file_header, new_bmp_header, pixel_array)
			util.HideProcedure(original_img, hide_file_path, result_img)
		}
	}
}

// insert an integer into the unexploit field, actually the image size field.
func insert_int_in_bmpinfo_header(bmpinfo_header []byte, data int32) []byte {
	new_header := make([]byte, len(bmpinfo_header))
	copy(new_header, bmpinfo_header)
	for i := 20; i < 24; i++ {
		new_header[i] = byte(data & 0x3)
		data = data >> 2
	}
	return new_header
}

func build_bmp_from_idfile(src_img_path, hide_file_path, dest_img_prefix, ids_file, export_dir string) {
	re := regexp.MustCompile("\\s+")
	ids := re.Split(string(util.ReadAll(ids_file)), -1)
	build_bmp(src_img_path, hide_file_path, dest_img_prefix, ids, export_dir)
}

func _print_tool_usage() {
	fmt.Fprintf(os.Stderr, "* build args: src_img_path "+
		"hide_file_path dest_img_prefix user_id_file export_dir\n")
}

func main() {
	if len(os.Args) < 6 {
		_print_tool_usage()
		return
	} else {
		build_bmp_from_idfile(os.Args[1], os.Args[2], os.Args[3], os.Args[4], os.Args[5])
	}
}
