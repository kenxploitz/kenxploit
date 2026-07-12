#!/usr/bin/env python3
"""
MC Bot Joiner - Standalone script untuk join MC server cracked
Sudah tested dan BERHASIL join ke mcperp.sg1.octavia.id:25626
"""

import socket
import struct
import uuid
import time
import random
import string
import zlib
import threading
import argparse


def wv(val):
    """Write VarInt"""
    out = b""
    while True:
        byte = val & 0x7F; val >>= 7
        if val != 0: byte |= 0x80
        out += struct.pack("B", byte)
        if val == 0: break
    return out


def ws(s_val):
    """Write String"""
    encoded = s_val.encode("utf-8")
    return wv(len(encoded)) + encoded


def rv_sock(sock):
    """Read VarInt from socket"""
    result = 0; shift = 0
    while True:
        b = sock.recv(1)
        if not b: raise Exception("Connection closed")
        byte = b[0]
        result |= (byte & 0x7F) << shift
        if (byte & 0x80) == 0: break
        shift += 7
    if result & (1 << 31): result -= 1 << 32
    return result


def rv_data(data, pos):
    """Read VarInt from data buffer"""
    result = 0; shift = 0
    while pos < len(data):
        byte = data[pos]; pos += 1
        result |= (byte & 0x7F) << shift
        if (byte & 0x80) == 0: break
        shift += 7
    if result & (1 << 31): result -= 1 << 32
    return result, pos


def read_packet(sock, compression=False):
    """Baca satu packet dari socket"""
    length = rv_sock(sock)
    data = b""
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk: raise Exception("Connection closed")
        data += chunk
    
    # Decompress
    if compression:
        dlen, pos = rv_data(data, 0)
        if dlen > 0:
            data = zlib.decompress(data[pos:])
        else:
            data = data[pos:]
    
    # Parse packet ID
    pid, pos = rv_data(data, 0)
    return pid, data, pos


def send_keepalive(sock, kid):
    """Kirim keep alive response"""
    resp = wv(0x15) + struct.pack(">q", kid)
    sock.send(wv(len(resp)) + resp)


def send_chat(sock, message):
    """Kirim chat message"""
    chat_data = wv(0x03) + ws(message)
    sock.send(wv(len(chat_data)) + chat_data)


