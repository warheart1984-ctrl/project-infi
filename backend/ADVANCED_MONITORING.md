# AAIS Advanced Monitoring & Observability

## Overview

This guide covers enterprise-grade observability:
- Distributed tracing
- Metrics collection and analysis
- Log aggregation and analysis
- Real-time alerting
- Performance monitoring
- Error tracking
- User behavior analytics

---

## 1. Distributed Tracing with Jaeger

### Jaeger Setup

```yaml
# kubernetes/jaeger.yaml

apiVersion: v1
kind: Service
metadata:
  name: jaeger
  namespace: monitoring
spec:
  ports:
  - name: jaeger-agent-zipkin-thrift
    port: 6831
    protocol: UDP
  - name: jaeger-collector
    port: 14268
  - name: jaeger-ui
    port: 16686
  selector:
    app: jaeger
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jaeger
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: jaeger
  template:
    metadata:
      labels:
        app: jaeger
    spec:
      containers:
      - name: jaeger
        image: jaegertracing/all-in-one:latest
        ports:
        - containerPort: 6831
          protocol: UDP
        - containerPort: 14268
        - containerPort: 16686
        env:
        - name: COLLECTOR_ZIPKIN_HOST_PORT
          value: ":9411"
```

### Distributed Tracing Implementation

```python
# src/distributed_tracing.py

from jaeger_client import Config
from opentelemetry import trace, metrics
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from src.logger import get_logger

logger = get_logger(__name__)

class DistributedTracing:
    """Setup distributed tracing"""
    
    @staticmethod
    def initialize_jaeger(service_name: str):
        """Initialize Jaeger tracing"""
        jaeger_exporter = JaegerExporter(
            agent_host_name="jaeger",
            agent_port=6831,
        )
        
        trace.set_tracer_provider(TracerProvider())
        trace.get_tracer_provider().add_span_processor(
            BatchSpanProcessor(jaeger_exporter)
        )
        
        logger.info(f"Jaeger tracing initialized for {service_name}")
    
    @staticmethod
    def instrument_flask(app):
        """Instrument Flask application"""
        FlaskInstrumentor().instrument_app(app)
        logger.info("Flask instrumented")
    
    @staticmethod
    def instrument_database():
        """Instrument database"""
        SQLAlchemyInstrumentor().instrument()
        logger.info("SQLAlchemy instrumented")
    
    @staticmethod
    def instrument_redis():
        """Instrument Redis"""
        RedisInstrumentor().instrument()
        logger.info("Redis instrumented")
    
    @staticmethod
    def create_span(span_name: str, attributes: dict = None):
        """Create custom span"""
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span(span_name) as span:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)
            return span
```

---

## 2. Metrics Collection with Prometheus

### Prometheus Configuration

```yaml
# kubernetes/prometheus.yaml

apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
    
    scrape_configs:
    - job_name: 'aais-backend'
      static_configs:
      - targets: ['localhost:8000']
      scrape_interval: 5s
    
    - job_name: 'aais-frontend'
      static_configs:
      - targets: ['localhost:3000']
    
    - job_name: 'kubernetes-pods'
      kubernetes_sd_configs:
      - role: pod
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:latest
        ports:
        - containerPort: 9090
        volumeMounts:
        - name: config
          mountPath: /etc/prometheus
        - name: storage
          mountPath: /prometheus
      volumes:
      - name: config
        configMap:
          name: prometheus-config
      - name: storage
        emptyDir: {}
```

### Custom Metrics

```python
# src/custom_metrics.py

from prometheus_client import Counter, Histogram, Gauge, Summary
import time

# Request metrics
request_count = Counter(
    'aais_requests_total',
    'Total requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'aais_request_duration_seconds',
    'Request duration',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0]
)

# Business metrics
text_generated = Counter(
    'aais_text_generated_total',
    'Total text generated',
    ['model', 'status']
)

image_generated = Counter(
    'aais_images_generated_total',
    'Total images generated',
    ['model', 'status']
)

# System metrics
active_connections = Gauge(
    'aais_active_connections',
    'Active database connections'
)

cache_hit_rate = Gauge(
    'aais_cache_hit_rate',
    'Cache hit rate percentage'
)

db_query_duration = Summary(
    'aais_db_query_duration_seconds',
    'Database query duration',
    ['query_type']
)

class MetricsCollector:
    """Collect custom metrics"""
    
    @staticmethod
    def record_request(method, endpoint, status, duration):
        """Record request metrics"""
        request_count.labels(
            method=method,
            endpoint=endpoint,
            status=status
        ).inc()
        
        request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    @staticmethod
    def record_text_generation(model, success):
        """Record text generation"""
        text_generated.labels(
            model=model,
            status='success' if success else 'failure'
        ).inc()
    
    @staticmethod
    def update_cache_hit_rate(hit_rate):
        """Update cache hit rate"""
        cache_hit_rate.set(hit_rate * 100)
    
    @staticmethod
    def record_db_query(query_type, duration):
        """Record database query"""
        db_query_duration.labels(query_type=query_type).observe(duration)
```

