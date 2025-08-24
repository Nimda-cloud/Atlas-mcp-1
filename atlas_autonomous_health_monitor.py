#!/usr/bin/env python3
"""
Atlas Autonomous Health Monitor
Comprehensive health monitoring for the autonomous Atlas system
"""

import requests
import time
import json
import subprocess
import sys
from datetime import datetime

class AtlasHealthMonitor:
    def __init__(self):
        self.services = {
            'atlas-core': 'http://localhost:8000/status',
            'atlas-frontend': 'http://localhost:8080/health',
            'mcp-automation': 'http://localhost:4002/health',
            'mcp-automator': 'http://localhost:4003/health',
            'mcp-tts': 'http://localhost:4004/health',
            'mcp-playwright': 'http://localhost:4005/health'
        }
        
    def check_service(self, name, url, timeout=10):
        """Check individual service health"""
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                return {'status': 'healthy', 'response_time': response.elapsed.total_seconds()}
            else:
                return {'status': 'unhealthy', 'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'status': 'unreachable', 'error': str(e)}
            
    def monitor_system(self, duration_minutes=5):
        """Monitor system health for specified duration"""
        print(f"🔍 Starting Atlas health monitoring for {duration_minutes} minutes...")
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        while time.time() < end_time:
            timestamp = datetime.now().isoformat()
            health_report = {'timestamp': timestamp, 'services': {}}
            
            for service_name, service_url in self.services.items():
                health = self.check_service(service_name, service_url)
                health_report['services'][service_name] = health
                
                status_icon = '✅' if health['status'] == 'healthy' else '❌'
                print(f"{status_icon} {service_name}: {health['status']}")
                
            # Check Docker containers
            try:
                result = subprocess.run(['docker', 'ps', '--format', 'json'], 
                                     capture_output=True, text=True)
                if result.returncode == 0:
                    containers = [json.loads(line) for line in result.stdout.strip().split('\n') if line]
                    atlas_containers = [c for c in containers if 'atlas' in c.get('Names', '').lower()]
                    health_report['docker_containers'] = len(atlas_containers)
                    print(f"🐳 Docker containers running: {len(atlas_containers)}")
            except Exception as e:
                health_report['docker_error'] = str(e)
                
            time.sleep(30)  # Check every 30 seconds
            
        print("✅ Health monitoring completed")
        return True

if __name__ == "__main__":
    monitor = AtlasHealthMonitor()
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    monitor.monitor_system(duration)
