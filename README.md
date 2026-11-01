<h1 align="center">MERN Crash Course 🚀</h1>

![Demo App](/frontend/public/screenshot-for-readme.png)

[Video Tutorial on Youtube](https://youtu.be/Dukz-3mS3Us)

About This Course:

-   ⚛️ Tech Stack: React.js, Node.js, Express.js, MongoDB, Chakra UI
-   🔥 Build an API
-   📱 Responsive UI With React.js and ChakraUI
-   🐞 Error Handling
-   🌐 Deployment
-   🚀 And Many More Cool Features
-   ✅ This is a lot of work. Support my work by subscribing to the [Channel](https://www.youtube.com/@asaprogrammer_)

### Setup .env file

```shell
MONGO_URI=your_mongo_uri
PORT=5000
```

### Run this app locally

```shell
npm run build
```

### Start the app

```shell
npm run start
```

### I'll see you in the next one! 🚀



nano install-security-tools.sh


#!/bin/bash

set -euo pipefail

# ==========================================
# DOCKER + TRIVY + SONARQUBE INSTALLER
# Ubuntu 22.04 / 24.04
# ==========================================

if [ "$EUID" -ne 0 ]; then
    echo "Please run this script with sudo:"
    echo "sudo bash install-security-tools.sh"
    exit 1
fi

CURRENT_USER="${SUDO_USER:-$USER}"

echo "=========================================="
echo " Installing Security Tools"
echo " User: $CURRENT_USER"
echo "=========================================="

# 1. Update Ubuntu
echo "[1/8] Updating system packages..."

apt-get update
apt-get install -y ca-certificates curl gnupg

# 2. Install Docker
echo "[2/8] Installing Docker..."

install -m 0755 -d /etc/apt/keyrings

curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc

chmod a+r /etc/apt/keyrings/docker.asc

. /etc/os-release

cat > /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: ${UBUNTU_CODENAME:-$VERSION_CODENAME}
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

apt-get update

apt-get install -y \
  docker-ce \
  docker-ce-cli \
  containerd.io \
  docker-buildx-plugin \
  docker-compose-plugin

# 3. Enable Docker
echo "[3/8] Starting Docker..."

systemctl enable docker
systemctl start docker

# Create Docker group and add current user
groupadd -f docker
usermod -aG docker "$CURRENT_USER"

# 4. Install Trivy
echo "[4/8] Installing Trivy..."

apt-get install -y wget

wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key \
  | gpg --dearmor --yes -o /usr/share/keyrings/trivy.gpg

echo "deb [signed-by=/usr/share/keyrings/trivy.gpg] https://aquasecurity.github.io/trivy-repo/deb generic main" \
  > /etc/apt/sources.list.d/trivy.list

apt-get update
apt-get install -y trivy

# 5. Configure Linux for SonarQube
echo "[5/8] Configuring kernel settings..."

cat > /etc/sysctl.d/99-sonarqube.conf <<EOF
vm.max_map_count=524288
fs.file-max=131072
EOF

sysctl --system

# 6. Create SonarQube directory
echo "[6/8] Creating SonarQube environment..."

mkdir -p /opt/sonarqube
cd /opt/sonarqube

# 7. Create Docker Compose configuration
echo "[7/8] Creating SonarQube container..."

cat > docker-compose.yml <<'EOF'
services:
  sonarqube:
    image: sonarqube:community
    container_name: sonarqube
    restart: unless-stopped

    ports:
      - "9000:9000"

    environment:
      SONAR_TELEMETRY_ENABLE: "false"

    volumes:
      - sonarqube_data:/opt/sonarqube/data
      - sonarqube_extensions:/opt/sonarqube/extensions
      - sonarqube_logs:/opt/sonarqube/logs

    ulimits:
      nofile:
        soft: 131072
        hard: 131072
      nproc: 8192

volumes:
  sonarqube_data:
  sonarqube_extensions:
  sonarqube_logs:
EOF

# 8. Start SonarQube
echo "[8/8] Starting SonarQube..."

docker compose pull
docker compose up -d

echo ""
echo "=========================================="
echo " INSTALLATION COMPLETED"
echo "=========================================="

echo ""
echo "Docker version:"
docker --version

echo ""
echo "Trivy version:"
trivy --version

echo ""
echo "SonarQube container:"
docker ps --filter name=sonarqube

echo ""
echo "SonarQube URL:"
echo "http://YOUR_EC2_PUBLIC_IP:9000"

echo ""
echo "Default SonarQube credentials:"
echo "Username: admin"
echo "Password: admin"

echo ""
echo "IMPORTANT:"
echo "1. Log out and log back in for Docker group changes."
echo "2. Change the default SonarQube password immediately."
echo "3. Restrict port 9000 in your AWS Security Group."
echo "4. Use HTTPS through a reverse proxy for internet access."
echo ""
echo "Installation finished!"




chmod +x install-security-tools.sh

sudo bash install-security-tools.sh