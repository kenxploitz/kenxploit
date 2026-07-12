#!/usr/bin/env python3
"""
Microsoft OAuth Authentication untuk Minecraft
Device Code Flow untuk mendapatkan Minecraft access token
"""

import requests
import json
import time
import uuid

class MinecraftAuth:
    """Microsoft OAuth Device Code Flow untuk Minecraft"""
    
    # Microsoft OAuth endpoints
    MS_DEVICE_CODE_URL = "https://login.microsoftonline.com/consumers/oauth2/v2.0/devicecode"
    MS_TOKEN_URL = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
    MC_LOGIN_URL = "https://login.live.com/oauth20_token.srf"
    MC_XBL_URL = "https://user.auth.xboxlive.com/user/authenticate"
    MC_XSTS_URL = "https://xsts.auth.xboxlive.com/xsts/authorize"
    MC_AUTH_URL = "https://api.minecraftservices.com/authentication/login_with_xbox"
    MC_PROFILE_URL = "https://api.minecraftservices.com/minecraft/profile"
    
    # Minecraft Launcher Client ID
    CLIENT_ID = "00000000402b5328"  # Official Minecraft Launcher
    
    SCOPES = "XboxLive.signin offline_access"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "MinecraftLauncher/2.2.1"})
    
    def start_device_code_flow(self):
        """Mulai Device Code Flow - user perlu login di browser"""
        print("\n" + "="*60)
        print("  MICROSOFT AUTHENTICATION - DEVICE CODE FLOW")
        print("="*60)
        
        # Step 1: Dapatkan device code
        print("\n[*] Step 1: Meminta device code...")
        
        resp = self.session.post(self.MS_DEVICE_CODE_URL, data={
            "client_id": self.CLIENT_ID,
            "scope": self.SCOPES,
        })
        
        if resp.status_code != 200:
            print(f"[-] Error: {resp.status_code} - {resp.text}")
            return None
        
        data = resp.json()
        
        device_code = data.get("device_code")
        user_code = data.get("user_code")
        verification_uri = data.get("verification_uri")
        expires_in = data.get("expires_in", 900)
        interval = data.get("interval", 5)
        
        print(f"\n{'='*60}")
        print(f"  Buka browser dan kunjungi:")
        print(f"  {verification_uri}")
        print(f"")
        print(f"  Masukkan kode: {user_code}")
        print(f"{'='*60}")
        print(f"\n[*] Menunggu autentikasi... (timeout: {expires_in}s)")
        
        # Step 2: Poll untuk authorization
        start_time = time.time()
        while time.time() - start_time < expires_in:
            time.sleep(interval)
            
            resp = self.session.post(self.MS_TOKEN_URL, data={
                "client_id": self.CLIENT_ID,
                "device_code": device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            })
            
            data = resp.json()
            
            if resp.status_code == 200:
                ms_token = data.get("access_token")
                ms_refresh = data.get("refresh_token")
                print("[+] Microsoft auth berhasil!")
                return self._complete_minecraft_auth(ms_token, ms_refresh)
            
            error = data.get("error", "")
            if error == "authorization_pending":
                print(".", end="", flush=True)
            elif error == "slow_down":
                interval += 5
                print(f"[*] Slow down, interval: {interval}s")
            elif error == "authorization_declined":
                print("\n[-] Autentikasi ditolak oleh user")
                return None
            elif error == "expired_token":
                print("\n[-] Token expired, coba lagi")
                return None
            else:
                print(f"\n[-] Error: {error} - {data.get('error_description', '')}")
                return None
        
        print("\n[-] Timeout menunggu autentikasi")
        return None
    
    def refresh_auth(self, refresh_token):
        """Refresh Microsoft token"""
        resp = self.session.post(self.MS_TOKEN_URL, data={
            "client_id": self.CLIENT_ID,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
            "scope": self.SCOPES,
        })
        
        if resp.status_code == 200:
            data = resp.json()
            ms_token = data.get("access_token")
            ms_refresh = data.get("refresh_token")
            return self._complete_minecraft_auth(ms_token, ms_refresh)
        
        return None
    
    def _complete_minecraft_auth(self, ms_token, ms_refresh):
        """Lengkapi proses auth: XBL → XSTS → Minecraft"""
        
        # Step 3: Xbox Live Token (XBL)
        print("[*] Step 3: Mendapatkan Xbox Live token...")
        
        resp = self.session.post(self.MC_XBL_URL, json={
            "Properties": {
                "AuthMethod": "RPS",
                "SiteName": "user.auth.xboxlive.com",
                "RpsTicket": f"d={ms_token}"
            },
            "RelyingParty": "http://auth.xboxlive.com",
            "TokenType": "JWT"
        }, headers={"Content-Type": "application/json"})
        
        if resp.status_code != 200:
            print(f"[-] XBL Error: {resp.status_code}")
            return None
        
        xbl_data = resp.json()
        xbl_token = xbl_data.get("Token")
        xbl_uhs = xbl_data.get("DisplayClaims", {}).get("xui", [{}])[0].get("uhs")
        
        print("[+] XBL token berhasil")
        
        # Step 4: XSTS Token
        print("[*] Step 4: Mendapatkan XSTS token...")
        
        resp = self.session.post(self.MC_XSTS_URL, json={
            "Properties": {
                "SandboxId": "RETAIL",
                "UserTokens": [xbl_token]
            },
            "RelyingParty": "rp://api.minecraftservices.com/",
            "TokenType": "JWT"
        }, headers={"Content-Type": "application/json"})
        
        if resp.status_code != 200:
            print(f"[-] XSTS Error: {resp.status_code}")
            error_code = resp.json().get("XErr", "")
            if error_code == 2148916233:
                print("    -> Akun tidak punya Xbox Live. Buat Xbox account dulu.")
            elif error_code == 2148916238:
                print("    -> Akun di bawah umur, perlu parent account.")
            return None
        
        xsts_data = resp.json()
        xsts_token = xsts_data.get("Token")
        xsts_uhs = xsts_data.get("DisplayClaims", {}).get("xui", [{}])[0].get("uhs")
        
        print("[+] XSTS token berhasil")
        
        # Step 5: Minecraft Access Token
        print("[*] Step 5: Mendapatkan Minecraft token...")
        
        resp = self.session.post(self.CC_AUTH_URL, json={
            "identityToken": f"XBL3.0 x={xbl_uhs};{xsts_token}"
        }, headers={"Content-Type": "application/json"})
        
        if resp.status_code != 200:
            print(f"[-] MC Auth Error: {resp.status_code} - {resp.text}")
            return None
        
        mc_data = resp.json()
        mc_token = mc_data.get("access_token")
        mc_expires = mc_data.get("expires_in")
        
        print("[+] Minecraft token berhasil!")
        
        # Step 6: Dapatkan profile (username, UUID)
        print("[*] Step 6: Mendapatkan profile...")
        
        resp = self.session.get(self.MC_PROFILE_URL, headers={
            "Authorization": f"Bearer {mc_token}"
        })
        
        if resp.status_code == 200:
            profile = resp.json()
            mc_username = profile.get("name")
            mc_uuid = profile.get("id")
            
            print(f"\n{'='*60}")
            print(f"  AUTH BERHASIL!")
            print(f"{'='*60}")
            print(f"  Username : {mc_username}")
            print(f"  UUID     : {mc_uuid}")
            print(f"  Token    : {mc_token[:20]}...")
            print(f"  Expires  : {mc_expires}s")
            print(f"  Refresh  : {ms_refresh[:20]}...")
            print(f"{'='*60}\n")
            
            return {
                "username": mc_username,
                "uuid": mc_uuid,
                "access_token": mc_token,
                "refresh_token": ms_refresh,
                "expires_in": mc_expires,
            }
        elif resp.status_code == 404:
            print("[-] Minecraft profile tidak ditemukan!")
            print("    -> Akun ini BELUM MEMILIKI MINECRAFT")
            print("    -> Beli Minecraft dulu atau gunakan akun lain")
            return None
        else:
            print(f"[-] Profile Error: {resp.status_code}")
            return None
    
    def save_token(self, token_data, filepath="mc_token.json"):
        """Simpan token ke file"""
        with open(filepath, "w") as f:
            json.dump(token_data, f, indent=2)
        print(f"[*] Token disimpan ke {filepath}")
    
    def load_token(self, filepath="mc_token.json"):
        """Load token dari file"""
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except:
            return None
    
    def verify_token(self, access_token):
        """Verifikasi apakah token masih valid"""
        resp = self.session.get(self.MC_PROFILE_URL, headers={
            "Authorization": f"Bearer {access_token}"
        })
        return resp.status_code == 200


if __name__ == "__main__":
    auth = MinecraftAuth()
    
    print("[*] Minecraft Authentication Tool")
    print("[*] Memerlukan akun Microsoft yang sudah beli Minecraft Java Edition\n")
    
    token_data = auth.start_device_code_flow()
    
    if token_data:
        auth.save_token(token_data)
        print("[+] Token berhasil didapatkan!")
        print(f"[+] Username: {token_data['username']}")
        print(f"[+] UUID: {token_data['uuid']}")
    else:
        print("[-] Gagal mendapatkan token")
