#!/usr/bin/env python3
"""
MC Bot Joiner v3 - Full login handling
Bot join, selesaikan login, stay alive, chat spam
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
        compressed = zlib.compress(data)
        if len(compressed) < len(data):
            packet = wv(len(data)) + compressed
        else:
            packet = wv(0) + data
    else:
        packet = wv(len(data)) + data
    
    sock.sendall(packet)


def send_client_settings(sock, compression=False):
    """Kirim Client Settings (wajib untuk beberapa server)"""
    payload = (
        ws("en_US") +      # Locale
        wv(8) +            # View distance (8 chunks)
        wv(0) +            # Chat mode (0 = enabled)
        b"\x01" +          # Chat colors
        wv(0x7F) +         # Displayed skin parts
        wv(1) +            # Main hand (1 = right)
        b"\x00" +          # Text filtering
        b"\x01"            # Allow listing
    )
    send_packet(sock, 0x08, payload, compression)


def send_plugin_message(sock, compression=False):
    """Kirim Plugin Message (brand)"""
    payload = ws("minecraft:brand") + ws("KenxBot")
    send_packet(sock, 0x0C, payload, compression)


def send_confirm_teleport(sock, tp_id, compression=False):
    """Konfirmasi teleport"""
    payload = struct.pack(">q", tp_id)
    send_packet(sock, 0x00, payload, compression)


def send_keepalive(sock, kid, compression=False):
    """Kirim keep alive response SEGERA"""
    payload = struct.pack(">q", kid)
    send_packet(sock, 0x15, payload, compression)


def send_chat(sock, message, compression=False):
    """Kirim chat message"""
    payload = ws(message)
    send_packet(sock, 0x04, payload, compression)


def send_position(sock, x=0.0, y=64.0, z=0.0, on_ground=True, compression=False):
    """Kirim posisi"""
    payload = (
        struct.pack(">d", x) +
        struct.pack(">d", y) +
        struct.pack(">d", z) +
        (b"\x01" if on_ground else b"\x00")
    )
    send_packet(sock, 0x0C, payload, compression)


def connect_bot(host, port, username, protocol=774):
    """Connect bot ke server dan selesaikan full login"""
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
        logged_in = False
        joined = False
        got_position = False
        start = time.time()
        packets_handled = 0
        
        while time.time() - start < 15:
            try:
                pid, data, pos = read_packet(s, compression)
                packets_handled += 1
                
                # === LOGIN PHASE ===
                
                if pid == 0x00:  # Disconnect
                    dlen, pos = rv_data(data, pos)
                    reason = data[pos:pos+dlen].decode("utf-8", errors="replace")
                    s.close()
                    return None, f"Disconnect: {reason[:80]}"
                
                elif pid == 0x02:  # Login Success
                    logged_in = True
                    # Kirim Client Settings dan Plugin Message
                    time.sleep(0.1)
                    send_client_settings(s, compression)
                    send_plugin_message(s, compression)
                
                elif pid == 0x03:  # Compression
                    thr, _ = rv_data(data, pos)
                    compression = True
                
                elif pid == 0x04:  # Login Plugin Request
                    pl_id, pos = rv_data(data, pos)
                    # Deny plugin
                    resp = wv(pl_id) + b"\x00"
                    send_packet(s, 0x02, resp, compression)
                
                # === PLAY PHASE ===
                
                elif pid in [0x28, 0x29, 0x2A, 0x2B, 0x2C, 0x2D, 0x2E]:  # Join Game
                    joined = True
                
                elif pid in [0x38, 0x3C, 0x3D, 0x3E, 0x3F]:  # Synchronize Position
                    try:
                        x = struct.unpack(">d", data[pos:pos+8])[0]
                        y = struct.unpack(">d", data[pos+8:pos+16])[0]
                        z = struct.unpack(">d", data[pos+16:pos+24])[0]
                        
                        # Cari teleport ID di sisa data
                        remaining = data[pos+24:]
                        tp_id = 0
                        for check_pos in range(0, len(remaining) - 8):
                            try:
                                val = struct.unpack(">q", remaining[check_pos:check_pos+8])[0]
                                if 0 < val < 1000000:
                                    tp_id = val
                                    break
                            except:
                                pass
                        
                        if tp_id:
                            send_confirm_teleport(s, tp_id, compression)
                        
                        got_position = True
                    except:
                        got_position = True
                
                elif pid in [0x1F, 0x23, 0x26, 0x21, 0x24, 0x25]:  # Keep Alive
                    try:
                        kid = struct.unpack(">q", data[pos:pos+8])[0]
                        send_keepalive(s, kid, compression)
                    except:
                        pass
                
                # Login complete
                if logged_in and joined and got_position:
                    return s, {"compression": compression}
                
                # Login success tanpa join (beberapa server)
                if logged_in and packets_handled > 10:
                    return s, {"compression": compression}
                    
            except socket.timeout:
                continue
            except Exception as e:
                if logged_in:
                    return s, {"compression": compression}
                s.close()
                return None, str(e)
        
        # Timeout tapi sudah login
        if logged_in:
            return s, {"compression": compression}
        
        s.close()
        return None, f"Timeout after {packets_handled} packets"
        
    except Exception as e:
        return None, str(e)


def bot_session(sock, username, state, chat_messages, chat_delay, running_flag):
    """Bot session - stay alive, chat, spam"""
    compression = state.get("compression", False)
    chat_idx = 0
    last_chat = time.time()
    
    while running_flag[0]:
        try:
            sock.settimeout(10)
            pid, data, pos = read_packet(sock, compression)
            
            # Keep Alive - RESPOND SEGERA
            if pid in [0x1F, 0x23, 0x26, 0x21, 0x24, 0x25]:
                try:
                    kid = struct.unpack(">q", data[pos:pos+8])[0]
                    send_keepalive(sock, kid, compression)
                except:
                    pass
            
            # Position update
            elif pid in [0x38, 0x3C, 0x3D, 0x3E, 0x3F]:
                try:
                    remaining = data[pos+24:]
                    tp_id = 0
                    for check_pos in range(0, min(len(remaining)-8, 50)):
                        try:
                            val = struct.unpack(">q", remaining[check_pos:check_pos+8])[0]
                            if 0 < val < 1000000:
                                tp_id = val
                                break
                        except:
                            pass
                    if tp_id:
                        send_confirm_teleport(sock, tp_id, compression)
                except:
                    pass
            
            # Chat spam
            if chat_messages and time.time() - last_chat > chat_delay:
                msg = chat_messages[chat_idx % len(chat_messages)]
                msg = msg.replace("{player}", username)
                msg = msg.replace("{random}", "".join(random.choices(string.ascii_lowercase, k=4)))
                msg = msg.replace("{time}", str(int(time.time())))
                msg = msg.replace("{count}", str(threading.active_count()))
                
                try:
                    send_chat(sock, msg, compression)
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
    parser = argparse.ArgumentParser(description="MC Bot Joiner v3")
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
    print(f"  MC BOT JOINER v3")
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
