#!/usr/bin/env python3
"""
Minecraft Java Edition Protocol Implementation
Raw socket implementation untuk handshake dan login
"""

import socket
import struct
import json
import socks
import ssl
import uuid
import time
import random
import string
import zlib

# Minecraft Protocol Versions
MC_PROTOCOL = {
    "1.8": 47,
    "1.9": 107,
    "1.10": 210,
    "1.11": 315,
    "1.12": 335,
    "1.12.1": 338,
    "1.12.2": 340,
    "1.13": 393,
    "1.13.1": 401,
    "1.13.2": 404,
    "1.14": 477,
    "1.14.1": 480,
    "1.14.2": 485,
    "1.14.3": 490,
    "1.14.4": 498,
    "1.15": 573,
    "1.15.1": 575,
    "1.15.2": 578,
    "1.16": 735,
    "1.16.1": 736,
    "1.16.2": 751,
    "1.16.3": 753,
    "1.16.4": 754,
    "1.16.5": 754,
    "1.17": 755,
    "1.17.1": 756,
    "1.18": 757,
    "1.18.1": 757,
    "1.18.2": 758,
    "1.19": 759,
    "1.19.1": 760,
    "1.19.2": 760,
    "1.19.3": 761,
    "1.19.4": 762,
    "1.20": 763,
    "1.20.1": 763,
    "1.20.2": 764,
    "1.20.3": 765,
    "1.20.4": 765,
    "1.20.5": 766,
    "1.20.6": 766,
    "1.21": 767,
    "1.21.1": 767,
    "1.21.2": 768,
    "1.21.3": 768,
    "1.21.4": 769,
    "1.21.5": 770,
    "1.21.6": 771,
    "1.21.7": 772,
    "1.21.8": 773,
    "1.21.9": 774,
    "1.21.10": 774,
    "1.21.11": 774,
}


class MCBuffer:
    """Buffer untuk Minecraft protocol packet encoding/decoding"""
    
    def __init__(self, data=b""):
        self.data = data
        self.pos = 0
    
    def write_varint(self, value):
        """Encode VarInt"""
        out = b""
        while True:
            byte = value & 0x7F
            value >>= 7
            if value != 0:
                byte |= 0x80
            out += struct.pack("B", byte)
            if value == 0:
                break
        self.data += out
        return self
    
    def read_varint(self):
        """Decode VarInt"""
        result = 0
        shift = 0
        while True:
            if self.pos >= len(self.data):
                raise Exception("Buffer underflow")
            byte = self.data[self.pos]
            self.pos += 1
            result |= (byte & 0x7F) << shift
            if (byte & 0x80) == 0:
                break
            shift += 7
            if shift >= 32:
                raise Exception("VarInt too big")
        # Convert to signed
        if result & (1 << 31):
            result -= 1 << 32
        return result
    
    def write_string(self, value):
        """Encode MC string (VarInt length + UTF-8)"""
        encoded = value.encode("utf-8")
        self.write_varint(len(encoded))
        self.data += encoded
        return self
    
    def write_ushort(self, value):
        """Encode unsigned short (big-endian)"""
        self.data += struct.pack(">H", value)
        return self
    
    def write_long(self, value):
        """Encode long (big-endian)"""
        self.data += struct.pack(">q", value)
        return self
    
    def write_byte(self, value):
        """Encode byte"""
        self.data += struct.pack("b", value)
        return self
    
    def write_ubyte(self, value):
        """Encode unsigned byte"""
        self.data += struct.pack("B", value)
        return self
    
    def write_uuid(self, value):
        """Encode UUID (16 bytes big-endian)"""
        if isinstance(value, str):
            value = uuid.UUID(value)
        self.data += value.bytes
        return self
    
    def read_string(self):
        """Decode MC string"""
        length = self.read_varint()
        if self.pos + length > len(self.data):
            raise Exception("String too long")
        result = self.data[self.pos:self.pos + length].decode("utf-8")
        self.pos += length
        return result
    
    def read_byte(self):
        """Decode byte"""
        result = struct.unpack("b", self.data[self.pos:self.pos + 1])[0]
        self.pos += 1
        return result
    
    def read_ubyte(self):
        """Decode unsigned byte"""
        result = struct.unpack("B", self.data[self.pos:self.pos + 1])[0]
        self.pos += 1
        return result
    
    def read_ushort(self):
        """Decode unsigned short"""
        result = struct.unpack(">H", self.data[self.pos:self.pos + 2])[0]
        self.pos += 2
        return result
    
    def read_long(self):
        """Decode long"""
        result = struct.unpack(">q", self.data[self.pos:self.pos + 8])[0]
        self.pos += 8
        return result
    
    def read_bool(self):
        """Decode boolean"""
        return self.read_ubyte() != 0
    
    def build_packet(self):
        """Build final packet: length + data"""
        return self.write_varint(len(self.data)).data