def connect_bot(host, port, username, protocol=774):
    """Connect satu bot ke server, return socket jika berhasil"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)
        s.connect((host, port))
        
        # Handshake
        hs = wv(0x00) + wv(protocol) + ws(host) + struct.pack(">H", port) + wv(2)
        s.send(wv(len(hs)) + hs)
        
        # Login Start
        login = wv(0x00) + ws(username) + uuid.uuid4().bytes
        s.send(wv(len(login)) + login)
        
        # Handle response
        compression = False
        start = time.time()
        
        while time.time() - start < 10:
            try:
                pid, data, pos = read_packet(s, compression)
                
                if pid == 0x00:  # Disconnect
                    dlen, pos = rv_data(data, pos)
                    reason = data[pos:pos+dlen].decode("utf-8", errors="replace")
                    s.close()
                    return None, f"Disconnect: {reason[:80]}"
                
                elif pid == 0x02:  # Login Success
                    return s, compression
                
                elif pid == 0x03:  # Compression
                    thr, _ = rv_data(data, pos)
                    compression = True
                
            except socket.timeout:
                continue
            except Exception as e:
                s.close()
                return None, str(e)
        
        s.close()
        return None, "Timeout"
        
    except Exception as e:
        return None, str(e)


def bot_session(sock, username, compression, chat_messages, chat_delay, running_flag):
    """Bot session - stay alive dan chat spam"""
    chat_idx = 0
    last_chat = time.time()
    
    while running_flag[0]:
        try:
            sock.settimeout(30)
            pid, data, pos = read_packet(sock, compression)
            
            # Keep Alive
            if pid in [0x1F, 0x23, 0x26, 0x21]:
                try:
                    kid = struct.unpack(">q", data[pos:pos+8])[0]
                    send_keepalive(sock, kid)
                except:
                    pass
            
            # Chat spam
            if chat_messages and time.time() - last_chat > chat_delay:
                msg = chat_messages[chat_idx % len(chat_messages)]
                msg = msg.replace("{player}", username)
                msg = msg.replace("{random}", "".join(random.choices(string.ascii_lowercase, k=4)))
                try:
                    send_chat(sock, msg)
                    print(f"  [CHAT] {username}: {msg}")
                except:
                    pass
                chat_idx += 1
                last_chat = time.time()
            
            # Disconnect
            if pid == 0x1A or pid == 0x19 or pid == 0x17 or pid == 0x00:
                break
                
        except socket.timeout:
            continue
        except Exception as e:
            break
    
    try:
        sock.close()
    except:
        pass


def main():
    parser = argparse.ArgumentParser(description="MC Bot Joiner - Cracked Server")
    parser.add_argument("-t", "--target", required=True, help="Server host")
    parser.add_argument("-p", "--port", type=int, default=25565, help="Port")
    parser.add_argument("-n", "--num-bots", type=int, default=5, help="Jumlah bot")
    parser.add_argument("-d", "--duration", type=int, default=60, help="Durasi (detik)")
    parser.add_argument("-v", "--version", default="1.21.11", help="MC version")
    parser.add_argument("--delay", type=float, default=1.5, help="Delay antar join")
    parser.add_argument("--prefix", default="Kenx", help="Nama prefix")
    parser.add_argument("--chat", nargs="+", help="Chat messages")
    parser.add_argument("--chat-delay", type=float, default=5, help="Chat delay")
    
    args = parser.parse_args()
    
    # Protocol version mapping
    proto_map = {"1.21.11": 774, "1.21.4": 769, "1.20.4": 765, "1.8": 47}
    protocol = proto_map.get(args.version, 774)
    
    print(f"\n{'='*60}")
    print(f"  MC BOT JOINER")
    print(f"{'='*60}")
    print(f"  Target   : {args.target}:{args.port}")
    print(f"  Version  : {args.version} (protocol {protocol})")
    print(f"  Bots     : {args.num_bots}")
    print(f"  Duration : {args.duration}s")
    print(f"  Chat     : {len(args.chat) if args.chat else 0} messages")
    print(f"{'='*60}\n")
    
    connected_bots = []
    failed = 0
    running_flag = [True]
    
    # Connect bots
    for i in range(args.num_bots):
        if not running_flag[0]:
            break
        
        username = f"{args.prefix}_{random.randint(1000,9999)}"
        print(f"[*] Connecting bot {i+1}/{args.num_bots}: {username}...")
        
        sock, result = connect_bot(args.target, args.port, username, protocol)
        
        if sock:
            print(f"  [+] Bot {username} LOGIN SUCCESS!")
            connected_bots.append((sock, username, result))
            
            # Start keep alive thread
            t = threading.Thread(target=bot_session, 
                               args=(sock, username, result, args.chat, args.chat_delay, running_flag))
            t.daemon = True
            t.start()
        else:
            print(f"  [-] Bot {username} FAILED: {result}")
            failed += 1
        
        time.sleep(args.delay)
    
    # Stats
    print(f"\n[*] Connected: {len(connected_bots)} | Failed: {failed}")
    print(f"[*] Menunggu {args.duration}s... (Ctrl+C untuk stop)")
    
    try:
        start = time.time()
        while time.time() - start < args.duration:
            time.sleep(5)
            elapsed = int(time.time() - start)
            print(f"[*] [{elapsed}s/{args.duration}s] Active bots: {len(connected_bots)}")
    except KeyboardInterrupt:
        print("\n[*] Ctrl+C terdeteksi!")
    
    # Cleanup
    running_flag[0] = False
    print(f"\n[*] Disconnecting {len(connected_bots)} bots...")
    for sock, name, _ in connected_bots:
        try:
            sock.close()
        except:
            pass
    
    print(f"[*] Done!")


if __name__ == "__main__":
    main()
