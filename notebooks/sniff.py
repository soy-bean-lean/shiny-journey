# Import necessary libraries
import pandas as pd
from scapy.all import sniff
import threading
import time
import socket
from dns import resolver, reversename

# Configure the DNS resolver to use Google's DNS server (8.8.8.8)
resolver = resolver.Resolver()
resolver.nameservers = ["8.8.8.8"]

# Function to perform reverse DNS lookup
def reverse_dns_lookup(ip):
    try:
        addr = reversename.from_address(ip)
        hostname = str(resolver.resolve(addr, "PTR")[0])
        return hostname
    except Exception as e:
        return ip

# Function to extract interesting cleartext strings from payload
def extract_strings(payload, min_length=4):
    result = []
    current_string = ''
    for char in payload:
        if 32 <= char <= 126:
            current_string += chr(char)
        else:
            if len(current_string) >= min_length:
                result.append(current_string)
            current_string = ''
    if len(current_string) >= min_length:
        result.append(current_string)
    return ', '.join(result)

# Updated process_packet function
def process_packet(packet):
    global packet_data  # Declare packet_data as global
    
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(packet.time))
    try:
        src = packet[0][1].src
        dst = packet[0][1].dst
        proto = packet[0][1].name
        length = len(packet)
    except AttributeError:
        return
    
    payload_strings = ''
    if packet.haslayer('Raw'):
        payload = packet['Raw'].load
        payload_strings = extract_strings(payload)

    src_hostname = reverse_dns_lookup(src)
    dst_hostname = reverse_dns_lookup(dst)
    
    new_data = pd.DataFrame({"Time": [timestamp], "Source": [src], "Source Hostname": [src_hostname], "Destination": [dst], "Destination Hostname": [dst_hostname], "Protocol": [proto], "Length": [length], "Payload Strings": [payload_strings]})
    packet_data = pd.concat([packet_data, new_data], ignore_index=True)

# Initialize an empty DataFrame to store packet information
packet_data = pd.DataFrame(columns=["Time", "Source", "Source Hostname", "Destination", "Destination Hostname", "Protocol", "Length", "Payload Strings"])

# Function to sniff packets
def sniff_packets(interface):
    sniff(iface=interface, prn=process_packet, store=0)

# Function to print summary every 10 seconds
def print_summary():
    while True:
        time.sleep(10)
        print("Summary (Last 10 seconds):\n", packet_data.groupby(["Source", "Source Hostname", "Destination", "Destination Hostname", "Protocol"]).size().reset_index(name="Count"))
        print("\n")

# Set your network interfaces (e.g., ['eth0', 'wlan0'])
network_interfaces = ["eth0", "tailscale0"]

# Start sniffing packets on each network interface
sniffer_threads = []
for interface in network_interfaces:
    sniffer_thread = threading.Thread(target=sniff_packets, args=(interface,))
    sniffer_thread.start()
    sniffer_threads.append(sniffer_thread)

# Start printing summary every 10 seconds
summary_thread = threading.Thread(target=print_summary)
summary_thread.start()


# Join the sniffer threads
for sniffer_thread in sniffer_threads:
    sniffer_thread.join()

# Join the summary thread
summary_thread.join()



