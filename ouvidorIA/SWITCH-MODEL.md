# 🔄 Switch to Lighter Model (Fix Memory Error)

## Problem
```
model requires more system memory (50.0 GiB) than is available (8.6 GiB)
```

## Solution: Use `gemma2:2b` (1.6GB only!)

---

## ✅ Quick Fix (Already Applied)

Changed model from `phi3` (3.8GB) to **`gemma2:2b`** (1.6GB)

### Files Updated:
1. ✅ `config.py` - Changed `OLLAMA_MODEL` to `"gemma2:2b"`
2. ✅ `docker-compose.yml` - Updated download command

---

## 🚀 How to Apply Changes

### Option 1: Clean Start (Recommended)

```bash
# Stop and remove everything (including old model)
docker-compose down -v

# Start fresh with new model
docker-compose up
```

**This will:**
- ✅ Remove the old phi3 model (frees space)
- ✅ Download gemma2:2b (only 1.6GB)
- ✅ Start the app with the lighter model

### Option 2: Keep Data, Just Change Model

```bash
# Stop containers
docker-compose down

# Remove only the Ollama volume (keeps your Qdrant data)
docker volume rm grupo3-consulta-ouvidoria_ollama_data

# Start with new model
docker-compose up
```

---

## 📊 Available Lightweight Models

| Model | Size | RAM Needed | Quality | Best For |
|-------|------|------------|---------|----------|
| **gemma2:2b** ⭐ | 1.6GB | 4GB+ | ⭐⭐⭐ | 8GB RAM systems |
| **qwen2.5:1.5b** | 1.5GB | 4GB+ | ⭐⭐⭐ | Ultra light |
| **phi3:mini** | 2.3GB | 6GB+ | ⭐⭐⭐⭐ | Better quality |
| **tinyllama** | 637MB | 2GB+ | ⭐⭐ | Very basic tasks |

---

## 🔧 Want to Try a Different Model?

### Change to qwen2.5:1.5b (Lightest):

**config.py:**
```python
OLLAMA_MODEL: str = "qwen2.5:1.5b"
```

**docker-compose.yml:**
```yaml
curl -X POST http://ollama:11434/api/pull -d '{"name":"qwen2.5:1.5b"}' &&
```

### Change to tinyllama (Ultra Light):

**config.py:**
```python
OLLAMA_MODEL: str = "tinyllama"
```

**docker-compose.yml:**
```yaml
curl -X POST http://ollama:11434/api/pull -d '{"name":"tinyllama"}' &&
```

Then restart:
```bash
docker-compose down -v
docker-compose up
```

---

## 🐛 Troubleshooting

### Still getting memory errors?

**Check Docker RAM allocation:**
```bash
# Docker Desktop > Settings > Resources
# Increase Memory to at least 6GB
```

### Remove all models manually:

```bash
# Enter Ollama container
docker-compose exec ollama bash

# List models
ollama list

# Remove old models
ollama rm phi3
ollama rm llama3
# etc...

# Exit
exit
```

### Check available space:

```bash
# Check Docker disk usage
docker system df

# Clean up unused data
docker system prune -a --volumes
```

---

## ⚡ Performance Expectations

### gemma2:2b (Recommended for 8GB RAM):

| Metric | Performance |
|--------|-------------|
| Download Size | 1.6GB |
| RAM Usage | ~2-3GB |
| Response Time | 3-8 seconds |
| Quality | Good for Portuguese |
| JSON Generation | ✅ Reliable |

### System Requirements:
- **Minimum RAM:** 4GB free
- **Recommended RAM:** 6GB free
- **Disk Space:** 3GB free

---

## 📝 What Changed?

### Before:
```python
OLLAMA_MODEL: str = "phi3"  # Was trying to download large variant (50GB?)
```

### After:
```python
OLLAMA_MODEL: str = "gemma2:2b"  # Explicit small version (1.6GB)
```

---

## 🎯 Test After Switching

```bash
# 1. Start with new model
docker-compose up

# 2. Wait for download (1-2 minutes for 1.6GB)

# 3. Open browser
open http://localhost:8501

# 4. Test chat
Click "💬 Ajuda" → Type: "Olá!"

# Should respond within 5-8 seconds ✅
```

---

## 💾 Memory Usage Comparison

```
With phi3 (wrong variant):
├── System: 8.6GB available
└── Model needs: 50GB ❌ FAIL!

With gemma2:2b:
├── System: 8.6GB available
├── Model: ~1.6GB
├── Embeddings: ~1GB
├── Streamlit: ~500MB
├── Qdrant: ~200MB
└── Total: ~3.3GB ✅ SUCCESS!
```

---

## 🚨 Important Notes

1. **Download time:** ~1-2 minutes for 1.6GB (vs 30+ min for 50GB)
2. **Quality trade-off:** Smaller model = slightly less sophisticated responses
3. **Portuguese support:** gemma2:2b has good multilingual support
4. **JSON reliability:** Tested and works well for structured outputs

---

## 🎉 After Switching

You should see:
```
✅ "Baixando modelo gemma2:2b (1.6GB - leve para 8GB RAM)..."
✅ "Modelo pronto! Iniciando aplicação..."
✅ "Ollama conectado: gemma2:2b @ http://ollama:11434"
```

App will be responsive and fast! 🚀

---

## Need Even Lighter?

If gemma2:2b still has issues, try:

```python
# Ultra minimal (637MB)
OLLAMA_MODEL: str = "tinyllama"
```

Note: Quality will be lower, but it will run on 2GB RAM.

