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
-H --hosts: Comma-separated list of hosts to attack. Example: host1,host2,host3 (required).
-p --port: The port to attack on the target (default is 80).
-r --max-retries: The maximum number of retries for establishing a connection (default is 5).
-t --timeout: Timeout in seconds for each socket connection (default is 4 seconds).
-n --num-sockets: Number of sockets to open for the attack (default is dynamically calculated based on the system’s open file limit, ulimit).
-w --wait: Time in seconds to wait between sending headers to keep the connections alive (default is 15 seconds).
--cpu-load: Maximum CPU load allowed before stopping new instances of the attack (default is 1.0, meaning 100% of CPU cores can be utilized).
```
