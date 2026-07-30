import requests
from deception import AdaptiveDeceptionEngine

class VirtualShellSession:
    """
    Virtual Shell Session
    Simulates a Linux shell environment for an attacker connected via SSH.
    Integrates directly with the Adaptive Deception Engine and logs all activity
    to the FastAPI Threat Intelligence backend.
    """

    def __init__(self, session_id: str, backend_url: str):
        self.session_id = session_id
        self.backend_url = backend_url
        self.cwd = "/root"
        self.username = "root"
        self.hostname = "prod-web-srv-01"
        self.deception_engine = AdaptiveDeceptionEngine()

    def get_prompt(self) -> str:
        symbol = "#" if self.username == "root" else "$"
        return f"{self.username}@{self.hostname}:{self.cwd}{symbol} "

    def log_event(self, event_type: str, input_data: str = "", output_data: str = ""):
        """Asynchronously send event logs to the Threat Intelligence Backend."""
        try:
            requests.post(
                f"{self.backend_url}/api/sessions/{self.session_id}/events",
                json={
                    "event_type": event_type,
                    "input_data": input_data,
                    "output_data": output_data
                },
                timeout=2
            )
        except Exception:
            pass  # Fail gracefully if backend is unreachable

    def execute_command(self, raw_cmd: str) -> str:
        cmd = raw_cmd.strip()
        if not cmd:
            return ""

        # Log command execution event to Threat Intelligence backend
        self.log_event(event_type="command_execution", input_data=cmd)

        # Pass command to Adaptive Deception Engine first
        deception_output, triggered, deception_type = self.deception_engine.inspect_and_respond(cmd)
        if triggered:
            # Log deception trap activation
            self.log_event(
                event_type="deception_triggered",
                input_data=cmd,
                output_data=f"Trap activated: {deception_type}"
            )
            return deception_output

        # Simulated standard Linux bash commands
        parts = cmd.split()
        base_cmd = parts[0]

        if base_cmd == "cd":
            if len(parts) > 1:
                target = parts[1]
                if target == "..":
                    if self.cwd != "/":
                        self.cwd = "/" + "/".join(self.cwd.strip("/").split("/")[:-1])
                        if not self.cwd:
                            self.cwd = "/"
                elif target.startswith("/"):
                    self.cwd = target
                else:
                    self.cwd = (self.cwd.rstrip("/") + "/" + target).replace("//", "/")
            return ""

        elif base_cmd == "pwd":
            return self.cwd + "\n"

        elif base_cmd == "whoami":
            return self.username + "\n"

        elif base_cmd == "id":
            return "uid=0(root) gid=0(root) groups=0(root)\n"

        elif base_cmd in ["ls", "ll"]:
            if self.cwd == "/root":
                return "total 12\ndrwxr-xr-x 2 root root 4096 Jul 30 12:00 .\ndrwxr-xr-x 18 root root 4096 Jul 30 11:55 ..\n-rw-r--r-- 1 root root  220 Jul 30 12:01 config.json\n-rwxr-xr-x 1 root root  512 Jul 30 12:05 deploy.sh\n"
            else:
                return "total 4\ndrwxr-xr-x 2 root root 4096 Jul 30 12:00 .\ndrwxr-xr-x 18 root root 4096 Jul 30 11:55 ..\n"

        elif base_cmd == "cat":
            if len(parts) > 1:
                filename = parts[1]
                if "config.json" in filename:
                    return '{\n  "db_host": "10.0.4.18",\n  "db_port": 3306,\n  "api_key": "sk_prod_9021849128"\n}\n'
                elif "deploy.sh" in filename:
                    return "#!/bin/bash\necho 'Deploying production web cluster...'\nsystemctl start app_service\n"
            return f"cat: {parts[1] if len(parts) > 1 else ''}: No such file or directory\n"

        elif base_cmd in ["sudo", "su"]:
            return "admin is not in the sudoers file. This incident will be reported.\n"

        elif base_cmd == "help":
            return "Available commands: cd, pwd, whoami, id, ls, cat, sudo, su, exit, clear, help\n"

        elif base_cmd == "clear":
            return "\033[H\033[2J"

        elif base_cmd == "exit":
            return "exit"

        else:
            return f"bash: {base_cmd}: command not found\n"
