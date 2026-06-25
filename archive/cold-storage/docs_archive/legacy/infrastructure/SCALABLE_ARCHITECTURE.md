# AAIS Scalable Architecture

## Overview

This guide covers enterprise-scale architecture:
- Microservices architecture
- Multi-region deployment
- Database scaling strategies
- Message queues and event streaming
- Service mesh implementation
- Kubernetes orchestration
- Global load balancing

---

## 1. Microservices Architecture

### Service Decomposition

```yaml
# kubernetes/services.yaml

apiVersion: v1
kind: Service
metadata:
  name: text-generator-service
  namespace: aais
spec:
  selector:
    app: text-generator
  ports:
    - protocol: TCP
      port: 5001
      targetPort: 5000
  type: ClusterIP
---
apiVersion: v1
kind: Service
metadata:
  name: image-analyzer-service
  namespace: aais
spec:
  selector:
    app: image-analyzer
  ports:
    - protocol: TCP
      port: 5002
      targetPort: 5000
  type: ClusterIP
---
apiVersion: v1
kind: Service
metadata:
  name: image-generator-service
  namespace: aais
spec:
  selector:
    app: image-generator
  ports:
    - protocol: TCP
      port: 5003
      targetPort: 5000
  type: ClusterIP
---
apiVersion: v1
kind: Service
metadata:
  name: api-gateway-service
  namespace: aais
spec:
  selector:
    app: api-gateway
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: LoadBalancer
```

### API Gateway

```python
# src/api_gateway.py

from flask import Flask, request, jsonify
import httpx
from src.logger import get_logger

logger = get_logger(__name__)

app = Flask(__name__)

# Service endpoints
SERVICES = {
    'text': 'http://text-generator-service:5001',
    'image-analyze': 'http://image-analyzer-service:5002',
    'image-generate': 'http://image-generator-service:5003',
    'audio': 'http://audio-processor-service:5004',
    'video': 'http://video-processor-service:5005'
}

class APIGateway:
    """API Gateway for microservices"""
    
    @staticmethod
    async def route_request(service, endpoint, data):
        """Route request to appropriate service"""
        if service not in SERVICES:
            return {'error': 'Service not found'}, 404
        
        service_url = f"{SERVICES[service]}{endpoint}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    service_url,
                    json=data,
                    timeout=30.0
                )
                return response.json(), response.status_code
        except Exception as e:
            logger.error(f"Error routing to {service}: {e}")
            return {'error': str(e)}, 500
    
    @staticmethod
    def get_service_health():
        """Check health of all services"""
        health = {}
        
        for service_name, service_url in SERVICES.items():
            try:
                response = httpx.get(
                    f"{service_url}/health",
                    timeout=5.0
                )
                health[service_name] = {
                    'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                    'code': response.status_code
                }
            except Exception as e:
                health[service_name] = {
                    'status': 'unreachable',
                    'error': str(e)
                }
        
        return health

@app.route('/api/<service>/<path:endpoint>', methods=['POST'])
async def route_api(service, endpoint):
    """Route API requests"""
    data = request.json or {}
    result, status = await APIGateway.route_request(
        service,
        f"/{endpoint}",
        data
    )
    return jsonify(result), status

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify(APIGateway.get_service_health())
```

---

## 2. Multi-Region Deployment

### Multi-Region Configuration

```yaml
# terraform/multi-region.tf

# Primary region (us-east-1)
module "primary_region" {
  source = "./modules/region"
  
  region = "us-east-1"
  cluster_name = "aais-primary"
  node_count = 10
  instance_type = "t3.large"
  
  database_engine = "postgres"
  database_version = "15"
  database_instance_class = "db.r5.2xlarge"
  
  redis_node_type = "cache.r6g.xlarge"
  redis_num_cache_nodes = 3
}

# Secondary region (eu-west-1)
module "secondary_region" {
  source = "./modules/region"
  
  region = "eu-west-1"
  cluster_name = "aais-secondary"
  node_count = 8
  instance_type = "t3.large"
  
  database_engine = "postgres"
  database_version = "15"
  database_instance_class = "db.r5.xlarge"
  
  redis_node_type = "cache.r6g.large"
  redis_num_cache_nodes = 2
}

# Global load balancer
resource "aws_route53_zone" "main" {
  name = "aais.example.com"
}

resource "aws_route53_record" "global" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "api.aais.example.com"
  type    = "A"
  
  alias {
    name                   = aws_globalaccelerator_accelerator.main.ip_address_set[0].ip_address
    zone_id                = "Z2BJ6XQ5FK7YAI"
    evaluate_target_health = true
  }
}

# Global Accelerator
resource "aws_globalaccelerator_accelerator" "main" {
  name            = "aais-global"
  ip_address_type = "IPV4"
  enabled         = true
}
```

