#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Optimization recommendations based on performance metrics
"""

import json
from typing import Dict, List

class OptimizationAnalyzer:
    def __init__(self):
        self.recommendations = []
    
    def analyze_response_times(self, metrics: Dict) -> List[str]:
        """Analyze response time metrics"""
        recommendations = []
        
        avg_time = metrics.get('avg', 0)
        p95_time = metrics.get('p95', 0)
        p99_time = metrics.get('p99', 0)
        
        if avg_time > 0.5:
            recommendations.append(
                "Average response time > 500ms. Consider:"
                "\n  - Enable caching"
                "\n  - Optimize database queries"
                "\n  - Use async operations"
            )
        
        if p95_time > 1.0:
            recommendations.append(
                "P95 response time > 1s. Consider:"
                "\n  - Identify slow endpoints"
                "\n  - Add database indexes"
                "\n  - Implement pagination"
            )
        
        if p99_time > 2.0:
            recommendations.append(
                "P99 response time > 2s. Consider:"
                "\n  - Profile slow operations"
                "\n  - Optimize algorithms"
                "\n  - Scale infrastructure"
            )
        
        return recommendations
    
    def analyze_error_rate(self, error_rate: float) -> List[str]:
        """Analyze error rate"""
        recommendations = []
        
        if error_rate > 0.01:
            recommendations.append(
                "Error rate > 1%. Consider:"
                "\n  - Review error logs"
                "\n  - Fix failing endpoints"
                "\n  - Improve error handling"
            )
        
        if error_rate > 0.001:
            recommendations.append(
                "Error rate > 0.1%. Consider:"
                "\n  - Monitor error trends"
                "\n  - Setup alerts"
                "\n  - Improve reliability"
            )
        
        return recommendations
    
    def analyze_resource_usage(self, resources: Dict) -> List[str]:
        """Analyze resource usage"""
        recommendations = []
        
        cpu = resources.get('cpu', 0)
        memory = resources.get('memory', 0)
        disk = resources.get('disk', 0)
        
        if cpu > 0.7:
            recommendations.append(
                "CPU usage > 70%. Consider:"
                "\n  - Optimize algorithms"
                "\n  - Use caching"
                "\n  - Scale horizontally"
            )
        
        if memory > 0.8:
            recommendations.append(
                "Memory usage > 80%. Consider:"
                "\n  - Profile memory leaks"
                "\n  - Optimize data structures"
                "\n  - Increase memory"
            )
        
        if disk > 0.8:
            recommendations.append(
                "Disk usage > 80%. Consider:"
                "\n  - Archive old data"
                "\n  - Cleanup logs"
                "\n  - Increase disk space"
            )
        
        return recommendations
    
    def generate_report(self, metrics: Dict) -> str:
        """Generate optimization report"""
        report = "\n" + "="*50
        report += "\nOptimization Report\n"
        report += "="*50 + "\n\n"
        
        # Response time analysis
        report += "Response Time Analysis:\n"
        for rec in self.analyze_response_times(metrics):
            report += f"  - {rec}\n"
        
        # Error rate analysis
        report += "\nError Rate Analysis:\n"
        error_rate = metrics.get('error_rate', 0)
        for rec in self.analyze_error_rate(error_rate):
            report += f"  - {rec}\n"
        
        # Resource usage analysis
        report += "\nResource Usage Analysis:\n"
        resources = metrics.get('resources', {})
        for rec in self.analyze_resource_usage(resources):
            report += f"  - {rec}\n"
        
        report += "\n" + "="*50 + "\n"
        return report

if __name__ == "__main__":
    # Example usage
    metrics = {
        'avg': 0.45,
        'p95': 0.8,
        'p99': 1.5,
        'error_rate': 0.0005,
        'resources': {
            'cpu': 0.65,
            'memory': 0.75,
            'disk': 0.60
        }
    }
    
    analyzer = OptimizationAnalyzer()
    report = analyzer.generate_report(metrics)
    print(report)
