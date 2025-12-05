# Epic 4: Oracle Cloud Deployment

> **Role**: Scrum Master
> **Created**: 2025-12-04
> **Epic Owner**: Developer
> **Priority**: P1 (Should Have for MVP)

---

## Epic Overview

### Goal
BookBrain 시스템을 Oracle Cloud Free Tier에 배포하여 외부에서 접근 가능하게 구성

### Success Criteria
- [ ] Docker 컨테이너로 앱 실행
- [ ] 외부 IP/도메인으로 접속 가능
- [ ] HTTPS 적용
- [ ] 기본 인증으로 접근 제한
- [ ] 백업 스크립트 동작

### Dependencies
- Epic 1, 2, 3 완료

---

## Stories

### Story 4.1: Docker 컨테이너화

**As a** Developer
**I want** 앱을 Docker 컨테이너로 패키징
**So that** 일관된 환경에서 배포할 수 있다

#### Acceptance Criteria
```gherkin
Given Dockerfile
When docker build 실행
Then 이미지가 생성된다
When docker run 실행
Then 앱이 컨테이너에서 동작한다
```

#### Tasks
- [ ] `docker/Dockerfile` 작성
- [ ] `docker-compose.yml` 작성
- [ ] 멀티스테이지 빌드 (최적화)
- [ ] 볼륨 마운트 설정
- [ ] 로컬 테스트

#### Dockerfile
```dockerfile
# docker/Dockerfile
FROM python:3.12-slim as builder

WORKDIR /app

# Install build deps
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# --- Runtime ---
FROM python:3.12-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy installed packages
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy app code
COPY src/ ./src/
COPY scripts/ ./scripts/

# Create data directory
RUN mkdir -p /app/data

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "src/ui/app.py", \
     "--server.address", "0.0.0.0", \
     "--server.port", "8501", \
     "--server.headless", "true"]
```

#### docker-compose.yml
```yaml
version: "3.8"

services:
  app:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    container_name: bookbrain-app
    restart: unless-stopped
    ports:
      - "8501:8501"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - CHROMA_HOST=chroma
      - CHROMA_PORT=8000
    volumes:
      - ../data:/app/data
    depends_on:
      chroma:
        condition: service_healthy

  chroma:
    image: chromadb/chroma:latest
    container_name: bookbrain-chroma
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - chroma_data:/chroma/chroma
    environment:
      - ANONYMIZED_TELEMETRY=false
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/heartbeat"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  chroma_data:
```

#### Definition of Done
- 로컬에서 `docker-compose up` 성공
- 브라우저에서 앱 접근 확인

---

### Story 4.2: Oracle Cloud 인스턴스 설정

**As a** Developer
**I want** Oracle Cloud에 서버 인스턴스 설정
**So that** 앱을 클라우드에 배포할 수 있다

#### Acceptance Criteria
```gherkin
Given Oracle Cloud 계정
When ARM 인스턴스 생성
Then SSH 접속이 가능하다
And Docker가 설치된다
And 필요한 포트가 열린다
```

#### Tasks
- [ ] Oracle Cloud 계정 설정 확인
- [ ] ARM Ampere 인스턴스 생성 (4 OCPU, 24GB)
- [ ] SSH 키 설정
- [ ] Docker & Docker Compose 설치
- [ ] Security List 설정 (포트 오픈)

#### Instance Setup Script
```bash
#!/bin/bash
# Oracle Cloud Ubuntu 22.04 초기 설정

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin -y

# Verify
docker --version
docker compose version

# Firewall (iptables)
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

#### Security List Rules
| Type | Protocol | Port | Source |
|------|----------|------|--------|
| Ingress | TCP | 22 | 0.0.0.0/0 (SSH) |
| Ingress | TCP | 80 | 0.0.0.0/0 (HTTP) |
| Ingress | TCP | 443 | 0.0.0.0/0 (HTTPS) |
| Egress | All | All | 0.0.0.0/0 |

#### Definition of Done
- SSH로 인스턴스 접속 성공
- Docker 명령어 동작 확인

---

### Story 4.3: 앱 배포

**As a** Developer
**I want** Docker 이미지를 서버에 배포
**So that** 클라우드에서 앱이 실행된다

#### Acceptance Criteria
```gherkin
Given 서버에 코드 배포
When docker compose up -d 실행
Then 컨테이너가 정상 실행된다
And 서버 IP로 앱 접근 가능하다
```

#### Tasks
- [ ] 코드를 서버로 전송 (git clone 또는 scp)
- [ ] `.env` 파일 설정
- [ ] 데이터 디렉토리 생성
- [ ] `docker compose up -d` 실행
- [ ] 로그 확인 및 디버깅

#### Deployment Steps
```bash
# 1. 서버 접속
ssh ubuntu@<oracle-ip>

# 2. 코드 클론
git clone https://github.com/yourusername/bookbrain.git
cd bookbrain

# 3. 환경 변수 설정
cp .env.example .env
nano .env  # OPENAI_API_KEY 등 설정

# 4. 데이터 디렉토리 준비
mkdir -p data/pdfs data/chroma

