# Python Slowloris Attack Tool

A Python implementation of the Slowloris DoS (Denial of Service) attack technique with advanced features like dynamic CPU load management, socket pooling, and server response monitoring.

## Features

- **Multi-threaded architecture**: Enables attacking multiple targets simultaneously
- **Dynamic resource management**: Adjusts attack intensity based on system load
- **Server response monitoring**: Tracks target server response times
- **Socket pooling**: Efficiently manages and recycles connections
- **Graceful termination**: Properly cleans up resources on exit
- **Configurable parameters**: Customize all aspects of the attack

## Requirements

- Python 3.6+
- Required packages:
  - requests
  - pyyaml
  - psutil

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/rtulke/slowmotion.git
   cd slowmotion
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `config.yaml` file in the same directory:
   ```yaml
   user_agents:
     - 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.9999.99 Safari/537.36'
     - 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15'
     # Add more user agents as needed
   ```

## Usage

Basic usage:

```
python slowloris.py -H example.com
```

Advanced usage with all options:

```
python slowloris.py -H example.com,example.org -p 80 -r 5 -t 4 -n 500 -w 15 -c 70.0 --max-instances 5
```

### Command-line Arguments

| Argument | Short | Description | Default |
|----------|-------|-------------|---------|
| `--hosts` | `-H` | Comma-separated list of target hosts | (required) |
| `--port` | `-p` | Target port number | 80 |
| `--max-retries` | `-r` | Maximum connection retry attempts | 5 |
| `--timeout` | `-t` | Socket timeout in seconds | 4 |
| `--num-sockets` | `-n` | Number of sockets per attack instance | (system-dependent) |
| `--wait` | `-w` | Time in seconds between sending headers | 15 |
| `--cpu-limit` | `-c` | CPU usage percentage limit | 70.0 |
| `--max-instances` | | Maximum number of attack instances | 5 |

## Architecture

The tool consists of several key components:

1. **SlowlorisAttack**: Thread class managing a single attack instance against a target
   - Maintains a pool of sockets
   - Periodically sends incomplete HTTP headers
   - Replaces failed connections

2. **ServerMonitor**: Thread class monitoring target server response
   - Periodically checks server status
   - Logs response times and status codes

3. **Resource Management**:
   - Monitors system CPU usage
   - Dynamically adjusts number of attack instances
   - Enforces resource limits

4. **Connection Handling**:
   - Proper socket initialization with retry logic
   - Random HTTP headers and cookies
   - Error handling for network issues

## Technical Details

### Attack Mechanism

The Slowloris attack works by:
1. Opening many connections to the target server
2. Sending partial HTTP headers very slowly
3. Keeping connections open without completing requests
4. Consuming the target's connection pool until it cannot serve legitimate users

### System Resource Monitoring

- CPU usage is continuously monitored
- If CPU usage exceeds the specified limit, attack intensity is reduced
- If CPU usage is below the limit, additional attack threads may be spawned

### Socket Management

- Each attack thread maintains its own socket pool
- Failed sockets are properly closed and removed from the pool
- New sockets are created to replace failed ones

## Development

Contributions to improve the tool are welcome. Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[MIT License](LICENSE)
