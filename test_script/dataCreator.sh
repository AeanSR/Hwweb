#!/usr/bin/env bash
# 生成quiz_id = 3(已截止，可批改)的solution数据
if [ $# -lt 1 ];then
    echo "usage ./dataCreator [file_prefix], eg ./dataCreator quiz_3"
    exit 1
fi

solutionsCreate(){
    file=$1_solutions.mongo
    strLeft='{"userId":"'
    strRight='","lastTime":"2013-08-22 11:13:05","status":3,"all_score":-1,"quiz_id":3,"solutions":[{"id":1,"type":1,"solution":["A"],"score":0,"status":1},{"id":2,"type":1,"solution":["C"],"score":10,"status":1},{"id":3,"type":1,"solution":["D"],"score":10,"status":1},{"id":4,"type":3,"solution":["我不知道"],"score":0,"status":1},{"id":5,"type":3,"solution":["设要排序的数组是A[0]……A[N-1]，首先任意选取一个数据（通常选用数组的第一个数）作为关键数据，然后将所有比它小的数都放到它前面，所有比它大的数都放到它后面，这个过程称为一趟快速排序。值得注意的是，快速排序不是一种稳定的排序算法，也就是说，多个相同的值的相对位置也许会在算法结束时产生变动。 一趟快速排序的算法是： 1）设置两个变量i、j，排序开始的时候：i=0，j=N-1； 2）以第一个数组元素作为关键数据，赋值给key，即key=A[0]； 3）从j开始向前搜索，即由后开始向前搜索(j--)，找到第一个小于key的值A[j]，将A[j]和A[i]互换； 4）从i开始向后搜索，即由前开始向后搜索(i++)，找到第一个大于key的A[i]，将A[i]和A[j]互换； 5）重复第3、4步，直到i=j； (3,4步中，没找到符合条件的值，即3中A[j]不小于key,4中A[i]不大于key的时候改变j、i的值，使得j=j-1，i=i+1，直至找到为止。找到符合条件的值，进行交换的时候i， j指针位置不变。另外，i==j这一过程一定正好是i+或j-完成的时候，此时令循环结束）。"],"score":0,"status":1}]}'
    echo "[" | tee $file
    for i in `seq $2 $3`; do
        tmp=$strLeft"20142801322"$i$strRight,
        echo $tmp | tee -a $file
    done
    echo "]" | tee -a $file
}

usersCreate(){
    file=$1_users.mongo
    strLeft='{name:"李春典", grade:"大一", username:"lichundian",password:"123456", userId:"'
    strRight='"}'
    echo "[" | tee $file
    for i in `seq $2 $3`; do
        tmp=$strLeft"20142801322"$i$strRight,
        echo $tmp | tee -a $file
    done
    echo "]" | tee -a $file
}

solutionsCreate $1 1000 1298
usersCreate $1 1000 1298
