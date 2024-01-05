#!/bin/bash

log_dir="/home/mm/netlog"
log_file="${log_dir}/netwatch_$(date +%Y%m%d-%H%M%S).txt"
temp_file="${log_dir}/nmap_results.txt"

# 删除最后一次修改在十天之前的日志文件
find ${log_dir} -type f -name "netwatch_*" -mtime +10 -delete

# 延迟,确保所有环境已经起来
# sleep 60
# scan_count=10  # 设置你想要进行nmap扫描的次数，还是会有nmap不到的可能，增大循环次数


# 提取默认网关的IP地址，并只取前三部分作为网段
default_gateway=$(ip r | grep default | awk '{print $3}')
#default_gateway="192.168.2"
network_segment=$(echo ${default_gateway} | cut -d '.' -f 1-3)


# 使用 nmap 执行第一个操作，并将IP地址保存到临时文件中
# 执行 nmap 扫描特定次数
# for i in $(seq 1 $scan_count); do
#    echo "Scanning ${network_segment}.0/24, iteration $i of $scan_count"
#    nmap -sn "${network_segment}.0/24" | grep 'Nmap scan report for' | awk '{print $5}' >> "${temp_file}"
# done

# 对扫描结果进行排序并去重，最后保存到文件中
# sort -u "${temp_file}" -o "${temp_file}"



# 为每个IP执行 ping 操作，并将输出追加到文件中
# while read ip; do
#    ping -c 3 -W 1 -i 0.5 ${ip} | while read -r line; do echo "$(date '+%Y-%m-%d %H:%M:%S') $line"; done >> "${log_file}"
# done < "${temp_file}"


# 执行第二个操作，并将输出追加到变量中
# 创建一个临时文件储存变量
tmp_file="${log_dir}/mktemp"

# 执行脚本并将输出重定向到临时文件
${log_dir}/get_gnss_data.sh > "$tmp_file"

# 使用 awk ，打印除最后一行外的所有行，追加到目标文件中
awk '{if (NR>1) print prev; prev=$0}' "$tmp_file" >> "${log_file}"

# 使用 tail -n 1 获取最后一行，并将其赋值给 GNSS_CONTENT 变量
GNSS_CONTENT=$(tail -n 1 "$tmp_file")
echo "can print $GNSS_CONTENT"

# 删除临时文件
rm "$tmp_file"


# 执行第三个操作，并将输出追加到文件中
python3 ${log_dir}/myroute.py >> "${log_file}"


# 执行第四个操作，并将输出追加到文件中
ping -c 3 -W 1 -i 0.5 baidu.com | while read -r line; do echo "$(date '+%Y-%m-%d %H:%M:%S') $line"; done >> "${log_file}"

count=0

while true; do

# 1. 读取之前获取的IP列表并再次执行 ping 操作，不再重新执行 nmap 扫描
#    while read ip; do
#       ping -c 3 -W 1 -i 0.5 ${ip} | while read -r line; do echo "$(date '+%Y-%m-%d %H:%M:%S') $line"; done >> "${log_file}"
#    done < "${temp_file}"

# 2. 获取经纬度信息，读取get_gnss_data.sh脚本的输出，并保留到GNSS_CONTENT变量

# 创建一个临时文件
tmp_file="${log_dir}/mktemp"

# 执行脚本并将输出重定向到临时文件
${log_dir}/get_gnss_data.sh > "$tmp_file"

# 使用 awk ，打印除最后一行外的所有行，追加到目标文件中
awk '{if (NR>1) print prev; prev=$0}' "$tmp_file" >> "${log_file}"

# 使用 tail -n 1 获取最后一行，并将其赋值给 GNSS_CONTENT 变量
GNSS_CONTENT=$(tail -n 1 "$tmp_file")
#echo "can print $GNSS_CONTENT"

# 删除临时文件
rm "$tmp_file"


# 3. 获取路由器信息，读取myroute1脚本的输出，同时保留最后一行在ROUTER_CONTENT 变量中

ROUTER_CONTENT="NULL, NULL, 0"
TIMEOUT=2
MAX_ATTEMPTS=3
for (( attempt_number=1; attempt_number<=$MAX_ATTEMPTS; attempt_number++ )); do
        echo "Attempt $attempt_number of $MAX_ATTEMPTS"  >> "$log_file"
        tmp_output=$(mktemp)
        timeout ${TIMEOUT}s python3 "${log_dir}/myroute1.py" > "$tmp_output" 2>&1
        status=$?
        #cat $tmp_output
        if [ $status -eq 0 ]; then
                #echo "Command succeeded."
                # 将除了最后一行以外的所有行写入到指定的输出文件中
                head -n -1 "$tmp_output" >> "$log_file"
                # 读取最后一行并保存至变量
                ROUTER_CONTENT=$(tail -n 1 "$tmp_output")
                # 删除临时文件
                rm "$tmp_output"
                break
        elif [ $status -eq 124 ]; then
                echo "Command timed out."
        else
                echo "Command failed with status $status."
        fi
        # 删除临时文件
        rm "$tmp_output"
done
if [ $status -ne 0 ]; then
        echo "route command failed after $MAX_ATTEMPTS attempts."  >> "$log_file"
fi
#echo $ROUTER_CONTENT

# 4. ping外网 ，获取ping baidu的结果输出到文件并且把avg的结果保存到变量中

    avg_rtt=0 #如果ping不通baidu那么保持初始值0
    while read -r line; do
    echo "$(date '+%Y-%m-%d %H:%M:%S') $line" >> "${log_file}" # 将读取到的每一行追加到日志文件
    if [[ "$line" == *"rtt"* ]]; then
        avg_rtt=$(echo $line | awk -F '/' '{print $5}')  # 保留avg结果到变量
    fi
    done < <(ping -c 3 -W 1 -i 0.5 baidu.com)   #注意需要进程交换操作，使得循环外可以获取avg_rtt

# 5. 输出结果汇总，便于excel统计
    let count++
    echo "Check_result_$count, $GNSS_CONTENT, $ROUTER_CONTENT, $avg_rtt" >> "${log_file}"


done
