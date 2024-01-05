
import subprocess
import os
import sys
from paramiko import SSHClient, AutoAddPolicy
import re
import requests
from urllib.parse import urlencode
from datetime import datetime

ROUTER_HUAWEI = "huawei"
ROUTER_USR = "usr"

User = "admin"
Password = "momenta123"


# 这里我省略了CheckHuawei和checkUsr函数，他们需要你去实现具体的逻辑

def get_default_gateway():
    try:
        result = subprocess.check_output("ip r | grep default | awk '{print $3}'", shell=True).decode().strip()
        return result if result else None
    except subprocess.CalledProcessError as e:
        print("无法获取默认网关: " + str(e))
        return None


def run_ssh_cmd(ip_addr, user, password, cmd):
    client = SSHClient()
    client.set_missing_host_key_policy(AutoAddPolicy())

    try:
        client.connect(ip_addr, username=user, password=password)
        stdin, stdout, stderr = client.exec_command(cmd)
        return stdout.read()
    finally:
        client.close()


def check_router_type(ip):
    resp = requests.get("http://{0}".format(ip))
    if "cgi-bin/luci" in resp.text:
        return ROUTER_USR

    resp = requests.get("https://{0}".format(ip), verify=False)
    if "csrf_token" in resp.text:
        return ROUTER_HUAWEI

    return ""


class UsrClient:
    def __init__(self, ip, user, passw):
        self.ip_addr = ip
        self.user = user
        self.passw = passw
        self.stok = ''
        self.url_prefix = ''
        self.session = requests.Session()

    def login(self):
        #url = f"http://{self.ip_addr}/cgi-bin/luci/"
        url = "http://{0}/cgi-bin/luci/".format(self.ip_addr)
        data = {
            'luci_username': self.user,
            'luci_password': self.passw
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        resp = self.session.post(url, data=urlencode(data), headers=headers)

        if resp.status_code != 200:
            # Handle error or throw exception
            raise Exception('Login failed with status code:', resp.status_code)

        final_url = resp.url
        stok_search = re.search(r'stok=([^/]+)', final_url)
        if not stok_search:
            raise Exception('stok not found')

        self.stok = stok_search.group(1)
        #self.url_prefix = f"http://{self.ip_addr}/cgi-bin/luci/;stok={self.stok}"
        self.url_prefix = "http://{0}/cgi-bin/luci/;stok={1}".format(self.ip_addr, self.stok)

    #http://192.168.1.1/cgi-bin/luci/;stok=64893c1f1ed67551201332872a1fa7ea/admin/network/5g_config
    def get_5g_config(self):
        url = "{}/admin/network/5g_config".format(self.url_prefix)
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        resp = self.session.get(url, headers=headers)
        if resp.status_code != 200:
            # Handle error or throw exception
            raise Exception('Failed to get 5G config with status code:', resp.status_code)

        body_text = resp.text.replace("\n", "")
        body_text_utf8 = body_text.encode('latin1').decode('utf-8')  # Assuming the original encoding is latin1, then convert to utf-8
        pattern = r'<td width="50%">.*?</td><td>(.*?)(?:</td><td><tr>|<tr>|</table>)'
        matches = re.findall(pattern, body_text_utf8)

        sim_state_match =re.findall(r"SIM卡状态:</td><td>(.+?)<tr>", body_text_utf8)
        network_type_match = re.findall(r"网络类型:</td><td>(.+?)<tr>", body_text_utf8)
        signal_strength_match = re.findall(r"信号强度:</td><td>(.+?)<tr>", body_text_utf8)
        version_match =re.findall(r"版本号:</td><td>(.+?)<tr>", body_text_utf8)
        series_match = re.findall(r"工厂序列号:</td><td>(.+?)<tr>", body_text_utf8)
        imei_match = re.findall(r"IMEI号:</td><td>(.+?)<tr>", body_text_utf8)
        cimi_match =re.findall(r"CIMI号:</td><td>(.+?)<tr>", body_text_utf8)
        iccid_match = re.findall(r"SIM卡ICCID:</td><td>(.+?)<tr>", body_text_utf8)
        attach_match = re.findall(r"附着状态:</td><td>(.+?)<tr>", body_text_utf8)
        ip_match =re.findall(r"IP地址:</td><td>(.+?)<tr>", body_text_utf8)
        operation_match = re.findall(r"运营商信息:</td><td>(.+?)<tr>", body_text_utf8)
        location_match = re.findall(r"位置区号:</td><td>(.+?)<tr>", body_text_utf8)
        cell_id_match = re.findall(r"小区ID:</td><td>(.+?)<tr>", body_text_utf8)

        # Assigning values to the report dictionary based on the order in the matches list
        report = {
            'SIM state': sim_state_match[0],
            'Network type': network_type_match[0],
            'Signal strength': signal_strength_match[0],
        }

        return report


if __name__ == "__main__":
    ip = get_default_gateway()
    # ip = '192.168.1.1'
    if ip is None:
        sys.exit(1)

    router_type = check_router_type(ip)
    rp = None  # Placeholder for RouterReport object
    err = None

    usr_client = UsrClient(ip=ip, user='root', passw='root')
    try:
        usr_client.login()
        router_report = usr_client.get_5g_config()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("{0} router ip : {1}".format(timestamp, ip))
        for key, value in router_report.items():
            print("{0} {1}: {2}".format(timestamp, key, value))
        print("%s, %s, %s"%(router_report['SIM state'], router_report['Network type'], router_report['Signal strength']))
        sys.stdout.flush()
    except Exception as e:
        print(str(e))
        sys.exit(1)

