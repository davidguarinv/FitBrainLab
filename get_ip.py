import socket
import netifaces

def get_ip_addresses():
    """Get all IP addresses for all network interfaces"""
    ip_list = []
    
    # Get all interfaces
    interfaces = netifaces.interfaces()
    
    for interface in interfaces:
        # Skip loopback interface
        if interface == 'lo' or interface.startswith('lo'):
            continue
            
        # Get addresses for this interface
        addresses = netifaces.ifaddresses(interface)
        
        # Get IPv4 addresses
        if netifaces.AF_INET in addresses:
            for addr in addresses[netifaces.AF_INET]:
                ip = addr['addr']
                if ip != '127.0.0.1':  # Skip localhost
                    ip_list.append((interface, ip))
    
    return ip_list

if __name__ == "__main__":
    print("Available IP addresses:")
    for interface, ip in get_ip_addresses():
        print(f"Interface: {interface}, IP: {ip}")
    
    # Also try socket approach
    print("\nTrying alternative method:")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        print(f"Most likely external IP: {s.getsockname()[0]}")
        s.close()
    except Exception as e:
        print(f"Error with socket method: {e}")
