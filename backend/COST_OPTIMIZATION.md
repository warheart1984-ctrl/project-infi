# AAIS Cost Optimization - Reduce Expenses

## Overview

This guide covers cost optimization strategies:
- Infrastructure cost reduction
- Database optimization
- Storage optimization
- Compute optimization
- Network cost reduction
- Monitoring and alerting
- Reserved instances
- Spot instances
- Auto-scaling optimization

---

## 1. Infrastructure Cost Analysis

### Current Cost Breakdown

```python
# src/cost_analyzer.py

import boto3
from datetime import datetime, timedelta
from src.logger import get_logger

logger = get_logger(__name__)

class CostAnalyzer:
    """Analyze and optimize costs"""
    
    def __init__(self):
        self.ce_client = boto3.client('ce')
        self.ec2_client = boto3.client('ec2')
    
    def get_cost_breakdown(self, days=30):
        """Get cost breakdown by service"""
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        response = self.ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.isoformat(),
                'End': end_date.isoformat()
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost'],
            GroupBy=[
                {'Type': 'DIMENSION', 'Key': 'SERVICE'}
            ]
        )
        
        costs = {}
        for result in response['ResultsByTime']:
            for group in result['Groups']:
                service = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                
                if service not in costs:
                    costs[service] = 0
                costs[service] += cost
        
        return costs
    
    def get_optimization_recommendations(self):
        """Get cost optimization recommendations"""
        recommendations = []
        
        # Check for unused resources
        unused_instances = self._find_unused_instances()
        if unused_instances:
            recommendations.append({
                'type': 'unused_instances',
                'description': f'Found {len(unused_instances)} unused EC2 instances',
                'potential_savings': len(unused_instances) * 50,
                'instances': unused_instances
            })
        
        # Check for unattached volumes
        unattached_volumes = self._find_unattached_volumes()
        if unattached_volumes:
            recommendations.append({
                'type': 'unattached_volumes',
                'description': f'Found {len(unattached_volumes)} unattached EBS volumes',
                'potential_savings': len(unattached_volumes) * 5,
                'volumes': unattached_volumes
            })
        
        # Check for unused elastic IPs
        unused_eips = self._find_unused_eips()
        if unused_eips:
            recommendations.append({
                'type': 'unused_eips',
                'description': f'Found {len(unused_eips)} unused Elastic IPs',
                'potential_savings': len(unused_eips) * 3.6,
                'eips': unused_eips
            })
        
        return recommendations
    
    def _find_unused_instances(self):
        """Find unused EC2 instances"""
        response = self.ec2_client.describe_instances(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
        )
        
        unused = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                if self._get_cpu_utilization(instance['InstanceId']) < 5:
                    unused.append(instance['InstanceId'])
        
        return unused
    
    def _find_unattached_volumes(self):
        """Find unattached EBS volumes"""
        response = self.ec2_client.describe_volumes(
            Filters=[{'Name': 'status', 'Values': ['available']}]
        )
        
        return [vol['VolumeId'] for vol in response['Volumes']]
    
    def _find_unused_eips(self):
        """Find unused Elastic IPs"""
        response = self.ec2_client.describe_addresses()
        
        return [
            addr['PublicIp'] for addr in response['Addresses']
            if 'InstanceId' not in addr or addr['InstanceId'] == ''
        ]
```

---

## 2. Compute Optimization

### Right-Sizing Instances

```python
# src/compute_optimization.py

import boto3
from src.logger import get_logger

logger = get_logger(__name__)

class ComputeOptimization:
    """Optimize compute resources"""
    
    def __init__(self):
        self.ec2_client = boto3.client('ec2')
        self.cloudwatch = boto3.client('cloudwatch')
    
    def analyze_instance_sizing(self):
        """Analyze if instances are properly sized"""
        response = self.ec2_client.describe_instances(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
        )
        
        recommendations = []
        
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                instance_type = instance['InstanceType']
                
                cpu_util = self._get_metric(instance_id, 'CPUUtilization')
                memory_util = self._get_metric(instance_id, 'MemoryUtilization')
                
                if cpu_util < 20 and memory_util < 30:
                    recommendations.append({
                        'instance_id': instance_id,
                        'current_type': instance_type,
                        'recommendation': 'Downsize instance',
                        'cpu_util': cpu_util,
                        'memory_util': memory_util,
                        'potential_savings': self._estimate_savings(instance_type)
                    })
        
        return recommendations
    
    def enable_spot_instances(self, percentage=70):
        """Enable Spot instances for cost savings"""
        logger.info(f"Enabling Spot instances for {percentage}% of workload")
        
        ecs_client = boto3.client('ecs')
        response = ecs_client.list_services(cluster='aais-cluster')
        
        for service_arn in response['serviceArns']:
            service = ecs_client.describe_services(
                cluster='aais-cluster',
                services=[service_arn]
            )['services'][0]
            
            ecs_client.update_service(
                cluster='aais-cluster',
                service=service['serviceName'],
                capacityProviderStrategy=[
                    {
                        'capacityProvider': 'FARGATE_SPOT',
                        'weight': percentage,
                        'base': 1
                    },
                    {
                        'capacityProvider': 'FARGATE',
                        'weight': 100 - percentage
                    }
                ]
            )
            
            logger.info(f"Updated service {service['serviceName']} to use Spot instances")
    
    def _get_metric(self, instance_id, metric_name):
        """Get CloudWatch metric"""
        response = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName=metric_name,
            Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
            StartTime=datetime.utcnow() - timedelta(days=7),
            EndTime=datetime.utcnow(),
            Period=3600,
            Statistics=['Average']
        )
        
        if response['Datapoints']:
            return sum(dp['Average'] for dp in response['Datapoints']) / len(response['Datapoints'])
        return 0
    
    def _estimate_savings(self, instance_type):
        """Estimate savings from downsizing"""
        savings_map = {
            't3.2xlarge': 200,
            't3.xlarge': 100,
            't3.large': 50,
            't3.medium': 25
        }
        return savings_map.get(instance_type, 0)
```

