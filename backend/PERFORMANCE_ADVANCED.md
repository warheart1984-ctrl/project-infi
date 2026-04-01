# AAIS Performance Optimization - Advanced Techniques

## Overview

This guide covers advanced performance optimization strategies:
- Database query optimization
- Caching strategies
- API response optimization
- Frontend performance
- Infrastructure optimization
- Monitoring and profiling

---

## 1. Database Query Optimization

### Add Database Indexes

```sql
-- Create indexes for frequently queried columns
CREATE INDEX idx_user_id ON generated_content(user_id);
CREATE INDEX idx_created_at ON generated_content(created_at);
CREATE INDEX idx_content_type ON generated_content(content_type);
CREATE INDEX idx_user_created ON generated_content(user_id, created_at);
CREATE INDEX idx_status ON generated_content(status);

-- Create indexes for authentication
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_user_username ON users(username);

-- Create indexes for caching
CREATE INDEX idx_cache_key ON cache_entries(key);
CREATE INDEX idx_cache_expiry ON cache_entries(expiry_time);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM generated_content WHERE user_id = 1 ORDER BY created_at DESC;
```

### Optimize Query Patterns

```python
# src/database_optimized.py

from sqlalchemy import and_, or_
from sqlalchemy.orm import joinedload
from src.database import db, GeneratedContent, User

class OptimizedQueries:
    """Optimized database queries"""
    
    @staticmethod
    def get_user_content_paginated(user_id, page=1, per_page=20):
        """Get user content with pagination"""
        return GeneratedContent.query.filter(
            GeneratedContent.user_id == user_id
        ).order_by(
            GeneratedContent.created_at.desc()
        ).paginate(page=page, per_page=per_page)
    
    @staticmethod
    def get_recent_content(limit=100):
        """Get recent content efficiently"""
        return GeneratedContent.query.order_by(
            GeneratedContent.created_at.desc()
        ).limit(limit).all()
    
    @staticmethod
    def get_content_by_type(content_type, limit=50):
        """Get content by type with limit"""
        return GeneratedContent.query.filter(
            GeneratedContent.content_type == content_type
        ).order_by(
            GeneratedContent.created_at.desc()
        ).limit(limit).all()
    
    @staticmethod
    def batch_get_user_stats(user_ids):
        """Get stats for multiple users efficiently"""
        from sqlalchemy import func
        
        return db.session.query(
            GeneratedContent.user_id,
            func.count(GeneratedContent.id).label('count'),
            func.avg(GeneratedContent.processing_time).label('avg_time')
        ).filter(
            GeneratedContent.user_id.in_(user_ids)
        ).group_by(
            GeneratedContent.user_id
        ).all()
```

### Connection Pooling

```python
# In src/database.py

from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,           # Number of connections to keep in pool
    max_overflow=40,        # Maximum overflow connections
    pool_recycle=3600,      # Recycle connections after 1 hour
    pool_pre_ping=True,     # Test connections before using
    echo=False
)
```

---

## 2. Advanced Caching Strategies

### Multi-Level Caching

```python
# src/cache_optimized.py

import hashlib
import json
from functools import wraps
from datetime import timedelta
from src.cache import redis_client
from src.logger import get_logger

logger = get_logger(__name__)

class CacheManager:
    """Advanced cache management"""
    
    # Cache TTLs
    TTL_SHORT = 300        # 5 minutes
    TTL_MEDIUM = 3600      # 1 hour
    TTL_LONG = 86400       # 24 hours
    
    @staticmethod
    def generate_cache_key(*args, **kwargs):
        """Generate cache key from arguments"""
        key_data = json.dumps({
            'args': args,
            'kwargs': kwargs
        }, sort_keys=True, default=str)
        return hashlib.md5(key_data.encode()).hexdigest()
    
    @staticmethod
    def cache_result(ttl=TTL_MEDIUM, key_prefix=''):
        """Decorator for caching function results"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = f"{key_prefix}:{CacheManager.generate_cache_key(*args, **kwargs)}"
                
                # Try to get from cache
                cached = redis_client.get(cache_key)
                if cached:
                    logger.debug(f"Cache hit: {cache_key}")
                    return json.loads(cached)
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Store in cache
                redis_client.setex(
                    cache_key,
                    ttl,
                    json.dumps(result, default=str)
                )
                logger.debug(f"Cache miss: {cache_key}")
                
                return result
            return wrapper
        return decorator
    
    @staticmethod
    def invalidate_pattern(pattern):
        """Invalidate cache by pattern"""
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
            logger.info(f"Invalidated {len(keys)} cache keys")

# Usage
@CacheManager.cache_result(ttl=CacheManager.TTL_LONG, key_prefix='user_stats')
def get_user_stats(user_id):
    # Expensive operation
    return calculate_user_stats(user_id)
```