class MCProtocol:
    """Minecraft Java Protocol Client"""
    
    def __init__(self, host, port=25565, version="1.20.4", proxy=None, proxy_type=None):
        self.host = host
        self.port = port
        self.version = version
        self.protocol_id = MC_PROTOCOL.get(version, 765)
        self.proxy = proxy
        self.proxy_type = proxy_type
        self.sock = None
        self.connected = False
        self.compression = False
        self.compression_threshold = 0
    
    def _create_socket(self):
        """Create socket (dengan proxy support)"""
        if self.proxy and self.proxy_type:
            p_host, p_port = self.proxy.split(":")
            if self.proxy_type == "socks4":
                s = socks.socksocket()
                s.set_proxy(socks.SOCKS4, p_host, int(p_port))
            elif self.proxy_type == "socks5":
                s = socks.socksocket()
                s.set_proxy(socks.SOCKS5, p_host, int(p_port))
            elif self.proxy_type == "http":
                # HTTP CONNECT tunnel
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((p_host, int(p_port)))
                connect_req = f"CONNECT {self.host}:{self.port} HTTP/1.1\r\nHost: {self.host}:{self.port}\r\n\r\n"
                s.send(connect_req.encode())
                resp = s.recv(4096)
                if b"200" not in resp:
                    raise Exception(f"HTTP CONNECT failed: {resp[:100]}")
                return s
            else:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        s.settimeout(10)
        return s
    
    def connect(self):
        """Koneksi ke server"""
        try:
            self.sock = self._create_socket()
            self.sock.connect((self.host, self.port))
            self.connected = True
            return True
        except Exception as e:
            self.connected = False
            return False
    
    def disconnect(self):
        """Tutup koneksi"""
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
            self.sock = None
            self.connected = False
    
    def send_packet(self, packet_data):
        """Kirim packet"""
        if not self.connected:
            raise Exception("Not connected")
        self.sock.send(packet_data)
    
    def recv_packet(self):
        """Terima packet"""
        if not self.connected:
            raise Exception("Not connected")
        
        # Baca length
        length = self._recv_varint()
        if length <= 0:
            return None, b""
        
        # Baca data
        data = b""
        while len(data) < length:
            chunk = self.sock.recv(length - len(data))
            if not chunk:
                raise Exception("Connection closed")
            data += chunk
        
        # Handle compression
        if self.compression:
            buf = MCBuffer(data)
            data_length = buf.read_varint()
            if data_length > 0:
                # Decompress
                compressed = data[buf.pos:]
                data = zlib.decompress(compressed)
            else:
                data = data[buf.pos:]
        
        # Parse packet ID
        buf = MCBuffer(data)
        packet_id = buf.read_varint()
        
        # Handle Set Compression packet
        if packet_id == 0x03:
            threshold = buf.read_varint()
            self.compression = True
            self.compression_threshold = threshold
        
        return packet_id, buf
    
    def _recv_varint(self):
        """Terima VarInt dari socket"""
        result = 0
        shift = 0
        while True:
            byte_data = self.sock.recv(1)
            if not byte_data:
                raise Exception("Connection closed")
            byte = byte_data[0]
            result |= (byte & 0x7F) << shift
            if (byte & 0x80) == 0:
                break
            shift += 7
            if shift >= 32:
                raise Exception("VarInt too big")
        if result & (1 << 31):
            result -= 1 << 32
        return result
    
    def send_handshake(self, next_state=2):
        """
        Kirim Handshake packet
        next_state: 1 = Status, 2 = Login
        """
        buf = MCBuffer()
        buf.write_varint(0x00)  # Packet ID
        buf.write_varint(self.protocol_id)  # Protocol version
        buf.write_string(self.host)  # Server address
        buf.write_ushort(self.port)  # Server port
        buf.write_varint(next_state)  # Next state
        
        packet = buf.build_packet()
        self.send_packet(packet)
    
    def send_login_start(self, username, uuid_val=None):
        """
        Kirim Login Start packet
        """
        buf = MCBuffer()
        buf.write_varint(0x00)  # Packet ID
        buf.write_string(username)  # Username
        
        if uuid_val:
            buf.write_uuid(uuid_val)
        else:
            # Generate random UUID
            buf.write_uuid(uuid.uuid4())
        
        packet = buf.build_packet()
        self.send_packet(packet)
    
    def send_status_request(self):
        """Kirim Status Request"""
        buf = MCBuffer()
        buf.write_varint(0x00)  # Packet ID
        packet = buf.build_packet()
        self.send_packet(packet)
    
    def send_status_ping(self):
        """Kirim Status Ping"""
        buf = MCBuffer()
        buf.write_varint(0x01)  # Packet ID
        buf.write_long(int(time.time() * 1000))  # Payload
        packet = buf.build_packet()
        self.send_packet(packet)
    
    def send_chat_message(self, message):
        """Kirim chat message"""
        buf = MCBuffer()
        buf.write_varint(0x03)  # Chat packet ID (1.20.4)
        buf.write_string(message)
        packet = buf.build_packet()
        self.send_packet(packet)
    
    def send_keep_alive(self, keepalive_id):
        """Kirim keep alive response"""
        buf = MCBuffer()
        buf.write_varint(0x15)  # Keep Alive packet ID (varies by version)
        buf.write_long(keepalive_id)
        packet = buf.build_packet()
        self.send_packet(packet)
    
    def get_server_status(self):
        """Dapatkan status server (MOTD, players, dll)"""
        try:
            self.connect()
            self.send_handshake(next_state=1)
            self.send_status_request()
            self.send_status_ping()
            
            packet_id, buf = self.recv_packet()
            if packet_id == 0x00:
                json_str = buf.read_string()
                return json.loads(json_str)
        except Exception as e:
            return {"error": str(e)}
        finally:
            self.disconnect()
        return None


def generate_random_username(length=8):
    """Generate random username untuk cracked server"""
    chars = string.ascii_letters + string.digits + "_"
    return "".join(random.choices(chars, k=length))


def generate_bot_names(prefix="Bot", count=100):
    """Generate list bot names"""
    names = []
    for i in range(count):
        suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
        names.append(f"{prefix}_{suffix}")
    return names


if __name__ == "__main__":
    # Test: cek server status
    import sys
    
    host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 25565
    
    print(f"[*] Checking {host}:{port}...")
    mc = MCProtocol(host, port)
    status = mc.get_server_status()
    
    if status and "error" not in status:
        print(f"[+] Server Status:")
        print(f"    Description: {status.get('description', 'N/A')}")
        print(f"    Version: {status.get('version', {}).get('name', 'N/A')}")
        print(f"    Protocol: {status.get('version', {}).get('protocol', 'N/A')}")
        players = status.get('players', {})
        print(f"    Players: {players.get('online', 0)}/{players.get('max', 0)}")
    else:
        print(f"[-] Error: {status}")
