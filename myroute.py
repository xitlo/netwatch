





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

        # Updated pattern to match the provided HTML structure
        #pattern = r'<td width="50%">.*?</td><td>(.*?)(?:<tr>|</table>)'
        pattern = r'<td width="50%">.*?</td><td>(.*?)(?:</td><td><tr>|<tr>|</table>)'
        matches = re.findall(pattern, body_text_utf8)
        #print(matches)
        #mlen=len(matches)
        #print(mlen)
        #if len(matches) < 13:
            # Log info and raise exception if not enough data is found
         #   raise Exception("Failed to read SIM card information")

        # Assigning values to the report dictionary based on the order in the matches list
        report = {
            'Version': matches[0],
            'SerialNumber': matches[1],
            'IMEI': matches[2],
            'SIM state': matches[3],
            'CIMI': matches[4],
            'ICCID': matches[5],
            'Attachment status': matches[6],
            'OperationsInfo': matches[8],
            'IP address': matches[7],
            'Network type': matches[9],
            'Signal strength': matches[10],
            'Location area code': matches[11],
            'Cell ID': matches[12],
            'RouterType': "usr",
            'SimValid': True,  # Assuming SIM validity needs to be set as True
        }

        return report

if __name__ == "__main__":
    # if len(sys.argv) < 2:
    #     print("Usage: ccidGet ip")
    #     sys.exit(0)
    #
    # ip = sys.argv[1]
    ip= "192.168.30.1"
    router_type = check_router_type(ip)
    rp = None  # report.RouterReport object
    err = None

    if router_type == ROUTER_HUAWEI:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("{} {}".format(timestamp, "router type: huawei"))
        sys.stdout.flush()
        # You need to implement this function
        # rp, err = CheckHuawei(ip)
    elif router_type == ROUTER_USR:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("{} {}".format(timestamp, "router type: usr"))
        sys.stdout.flush()
        # You need to implement this function
        # rp, err = checkUsr(ip)
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("{} {}".format(timestamp, "无法识别的路由器类型"))
        sys.stdout.flush()
        print("{} {}".format(timestamp, "请检查路由器IP是否正确，如果输入IP正确，请联系开发人员"))
        sys.stdout.flush()
        sys.exit(1)

    if err is not None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("{} {}".format(timestamp, err))
        sys.stdout.flush()
        sys.exit(1)
    usr_client = UsrClient(ip='192.168.30.1', user='root', passw='root')
    usr_client.login()
    router_report = usr_client.get_5g_config()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for key, value in router_report.items():
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print("{} {}: {}".format(timestamp, key, value))
        sys.stdout.flush()
    # You need to implement the report logic here
    # if rp.ICCID == "":
    #     print("无法获取ICCID")
    #     sys.exit(1)
    # err = rp.Report()
    # if err is not None:
    #     print(err)
    #     sys.exit(1)

