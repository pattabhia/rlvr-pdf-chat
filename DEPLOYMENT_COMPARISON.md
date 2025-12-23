# RunPod Deployment Options: Docker vs Native

## 📋 Quick Comparison

| Feature | Docker (All-in-One) | Native |
|---------|---------------------|--------|
| **Setup Time** | 5-10 min (build + start) | 2-3 min (script run) |
| **Complexity** | Low (single command) | Medium (multiple processes) |
| **Isolation** | ✅ Fully isolated | ❌ Shares host environment |
| **Resource Usage** | ~500MB overhead | Minimal overhead |
| **Debugging** | Need shell access | Direct log access |
| **Updates** | Rebuild image | Git pull + restart |
| **Portability** | ✅ Highly portable | ⚠️ Platform-specific |
| **Process Management** | Supervisor (automatic) | Manual (nohup) |
| **Persistence** | Docker volumes | Direct filesystem |
| **GPU Access** | ✅ Via Docker runtime | ✅ Direct access |

---

## 🐳 Docker Deployment

### ✅ Pros
- **Single command deployment** - `./runpod_docker_deploy.sh start`
- **Fully isolated** - No conflicts with host packages
- **Automatic process management** - Supervisor handles restarts
- **Portable** - Same image works anywhere
- **Clean shutdown** - All processes stopped together
- **Version control** - Tag and version images
- **Rollback capability** - Keep old images

### ❌ Cons
- **Build time** - Initial build takes 5-10 minutes
- **Image size** - ~5-8GB Docker image
- **Debugging** - Need to shell into container
- **Resource overhead** - Docker daemon + container overhead
- **Update process** - Rebuild image for code changes

### 🎯 Best For
- **Production deployments**
- **Multiple environments** (dev, staging, prod)
- **Team collaboration** (consistent environment)
- **Long-running instances**
- **When you want "set and forget"**

### 📋 Quick Start
```bash
cd /workspace/rlvr-pdf-chat
git pull

# Build once
./runpod_docker_deploy.sh build

# Start (fast after build)
./runpod_docker_deploy.sh start

# Check status
./runpod_docker_deploy.sh status

# View logs
./runpod_docker_deploy.sh logs
```

---

## 🔧 Native Deployment

### ✅ Pros
- **Fast startup** - Services start in 30-60 seconds
- **Direct access** - Logs in `/tmp/*.log`
- **Easy debugging** - Direct process inspection
- **Quick updates** - Git pull + restart service
- **No overhead** - Native performance
- **Flexible** - Restart individual services
- **Development-friendly** - Edit and test quickly

### ❌ Cons
- **Manual process management** - Need to track PIDs
- **No auto-restart** - Services don't restart on crash
- **Environment conflicts** - Shared Python packages
- **Multiple commands** - Start each service separately
- **Cleanup required** - Kill processes manually

### 🎯 Best For
- **Development and testing**
- **Quick iterations**
- **Debugging issues**
- **Learning the system**
- **Short-lived instances**
- **When you need direct access**

### 📋 Quick Start
```bash
cd /workspace/rlvr-pdf-chat
git pull

# Start everything
./runpod_launch_all.sh

# Check status
curl http://localhost:8501
ps aux | grep uvicorn

# View logs
tail -f /tmp/qa-orchestrator.log
```

---

## 🤔 Which Should You Choose?

### Choose **Docker** if:
- ✅ You want a production-ready deployment
- ✅ You're running for extended periods (days/weeks)
- ✅ You want automatic process management
- ✅ You need consistent environments
- ✅ You're comfortable with Docker
- ✅ You want easy rollback capability

### Choose **Native** if:
- ✅ You're actively developing/debugging
- ✅ You need fast iteration cycles
- ✅ You want direct log access
- ✅ You're running short experiments
- ✅ You need to restart individual services
- ✅ You want minimal resource usage

---

## 🔄 Hybrid Approach

You can use both! Here's a recommended workflow:

### Development Phase
```bash
# Use native for fast iteration
./runpod_launch_all.sh

# Make changes, test, debug
vim services/qa-orchestrator/src/qa_service.py
pkill -f "uvicorn.*8001"
cd services/qa-orchestrator
PYTHONPATH=... uvicorn src.main:app --port 8001

# Iterate quickly
```

### Production Phase
```bash
# Once stable, switch to Docker
git commit -am "Stable version"
./runpod_docker_deploy.sh build
./runpod_docker_deploy.sh start

# Let it run for days/weeks
```

---

## 📊 Resource Comparison

### Docker
```
Memory Usage:
- Docker daemon: ~200MB
- Container base: ~300MB
- Services: ~2-3GB (same as native)
- Total: ~2.5-3.5GB

Disk Usage:
- Docker image: ~5-8GB
- Volumes: ~1-2GB (data)
- Total: ~6-10GB
```

### Native
```
Memory Usage:
- Services only: ~2-3GB
- Total: ~2-3GB

Disk Usage:
- Code: ~100MB
- Data: ~1-2GB
- Total: ~1.2-2.1GB
```

---

## 🐛 Debugging Comparison

### Docker
```bash
# View logs
./runpod_docker_deploy.sh logs

# Shell into container
./runpod_docker_deploy.sh shell

# Inside container
supervisorctl status
tail -f /var/log/supervisor/qa-orchestrator.log

# Restart service
supervisorctl restart qa-orchestrator
```

### Native
```bash
# View logs directly
tail -f /tmp/qa-orchestrator.log

# Check processes
ps aux | grep uvicorn

# Restart service
pkill -f "uvicorn.*8001"
cd services/qa-orchestrator
PYTHONPATH=... uvicorn src.main:app --port 8001 &
```

---

## 🚀 Migration Between Deployments

### Native → Docker
```bash
# Stop native services
pkill -f uvicorn
pkill -f streamlit
pkill -f "python -m src.worker"
pkill -f qdrant

# Copy data (if needed)
cp -r /workspace/rlvr-pdf-chat/data ./data-backup

# Start Docker
./runpod_docker_deploy.sh start
```

### Docker → Native
```bash
# Stop Docker
./runpod_docker_deploy.sh stop

# Copy data from container (if needed)
docker cp rlvr-all-in-one:/app/data/dpo_data ./data/

# Start native
./runpod_launch_all.sh
```

---

## 💡 Recommendations

### For Your Use Case (DPO Dataset Generation)

**Start with Native:**
1. Fast setup to test the system
2. Ask questions, generate DPO data
3. Debug any issues quickly
4. Iterate on prompts/settings

**Switch to Docker when:**
1. You're happy with the configuration
2. You want to run overnight/multi-day
3. You need automatic restarts
4. You're ready for "production" data collection

### Command Summary

```bash
# Native deployment
./runpod_launch_all.sh

# Docker deployment
./runpod_docker_deploy.sh build  # Once
./runpod_docker_deploy.sh start  # Every time
```

---

## 📚 Documentation Links

- **Native Deployment:** See `RUNPOD_SETUP.md`
- **Docker Deployment:** See `DOCKER_DEPLOYMENT.md`
- **Troubleshooting:** Both guides have troubleshooting sections