---

## 3. Log Aggregation with ELK Stack

### Elasticsearch Configuration

```yaml
# kubernetes/elasticsearch.yaml

apiVersion: v1
kind: Service
metadata:
  name: elasticsearch
  namespace: monitoring
spec:
  ports:
  - port: 9200
    name: rest
  - port: 9300
    name: inter-node
  selector:
    app: elasticsearch
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: elasticsearch
  namespace: monitoring
spec:
  replicas: 1
  selector:
    matchLabels:
      app: elasticsearch
  template:
    metadata:
      labels:
        app: elasticsearch
    spec:
      containers:
      - name: elasticsearch
        image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
        ports:
        - containerPort: 9200
          name: rest
        - containerPort: 9300
          name: inter-node
        env:
        - name: cluster.name
          value: aais-cluster
        - name: discovery.type
          value: single-node
        - name: xpack.security.enabled
          value: "false"
        resources:
          limits:
            cpu: 1000m
            memory: 2Gi
          requests:
            cpu: 500m
            memory: 1Gi
```

### Logstash Configuration

```yaml
# kubernetes/logstash.yaml

apiVersion: v1
kind: ConfigMap
metadata:
  name: logstash-config
  namespace: monitoring
data:
  logstash.conf: |
    input {
      tcp {
        port => 5000
        codec => json
      }
    }
    
    filter {
      if [type] == "aais-backend" {
        grok {
          match => { "message" => "%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:level} %{DATA:logger} %{GREEDYDATA:message}" }
        }
      }
    }
    
    output {
      elasticsearch {
        hosts => ["elasticsearch:9200"]
        index => "aais-%{+YYYY.MM.dd}"
      }
    }
```

### Kibana Dashboards

```python
# src/kibana_dashboards.py

from elasticsearch import Elasticsearch
from src.logger import get_logger

logger = get_logger(__name__)

class KibanaDashboards:
    """Create Kibana dashboards"""
    
    def __init__(self):
        self.es = Elasticsearch(['http://elasticsearch:9200'])
    
    def create_performance_dashboard(self):
        """Create performance dashboard"""
        dashboard = {
            "title": "AAIS Performance",
            "panels": [
                {
                    "title": "Request Rate",
                    "query": "SELECT COUNT(*) FROM aais-* WHERE timestamp > now-1h"
                },
                {
                    "title": "Response Time (P95)",
                    "query": "SELECT PERCENTILE(duration, 0.95) FROM aais-*"
                },
                {
                    "title": "Error Rate",
                    "query": "SELECT COUNT(*) FROM aais-* WHERE status >= 400"
                },
                {
                    "title": "Cache Hit Rate",
                    "query": "SELECT cache_hits / (cache_hits + cache_misses) FROM metrics"
                }
            ]
        }
        
        logger.info("Performance dashboard created")
        return dashboard
    
    def create_error_dashboard(self):
        """Create error tracking dashboard"""
        dashboard = {
            "title": "AAIS Errors",
            "panels": [
                {
                    "title": "Error Count by Type",
                    "query": "SELECT error_type, COUNT(*) FROM aais-* WHERE level='ERROR' GROUP BY error_type"
                },
                {
                    "title": "Error Timeline",
                    "query": "SELECT timestamp, error_message FROM aais-* WHERE level='ERROR' ORDER BY timestamp DESC"
                },
                {
                    "title": "Top Errors",
                    "query": "SELECT error_message, COUNT(*) FROM aais-* WHERE level='ERROR' GROUP BY error_message LIMIT 10"
                }
            ]
        }
        
        logger.info("Error dashboard created")
        return dashboard
```

---

## 4. Real-Time Alerting

### Alert Rules

```yaml
# kubernetes/alert-rules.yaml

apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: aais-alerts
  namespace: monitoring
spec:
  groups:
  - name: aais.rules
    interval: 30s
    rules:
    - alert: HighErrorRate
      expr: rate(aais_requests_total{status=~"5.."}[5m]) > 0.05
      for: 5m
      annotations:
        summary: "High error rate detected"
        description: "Error rate is {{ $value | humanizePercentage }}"
    
    - alert: HighResponseTime
      expr: histogram_quantile(0.95, aais_request_duration_seconds) > 0.2
      for: 5m
      annotations:
        summary: "High response time detected"
        description: "P95 response time is {{ $value }}s"
    
    - alert: LowCacheHitRate
      expr: aais_cache_hit_rate < 80
      for: 10m
      annotations:
        summary: "Low cache hit rate"
        description: "Cache hit rate is {{ $value }}%"
    
    - alert: DatabaseConnectionPoolExhausted
      expr: aais_active_connections > 90
      for: 5m
      annotations:
        summary: "Database connection pool exhausted"
        description: "Active connections: {{ $value }}"
```