# 5. PDF 파일 업로드 (별도 터미널)
scp -r ./pdfs/* ubuntu@<oracle-ip>:~/bookbrain/data/pdfs/

# 6. 컨테이너 실행
docker compose up -d

# 7. 로그 확인
docker compose logs -f

# 8. 데이터 수집 (첫 실행)
docker compose exec app python scripts/ingest.py --pdf-dir /app/data/pdfs
```

#### Definition of Done
- 서버 IP:8501로 앱 접근
- 검색 기능 동작 확인

---

### Story 4.4: Nginx 리버스 프록시 설정

**As a** Developer
**I want** Nginx로 리버스 프록시 설정
**So that** 80/443 포트로 접근하고 SSL을 적용할 수 있다

#### Acceptance Criteria
```gherkin
Given Nginx 설정
When http://domain.com 접속
Then Streamlit 앱으로 프록시된다
And WebSocket 연결이 동작한다
```

#### Tasks
- [ ] Nginx 컨테이너 추가 (docker-compose)
- [ ] `nginx.conf` 작성
- [ ] WebSocket 프록시 설정
- [ ] 테스트

#### docker-compose with Nginx
```yaml
# docker-compose.prod.yml
version: "3.8"

services:
  app:
    # ... (기존 설정)
    expose:
      - "8501"  # 내부만 노출

  chroma:
    # ... (기존 설정)

  nginx:
    image: nginx:alpine
    container_name: bookbrain-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./docker/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./docker/nginx/.htpasswd:/etc/nginx/.htpasswd:ro
      - ./certbot/conf:/etc/letsencrypt:ro
      - ./certbot/www:/var/www/certbot:ro
    depends_on:
      - app

  certbot:
    image: certbot/certbot
    container_name: bookbrain-certbot
    volumes:
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
```

#### Nginx Config
```nginx
# docker/nginx/nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream streamlit {
        server app:8501;
    }

    server {
        listen 80;
        server_name your-domain.com;

        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }

        location / {
            return 301 https://$host$request_uri;
        }
    }

    server {
        listen 443 ssl;
        server_name your-domain.com;

        ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

        # Basic Auth
        auth_basic "BookBrain";
        auth_basic_user_file /etc/nginx/.htpasswd;

        # Proxy to Streamlit
        location / {
            proxy_pass http://streamlit;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 86400;
        }

        # WebSocket
        location /_stcore/stream {
            proxy_pass http://streamlit/_stcore/stream;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_read_timeout 86400;
        }
    }
}
```

#### Definition of Done
- HTTP → HTTPS 리다이렉트 동작
- Streamlit WebSocket 정상 동작

---

### Story 4.5: SSL 인증서 (Let's Encrypt)

**As a** Developer
**I want** Let's Encrypt로 무료 SSL 인증서 발급
**So that** HTTPS로 안전하게 접속할 수 있다

#### Acceptance Criteria
```gherkin
Given 도메인 연결된 서버
When certbot 실행
Then SSL 인증서가 발급된다
And 자동 갱신이 설정된다
```

#### Tasks
- [ ] 도메인 설정 (또는 무료 도메인)
- [ ] Certbot 실행
- [ ] 자동 갱신 cron 설정
- [ ] 인증서 테스트

#### SSL Setup
```bash
# 1. 도메인 없이 테스트 시 - IP로 직접 접속 (SSL 없이)
# 또는 무료 도메인 사용: freedns, duckdns 등

# 2. 인증서 발급 (도메인 있을 때)
# 먼저 nginx가 80 포트에서 HTTP로 동작해야 함

docker compose run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email your@email.com \
    --agree-tos \
    --no-eff-email \
    -d your-domain.com

# 3. 자동 갱신 (crontab)
0 12 * * * docker compose run --rm certbot renew --quiet && docker compose exec nginx nginx -s reload
```

#### Definition of Done
- https://domain.com 접속 성공
- 브라우저에서 자물쇠 아이콘 확인

---

### Story 4.6: Basic 인증 설정

**As a** Developer
**I want** 간단한 비밀번호 인증
**So that** 무단 접근을 방지할 수 있다

#### Acceptance Criteria
```gherkin
Given Basic Auth 설정
When 앱 접속
Then 사용자명/비밀번호 입력 요구
When 올바른 정보 입력
Then 앱 접근 허용
```

#### Tasks
- [ ] `.htpasswd` 파일 생성
- [ ] Nginx 설정에 auth_basic 추가
- [ ] 테스트

#### htpasswd 생성
```bash
# htpasswd 파일 생성
sudo apt install apache2-utils
htpasswd -c docker/nginx/.htpasswd admin
# 비밀번호 입력

# 또는 Docker로
docker run --rm httpd:alpine htpasswd -nb admin yourpassword > docker/nginx/.htpasswd
```

#### Definition of Done
- 인증 없이 접속 시 401 에러
- 올바른 인증 후 접속 성공

---

### Story 4.7: 백업 및 복구 스크립트

**As a** Developer
**I want** 데이터 백업 스크립트
**So that** 데이터 손실에 대비할 수 있다

#### Acceptance Criteria
```gherkin
Given 백업 스크립트
When ./scripts/backup.sh 실행
Then Chroma DB와 BM25 인덱스가 백업된다
And 타임스탬프가 붙은 압축 파일 생성
```

#### Tasks
- [ ] `scripts/backup.sh` 작성
- [ ] `scripts/restore.sh` 작성
- [ ] 주간 cron 설정
- [ ] 백업 보관 정책 (최근 4개)

#### backup.sh
```bash
#!/bin/bash
# scripts/backup.sh

set -e

BACKUP_DIR="/home/ubuntu/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="bookbrain_backup_${TIMESTAMP}"

echo "Starting backup: ${BACKUP_NAME}"

# Create backup directory
mkdir -p ${BACKUP_DIR}/${BACKUP_NAME}

# Stop containers briefly for consistent backup
docker compose stop app

# Backup Chroma data
docker compose exec -T chroma tar -czf - /chroma/chroma > ${BACKUP_DIR}/${BACKUP_NAME}/chroma.tar.gz

# Backup BM25 index
cp /home/ubuntu/bookbrain/data/bm25_index.pkl ${BACKUP_DIR}/${BACKUP_NAME}/

# Backup env (without secrets shown)
cp /home/ubuntu/bookbrain/.env ${BACKUP_DIR}/${BACKUP_NAME}/

# Restart containers
docker compose start app

# Compress
cd ${BACKUP_DIR}
tar -czf ${BACKUP_NAME}.tar.gz ${BACKUP_NAME}
rm -rf ${BACKUP_NAME}

# Keep only last 4 backups
ls -t bookbrain_backup_*.tar.gz | tail -n +5 | xargs -r rm

echo "Backup completed: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
```

#### restore.sh
```bash
#!/bin/bash
# scripts/restore.sh

set -e

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: ./restore.sh <backup_file.tar.gz>"
    exit 1
fi

echo "Restoring from: ${BACKUP_FILE}"

# Stop containers
docker compose down

# Extract backup
tar -xzf ${BACKUP_FILE} -C /tmp
BACKUP_NAME=$(basename ${BACKUP_FILE} .tar.gz)

# Restore Chroma
docker volume rm bookbrain_chroma_data || true
docker volume create bookbrain_chroma_data
docker run --rm -v bookbrain_chroma_data:/chroma/chroma -v /tmp/${BACKUP_NAME}:/backup alpine \
    tar -xzf /backup/chroma.tar.gz -C /

# Restore BM25
cp /tmp/${BACKUP_NAME}/bm25_index.pkl /home/ubuntu/bookbrain/data/

# Cleanup
rm -rf /tmp/${BACKUP_NAME}

# Restart
docker compose up -d

echo "Restore completed"
```

#### Definition of Done
- 백업 실행 및 파일 생성 확인
- 복구 테스트 성공

---

### Story 4.8: 모니터링 및 로깅

**As a** Developer
**I want** 기본적인 로그 확인 방법
**So that** 문제 발생 시 디버깅할 수 있다

#### Acceptance Criteria
```gherkin
Given 실행 중인 컨테이너
When 로그 확인 명령 실행
Then 앱 로그가 출력된다
And 에러 로그를 필터링할 수 있다
```

#### Tasks
- [ ] Docker 로그 명령어 문서화
- [ ] 로그 로테이션 설정
- [ ] 간단한 헬스체크 엔드포인트
- [ ] Uptime 모니터링 (선택: UptimeRobot)

#### Log Commands
```bash
# 전체 로그
docker compose logs -f

# 앱만
docker compose logs -f app

# 최근 100줄
docker compose logs --tail 100 app

# 에러만
docker compose logs app 2>&1 | grep -i error

# 로그 파일 저장
docker compose logs app > app.log
```

#### Uptime Monitoring (Optional)
- UptimeRobot (무료): 5분마다 헬스체크
- URL: https://your-domain.com/_stcore/health

#### Definition of Done
- 로그 확인 명령어 동작
- 헬스체크 응답 확인

---

## Sprint Planning Suggestion

### Sprint 8 (Containerization)
- Story 4.1: Docker 컨테이너화
- Story 4.2: Oracle Cloud 인스턴스
- Story 4.3: 앱 배포

### Sprint 9 (Production Ready)
- Story 4.4: Nginx 리버스 프록시
- Story 4.5: SSL 인증서
- Story 4.6: Basic 인증
- Story 4.7: 백업 스크립트
- Story 4.8: 모니터링

---

## Deployment Checklist

### Pre-deployment
- [ ] 모든 테스트 통과
- [ ] 환경 변수 문서화
- [ ] Docker 이미지 로컬 테스트

### Deployment
- [ ] 서버 인스턴스 준비
- [ ] Docker 설치
- [ ] 코드 배포
- [ ] 데이터 수집 완료

### Post-deployment
- [ ] 앱 접속 테스트
- [ ] 검색 기능 테스트
- [ ] SSL 확인
- [ ] 백업 스크립트 테스트
- [ ] 문서 업데이트