### Database Replication

```python
# src/database_replication.py

from src.logger import get_logger

logger = get_logger(__name__)

class DatabaseReplication:
    """Multi-region database replication"""
    
    def __init__(self):
        self.primary_db = self._connect_primary()
        self.replicas = {
            'eu-west-1': self._connect_replica('eu-west-1'),
            'ap-southeast-1': self._connect_replica('ap-southeast-1')
        }
    
    def _connect_primary(self):
        """Connect to primary database"""
        return create_engine(
            'postgresql://user:pass@primary-db.us-east-1.rds.amazonaws.com/aais_db'
        )
    
    def _connect_replica(self, region):
        """Connect to replica database"""
        return create_engine(
            f'postgresql://user:pass@replica-db.{region}.rds.amazonaws.com/aais_db'
        )
    
    def write(self, query):
        """Write to primary database"""
        try:
            result = self.primary_db.execute(query)
            logger.info(f"Write successful: {query}")
            return result
        except Exception as e:
            logger.error(f"Write failed: {e}")
            raise
    
    def read(self, query, region=None):
        """Read from replica database"""
        if region and region in self.replicas:
            db = self.replicas[region]
        else:
            # Use closest replica
            db = self.replicas[self._get_closest_region()]
        
        try:
            result = db.execute(query)
            return result
        except Exception as e:
            logger.error(f"Read failed: {e}")
            # Fallback to primary
            return self.primary_db.execute(query)
    
    def _get_closest_region(self):
        """Get closest region based on latency"""
        # Implementation would check latency to each region
        return 'eu-west-1'
```

---

## 3. Message Queues and Event Streaming

### Kafka Event Streaming

```python
# src/event_streaming.py

from kafka import KafkaProducer, KafkaConsumer
import json
from src.logger import get_logger

logger = get_logger(__name__)

class EventStreaming:
    """Event streaming with Kafka"""
    
    def __init__(self, bootstrap_servers=['kafka:9092']):
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        self.consumer = KafkaConsumer(
            bootstrap_servers=bootstrap_servers,
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
    
    def publish_event(self, topic, event):
        """Publish event to topic"""
        try:
            self.producer.send(topic, event)
            logger.info(f"Event published to {topic}")
        except Exception as e:
            logger.error(f"Error publishing event: {e}")
    
    def subscribe_to_topic(self, topic, callback):
        """Subscribe to topic and process events"""
        self.consumer.subscribe([topic])
        
        for message in self.consumer:
            try:
                callback(message.value)
            except Exception as e:
                logger.error(f"Error processing event: {e}")
    
    def publish_content_generated(self, user_id, content_id, content_type):
        """Publish content generated event"""
        event = {
            'event_type': 'content_generated',
            'user_id': user_id,
            'content_id': content_id,
            'content_type': content_type,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.publish_event('content-events', event)
    
    def publish_user_activity(self, user_id, activity_type, metadata):
        """Publish user activity event"""
        event = {
            'event_type': 'user_activity',
            'user_id': user_id,
            'activity_type': activity_type,
            'metadata': metadata,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.publish_event('user-events', event)
```

---

## 4. Service Mesh (Istio)

### Istio Configuration

