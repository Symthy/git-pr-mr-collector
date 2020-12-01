#!/bin/sh
INTERVAL_SEC=5
OUTPUT_PATH="/root/statlog"

top -bi -d ${INTERVAL_SEC} >> ${OUTPUT_PATH}/top_`date "+%Y%m%d"`-.log &
iostat -cyt ${INTERVAL_SEC} >> ${OUTPUT_PATH}/iostat_cpu_`date "+%Y%m%d"`-.log &
iostat -dyt -p ALL ${INTERVAL_SEC} >> ${OUTPUT_PATH}/iostat_dev_`date "+%Y%m%d"`-.log &
iostat -xdyt -p ALL ${INTERVAL_SEC} >> ${OUTPUT_PATH}/iostat_x_dev_`date "+%Y%m%d"`-.log &
while true
do
   vmstat | awk '{ "date \"+%Y/%m/%d %H:%M:%S\"" | getline var; print var " ", $0 }' >> ${OUTPUT_PATH}/vmstat_`date "+%Y%m%d"`.log
   free | awk '{ "date \"+%Y/%m/%d %H:%M:%S\"" | getline var; print var " ", $0 }' >> ${OUTPUT_PATH}/free_`date "+%Y%m%d"`.log
   sleep ${INTERVAL_SEC}
done