### Cache Warming

```python
# src/cache_warmer.py

from src.cache_optimized import CacheManager
from src.database import User, GeneratedContent
from src.logger import get_logger

logger = get_logger(__name__)

class CacheWarmer:
    """Pre-populate cache with frequently accessed data"""
    
    @staticmethod
    def warm_popular_content():
        """Cache popular content"""
        logger.info("Warming cache with popular content...")
        
        # Get top 100 most viewed content
        popular = GeneratedContent.query.order_by(
            GeneratedContent.view_count.desc()
        ).limit(100).all()
        
        for content in popular:
            cache_key = f"content:{content.id}"
            redis_client.setex(
                cache_key,
                CacheManager.TTL_LONG,
                json.dumps(content.to_dict())
            )
        
        logger.info(f"Warmed cache with {len(popular)} items")
    
    @staticmethod
    def warm_user_stats():
        """Cache user statistics"""
        logger.info("Warming cache with user stats...")
        
        users = User.query.limit(1000).all()
        
        for user in users:
            stats = get_user_stats(user.id)
            cache_key = f"user_stats:{user.id}"
            redis_client.setex(
                cache_key,
                CacheManager.TTL_MEDIUM,
                json.dumps(stats)
            )
        
        logger.info(f"Warmed cache with stats for {len(users)} users")
```

---

## 3. API Response Optimization

### Response Compression

```python
# In src/main.py

from flask_compress import Compress

Compress(app)

# Configure compression
app.config['COMPRESS_LEVEL'] = 6
app.config['COMPRESS_MIN_SIZE'] = 1000
```

### Pagination and Filtering

```python
# src/api_optimized.py

from flask import request, jsonify
from src.database_optimized import OptimizedQueries

@app.route('/api/content', methods=['GET'])
def get_content():
    """Get content with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    content_type = request.args.get('type', None)
    
    # Limit per_page to prevent abuse
    per_page = min(per_page, 100)
    
    if content_type:
        query = GeneratedContent.query.filter(
            GeneratedContent.content_type == content_type
        )
    else:
        query = GeneratedContent.query
    
    paginated = query.order_by(
        GeneratedContent.created_at.desc()
    ).paginate(page=page, per_page=per_page)
    
    return jsonify({
        'items': [item.to_dict() for item in paginated.items],
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': page
    })

@app.route('/api/search', methods=['GET'])
def search():
    """Search with full-text search"""
    query = request.args.get('q', '')
    
    if not query or len(query) < 3:
        return jsonify({'error': 'Query too short'}), 400
    
    # Use PostgreSQL full-text search
    results = GeneratedContent.query.filter(
        GeneratedContent.content.ilike(f'%{query}%')
    ).limit(50).all()
    
    return jsonify({
        'results': [r.to_dict() for r in results],
        'count': len(results)
    })
```

### Selective Field Loading

```python
# src/serializers.py

class ContentSerializer:
    """Serialize content with selective fields"""
    
    @staticmethod
    def to_dict_minimal(content):
        """Minimal representation"""
        return {
            'id': content.id,
            'type': content.content_type,
            'created_at': content.created_at.isoformat()
        }
    
    @staticmethod
    def to_dict_summary(content):
        """Summary representation"""
        return {
            'id': content.id,
            'type': content.content_type,
            'title': content.title,
            'preview': content.content[:200],
            'created_at': content.created_at.isoformat()
        }
    
    @staticmethod
    def to_dict_full(content):
        """Full representation"""
        return {
            'id': content.id,
            'type': content.content_type,
            'title': content.title,
            'content': content.content,
            'metadata': content.metadata,
            'created_at': content.created_at.isoformat(),
            'processing_time': content.processing_time
        }
```

---

## 4. Frontend Performance Optimization

### Code Splitting and Lazy Loading

```jsx
// frontend/src/App.jsx

import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

// Lazy load components
const Dashboard = lazy(() => import('./pages/Dashboard'));
const TextGenerator = lazy(() => import('./pages/TextGenerator'));
const ImageAnalyzer = lazy(() => import('./pages/ImageAnalyzer'));
const Analytics = lazy(() => import('./pages/Analytics'));

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<div>Loading...</div>}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/text" element={<TextGenerator />} />
          <Route path="/image" element={<ImageAnalyzer />} />
          <Route path="/analytics" element={<Analytics />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}

export default App;
```

