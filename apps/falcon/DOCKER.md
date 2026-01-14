# Falcon Trading Platform - Docker Deployment Guide

## Overview

This guide covers deploying Falcon Trading Platform using Docker containers. The containerized deployment includes:

- FHS-compliant installation via `make install`
- Dedicated falcon service account
- Nginx reverse proxy with HTTPS
- Support for both SQLite and PostgreSQL
- Automated GitHub Container Registry builds
- Health checks and proper logging

## Quick Start

### Using Docker Compose (Recommended)

**SQLite Mode (Default):**
```bash
# Start Falcon with SQLite
docker-compose up -d falcon

# Configure API keys
docker exec -it falcon-trading /bin/bash
# Edit /etc/falcon/secrets.env

# Restart to apply changes
docker-compose restart falcon

# Access at http://localhost:5000
```

**PostgreSQL Mode:**
```bash
# Start Falcon with PostgreSQL
docker-compose --profile postgres up -d

# Configure API keys
docker exec -it falcon-trading-postgres /bin/bash
# Edit /etc/falcon/secrets.env

# Restart to apply changes
docker-compose --profile postgres restart

# Access at http://localhost:5001
```

### Using Docker CLI

**Build the image:**
```bash
docker build -t falcon-trading:latest .
```

**Run with SQLite:**
```bash
docker run -d \
  --name falcon-trading \
  -p 80:80 \
  -p 443:443 \
  -p 5000:5000 \
  -v falcon-config:/etc/falcon \
  -v falcon-data:/var/lib/falcon \
  -v falcon-cache:/var/cache/falcon \
  -v falcon-logs:/var/log/falcon \
  -e FALCON_ENV=production \
  falcon-trading:latest
```

**Run with PostgreSQL:**
```bash
# First, start PostgreSQL
docker run -d \
  --name falcon-postgres \
  -e POSTGRES_DB=falcon \
  -e POSTGRES_USER=falcon \
  -e POSTGRES_PASSWORD=secure_password \
  -v postgres-data:/var/lib/postgresql/data \
  postgres:16-alpine

# Then start Falcon
docker run -d \
  --name falcon-trading \
  -p 80:80 \
  -p 443:443 \
  -p 5000:5000 \
  --link falcon-postgres:postgres \
  -v falcon-config:/etc/falcon \
  -v falcon-data:/var/lib/falcon \
  -e FALCON_ENV=production \
  -e DB_TYPE=postgresql \
  -e DB_HOST=postgres \
  -e DB_NAME=falcon \
  -e DB_USER=falcon \
  -e DB_PASSWORD=secure_password \
  falcon-trading:latest
```

## Using Pre-built Images from GitHub Container Registry

Pre-built images are automatically published to GitHub Container Registry (ghcr.io) on every commit to main and development branches.

**Pull and run the latest image:**
```bash
# Pull latest from main branch
docker pull ghcr.io/davdunc/falcon:latest

# Run the container
docker run -d \
  --name falcon-trading \
  -p 5000:5000 \
  -v falcon-config:/etc/falcon \
  -v falcon-data:/var/lib/falcon \
  ghcr.io/davdunc/falcon:latest
```

**Available tags:**
- `latest` - Latest build from main branch
- `main` - Latest build from main branch
- `development` - Latest build from development branch
- `main-<sha>` - Specific commit from main branch
- `development-<sha>` - Specific commit from development branch

## Configuration

### Environment Variables

Set these as Docker environment variables (-e flag) or in docker-compose.yml:

**Required:**
- `MASSIVE_API_KEY` - Polygon.io API key for market data
- `CLAUDE_API_KEY` - Claude API key for AI features

**Optional:**
- `OPENAI_API_KEY` - OpenAI API key
- `PERPLEXITY_API_KEY` - Perplexity API key
- `FINVIZ_SCREENER_URL` - Custom Finviz screener URL

**Database (SQLite - default):**
- `DB_TYPE=sqlite`
- `DB_PATH=/var/lib/falcon/paper_trading.db`

