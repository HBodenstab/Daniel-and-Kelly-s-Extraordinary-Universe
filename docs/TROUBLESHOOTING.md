# Troubleshooting Guide

Comprehensive guide to diagnosing and resolving common issues in the Extraordinary Universe Search system.

---

## Table of Contents

- [Installation Issues](#installation-issues)
- [Data Ingestion Issues](#data-ingestion-issues)
- [Search Issues](#search-issues)
- [API Issues](#api-issues)
- [Performance Issues](#performance-issues)
- [Database Issues](#database-issues)
- [Deployment Issues](#deployment-issues)
- [Diagnostic Commands](#diagnostic-commands)
- [Getting Help](#getting-help)

---

## Installation Issues

### Issue: `pip install` fails with dependency conflicts

**Symptoms**:
```
ERROR: Could not find a version that satisfies the requirement numpy>=1.26.0,<2.0.0
```

**Diagnosis**:
```bash
python --version  # Check Python version
pip --version     # Check pip version
```

**Solutions**:

1. **Upgrade pip**:
   ```bash
   pip install --upgrade pip
   ```

2. **Use specific Python version**:
   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Install dependencies individually**:
   ```bash
   pip install numpy==1.26.0
   pip install -r requirements.txt
   ```

**Prevention**: Always use Python 3.11+ and latest pip.

---

### Issue: `ModuleNotFoundError: No module named 'app'`

**Symptoms**:
```
python -m app.cli update
ModuleNotFoundError: No module named 'app'
```

**Diagnosis**:
```bash
pwd  # Check current directory
ls   # Check for app/ directory
```

**Solutions**:

1. **Ensure in project root**:
   ```bash
   cd path/to/Daniel-and-Kelly-s-Extraordinary-Universe
   python -m app.cli update
   ```

2. **Verify virtual environment**:
   ```bash
   which python  # Should show .venv/bin/python
   pip list      # Should show installed packages
   ```

3. **Reinstall in development mode**:
   ```bash
   pip install -e .
   ```

---

### Issue: `sentence-transformers` download fails

**Symptoms**:
```
ConnectionError: Could not download model sentence-transformers/all-MiniLM-L6-v2
```

**Diagnosis**:
```bash
curl -I https://huggingface.co/  # Check connectivity
```

**Solutions**:

1. **Check internet connection**

2. **Use proxy if needed**:
   ```bash
   export HTTP_PROXY=http://proxy:8080
   export HTTPS_PROXY=http://proxy:8080
   ```

3. **Download model manually**:
   ```python
   from sentence_transformers import SentenceTransformer
   model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
   model.save('models/all-MiniLM-L6-v2')
   ```

4. **Use local model**:
   ```bash
   export MODEL_NAME=models/all-MiniLM-L6-v2
   ```

---

## Data Ingestion Issues

### Issue: `No episodes found` during update

**Symptoms**:
```
INFO - Found 0 episodes
ERROR - No episodes found
```

**Diagnosis**:
```bash
# Check RSS feed accessibility
curl -I $RSS_URL

# Test RSS parsing
python -c "
from app.fetch import fetch_episode_data
episodes = fetch_episode_data()
print(f'Found {len(episodes)} episodes')
"
```

**Solutions**:

1. **Verify RSS URL**:
   ```bash
   echo $RSS_URL
   # Should be: https://omny.fm/shows/daniel-and-kellys-extraordinary-universe/playlists/podcast.rss
   ```

2. **Check network connectivity**:
   ```bash
   ping omny.fm
   ```

3. **Inspect RSS response**:
   ```bash
   curl -s $RSS_URL | head -50
   # Should show XML with <rss> tag
   ```

4. **Check for rate limiting**:
   - Wait 5 minutes and retry
   - Increase `SCRAPE_DELAY` in config

**Root Causes**:
- Network issues
- RSS feed URL changed
- Rate limiting
- Firewall blocking requests

---

### Issue: Transcript extraction fails for all episodes

**Symptoms**:
```
WARNING - Could not extract transcript for episode: <title>
WARNING - Could not extract transcript for episode: <title>
...
```

**Diagnosis**:
```bash
# Test single episode parsing
python -c "
from app.fetch import fetch_episode_page
from app.parse import extract_transcript

html = fetch_episode_page('https://omny.fm/shows/daniel-and-kellys-extraordinary-universe/...')
transcript = extract_transcript(html)
print(f'Transcript length: {len(transcript)}')
print(transcript[:200])
"
```

**Solutions**:

1. **Update parser** if HTML structure changed:
   - Inspect episode page HTML
   - Update selectors in `app/parse.py`

2. **Fallback gracefully**:
   - System uses title + description if transcript missing
   - This is expected behavior for some episodes

3. **Check user agent**:
   ```bash
   export USER_AGENT="Podcast Search Bot 1.0"
   ```

**Note**: Some episodes legitimately don't have transcripts. System handles this gracefully.

---

### Issue: Out of memory during embedding generation

**Symptoms**:
```
MemoryError: Unable to allocate array
Killed
```

**Diagnosis**:
```bash
# Check available memory
free -h  # Linux
vm_stat  # macOS

# Check embedding batch size
python -c "from app.config import CHUNK_SIZE; print(CHUNK_SIZE)"
```

**Solutions**:

1. **Reduce chunk size**:
   ```bash
   export CHUNK_SIZE=800  # Down from 1200
   ```

2. **Process in batches** (modify `app/embed.py`):
   ```python
   def embed_chunks(chunks, batch_size=100):
       embeddings = []
       for i in range(0, len(chunks), batch_size):
           batch = chunks[i:i+batch_size]
           emb = model.encode([c.text for c in batch])
           embeddings.append(emb)
       return np.vstack(embeddings)
   ```

3. **Increase system swap**:
   ```bash
   # Linux
   sudo dd if=/dev/zero of=/swapfile bs=1G count=4
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

4. **Use smaller model**:
   ```bash
   export MODEL_NAME=sentence-transformers/paraphrase-MiniLM-L3-v2  # Lighter model
   ```

---

### Issue: Update process takes too long (>1 hour)

**Symptoms**:
- Update runs for hours without completing

**Diagnosis**:
```bash
# Check progress
python -m app.cli stats

# Monitor process
htop  # or top
```

**Solutions**:

1. **Check for network delays**:
   - Reduce `SCRAPE_DELAY` in config (careful with rate limiting)
   - Use faster network connection

2. **Profile bottleneck**:
   ```python
   import cProfile
   cProfile.run('fetch_episode_data()', sort='cumtime')
   ```

3. **Use incremental updates** (future feature):
   - Only fetch new episodes
   - Check guid before processing

**Expected Times** (150 episodes):
- RSS fetch: 2-3 minutes
- HTML parsing: 5-10 minutes
- Chunking: <1 minute
- Embedding: 8-15 minutes
- Indexing: <1 minute
- **Total: 15-30 minutes**

---

## Search Issues

### Issue: Search returns no results

**Symptoms**:
```bash
python -m app.cli search "quantum mechanics"
INFO - Found 0 results
```

**Diagnosis**:
```bash
# Check index status
python -m app.cli stats

# Expected output:
# Episodes in database: 145
# Chunks in database: 2431
# Search index vectors: 2431
```

**Solutions**:

1. **Verify index is built**:
   ```bash
   ls -lh data/index.faiss data/embeddings.npz
   # Both files should exist and be >1MB
   ```

2. **Rebuild index**:
   ```bash
   python -m app.cli clear
   python -m app.cli update
   ```

3. **Try lexical-only search**:
   ```bash
   python -m app.cli search "quantum mechanics" --lexical-only
   ```
   - If this works, issue is with semantic index
   - If this doesn't work, issue is with database

4. **Check database**:
   ```bash
   sqlite3 data/episodes.sqlite "SELECT COUNT(*) FROM episodes;"
   # Should be >0
   ```

**Root Causes**:
- Index not built
- Index file corrupted
- Database empty
- Embeddings dimension mismatch

---

### Issue: Search results are not relevant

**Symptoms**:
- Query: "quantum mechanics"
- Results: Episodes about cooking, unrelated topics

**Diagnosis**:
```bash
# Check result scores
python -m app.cli search "quantum mechanics" --top-k 10
# Look at score, semantic_score, lexical_score for each result
```

**Solutions**:

1. **Adjust hybrid alpha**:
   ```bash
   # Favor semantic (understanding)
   export HYBRID_ALPHA=0.9
   
   # Favor lexical (keywords)
   export HYBRID_ALPHA=0.3
   ```

2. **Use more specific queries**:
   - ❌ "quantum" (too broad)
   - ✅ "quantum entanglement and bell's inequality"

3. **Try semantic-only search**:
   ```bash
   export HYBRID_ALPHA=1.0  # Pure semantic
   ```

4. **Check embedding quality**:
   ```python
   from app.embed import embed_query
   emb1 = embed_query("quantum mechanics")
   emb2 = embed_query("classical physics")
   similarity = np.dot(emb1, emb2)
   print(f"Similarity: {similarity:.3f}")  # Should be 0.6-0.8 (related but distinct)
   ```

**Expected Score Ranges**:
- **0.9-1.0**: Highly relevant (exact topic match)
- **0.7-0.9**: Very relevant (related topic)
- **0.5-0.7**: Moderately relevant (tangential)
- **<0.5**: Weakly relevant (should filter out)

---

### Issue: Duplicate episodes in search results

**Symptoms**:
- Same episode appears multiple times in results

**Diagnosis**:
```python
from app.rank import rank_results
# Check if deduplication is working
```

**Solutions**:

1. **Verify deduplication** in `app/rank.py`:
   ```python
   # Should group by episode_id and keep max score
   episode_scores = {}
   for result in results:
       if result.episode_id not in episode_scores:
           episode_scores[result.episode_id] = result
       else:
           if result.score > episode_scores[result.episode_id].score:
               episode_scores[result.episode_id] = result
   ```

2. **Check for duplicate chunks**:
   ```bash
   sqlite3 data/episodes.sqlite "
   SELECT episode_id, COUNT(*) as chunk_count 
   FROM chunks 
   GROUP BY episode_id 
   HAVING chunk_count > 50;
   "
   ```

**Root Cause**: Deduplication logic not running or episode_id mismatch.

---

### Issue: Search is slow (>5 seconds)

**Symptoms**:
- Queries take 5+ seconds to return

**Diagnosis**:
```python
import time

# Profile search stages
start = time.time()
query_emb = embed_query("test")
print(f"Embedding: {time.time() - start:.3f}s")

start = time.time()
results = semantic_search(query_emb, 10)
print(f"FAISS: {time.time() - start:.3f}s")

start = time.time()
ranked = rank_results("test", results, 10)
print(f"Ranking: {time.time() - start:.3f}s")
```

**Solutions**:

1. **Use approximate FAISS index** (for large datasets):
   ```python
   # In app/index.py
   quantizer = faiss.IndexFlatIP(dimension)
   index = faiss.IndexIVFFlat(quantizer, dimension, nlist=100)
   ```

2. **Reduce top_k**:
   ```bash
   python -m app.cli search "query" --top-k 5  # Instead of 50
   ```

3. **Cache embeddings**:
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=1000)
   def embed_query(query: str):
       return model.encode([query])[0]
   ```

4. **Profile and optimize bottleneck**:
   ```bash
   python -m cProfile -s cumtime -m app.cli search "query"
   ```

**Expected Latency**:
- Query embedding: 10-20ms
- FAISS search: 5-10ms
- Ranking: 30-50ms
- Database fetch: 20-40ms
- **Total: 65-120ms**

---

## API Issues

### Issue: API returns 500 Internal Server Error

**Symptoms**:
```
POST /api/search
500 Internal Server Error
```

**Diagnosis**:
```bash
# Check server logs
uvicorn app.api:app --reload --log-level debug

# Test health endpoint
curl http://localhost:8000/health
```

**Solutions**:

1. **Check logs** for exception traceback

2. **Verify index is loaded**:
   ```bash
   curl http://localhost:8000/api/stats
   # Check "index_loaded": true
   ```

3. **Restart server**:
   ```bash
   # Kill existing process
   pkill -f uvicorn
   
   # Start fresh
   uvicorn app.api:app --reload
   ```

4. **Test search manually**:
   ```python
   from app.embed import embed_query
   from app.index import semantic_search, is_index_loaded
   
   print(f"Index loaded: {is_index_loaded()}")
   emb = embed_query("test")
   results = semantic_search(emb, 5)
   print(f"Results: {len(results)}")
   ```

---

### Issue: CORS errors in web interface

**Symptoms**:
```
Access to fetch at 'http://localhost:8000/api/search' from origin 'null' 
has been blocked by CORS policy
```

**Diagnosis**:
- Opening `index.html` directly (file:// protocol)

**Solutions**:

1. **Use proper server**:
   ```bash
   # Don't open file:///path/to/index.html
   # Instead, use the API server
   uvicorn app.api:app --reload
   # Navigate to http://localhost:8000
   ```

2. **Add CORS middleware** (if serving from different domain):
   ```python
   from fastapi.middleware.cors import CORSMiddleware
   
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:3000"],
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

---

### Issue: API is not accessible from other machines

**Symptoms**:
- `curl http://localhost:8000` works on server
- `curl http://192.168.1.100:8000` fails from other machines

**Diagnosis**:
```bash
# Check if listening on all interfaces
netstat -an | grep 8000
# Should show 0.0.0.0:8000, not 127.0.0.1:8000
```

**Solutions**:

1. **Bind to 0.0.0.0**:
   ```bash
   uvicorn app.api:app --host 0.0.0.0 --port 8000
   ```

2. **Check firewall**:
   ```bash
   # macOS
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /path/to/python
   
   # Linux
   sudo ufw allow 8000
   ```

---

## Performance Issues

### Issue: High memory usage (>8GB)

**Diagnosis**:
```bash
# Check memory usage
ps aux | grep python
top -p $(pgrep -f "python.*app")
```

**Solutions**:

1. **Check for memory leaks**:
   ```python
   import tracemalloc
   tracemalloc.start()
   # Run operations
   snapshot = tracemalloc.take_snapshot()
   top_stats = snapshot.statistics('lineno')
   for stat in top_stats[:10]:
       print(stat)
   ```

2. **Unload model after indexing**:
   ```python
   # After building index
   del model
   import gc
   gc.collect()
   ```

3. **Use memory-mapped FAISS index**:
   ```python
   index = faiss.read_index("data/index.faiss", faiss.IO_FLAG_MMAP)
   ```

---

### Issue: CPU usage consistently at 100%

**Diagnosis**:
```bash
top
# Check which process is using CPU
```

**Solutions**:

1. **Check for infinite loops** in logs

2. **Limit concurrent requests**:
   ```bash
   gunicorn app.api:app --workers 2 --worker-class uvicorn.workers.UvicornWorker
   ```

3. **Profile CPU usage**:
   ```bash
   python -m cProfile -o profile.stats -m app.cli search "query"
   python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumtime'); p.print_stats(20)"
   ```

---

## Database Issues

### Issue: `database is locked` error

**Symptoms**:
```
sqlite3.OperationalError: database is locked
```

**Diagnosis**:
```bash
# Check for other processes using database
lsof data/episodes.sqlite
```

**Solutions**:

1. **Close other connections**:
   ```bash
   pkill -f "sqlite3.*episodes.sqlite"
   ```

2. **Increase timeout**:
   ```python
   # In app/database.py
   connect_args = {"timeout": 60}  # Increase from 30
   ```

3. **Use WAL mode**:
   ```python
   import sqlite3
   conn = sqlite3.connect("data/episodes.sqlite")
   conn.execute("PRAGMA journal_mode=WAL")
   conn.close()
   ```

4. **Migrate to PostgreSQL** for production

---

### Issue: Database corruption

**Symptoms**:
```
sqlite3.DatabaseError: database disk image is malformed
```

**Diagnosis**:
```bash
sqlite3 data/episodes.sqlite "PRAGMA integrity_check;"
```

**Solutions**:

1. **Attempt recovery**:
   ```bash
   sqlite3 data/episodes.sqlite ".recover" | sqlite3 data/episodes_recovered.sqlite
   ```

2. **Restore from backup** (if available)

3. **Rebuild from scratch**:
   ```bash
   rm data/episodes.sqlite
   python -m app.cli update
   ```

**Prevention**:
- Regular backups
- Use PostgreSQL for production
- Avoid killing processes during writes

---

## Deployment Issues

### Issue: Railway deployment fails

**Symptoms**:
```
Build failed: No Python version specified
```

**Diagnosis**:
- Check Railway logs in dashboard

**Solutions**:

1. **Specify Python version** in `runtime.txt`:
   ```
   python-3.11.5
   ```

2. **Check Procfile**:
   ```
   web: gunicorn app.api:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
   ```

3. **Verify environment variables** in Railway dashboard

4. **Check build logs** for specific errors

---

### Issue: Railway app crashes after deployment

**Symptoms**:
- App deploys successfully but crashes immediately

**Diagnosis**:
```bash
railway logs
```

**Solutions**:

1. **Check for missing files**:
   - FAISS index (regenerate on startup if missing)
   - Model files (download on startup)

2. **Environment variables**:
   ```bash
   railway variables
   # Verify DATABASE_URL is set
   ```

3. **Memory limits**:
   - Railway may have memory limits
   - Reduce model size or optimize

4. **Check PostgreSQL connection**:
   ```bash
   railway run python -c "from app.database import db; print(db.get_episode_count())"
   ```

---

## Diagnostic Commands

### System Health Check

```bash
#!/bin/bash
echo "=== System Health Check ==="

echo "1. Python version:"
python --version

echo "2. Virtual environment:"
which python

echo "3. Database:"
sqlite3 data/episodes.sqlite "SELECT COUNT(*) as episodes FROM episodes; SELECT COUNT(*) as chunks FROM chunks;"

echo "4. Index files:"
ls -lh data/index.faiss data/embeddings.npz

echo "5. Stats:"
python -m app.cli stats

echo "6. Search test:"
python -m app.cli search "test query" --top-k 1

echo "7. API health:"
curl -s http://localhost:8000/health | jq .

echo "=== Health Check Complete ==="
```

### Performance Benchmark

```python
import time
from app.embed import embed_query
from app.index import semantic_search
from app.rank import rank_results

# Test 10 queries
queries = ["quantum mechanics", "general relativity", "dark matter", 
           "consciousness", "time travel", "black holes",
           "string theory", "evolution", "climate change", "ai ethics"]

times = []
for query in queries:
    start = time.time()
    emb = embed_query(query)
    results = semantic_search(emb, 10)
    ranked = rank_results(query, results, 10)
    elapsed = time.time() - start
    times.append(elapsed)
    print(f"{query}: {elapsed:.3f}s")

print(f"\nAverage: {sum(times)/len(times):.3f}s")
print(f"Min: {min(times):.3f}s")
print(f"Max: {max(times):.3f}s")
```

---

## Getting Help

### Before Asking for Help

1. **Check this guide** for your specific issue
2. **Search existing issues** on GitHub
3. **Enable debug logging**:
   ```bash
   export LOG_LEVEL=DEBUG
   ```
4. **Collect diagnostics**:
   ```bash
   python -m app.cli stats
   ls -lh data/
   python --version
   pip list
   ```

### Reporting Issues

**Include**:
- Operating system and version
- Python version
- Full error message and traceback
- Steps to reproduce
- What you've tried
- Diagnostic output

**Template**:
```markdown
## Environment
- OS: macOS 14.5
- Python: 3.11.5
- Database: SQLite

## Issue
When running `python -m app.cli update`, I get...

## Error Message
```
[paste full error]
```

## Steps to Reproduce
1. Fresh install
2. Run update command
3. Error occurs at embedding step

## What I've Tried
- Reinstalled dependencies
- Cleared database
- Checked internet connection

## Diagnostics
```
[paste output of stats, logs, etc.]
```
```

### Community Support

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and community help
- **Documentation**: Check docs/ for detailed guides

### Professional Support

For production deployments and custom implementations, consider consulting with specialists from [BeagleMind.com](https://BeagleMind.com).

---

*Troubleshooting methodology refined through real-world deployments by [BeagleMind.com](https://BeagleMind.com).*


