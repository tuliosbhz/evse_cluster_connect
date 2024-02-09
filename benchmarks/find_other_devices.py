from scapy.all import ARP, Ether, srp

def scan_local_network(ip_range):
    arp_request = ARP(pdst=ip_range)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")  # Broadcast MAC address
    packet = ether/arp_request

    result = srp(packet, timeout=3, verbose=False)[0]

    devices = []
    for sent, received in result:
        devices.append({'ip': received.psrc, 'mac': received.hwsrc})
    return devices

def main():
    local_network = "192.168.219.0/24"  # Change this to match your network
    print(f"Scanning {local_network} for Raspberry Pi devices...")
    devices = scan_local_network(local_network)

    print("\nRaspberry Pi devices found:")
    for device in devices:
        print(f"IP: {device['ip']}, MAC Address: {device['mac']}")

if __name__ == "__main__":
    main()
