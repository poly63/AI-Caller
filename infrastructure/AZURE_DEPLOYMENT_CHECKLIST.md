# SmartCall AI Azure Deployment Checklist (Pilot V1)

## 1. Prerequisites
- Azure subscription with permissions for VM, networking, and DNS.
- Domain name and DNS control.
- OpenAI API key.
- Local machine with `az` CLI and SSH access.

## 2. Resource Planning (Pilot)
- Region: `Central India` (or nearest India region).
- VM size: start with `Standard_D8s_v5` (increase based on load test).
- Managed disk: 200GB+ for DB + logs.
- NSG rules:
  - `22/tcp` from admin IP only
  - `80/tcp` from internet
  - `443/tcp` from internet

## 3. Provision VM
```bash
az group create --name smartcall-rg --location centralindia

az vm create \
  --resource-group smartcall-rg \
  --name smartcall-prod-vm \
  --image Ubuntu2204 \
  --size Standard_D8s_v5 \
  --admin-username azureuser \
  --generate-ssh-keys
```

## 4. Server Bootstrap
```bash
ssh azureuser@<PUBLIC_IP>
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker $USER
```

Reconnect SSH after adding docker group.

## 5. Deploy Project
```bash
sudo mkdir -p /opt/smartcall-ai
sudo chown -R $USER:$USER /opt/smartcall-ai
cd /opt/smartcall-ai
```

Copy project to server (git clone or SCP), then:
```bash
cp .env.example .env
nano .env
```
Update secrets before starting.

## 6. Start Production Stack
```bash
cd /opt/smartcall-ai/infrastructure
docker compose --env-file ../.env -f docker-compose.production.yml up -d --build
docker compose -f docker-compose.production.yml ps
```

## 7. Validate Health
```bash
curl http://localhost/health
curl http://localhost/api/analytics/dashboard -H "X-Tenant-Id: public"
```

## 8. TLS (HTTPS)
- Point DNS `A` record to VM public IP.
- Install reverse proxy TLS (recommended: Certbot on host, or Azure Front Door/Application Gateway TLS termination).

Host-based certbot example:
```bash
sudo apt-get install -y certbot
sudo certbot certonly --standalone -d <your-domain>
```

Then mount certs into Nginx or terminate TLS at Azure edge.

## 9. Backups
- Enable PostgreSQL volume backup:
  - Daily DB dump cron.
  - Weekly offsite copy (Azure Blob Storage).
- Backup `.env` securely in key vault/secrets manager.

## 10. Monitoring
- Enable Azure Monitor agent on VM.
- Alerting:
  - CPU > 80% for 10 min
  - Memory > 80% for 10 min
  - Disk > 75%
  - HTTP 5xx spikes

## 11. Scale Path (After Pilot)
- Move from VM to AKS.
- Managed PostgreSQL + Managed Redis.
- Split worker deployment replicas from API replicas.
- Add queue depth autoscaling.