### Alert Manager Configuration

```yaml
# kubernetes/alertmanager.yaml

apiVersion: v1
kind: ConfigMap
metadata:
  name: alertmanager-config
  namespace: monitoring
data:
  alertmanager.yml: |
    global:
      resolve_timeout: 5m
    
    route:
      receiver: 'default'
      group_by: ['alertname', 'cluster']
      group_wait: 10s
      group_interval: 10s
      repeat_interval: 12h
      routes:
      - match:
          severity: critical
        receiver: 'critical'
        continue: true
      - match:
          severity: warning
        receiver: 'warning'
    
    receivers:
    - name: 'default'
      slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#alerts'
    
    - name: 'critical'
      slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#critical-alerts'
      pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_KEY'
    
    - name: 'warning'
      slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#warnings'
```

---

## 5. User Behavior Analytics

### Analytics Collection

```python
# src/analytics_collector.py

from datetime import datetime
from src.database import db, AnalyticsEvent
from src.logger import get_logger

logger = get_logger(__name__)

class AnalyticsCollector:
    """Collect user behavior analytics"""
    
    @staticmethod
    def track_event(user_id: str, event_type: str, metadata: dict = None):
        """Track user event"""
        event = AnalyticsEvent(
            user_id=user_id,
            event_type=event_type,
            metadata=metadata or {},
            timestamp=datetime.utcnow()
        )
        
        db.session.add(event)
        db.session.commit()
        
        logger.debug(f"Event tracked: {event_type} for user {user_id}")
    
    @staticmethod
    def get_user_journey(user_id: str):
        """Get user journey"""
        events = AnalyticsEvent.query.filter(
            AnalyticsEvent.user_id == user_id
        ).order_by(AnalyticsEvent.timestamp).all()
        
        return [
            {
                'event_type': e.event_type,
                'timestamp': e.timestamp.isoformat(),
                'metadata': e.metadata
            }
            for e in events
        ]
    
    @staticmethod
    def get_funnel_analysis(funnel_steps: list):
        """Analyze conversion funnel"""
        results = {}
        
        for i, step in enumerate(funnel_steps):
            count = AnalyticsEvent.query.filter(
                AnalyticsEvent.event_type == step
            ).count()
            
            results[step] = {
                'count': count,
                'conversion_rate': count / results[funnel_steps[0]]['count'] if i > 0 else 1.0
            }
        
        return results
    
    @staticmethod
    def get_cohort_analysis(cohort_date):
        """Analyze user cohorts"""
        cohort_users = AnalyticsEvent.query.filter(
            AnalyticsEvent.timestamp >= cohort_date
        ).distinct(AnalyticsEvent.user_id).count()
        
        return {
            'cohort_date': cohort_date.isoformat(),
            'user_count': cohort_users
        }
```

---

## 6. Monitoring Checklist

- [ ] Jaeger distributed tracing
- [ ] Prometheus metrics
- [ ] Elasticsearch log aggregation
- [ ] Kibana dashboards
- [ ] Alert rules
- [ ] Alert manager
- [ ] Slack integration
- [ ] PagerDuty integration
- [ ] Custom metrics
- [ ] User analytics
- [ ] Performance dashboards
- [ ] Error tracking
- [ ] Health checks
- [ ] SLA monitoring

---

## 7. Key Metrics to Monitor

| Metric | Target | Alert Threshold |
|--------|--------|------------------|
| Request Rate | 10,000+ req/s | > 15,000 req/s |
| P95 Response Time | < 100ms | > 200ms |
| Error Rate | < 0.01% | > 0.1% |
| Cache Hit Rate | > 95% | < 80% |
| Database Connections | < 50 | > 90 |
| CPU Usage | < 70% | > 85% |
| Memory Usage | < 80% | > 90% |
| Disk Usage | < 80% | > 90% |

---

## Support

- Jaeger: https://www.jaegertracing.io/
- Prometheus: https://prometheus.io/
- Elasticsearch: https://www.elastic.co/
- Kibana: https://www.elastic.co/kibana
- AlertManager: https://prometheus.io/docs/alerting/latest/overview/
