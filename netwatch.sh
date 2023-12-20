







#!/bin/bash

log_dir="/home/mm/netlog"
log_file="${log_dir}/netwatch_$(date +%Y%m%d-%H%M%S).txt"
temp_file="${log_dir}/nmap_results.txt"

# 删除最后一次修改在一周之前的日志文件
find ${log_dir} -type f -name "netwatch_*" -mtime +7 -delete


#sleep 300

# 使用 nmap 执行第一个操作，并将IP地址保存到临时文件中
nmap -sn 192.168.30.0/24 | grep 'Nmap scan report for' | awk '{print $5}' > "${temp_file}"

# 为每个IP执行 ping 操作，并将输出追加到文件中
while read ip; do
    ping -c 3 -W 1 -i 0.5 ${ip} | while read -r line; do echo "$(date '+%Y-%m-%d %H:%M:%S') $line"; done >> "${log_file}"
done < "${temp_file}"

# 执行第二个操作，并将输出追加到文件中
${log_dir}/get_gnss_data.sh >> "${log_file}"

# 执行第三个操作，并将输出追加到文件中
python3 ${log_dir}/myroute.py >> "${log_file}"

# 执行第四个操作，并将输出追加到文件中
ping -c 3 -W 1 -i 0.5 www.baidu.com | while read -r line; do echo "$(date '+%Y-%m-%d %H:%M:%S') $line"; done >> "${log_file}"

while true; do
    # 读取之前获取的IP列表并再次执行 ping 操作，不再重新执行 nmap 扫描
    while read ip; do
        ping -c 3 -W 1 -i 0.5 ${ip} | while read -r line; do echo "$(date '+%Y-%m-%d %H:%M:%S') $line"; done >> "${log_file}"
    done < "${temp_file}"

    # 执行第二个操作，并将输出追加到文件中
    ${log_dir}/get_gnss_data.sh >> "${log_file}"

    # 执行第三个操作，并将输出追加到文件中
    python3 ${log_dir}/myroute1.py >> "${log_file}"

    # 执行第四个操作，并将输出追加到文件中
    ping -c 3 -W 1 -i 0.5 www.baidu.com | while read -r line; do echo "$(date '+%Y-%m-%d %H:%M:%S') $line"; done >> "${log_file}"
    
    #sleep 60
done
