#!/usr/bin/env python3
"""
MC Bot Joiner v2 - Fixed keep alive timeout
Bot bisa join, stay connected, chat, dan spam
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
    
    if compression:
        dlen, pos = rv_data(data, 0)
        if dlen > 0:
            data = zlib.decompress(data[pos:])
        else:
            data = data[pos:]
    
    pid, pos = rv_data(data, 0)
    return pid, data, pos


def send_packet(sock, packet_id, payload, compression=False):
    """Kirim packet ke server"""
    data = wv(packet_id) + payload
    
    if compression:
        # Compressed format: data_length (varint) + compressed_data
        compressed = zlib.compress(data)
        if len(compressed) < len(data):
            packet = wv(len(data)) + compressed
        else:
            packet = wv(0) + data
    else:
        packet = wv(len(data)) + data
    
    sock.send(packet)


def connect_bot(host, port, username, protocol=774):
    """Connect bot ke server"""
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
                    return s, {"compression": compression}
                
                elif pid == 0x03:  # Compression
                    thr, _ = rv_data(data, pos)
                    compression = True
                
                elif pid == 0x04:  # Login Plugin Request
                    # Respond with plugin response (deny)
                    try:
                        pl_id, pos = rv_data(data, pos)
                        # Send plugin response (successful=false)
                        resp = wv(pl_id) + b"\x00"
                        send_packet(s, 0x02 if not compression else 0x02, resp, compression)
                    except:
                        pass
                
            except socket.timeout:
                continue
            except Exception as e:
                s.close()
                return None, str(e)
        
        s.close()
        return None, "Timeout"
        
    except Exception as e:
        return None, str(e)


def bot_session(sock, username, state, chat_messages, chat_delay, running_flag):
    """Bot session - stay alive, chat, dan spam"""
    compression = state.get("compression", False)
    chat_idx = 0
    last_chat = time.time()
    packets_received = 0
    
    while running_flag[0]:
        try:
            sock.settimeout(15)  # Lebih pendek untuk responsif
            pid, data, pos = read_packet(sock, compression)
            packets_received += 1
            
            # Keep Alive (server -> client)
            if pid in [0x1F, 0x23, 0x26, 0x21, 0x24, 0x25]:
                try:
                    kid = struct.unpack(">q", data[pos:pos+8])[0]
                    # Kirim keep alive SEGERA
                    ka_resp = wv(0x15) + struct.pack(">q", kid)
                    sock.send(wv(len(ka_resp)) + ka_resp)
                except:
                    pass
            
            # Synchronize Position
            elif pid in [0x38, 0x3C, 0x3D, 0x3E]:
                try:
                    x = struct.unpack(">d", data[pos:pos+8])[0]
                    y = struct.unpack(">d", data[pos+8:pos+16])[0]
                    z = struct.unpack(">d", data[pos+16:pos+24])[0]
                    # Confirm teleport
                    tp_id, _ = rv_data(data, pos+24)
                    confirm = wv(0x00) + struct.pack(">q", tp_id if tp_id else 0)
                    sock.send(wv(len(confirm)) + confirm)
                except:
                    pass
            
            # Chat spam
            if chat_messages and time.time() - last_chat > chat_delay:
                msg = chat_messages[chat_idx % len(chat_messages)]
                msg = msg.replace("{player}", username)
                msg = msg.replace("{random}", "".join(random.choices(string.ascii_lowercase, k=4)))
                msg = msg.replace("{time}", str(int(time.time())))
                
                try:
                    send_packet(sock, 0x04, ws(msg), compression)
                    print(f"  [CHAT] {username}: {msg}")
                except:
                    pass
                
                chat_idx += 1
                last_chat = time.time()
            
            # Disconnect
            if pid == 0x1A or pid == 0x19 or pid == 0x17 or pid == 0x00:
                break
                
        except socket.timeout:
            # Timeout bukan error, lanjut
            continue
        except Exception as e:
            break
    
    try:
        sock.close()
    except:
        pass


def main():
    parser = argparse.ArgumentParser(description="MC Bot Joiner v2 - Cracked Server")
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
    
    proto_map = {"1.21.11": 774, "1.21.4": 769, "1.20.4": 765, "1.8": 47}
    protocol = proto_map.get(args.version, 774)
    
    print(f"\n{'='*60}")
    print(f"  MC BOT JOINER v2")
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
    
    for i in range(args.num_bots):
        if not running_flag[0]:
            break
        
        username = f"{args.prefix}_{random.randint(1000,9999)}"
        print(f"[*] Connecting bot {i+1}/{args.num_bots}: {username}...")
        
        sock, state = connect_bot(args.target, args.port, username, protocol)
        
        if sock:
            print(f"  [+] Bot {username} LOGIN SUCCESS!")
            connected_bots.append((sock, username, state))
            
            t = threading.Thread(target=bot_session, 
                               args=(sock, username, state, args.chat, args.chat_delay, running_flag))
            t.daemon = True
            t.start()
        else:
            print(f"  [-] Bot {username} FAILED: {state}")
            failed += 1
        
        time.sleep(args.delay)
    
    print(f"\n[*] Connected: {len(connected_bots)} | Failed: {failed}")
    print(f"[*] Menunggu {args.duration}s... (Ctrl+C untuk stop)\n")
    
    try:
        start = time.time()
        while time.time() - start < args.duration:
            time.sleep(5)
            elapsed = int(time.time() - start)
            print(f"[*] [{elapsed}s/{args.duration}s] Active: {len(connected_bots)}")
    except KeyboardInterrupt:
        print("\n[*] Ctrl+C!")
    
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
