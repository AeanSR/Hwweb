# data initialization for system release

```
./dataImport.sh # mongo database preparation
cd hideinfo_bmp_produce
cp ../userId.csv . # 删除第一行表头，注意添加测试用户
cp ../../static/code_project/{ucas.bmp,Richard_Karp.txt} .
mkdir tmp
ucas.bmp Richard_Karp.txt ucas_ userId.csv ./tmp
mkdir ../../static/bmp_library
mv ./tmp/* ../../static/bmp_library
```