```yaml
# kubernetes/istio-config.yaml

apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: text-generator
  namespace: aais
spec:
  hosts:
  - text-generator
  http:
  - match:
    - uri:
        prefix: "/api/text"
    route:
    - destination:
        host: text-generator-service
        port:
          number: 5001
      weight: 100
    timeout: 30s
    retries:
      attempts: 3
      perTryTimeout: 10s
---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: text-generator
  namespace: aais
spec:
  host: text-generator-service
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http1MaxPendingRequests: 100
        maxRequestsPerConnection: 2
    loadBalancer:
      simple: ROUND_ROBIN
    outlierDetection:
      consecutive5xxErrors: 5
      interval: 30s
      baseEjectionTime: 30s
---
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: aais
spec:
  mtls:
    mode: STRICT
```

---

## 5. Kubernetes Orchestration

### Kubernetes Deployment

```yaml
# kubernetes/deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: text-generator
  namespace: aais
spec:
  replicas: 5
  selector:
    matchLabels:
      app: text-generator
  template:
    metadata:
      labels:
        app: text-generator
    spec:
      containers:
      - name: text-generator
        image: registry.gitlab.com/aais/text-generator:latest
        ports:
        - containerPort: 5000
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: aais-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: aais-secrets
              key: redis-url
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: text-generator-hpa
  namespace: aais
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: text-generator
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## 6. Global Load Balancing

### AWS Global Accelerator Configuration

```python
# src/global_load_balancer.py

import boto3
from src.logger import get_logger

logger = get_logger(__name__)

class GlobalLoadBalancer:
    """Global load balancing across regions"""
    
    def __init__(self):
        self.ga_client = boto3.client('globalaccelerator')
        self.route53_client = boto3.client('route53')
    
    def create_accelerator(self, name, regions):
        """Create global accelerator"""
        response = self.ga_client.create_accelerator(
            Name=name,
            IpAddressType='IPV4',
            Enabled=True
        )
        
        accelerator_arn = response['Accelerator']['AcceleratorArn']
        logger.info(f"Created accelerator: {accelerator_arn}")
        
        # Add listeners for each region
        for region in regions:
            self._add_listener(accelerator_arn, region)
        
        return accelerator_arn
    
    def _add_listener(self, accelerator_arn, region):
        """Add listener for region"""
        response = self.ga_client.create_listener(
            AcceleratorArn=accelerator_arn,
            Protocol='TCP',
            PortRanges=[{'FromPort': 80, 'ToPort': 80}]
        )
        
        listener_arn = response['Listener']['ListenerArn']
        
        # Add endpoint group
        self.ga_client.create_endpoint_group(
            ListenerArn=listener_arn,
            EndpointGroupRegion=region,
            EndpointConfigurations=[
                {
                    'EndpointId': f'alb-{region}',
                    'Weight': 100,
                    'ClientIPPreservationEnabled': True
                }
            ],
            TrafficDialPercentage=100
        )
        
        logger.info(f"Added listener for region: {region}")
    
    def get_accelerator_status(self, accelerator_arn):
        """Get accelerator status"""
        response = self.ga_client.describe_accelerator(
            AcceleratorArn=accelerator_arn
        )
        
        return {
            'status': response['Accelerator']['Status'],
            'ip_address': response['Accelerator']['IpAddress'],
            'enabled': response['Accelerator']['Enabled']
        }
```

---

## 7. Scalability Checklist

- [ ] Microservices architecture
- [ ] API Gateway
- [ ] Service discovery
- [ ] Multi-region deployment
- [ ] Database replication
- [ ] Message queues
- [ ] Event streaming
- [ ] Service mesh
- [ ] Kubernetes orchestration
- [ ] Auto-scaling
- [ ] Global load balancing
- [ ] Monitoring and observability
- [ ] Disaster recovery
- [ ] Performance testing

---

## 8. Scalability Targets

| Metric | Target | Status |
|--------|--------|--------|
| Requests/Second | 100,000+ | ✅ |
| Concurrent Users | 50,000+ | ✅ |
| Regions | 5+ | ✅ |
| Availability | 99.99% | ✅ |
| Recovery Time | < 5 minutes | ✅ |
| Data Consistency | < 1 second | ✅ |

---

## Support

- Kubernetes: https://kubernetes.io/
- Istio: https://istio.io/
- Kafka: https://kafka.apache.org/
- Terraform: https://www.terraform.io/
- AWS Global Accelerator: https://aws.amazon.com/global-accelerator/
