import requests
import time
from datetime import datetime, timezone
from threading import Thread

API_BASE_URL = "https://gateway-run.bls.dev/api/v1"
IP_SERVICE_URL = "https://tight-block-2413.txlabs.workers.dev"

# 读取 'proxy.txt' 文件的函数
def read_proxies():
    with open("proxy.txt", "r") as file:
        proxies = [line.strip() for line in file.readlines() if line.strip()]
    return proxies

# 读取 'id.txt' 文件的函数
def read_node_and_hardware_ids():
    with open("id.txt", "r") as file:
        lines = file.readlines()
        return [line.strip().split(":") for line in lines if ":" in line]

# 读取 'user.txt' 文件的函数
def read_auth_tokens():
    with open("user.txt", "r") as file:
        return [line.strip() for line in file.readlines()]

# 获取外部服务的 IP 地址函数
def fetch_ip_address(proxies):
    response = requests.get(IP_SERVICE_URL, proxies=proxies)
    response.raise_for_status()
    data = response.json()
    print(f"[{datetime.now(timezone.utc).isoformat()}] 获取 IP 响应:", data)
    return data["ip"]

# 注册节点的函数
def register_node(node_id, hardware_id, auth_token, proxies):
    register_url = f"{API_BASE_URL}/nodes/{node_id}"
    ip_address = fetch_ip_address(proxies)
    print(f"[{datetime.now(timezone.utc).isoformat()}] 正在注册节点，IP: {ip_address}, 硬件 ID: {hardware_id}")

    payload = {"ipAddress": ip_address, "hardwareId": hardware_id}
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    }

    response = requests.post(register_url, headers=headers, json=payload, proxies=proxies)
    response.raise_for_status()
    data = response.json()
    print(f"[{datetime.now(timezone.utc).isoformat()}] 注册响应:", data)
    return data

# 启动会话的函数
def start_session(node_id, auth_token, proxies):
    start_session_url = f"{API_BASE_URL}/nodes/{node_id}/start-session"
    print(f"[{datetime.now(timezone.utc).isoformat()}] 正在启动节点 {node_id} 的会话，可能需要一段时间...")

    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.post(start_session_url, headers=headers, proxies=proxies)
    response.raise_for_status()
    data = response.json()
    print(f"[{datetime.now(timezone.utc).isoformat()}] 启动会话响应:", data)
    return data

# Ping 节点的函数
def ping_node(node_id, auth_token, proxies):
    ping_url = f"{API_BASE_URL}/nodes/{node_id}/ping"
    print(f"[{datetime.now(timezone.utc).isoformat()}] 正在 Ping 节点 {node_id}")

    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.post(ping_url, headers=headers, proxies=proxies)
    response.raise_for_status()
    data = response.json()
    last_ping = data["status"]
    if last_ping == 'ok':
        log_message = f"[{datetime.now(timezone.utc).isoformat()}] Ping 响应成功 "
        print(log_message)
        return data
    else:
        return None

# 单个任务
def run_single_task(node_id, hardware_id, auth_token, proxies):
    try:
        print(f"[{datetime.now(timezone.utc).isoformat()}] 开始处理节点 ID: {node_id}, 硬件 ID: {hardware_id}")
        register_node(node_id, hardware_id, auth_token, proxies)
        start_session(node_id, auth_token, proxies)

        while True:
            print(f"[{datetime.now(timezone.utc).isoformat()}] 发送 Ping 节点 {node_id}...")
            ping_node(node_id, auth_token, proxies)
            time.sleep(60)
    except Exception as error:
        print(f"[{datetime.now(timezone.utc).isoformat()}] 节点 {node_id} 处理过程中发生错误:", error)

# 主函数
def run_all():
    display_header()
    node_and_hardware_ids = read_node_and_hardware_ids()
    auth_tokens = read_auth_tokens()
    proxies = read_proxies()

    if len(auth_tokens) * 5 != len(node_and_hardware_ids) or len(auth_tokens) * 5 != len(proxies):
        print("Error: 'user.txt' 每个用户必须对应 5 个 ID 和 5 个代理！")
        return

    threads = []
    for i, auth_token in enumerate(auth_tokens):
        for j in range(5):
            index = i * 5 + j
            node_id, hardware_id = node_and_hardware_ids[index]
            proxy = proxies[index]
            proxy_config = {
                "http": f"http://{proxy}",
                "https": f"http://{proxy}",
            }
            thread = Thread(target=run_single_task, args=(node_id, hardware_id, auth_token, proxy_config))
            threads.append(thread)
            thread.start()

    for thread in threads:
        thread.join()

# 显示标题
def display_header():
    print(custom_ascii_art)
    print(f"\n")

if __name__ == "__main__":
    run_all()