---

## 3. Storage Optimization

### S3 Cost Optimization

```python
# src/storage_optimization.py

import boto3
from datetime import datetime, timedelta
from src.logger import get_logger

logger = get_logger(__name__)

class StorageOptimization:
    """Optimize storage costs"""
    
    def __init__(self):
        self.s3_client = boto3.client('s3')
    
    def analyze_s3_costs(self):
        """Analyze S3 storage costs"""
        response = self.s3_client.list_buckets()
        
        analysis = {}
        total_cost = 0
        
        for bucket in response['Buckets']:
            bucket_name = bucket['Name']
            size_bytes = self._get_bucket_size(bucket_name)
            size_gb = size_bytes / (1024**3)
            cost = size_gb * 0.023
            total_cost += cost
            
            analysis[bucket_name] = {
                'size_gb': size_gb,
                'estimated_cost': cost,
                'recommendations': self._get_bucket_recommendations(bucket_name)
            }
        
        return {'buckets': analysis, 'total_cost': total_cost}
    
    def enable_s3_lifecycle_policies(self, bucket_name):
        """Enable lifecycle policies for cost savings"""
        lifecycle_config = {
            'Rules': [
                {
                    'Id': 'archive-old-logs',
                    'Status': 'Enabled',
                    'Filter': {'Prefix': 'logs/'},
                    'Transitions': [
                        {'Days': 30, 'StorageClass': 'STANDARD_IA'},
                        {'Days': 90, 'StorageClass': 'GLACIER'}
                    ],
                    'Expiration': {'Days': 365}
                },
                {
                    'Id': 'delete-temp-files',
                    'Status': 'Enabled',
                    'Filter': {'Prefix': 'temp/'},
                    'Expiration': {'Days': 7}
                }
            ]
        }
        
        self.s3_client.put_bucket_lifecycle_configuration(
            Bucket=bucket_name,
            LifecycleConfiguration=lifecycle_config
        )
        
        logger.info(f"Lifecycle policies enabled for {bucket_name}")
    
    def _get_bucket_size(self, bucket_name):
        """Get total bucket size"""
        cloudwatch = boto3.client('cloudwatch')
        
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/S3',
            MetricName='BucketSizeBytes',
            Dimensions=[{'Name': 'BucketName', 'Value': bucket_name}],
            StartTime=datetime.utcnow() - timedelta(days=1),
            EndTime=datetime.utcnow(),
            Period=86400,
            Statistics=['Average']
        )
        
        if response['Datapoints']:
            return response['Datapoints'][-1]['Average']
        return 0
```

---

## 4. Database Optimization

### RDS Cost Optimization

```python
# src/database_cost_optimization.py

import boto3
from src.logger import get_logger

logger = get_logger(__name__)

class DatabaseCostOptimization:
    """Optimize database costs"""
    
    def __init__(self):
        self.rds_client = boto3.client('rds')
    
    def analyze_rds_costs(self):
        """Analyze RDS costs"""
        response = self.rds_client.describe_db_instances()
        
        analysis = {}
        
        for db in response['DBInstances']:
            db_id = db['DBInstanceIdentifier']
            instance_class = db['DBInstanceClass']
            
            analysis[db_id] = {
                'instance_class': instance_class,
                'engine': db['Engine'],
                'multi_az': db['MultiAZ'],
                'storage_gb': db['AllocatedStorage'],
                'recommendations': self._get_db_recommendations(db)
            }
        
        return analysis
    
    def optimize_rds_instance(self, db_instance_id):
        """Optimize RDS instance"""
        db = self.rds_client.describe_db_instances(
            DBInstanceIdentifier=db_instance_id
        )['DBInstances'][0]
        
        if db['MultiAZ'] and not self._is_production(db_instance_id):
            logger.info(f"Disabling Multi-AZ for {db_instance_id}")
            self.rds_client.modify_db_instance(
                DBInstanceIdentifier=db_instance_id,
                MultiAZ=False,
                ApplyImmediately=False
            )
    
    def _get_db_recommendations(self, db):
        """Get recommendations for database"""
        recommendations = []
        
        if db['MultiAZ']:
            recommendations.append('Consider disabling Multi-AZ for non-production')
        
        if db['DBInstanceClass'] in ['db.t3.2xlarge', 'db.t3.xlarge']:
            recommendations.append('Consider downsizing instance class')
        
        if db['AllocatedStorage'] > 100:
            recommendations.append('Review storage allocation')
        
        return recommendations
    
    def _is_production(self, db_instance_id):
        """Check if database is production"""
        return 'prod' in db_instance_id.lower()
```

