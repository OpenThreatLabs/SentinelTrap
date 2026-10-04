import os
import socket
import sys
import threading
import traceback
import paramiko
import requests
from shell import VirtualShellSession

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

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
        self.exec_command = None

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
                    "password_attempted": password,
                    "protocol": "SSH"
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

    def check_channel_exec_request(self, channel, command):
        self.exec_command = command.decode('utf-8', errors='ignore')
        self.event.set()
        return True

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True

def handle_connection(client_socket, client_ip):
    server = None
    chan = None
    transport = None
    try:
        transport = paramiko.Transport(client_socket)
        transport.add_server_key(HOST_KEY)
        server = HoneypotSSHServer(client_ip)
        
        try:
            transport.start_server(server=server)
        except paramiko.SSHException:
            print("[-] SSH negotiation failed.")
            return

        # Wait for channel open
        chan = transport.accept(20)
        if chan is None:
            print("[-] No channel opened.")
            return
        
        # Wait for shell or exec request
        server.event.wait(10)
        if not server.event.is_set():
            print("[-] Client did not request a shell or exec.")
            return

        # Initialize integrated virtual shell session
        shell = VirtualShellSession(server.session_id, BACKEND_URL)

        if server.exec_command is not None:
            # Handle non-interactive SSH exec request
            response = shell.execute_command(server.exec_command)
            if response:
                formatted_response = response.replace('\n', '\r\n')
                chan.send(formatted_response)
            chan.send_exit_status(0)
            return

        # Interactive shell session
        chan.send("\r\nWelcome to Ubuntu 22.04.1 LTS (GNU/Linux 5.15.0-52-generic x86_64)\r\n\r\n")
        chan.send(" * Documentation:  https://help.ubuntu.com\r\n")
        chan.send(" * Management:     https://landscape.canonical.com\r\n")
        chan.send(" * Support:        https://ubuntu.com/advantage\r\n\r\n")
        
        chan.send(shell.get_prompt())
        
        buf = ""
        escape_buf = ""
        while True:
            chunk = chan.recv(1024).decode('utf-8', errors='ignore')
            if not chunk:
                break
                
            for char in chunk:
                # Absorb complete ANSI escape sequences (e.g. arrow keys \x1b[A, \x1b[B, \x1b[C, \x1b[D)
                if escape_buf:
                    escape_buf += char
                    if escape_buf.startswith("\x1b["):
                        if len(escape_buf) > 2 and (0x40 <= ord(char) <= 0x7E or len(escape_buf) > 16):
                            escape_buf = ""
                    elif escape_buf.startswith("\x1bO"):
                        if len(escape_buf) >= 3:
                            escape_buf = ""
                    else:
                        if len(escape_buf) >= 2:
                            escape_buf = ""
                    continue

                if char == '\x1b':
                    escape_buf = "\x1b"
                    continue

                # Handle keypresses for terminal emulation
                if char in ['\r', '\n']:
                    chan.send('\r\n')
                    response = shell.execute_command(buf)
                    if response == "exit":
                        return
                    elif response:
                        formatted_response = response.replace('\n', '\r\n')
                        chan.send(formatted_response)
                    
                    buf = ""
                    chan.send(shell.get_prompt())
                elif char in ['\x7f', '\x08', '\b']: # Backspace (DEL, BS, ^H)
                    if len(buf) > 0:
                        buf = buf[:-1]
                        chan.send('\b \b')
                elif char == '\x03': # Ctrl+C
                    chan.send('^C\r\n')
                    buf = ""
                    chan.send(shell.get_prompt())
                elif char == '\x04': # Ctrl+D
                    return
                elif ord(char) >= 32 or char == '\t':
                    buf += char
                    chan.send(char)

    except Exception as e:
        print(f"[-] Exception handling connection: {e}")
        traceback.print_exc()
    finally:
        # Guarantee session close notification and socket cleanup
        if server and server.session_id:
            try:
                requests.patch(f"{BACKEND_URL}/api/sessions/{server.session_id}", timeout=2)
            except Exception:
                pass
        if chan:
            try:
                chan.close()
            except Exception:
                pass
        if transport:
            try:
                transport.close()
            except Exception:
                pass
        try:
            client_socket.close()
        except Exception:
            pass

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
