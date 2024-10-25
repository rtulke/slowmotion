# slowmotion
Slowmotion is a Python based HTTP/S Attacker


# Description
This script performs a Slowloris attack, which opens multiple HTTP connections to a target server and keeps them alive by slowly sending partial headers, thereby exhausting the server’s resources. It dynamically adjusts based on system limits and uses multiple threads to manage sockets and monitor CPU usage.

- The script calculates the maximum number of open sockets allowed by the system
- It creates threads for each host, which open connections, send partial headers, and periodically keep them alive to overwhelm the target server
- It monitors CPU usage to dynamically adjust how many instances of the attack are running, ensuring the system isn’t overloaded

I will extend and rebuild the script this is my first draft let me know where there are problems ;)

# Features

- Socket Initialization: Opens a connection to a target server and sends partial HTTP headers
- Slowloris Attack Logic: Keeps connections alive by periodically sending small chunks of data
- Resource Monitoring: Monitors CPU usage and dynamically spawns new attack instances as needed
- System Resource Limits: Uses system limits (ulimit) to determine the maximum number of open sockets
- Cookie and User-Agent Randomization: Sends random cookies and user-agents to make the attack less predictable.

# Parameters

```
-H --hosts: Comma-separated list of hosts to attack (e.g., host1,host2) (required).
-p --port: Target port (default: 80).
-r --max-retries: Max connection retries (default: 5).
-t --timeout: Timeout per socket in seconds (default: 4).
-n --num-sockets: Number of sockets to open (default: dynamically based on ulimit).
-w --wait: Wait time between sending headers in seconds (default: 15).
-c --cpu-load: Max CPU load before stopping new attacks (default: 1.0 = 100%).
```
