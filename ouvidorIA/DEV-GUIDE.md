# 🔥 Hot Reload Development Guide

## What is Hot Reload?

Hot reload automatically restarts your Streamlit app when you save changes to your Python files. No need to rebuild Docker containers or manually refresh!

---

## ✅ Hot Reload is Now Configured

### What Changed:

1. **docker-compose.yml**
   - Added `--server.runOnSave=true` - Auto-rerun on file changes
   - Added `--server.fileWatcherType=poll` - Better for Docker
   - Volume mount already configured: `./:/app`

2. **`.streamlit/config.toml`**
   - Created configuration file with hot reload settings
   - Set logging level to "info"
   - Disabled usage stats for faster startup

---

## 🚀 How to Use

### 1. Start the Application

```bash
cd /Users/paulo.goncalves/Documents/unb/grupo3-consulta-ouvidoria/ouvidorIA
docker-compose up
```

### 2. Make Code Changes

Edit any Python file:
- `src/rag/service.py`
- `src/ui/interface.py`
- `main.py`
- `config.py`
- etc.

### 3. Save the File

Press `Cmd+S` (Mac) or `Ctrl+S` (Windows/Linux)

### 4. Watch the Magic! ✨

The browser will automatically show:
```
🔄 Rerunning...
```

Your changes are live in ~2-5 seconds!

---

## 📝 What Files Trigger Reload?

Hot reload watches these file types:
- ✅ `.py` files (Python)
- ✅ `.toml` files (Config)
- ❌ `.txt` files (Requirements - needs rebuild)
- ❌ Dockerfile (needs rebuild)
- ❌ docker-compose.yml (needs restart)

---

## 🔄 When You Need to Rebuild

### Files that require `docker-compose up --build`:

1. **requirements.txt** - New Python packages
   ```bash
   docker-compose up --build
   ```

2. **Dockerfile** - Container configuration changes
   ```bash
   docker-compose up --build
   ```

### Files that require `docker-compose restart`:

1. **docker-compose.yml** - Service configuration
   ```bash
   docker-compose restart streamlit
   ```

2. **Environment variables** - .env file changes
   ```bash
   docker-compose restart streamlit
   ```

---

## 💡 Development Workflow

### Typical Session:

```bash
# 1. Start containers (once)
docker-compose up

# 2. Edit code in your IDE
# Changes auto-reload! ✨

# 3. Add new package? Rebuild:
docker-compose up --build

# 4. Done? Stop containers:
Ctrl+C
docker-compose down
```

---

## 🎯 Example: Making Changes

### Example 1: Change a prompt

**File:** `src/rag/service.py`

```python
# Edit line 98
"Você é o OuvidorIA, assistente oficial do Fala.BR.\n"
# Change to:
"Você é o OuvidorIA, seu assistente pessoal do Fala.BR.\n"
```

**Save** → Browser auto-reloads in ~3 seconds! ✅

### Example 2: Change UI text

**File:** `src/ui/interface.py`

```python
# Edit line 19
"content": "Olá! Sou o assistente virtual do Fala.BR..."
# Change to:
"content": "Olá! Como posso ajudar você hoje?"
```

**Save** → Browser auto-reloads! ✅

### Example 3: Add new Python package ❌ (needs rebuild)

**File:** `requirements.txt`

```txt
# Add new line:
pandas
```

**Need to rebuild:**
```bash
docker-compose up --build
```

---

## 🐛 Troubleshooting

### Issue: Changes not showing up

**Solution 1:** Check if file is being watched
```bash
# Look at logs
docker-compose logs -f streamlit

# Should see:
# "Source file changed: /app/src/..."
```

**Solution 2:** Force refresh
- Press `Ctrl+Shift+R` (hard refresh in browser)
- Or click "Always rerun" in Streamlit UI

**Solution 3:** Restart container
```bash
docker-compose restart streamlit
```

### Issue: "File watcher not working"

**Check volume mount:**
```bash
docker-compose ps
# Should see: ./:/app in volumes
```

**Solution:**
```bash
docker-compose down
docker-compose up
```

### Issue: Too many reruns

**If app keeps rerunning:**
- Check for files being auto-saved by your IDE
- Temporarily disable auto-save
- Or add file to `.gitignore` if it's a temp file

---

## ⚙️ Configuration Options

### `.streamlit/config.toml`

```toml
[server]
runOnSave = true              # Enable hot reload
fileWatcherType = "poll"      # Use polling (better for Docker)

[client]
toolbarMode = "minimal"       # Cleaner UI

[logger]
level = "info"                # Set logging verbosity
```

### Custom Settings

Edit `.streamlit/config.toml` to customize:

```toml
# Disable hot reload (not recommended for dev)
runOnSave = false

# Change theme
[theme]
primaryColor = "#28a745"
backgroundColor = "#FFFFFF"
```

---

## 🎨 IDE Integration Tips

### VS Code
1. Install "Streamlit" extension
2. Auto-save: File → Auto Save ✅
3. Format on save: Settings → Format On Save ✅

### PyCharm
1. Auto-save: Settings → Appearance → System Settings → Autosave
2. File Watchers: Settings → Tools → File Watchers

### Cursor (Your IDE)
- Auto-save is likely already enabled
- Just edit and save - hot reload handles the rest!

---

## 📊 Performance

| Action | Time | Rebuild Needed? |
|--------|------|----------------|
| Edit .py file | ~3s | ❌ No |
| Edit config.py | ~3s | ❌ No |
| Edit .toml | ~3s | ❌ No |
| Add package | ~30s | ✅ Yes |
| Edit Dockerfile | ~60s | ✅ Yes |

---

## 🎯 Best Practices

1. **Keep containers running** during development
2. **Edit directly** in your IDE (changes sync to container)
3. **Watch the logs** to see reload events
4. **Rebuild only when needed** (new packages, Docker changes)
5. **Use git** to track your changes

---

## 📚 Additional Resources

- [Streamlit Configuration Docs](https://docs.streamlit.io/library/advanced-features/configuration)
- [Streamlit Caching](https://docs.streamlit.io/library/advanced-features/caching)
- [Docker Volumes](https://docs.docker.com/storage/volumes/)

---

## 🎉 You're All Set!

Just start coding and save - hot reload takes care of the rest!

```bash
# Start developing:
docker-compose up

# Code, save, watch magic happen! ✨
```

Happy coding! 🚀

