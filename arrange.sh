#!/usr/bin/env bash
# arrange the upload file into [presentation|report]/classNo/pro_id/
for j in `seq 1 4`; do 
    if [ -d users_upload/report_files/$j ]; then 
        cd users_upload/report_files/$j; 
        for i in `seq 1 12`;do
            if [  `find ./ -name "2014-${j}-${i}-*-presentation.pdf" | wc -l` != 0 ];then
                if [ ! -d ../final/presentation/class-$i/exp-$j ];then
                    mkdir -p ../final/presentation/class-$i/exp-$j ;
                fi
                cp 2014-$j-$i-*-presentation.pdf ../final/presentation/class-$i/exp-$j;
            fi 
            if [  `find ./ -name "2014-${j}-${i}-*-report.pdf" | wc -l` != 0 ];then
                if [ ! -d ../final/report/$i/$j ];then
                    mkdir -p ../final/report/class-$i/exp-$j ;
                fi
                cp 2014-$j-$i-*-report.pdf ../final/report/class-$i/exp-$j;
            fi
        done

        cd ../../
    fi
done