**Database (PostgreSQL):**
- `DB_TYPE=postgresql`
- `DB_HOST=postgres`
- `DB_PORT=5432`
- `DB_NAME=falcon`
- `DB_USER=falcon`
- `DB_PASSWORD=secure_password`

### Volume Mounts

Persist data by mounting these volumes:

- `/etc/falcon` - Configuration and secrets
- `/var/lib/falcon` - Database and runtime data
- `/var/cache/falcon` - Cache data
- `/var/log/falcon` - Application logs

### Secrets Management

**Option 1: Environment Variables (docker-compose.yml)**
```yaml
services:
  falcon:
    environment:
      - MASSIVE_API_KEY=your_key_here
      - CLAUDE_API_KEY=your_key_here
```

**Option 2: Secrets File (Mounted Volume)**
```bash
# Create secrets file locally
mkdir -p ./config
cat > ./config/secrets.env << EOF
MASSIVE_API_KEY=your_key_here
CLAUDE_API_KEY=your_key_here
EOF

# Mount it in container
docker run -d \
  -v ./config:/etc/falcon \
  falcon-trading:latest
```

**Option 3: Docker Secrets (Swarm Mode)**
```bash
# Create secrets
echo "your_api_key" | docker secret create massive_api_key -
echo "your_claude_key" | docker secret create claude_api_key -

# Use in stack deploy
docker stack deploy -c docker-stack.yml falcon
```

## Health Checks

The container includes a built-in health check:

```bash
# Check container health
docker ps

# Manually test health endpoint
curl http://localhost:5000/health
```

Health check configuration:
- **Interval:** 30 seconds
- **Timeout:** 10 seconds
- **Start Period:** 40 seconds
- **Retries:** 3

## Monitoring and Logs

**View logs:**
```bash
# Docker CLI
docker logs falcon-trading -f

# Docker Compose
docker-compose logs falcon -f

# Application logs inside container
docker exec falcon-trading tail -f /var/log/falcon/app.log
```

**Check service status:**
```bash
# Enter container
docker exec -it falcon-trading /bin/bash

# Check processes
ps aux | grep python

# Check nginx
nginx -t
```

## Networking

### Exposed Ports

- **5000** - Flask application (direct access)
- **80** - HTTP (redirects to HTTPS)
- **443** - HTTPS (nginx reverse proxy)

### Docker Compose Networking

Services communicate via the `falcon-network` bridge network:
- Falcon container can reach PostgreSQL at `postgres:5432`
- External access via published ports

## Database Management

### SQLite (Default)

Data is stored in `/var/lib/falcon/paper_trading.db` inside the container.

**Backup database:**
```bash
docker cp falcon-trading:/var/lib/falcon/paper_trading.db ./backup.db
```

**Restore database:**
```bash
docker cp ./backup.db falcon-trading:/var/lib/falcon/paper_trading.db
docker restart falcon-trading
```

### PostgreSQL

**Access PostgreSQL:**
```bash
docker exec -it falcon-postgres psql -U falcon -d falcon
```

**Backup database:**
```bash
docker exec falcon-postgres pg_dump -U falcon falcon > backup.sql
```

**Restore database:**
```bash
cat backup.sql | docker exec -i falcon-postgres psql -U falcon -d falcon
```

## Upgrading

**Pull latest image:**
```bash
# Stop current container
docker-compose down

# Pull latest image
docker-compose pull

# Start with new image
docker-compose up -d

# Or for manual pull
docker pull ghcr.io/davdunc/falcon:latest
```

**Upgrade with data preservation:**
```bash
# Backup data
docker cp falcon-trading:/var/lib/falcon ./falcon-backup

# Remove old container (volumes are preserved)
docker-compose down

# Pull new image
docker-compose pull

# Start new container (uses existing volumes)
docker-compose up -d
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs falcon-trading

# Common issues:
# - Missing API keys in /etc/falcon/secrets.env
# - Database connection issues
# - Port conflicts (5000, 80, 443)

# Check if ports are available
netstat -tlnp | grep -E ':(80|443|5000)'
```