### Image Optimization

```jsx
// frontend/src/components/OptimizedImage.jsx

import React from 'react';

function OptimizedImage({ src, alt, width, height }) {
  return (
    <picture>
      <source srcSet={`${src}?w=800&q=80&fm=webp`} type="image/webp" />
      <source srcSet={`${src}?w=800&q=80`} type="image/jpeg" />
      <img
        src={`${src}?w=800&q=80`}
        alt={alt}
        width={width}
        height={height}
        loading="lazy"
        decoding="async"
      />
    </picture>
  );
}

export default OptimizedImage;
```

### Virtual Scrolling for Large Lists

```jsx
// frontend/src/components/VirtualList.jsx

import React from 'react';
import { FixedSizeList as List } from 'react-window';

function VirtualList({ items, itemSize = 50, height = 600 }) {
  const Row = ({ index, style }) => (
    <div style={style} className="list-item">
      {items[index].title}
    </div>
  );

  return (
    <List
      height={height}
      itemCount={items.length}
      itemSize={itemSize}
      width="100%"
    >
      {Row}
    </List>
  );
}

export default VirtualList;
```

---

## 5. Infrastructure Optimization

### Database Connection Pooling

```bash
# Update docker-compose.yml for RDS
services:
  backend:
    environment:
      - DATABASE_POOL_SIZE=20
      - DATABASE_MAX_OVERFLOW=40
      - DATABASE_POOL_RECYCLE=3600
```

### Redis Optimization

```bash
# Update Redis configuration
requirepass your_strong_password
maxmemory 2gb
maxmemory-policy allkeys-lru
tcp-backlog 511
timeout 0
tcp-keepalive 300
```

### ECS Task Optimization

```bash
# Update ECS task definition
{
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [{
    "name": "backend",
    "cpu": 512,
    "memory": 1024,
    "essential": true,
    "environment": [
      {"name": "WORKERS", "value": "4"},
      {"name": "THREADS", "value": "2"},
      {"name": "TIMEOUT", "value": "120"}
    ]
  }]
}
```

---

## 6. Monitoring and Profiling

### Application Performance Monitoring

```python
# src/monitoring.py

from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps

# Define metrics
request_count = Counter(
    'aais_requests_total',
    'Total requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'aais_request_duration_seconds',
    'Request duration',
    ['method', 'endpoint']
)

active_requests = Gauge(
    'aais_active_requests',
    'Active requests'
)

def monitor_request(func):
    """Decorator to monitor request metrics"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        active_requests.inc()
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            status = 'success'
            return result
        except Exception as e:
            status = 'error'
            raise
        finally:
            duration = time.time() - start_time
            active_requests.dec()
            request_duration.labels(
                method=request.method,
                endpoint=request.path
            ).observe(duration)
            request_count.labels(
                method=request.method,
                endpoint=request.path,
                status=status
            ).inc()
    
    return wrapper
```

### Query Performance Monitoring

```python
# src/query_monitor.py

from sqlalchemy import event
from sqlalchemy.engine import Engine
from src.logger import get_logger
import time

logger = get_logger(__name__)

@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total_time = time.time() - conn.info['query_start_time'].pop(-1)
    
    if total_time > 0.5:  # Log slow queries
        logger.warning(f"Slow query ({total_time:.2f}s): {statement}")
```

---

## 7. Performance Optimization Checklist

- [ ] Database indexes created
- [ ] Query optimization implemented
- [ ] Connection pooling configured
- [ ] Multi-level caching enabled
- [ ] Cache warming implemented
- [ ] Response compression enabled
- [ ] Pagination implemented
- [ ] Code splitting enabled
- [ ] Image optimization done
- [ ] Virtual scrolling for lists
- [ ] APM monitoring enabled
- [ ] Query monitoring enabled
- [ ] Load testing completed
- [ ] Performance baselines established
- [ ] Alerts configured

---

## 8. Performance Targets

| Metric | Target | Current |
|--------|--------|----------|
| API Response Time (p95) | < 200ms | - |
| Database Query Time | < 50ms | - |
| Cache Hit Rate | > 90% | - |
| Frontend Load Time | < 2s | - |
| Time to Interactive | < 3s | - |
| Largest Contentful Paint | < 2.5s | - |
| Cumulative Layout Shift | < 0.1 | - |

---

## Support

- SQLAlchemy: https://docs.sqlalchemy.org/
- Redis: https://redis.io/documentation
- React Performance: https://react.dev/reference/react/Profiler
- Web Vitals: https://web.dev/vitals/
