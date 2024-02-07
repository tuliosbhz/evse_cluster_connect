import socket
import threading
import json

class FindOtherNodes:
    def __init__(self, evse_id, cluster_id):
        self.evse_id = evse_id
        self.cluster_id = cluster_id
        self.my_ip = "192.168.219.6"  # Replace with the actual IP of your device
        self.my_port = 12345  # Replace with the actual port of your device
        self.other_nodes = set()  # Store discovered nodes

        # Start discovery and listening threads
        discovery_thread = threading.Thread(target=self.start_discovery)
        discovery_thread.start()

    def send_broadcast(self):
        message = {
            "command": "discover",
            "cluster_id": self.cluster_id,
            "ip": self.my_ip,
            "port": self.my_port
        }
        data = json.dumps(message).encode()

        # Broadcasting to the local network
        broadcast_address = "192.168.219.255"  # Adjust the broadcast address based on your network
        broadcast_port = 12345

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(data, (broadcast_address, broadcast_port))

    def listen_for_responses(self):
        listen_address = ("", self.my_port)

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind(listen_address)

            while True:
                data, addr = sock.recvfrom(1024)
                message = json.loads(data.decode())

                if (
                    message.get("command") == "discovery_response" and
                    message.get("cluster_id") == self.cluster_id
                ):
                    discovered_node_ip = message.get("ip")
                    discovered_node_port = message.get("port")
                    self.other_nodes.add((discovered_node_ip, discovered_node_port))
                    print(f"Discovered Charger at {discovered_node_ip}:{discovered_node_port}")

    def start_discovery(self):
        # Send broadcast in a separate thread
        discovery_thread = threading.Thread(target=self.send_broadcast)
        discovery_thread.start()

        # Listen for responses in the main thread
        self.listen_for_responses()

# Example usage
charger_instance = Charger(evse_id=1, cluster_id="cluster001")
