import os
import socket
import sys
import threading
import traceback
import paramiko
import requests
from shell import VirtualShellSession

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Generate host key programmatically if it doesn't exist
HOST_KEY_FILE = "test_rsa.key"
if not os.path.exists(HOST_KEY_FILE):
    print("[*] Generating dummy RSA host key...")
    key = paramiko.RSAKey.generate(2048)
    key.write_private_key_file(HOST_KEY_FILE)
HOST_KEY = paramiko.RSAKey(filename=HOST_KEY_FILE)

class HoneypotSSHServer(paramiko.ServerInterface):
    def __init__(self, client_ip):
        self.event = threading.Event()
        self.client_ip = client_ip
        self.session_id = None
        self.username = None

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        self.username = username
        print(f"[+] Login Attempt: IP={self.client_ip} | User={username} | Pass={password}")
        
        # Log session registration to FastAPI backend
        try:
            r = requests.post(
                f"{BACKEND_URL}/api/sessions",
                json={
                    "ip_address": self.client_ip,
                    "username_attempted": username,
                    "password_attempted": password
                },
                timeout=3
            )
            if r.status_code == 200:
                self.session_id = r.json().get("session_id")
        except Exception as e:
            print(f"[-] Failed to register session in backend: {e}")
            
        return paramiko.AUTH_SUCCESSFUL

    def get_allowed_auths(self, username):
        return 'password'

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True

def handle_connection(client_socket, client_ip):
    try:
        transport = paramiko.Transport(client_socket)
        transport.add_server_key(HOST_KEY)
        server = HoneypotSSHServer(client_ip)
        
        try:
            transport.start_server(server=server)
        except paramiko.SSHException:
            print("[-] SSH negotiation failed.")
            return

        # Wait for shell request
        chan = transport.accept(20)
        if chan is None:
            print("[-] No channel opened.")
            return
        
        server.event.wait(10)
        if not server.event.is_set():
            print("[-] Client did not request a shell.")
            return

        # Initialize integrated virtual shell session
        shell = VirtualShellSession(server.session_id, BACKEND_URL)
        
        chan.send("\r\nWelcome to Ubuntu 22.04.1 LTS (GNU/Linux 5.15.0-52-generic x86_64)\r\n\r\n")
        chan.send(" * Documentation:  https://help.ubuntu.com\r\n")
        chan.send(" * Management:     https://landscape.canonical.com\r\n")
        chan.send(" * Support:        https://ubuntu.com/advantage\r\n\r\n")
        
        chan.send(shell.get_prompt())
        
        buf = ""
        while True:
            char = chan.recv(1024).decode('utf-8', errors='ignore')
            if not char:
                break
                
            # Handle keypresses for terminal emulation
            if char in ['\r', '\n']:
                chan.send('\r\n')
                response = shell.execute_command(buf)
                if response == "exit":
                    break
                elif response:
                    formatted_response = response.replace('\n', '\r\n')
                    chan.send(formatted_response)
                
                buf = ""
                chan.send(shell.get_prompt())
            elif char == '\x7f': # Backspace
                if len(buf) > 0:
                    buf = buf[:-1]
                    chan.send('\b \b')
            elif char == '\x03': # Ctrl+C
                chan.send('^C\r\n')
                buf = ""
                chan.send(shell.get_prompt())
            elif char == '\x04': # Ctrl+D
                break
            else:
                buf += char
                chan.send(char)

        # Notify backend that session has ended
        if server.session_id:
            try:
                requests.patch(f"{BACKEND_URL}/api/sessions/{server.session_id}", timeout=2)
            except Exception:
                pass

        chan.close()
    except Exception as e:
        print(f"[-] Exception handling connection: {e}")
        traceback.print_exc()
    finally:
        client_socket.close()

def main():
    server_port = int(os.getenv("PORT", "2222"))
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind(('0.0.0.0', server_port))
    except Exception as e:
        print(f"[-] Bind failed: {e}")
        sys.exit(1)
        
    server_socket.listen(100)
    print(f"[*] SSH Honeypot listening on port {server_port}...")
    
    while True:
        try:
            client_socket, client_addr = server_socket.accept()
            print(f"[+] Incoming connection from {client_addr[0]}:{client_addr[1]}")
            t = threading.Thread(target=handle_connection, args=(client_socket, client_addr[0]))
            t.daemon = True
            t.start()
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[-] Accept failed: {e}")

if __name__ == '__main__':
    main()