### Health Check Failing

```bash
# Check health endpoint manually
curl -v http://localhost:5000/health

# Check Flask application status
docker exec falcon-trading ps aux | grep python

# Check application logs
docker logs falcon-trading -f
```

### Database Connection Issues

**SQLite:**
```bash
# Check database file exists
docker exec falcon-trading ls -l /var/lib/falcon/paper_trading.db

# Check permissions
docker exec falcon-trading ls -l /var/lib/falcon/
```

**PostgreSQL:**
```bash
# Test connection from Falcon container
docker exec falcon-trading \
  /opt/falcon/venv/bin/python3 -c "
import psycopg2
conn = psycopg2.connect(
    host='postgres',
    database='falcon',
    user='falcon',
    password='secure_password'
)
print('Connection successful!')
"

# Check PostgreSQL logs
docker logs falcon-postgres
```

### Permission Issues

```bash
# Fix ownership inside container
docker exec -u root falcon-trading \
  chown -R falcon:falcon /var/lib/falcon /var/cache/falcon /var/log/falcon
```

## Development Workflow

**Build and test locally:**
```bash
# Build image
docker build -t falcon-trading:dev .

# Run tests
docker run --rm falcon-trading:dev \
  /opt/falcon/venv/bin/python3 -m pytest

# Run with live code (mount source)
docker run -d \
  --name falcon-dev \
  -p 5000:5000 \
  -v $(pwd):/opt/falcon \
  falcon-trading:dev
```

## GitHub Actions CI/CD

The repository includes automated Docker builds via GitHub Actions:

**Workflow:** `.github/workflows/docker.yml`

**Triggers:**
- Push to `main` or `development`
- Pull requests to `main`
- Manual workflow dispatch

**Tests performed:**
- Container structure validation
- Make install verification
- Python module imports
- Database initialization
- Configuration validation
- Health endpoint check
- Docker Compose integration test

**Artifacts:**
- Images pushed to `ghcr.io/davdunc/falcon`
- Tagged with branch name, commit SHA, and `latest`

## Production Deployment

### Using Docker Swarm

```yaml
# docker-stack.yml
version: '3.8'

services:
  falcon:
    image: ghcr.io/davdunc/falcon:latest
    deploy:
      replicas: 3
      restart_policy:
        condition: on-failure
    secrets:
      - massive_api_key
      - claude_api_key
    environment:
      - FALCON_ENV=production
    volumes:
      - falcon-data:/var/lib/falcon
    networks:
      - falcon-network

secrets:
  massive_api_key:
    external: true
  claude_api_key:
    external: true
```

Deploy:
```bash
docker stack deploy -c docker-stack.yml falcon
```

### Using Kubernetes

See [KUBERNETES.md](KUBERNETES.md) for Kubernetes deployment guide (coming soon).

## Security Considerations

1. **Secrets:** Never commit API keys to git. Use environment variables, Docker secrets, or mounted volumes.

2. **SSL/TLS:** The container includes self-signed certificates. For production, mount proper certificates:
   ```bash
   docker run -d \
     -v ./certs:/etc/nginx/ssl \
     falcon-trading:latest
   ```

3. **Network Security:** Use Docker networks to isolate containers:
   ```yaml
   networks:
     falcon-network:
       driver: bridge
       internal: true  # No external access
   ```

4. **User Privileges:** Container runs as `falcon` user (non-root) for security.

5. **Read-only Filesystem:** Consider running with read-only filesystem:
   ```bash
   docker run --read-only \
     --tmpfs /tmp \
     -v falcon-data:/var/lib/falcon:rw \
     falcon-trading:latest
   ```

## Support

- **Documentation:** See [INSTALL.md](INSTALL.md) and [README.md](README.md)
- **GitHub Issues:** https://github.com/davdunc/falcon/issues
- **Container Registry:** https://github.com/davdunc/falcon/pkgs/container/falcon

---

**Happy Trading!**
