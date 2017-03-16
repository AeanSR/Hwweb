package util

import (
	"fmt"
	"io/ioutil"
	"os"
)

const (
	// all in byte
	FILE_HEADER_SIZE    = 14 // standard size of file header
	BMPINFO_HEADER_SIZE = 40 // standard size of bmpinfo header
	LENGTH_FIELD_SIZE   = 16 // size of occupancy in bmp for the length of hidden data
	INFO_UNIT_SIZE      = 4  // size of occupancy in bmp for a byte of hidden data
)

// Transform bytes to an integer in a little-endian way
func _4byte2int(bs []byte) int {
	var num int = 0
	for i := len(bs) - 1; i >= 0; i-- {
		num = num*256 + int(bs[i])
	}
	return num
}

// Read all bytes from a file
func ReadAll(path string) []byte {
	if all, err := ioutil.ReadFile(path); err != nil {
		fmt.Fprintf(os.Stderr, "%v", err)
		os.Exit(1)
		return []byte{}
	} else {
		return all
	}
}

// Write all data to a file.
func WriteAll(data []byte, path string) {
	if err := ioutil.WriteFile(path, data, 0666); err != nil {
		fmt.Fprintf(os.Stderr, "%v", err)
		os.Exit(1)
		return
	}
}

// Output the bmp file through the indepensible three parts.
// @param imp_path. Output path for the bmp image.
// @param fh, bh, pixel_array. File header, bmpinfo header, pixel array.
// @return possible errors for output
func ProduceImg(img_path string, fh, bh, pixel_array []byte) error {
	if f, err := os.OpenFile(img_path, os.O_RDWR|os.O_CREATE, 0660); err != nil {
		return err
	} else {
		f.Write(fh)
		f.Write(bh)
		f.Write(pixel_array)
		if err := f.Close(); err != nil {
			return err
		} else {
			return nil
		}
	}
}

// Retrieve three parts of the bmp file: file header, bmpinfo header and pixel
// array. Note the bmp file may contain other parts after the pixel array.
// @param imp_path. The bmp file path.
// @return file_header. File heder of 14 bytes.
// @return bmpinfo_header. Bmpinfo header of 40 bytes.
// @return pixel_array. Pixel array of bytes.
// @return err. Possible error that warns the users.
func GetPartsOfBmp(img_path string) (file_header, bmpinfo_header,
	pixel_array []byte, err error) {
	var src_f *os.File
	if src_f, err = os.Open(img_path); err != nil {
		return
	}
	// TODO Your code here
	// Note: 1. Must initialize file_header/bmpinfo_header/pixel_array before
	// you assigning value to them.
	// 2. Return the possible errors such as the file doesn't exist or not obey
	// the bmp standard, when the function should return immediately.

	file_header = make([]byte, FILE_HEADER_SIZE)
	bmpinfo_header = make([]byte, BMPINFO_HEADER_SIZE)

	var read_cnt int
	if read_cnt, err = src_f.Read(file_header); err != nil {
		return
	} else if read_cnt != FILE_HEADER_SIZE || string(file_header[:2]) != "BM" {
		err = fmt.Errorf("The header of %v doesn't obey the window bmp standard",
			img_path)
		return
	}

	if read_cnt, err = src_f.Read(bmpinfo_header); err != nil {
		return
	} else if read_cnt != BMPINFO_HEADER_SIZE || _4byte2int(bmpinfo_header[:4]) !=
		BMPINFO_HEADER_SIZE {
		err = fmt.Errorf("The bmpinfo header of %v doesn't obey the window bmp standard",
			img_path)
		return
	}

	width_pixel := _4byte2int(bmpinfo_header[4:8])
	height_pixel := _4byte2int(bmpinfo_header[8:12])

	pixel_data_size := width_pixel * height_pixel * 3

	pixel_array = make([]byte, pixel_data_size)
	if read_cnt, err = src_f.Read(pixel_array[:]); err != nil || read_cnt !=
		pixel_data_size {
		err = fmt.Errorf("The pixels data size isn't equivalent to one indicated in " +
			"the bmpinfo header")
		return
	}
	err = src_f.Close()
	return
}

// Hide information into the pixel array
// @param hide_data. The data to be hidden
// @param pixel_array. The original pixel array
// @return the modified pixel data, which hides info.
func HideInfo(hide_data []byte, pixel_array []byte) []byte {
	// TODO Your code here
	if (len(hide_data)+1)*4 > len(pixel_array) {
		fmt.Fprintf(os.Stderr, "Information is too large to be hidden into the bmp file\n")
		os.Exit(1)
		return []byte{}
	}

	// insert the length (Max:2^32-1) of the info to be hidden
	length := len(hide_data)
	if length > 0xFFFFFFFF {
		fmt.Fprintf(os.Stderr, "Length of the data is too big, more than 2^32-1\n")
		os.Exit(1)
		return []byte{}
	} else {
		fmt.Printf("The size of the hidden info is %v bytes\n", length)
		insert_data(length, pixel_array[:LENGTH_FIELD_SIZE], LENGTH_FIELD_SIZE)
	}

	// insert the data itself
	for index, data := range hide_data {
		offset := (index << 2) + LENGTH_FIELD_SIZE
		insert_data(int(data), pixel_array[offset:offset+INFO_UNIT_SIZE], INFO_UNIT_SIZE)
	}
	return pixel_array
}

// Restore the hidden data from the pixel array.
// @param pixel_array. Pixel array in bmp file.
// @return. The hidden data in byte array.
func ShowInfo(pixel_array []byte) []byte {
	// TODO Your code here
	length := restore_data(pixel_array[:LENGTH_FIELD_SIZE], LENGTH_FIELD_SIZE)
	fmt.Printf("The size of the hidden info is %v bytes\n", length)
	info := make([]byte, length)
	for i := 0; i < length; i++ {
		offset := (i << 2) + LENGTH_FIELD_SIZE
		info[i] = byte(restore_data(pixel_array[offset:offset+INFO_UNIT_SIZE], INFO_UNIT_SIZE))
	}
	return info
}

// insert one data to the array with @param size elements
func insert_data(data int, array []byte, size int) {
	if len(array) < size {
		fmt.Fprintf(os.Stderr, "Array length is less than @param size\n")
		return
	}
	for i := 0; i < size; i++ {
		v := byte(data & 0x3)
		array[i] &= 0xF4
		array[i] |= v
		data = data >> 2
	}
}

// restore data
func restore_data(array []byte, size int) int {
	if len(array) < size {
		fmt.Fprintf(os.Stderr, "Array length is less than @param size\n")
		return 0
	}
	num := 0
	for i := size - 1; i >= 0; i-- {
		v := int(array[i] & 0x3)
		num = num<<2 + v
	}
	return num
}

func HideProcedure(src_img_path, hide_file_path, dest_img_path string) {
	fmt.Printf("Hide %v into %v -> %v\n", hide_file_path, src_img_path, dest_img_path)
	if file_header, bmpinfo_header, pixel_array,
		err := GetPartsOfBmp(src_img_path); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
		return
	} else {
		hide_data := ReadAll(hide_file_path)
		new_pixel_array := HideInfo(hide_data, pixel_array)
		ProduceImg(dest_img_path, file_header, bmpinfo_header, new_pixel_array)
	}
}

func ShowProcedure(src_img_path, data_path string) {
	fmt.Printf("Show hidden info from %v, then write it to %v\n",
		src_img_path, data_path)
	if _, _, pixel_array, err := GetPartsOfBmp(src_img_path); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
		return
	} else {
		info := ShowInfo(pixel_array)
		WriteAll(info, data_path)
	}
}
