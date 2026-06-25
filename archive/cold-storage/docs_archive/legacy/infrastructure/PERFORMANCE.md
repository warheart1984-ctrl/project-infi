# Performance Testing & Optimization Guide

## Performance Benchmarks

### Target Metrics
- **Response Time**: < 500ms (p95)
- **Throughput**: > 100 requests/second
- **Error Rate**: < 0.1%
- **CPU Usage**: < 70%
- **Memory Usage**: < 80%
- **Cache Hit Rate**: > 80%

## Load Testing

### Setup

```bash
# Install locust
pip install locust

# Install Apache Bench
sudo apt-get install apache2-utils

# Install wrk
git clone https://github.com/wg/wrk.git
cd wrk
make
```

### Run Load Tests

#### Using Locust

```bash
# Start Locust
locust -f locustfile.py --host=http://localhost:5000

# Access web UI at http://localhost:8089
```

#### Using Apache Bench

```bash
# 1000 requests, 10 concurrent
ab -n 1000 -c 10 http://localhost:5000/health

# With POST data
ab -n 1000 -c 10 -p data.json -T application/json http://localhost:5000/api/text/generate
```

#### Using wrk

```bash
# 4 threads, 100 connections, 30 seconds
wrk -t4 -c100 -d30s http://localhost:5000/health

# With custom script
wrk -t4 -c100 -d30s -s script.lua http://localhost:5000/api/text/generate
```

## Profiling

### Python Profiling

```bash
# Install profiling tools
pip install py-spy memory-profiler line-profiler

# CPU profiling
py-spy record -o profile.svg -- python -m src.main

# Memory profiling
python -m memory_profiler src/main.py

# Line profiling
kernprof -l -v src/main.py
```

### Database Profiling

```bash
# Enable query logging
echo "log_statement = 'all'" >> /etc/postgresql/postgresql.conf

# View slow queries
SELECT query, calls, mean_time FROM pg_stat_statements ORDER BY mean_time DESC;
```

## Optimization Techniques

### 1. Caching Strategy

```python
# Cache model outputs
from src.cache import cache

def generate_text(prompt):
    # Check cache first
    cached = cache.get('text_gen', {'prompt': prompt})
    if cached:
        return cached
    
    # Generate if not cached
    result = ai_model.generate_text(prompt)
    
    # Cache result
    cache.set('text_gen', {'prompt': prompt}, result, ttl=3600)
    return result
```

### 2. Database Optimization

```sql
-- Add indexes
CREATE INDEX idx_user_id ON generated_content(user_id);
CREATE INDEX idx_created_at ON generated_content(created_at);
CREATE INDEX idx_content_type ON generated_content(content_type);

-- Analyze query plans
EXPLAIN ANALYZE SELECT * FROM generated_content WHERE user_id = 1;

-- Vacuum and analyze
VACUUM ANALYZE;
```

### 3. API Optimization

```python
# Use pagination
@app.route('/api/history')
def get_history():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    items = GeneratedContent.query.paginate(page, per_page)
    return jsonify(items.to_dict())

# Use compression
from flask_compress import Compress
Compress(app)

# Use async for long operations
from celery import Celery
celery = Celery(app.name)

@celery.task
def generate_text_async(prompt):
    return ai_model.generate_text(prompt)
```

### 4. Frontend Optimization

```javascript
// Code splitting
const TextGenerator = React.lazy(() => import('./pages/TextGenerator'));

// Image optimization
<img src="image.jpg" loading="lazy" />

// Memoization
const MemoizedComponent = React.memo(Component);

// Virtual scrolling for large lists
import { FixedSizeList } from 'react-window';
```

### 5. Infrastructure Optimization

```yaml
# Docker optimization
FROM python:3.10-slim as builder
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.10-slim
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
```

## Monitoring & Metrics

### Application Metrics

```python
from prometheus_client import Counter, Histogram, Gauge

# Request counter
request_count = Counter('requests_total', 'Total requests')

# Response time histogram
response_time = Histogram('response_time_seconds', 'Response time')

# Active connections gauge
active_connections = Gauge('active_connections', 'Active connections')
```

### System Metrics

```bash
# CPU usage
top -b -n 1 | grep Cpu

# Memory usage
free -h

# Disk usage
df -h

# Network usage
iftop -n
```

## Performance Reports

### Generate Report

```bash
# Run tests
locust -f locustfile.py --headless -u 100 -r 10 -t 5m --csv=results

# Analyze results
python analyze_results.py results_stats.csv
```

## Optimization Checklist

- [ ] Enable caching
- [ ] Add database indexes
- [ ] Optimize queries
- [ ] Compress responses
- [ ] Minify assets
- [ ] Use CDN
- [ ] Enable HTTP/2
- [ ] Optimize images
- [ ] Lazy load components
- [ ] Use async operations
- [ ] Monitor performance
- [ ] Set up alerts

## Performance Goals

### Phase 1 (MVP)
- Response time: < 1000ms
- Throughput: > 10 req/s
- Error rate: < 1%

### Phase 2 (Growth)
- Response time: < 500ms
- Throughput: > 100 req/s
- Error rate: < 0.1%

### Phase 3 (Scale)
- Response time: < 200ms
- Throughput: > 1000 req/s
- Error rate: < 0.01%