---

## 5. Network Cost Optimization

### Data Transfer Optimization

```python
# src/network_cost_optimization.py

import boto3
from datetime import datetime, timedelta
from src.logger import get_logger

logger = get_logger(__name__)

class NetworkCostOptimization:
    """Optimize network costs"""
    
    def __init__(self):
        self.ec2_client = boto3.client('ec2')
        self.cloudwatch = boto3.client('cloudwatch')
    
    def analyze_data_transfer_costs(self):
        """Analyze data transfer costs"""
        response = self.ec2_client.describe_instances(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
        )
        
        analysis = {}
        
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                network_out = self._get_metric(instance_id, 'NetworkOut')
                cost = (network_out / (1024**3)) * 0.09
                
                analysis[instance_id] = {
                    'network_out_gb': network_out / (1024**3),
                    'estimated_monthly_cost': cost * 30,
                    'recommendations': self._get_network_recommendations(instance_id)
                }
        
        return analysis
    
    def enable_cloudfront_caching(self):
        """Enable CloudFront for cost savings"""
        logger.info("CloudFront reduces data transfer costs by 77%")
        logger.info("Recommended: Use CloudFront for static content")
    
    def _get_metric(self, instance_id, metric_name):
        """Get CloudWatch metric"""
        response = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName=metric_name,
            Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
            StartTime=datetime.utcnow() - timedelta(days=30),
            EndTime=datetime.utcnow(),
            Period=86400,
            Statistics=['Sum']
        )
        
        if response['Datapoints']:
            return sum(dp['Sum'] for dp in response['Datapoints'])
        return 0
```

---

## 6. Cost Monitoring Dashboard

### Real-Time Cost Tracking

```python
# src/cost_dashboard.py

from src.cost_analyzer import CostAnalyzer
from src.compute_optimization import ComputeOptimization
from src.storage_optimization import StorageOptimization
from src.database_cost_optimization import DatabaseCostOptimization
from src.network_cost_optimization import NetworkCostOptimization
from src.logger import get_logger

logger = get_logger(__name__)

class CostDashboard:
    """Cost optimization dashboard"""
    
    def __init__(self):
        self.cost_analyzer = CostAnalyzer()
        self.compute = ComputeOptimization()
        self.storage = StorageOptimization()
        self.database = DatabaseCostOptimization()
        self.network = NetworkCostOptimization()
    
    def get_cost_summary(self):
        """Get comprehensive cost summary"""
        return {
            'cost_breakdown': self.cost_analyzer.get_cost_breakdown(),
            'optimization_recommendations': self.cost_analyzer.get_optimization_recommendations(),
            'compute_analysis': self.compute.analyze_instance_sizing(),
            's3_analysis': self.storage.analyze_s3_costs(),
            'rds_analysis': self.database.analyze_rds_costs(),
            'network_analysis': self.network.analyze_data_transfer_costs()
        }
    
    def get_potential_savings(self):
        """Calculate potential savings"""
        recommendations = self.cost_analyzer.get_optimization_recommendations()
        
        total_savings = 0
        for rec in recommendations:
            total_savings += rec.get('potential_savings', 0)
        
        return {
            'total_monthly_savings': total_savings,
            'annual_savings': total_savings * 12,
            'recommendations_count': len(recommendations)
        }
```

---

## 7. Cost Optimization Checklist

- [ ] Analyze current costs
- [ ] Remove unused resources
- [ ] Right-size instances
- [ ] Enable Spot instances (70% savings)
- [ ] Purchase reserved instances (30-40% savings)
- [ ] Enable S3 lifecycle policies
- [ ] Enable S3 Intelligent-Tiering
- [ ] Optimize RDS instances
- [ ] Disable Multi-AZ for non-production
- [ ] Enable CloudFront caching
- [ ] Monitor costs continuously
- [ ] Set up cost alerts
- [ ] Review monthly bills
- [ ] Implement auto-scaling

---

## 8. Estimated Monthly Savings

| Optimization | Current Cost | Optimized Cost | Monthly Savings |
|--------------|--------------|----------------|------------------|
| Compute (Spot) | $100 | $30 | $70 |
| Storage (Lifecycle) | $50 | $15 | $35 |
| Database (Downsize) | $50 | $30 | $20 |
| Network (CloudFront) | $30 | $10 | $20 |
| **Total** | **$230** | **$85** | **$145** |

**Annual Savings: $1,740 (63% reduction)**

---

## Support

- AWS Cost Explorer: https://aws.amazon.com/aws-cost-management/aws-cost-explorer/
- AWS Trusted Advisor: https://aws.amazon.com/premiumsupport/technology/trusted-advisor/
- AWS Compute Optimizer: https://aws.amazon.com/compute-optimizer/
