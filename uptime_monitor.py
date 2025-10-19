"""
Uptime Monitoring Module for Discord Bot
Sends periodic pings to Uptime Kuma PUSH service to monitor bot uptime
"""

import aiohttp
import asyncio
import json
from datetime import datetime
from typing import Optional
import logging

class UptimeMonitor:
    """
    Uptime monitoring class that sends periodic pings to Uptime Kuma PUSH service
    """
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize the uptime monitor"""
        self.config_path = config_path
        self.enabled = False
        self.push_url = None
        self.interval_minutes = 1
        self.timeout_seconds = 30
        self.task = None
        self.running = False
        self.ping_count = 0
        self.last_ping_time = None
        self.last_error = None
        
        # Load configuration
        self._load_config()
    
    def _load_config(self):
        """Load configuration from config.json"""
        try:
            with open(self.config_path, "r") as file:
                config = json.load(file)
                monitoring_config = config.get("uptime_monitoring", {})
                
                self.enabled = monitoring_config.get("enabled", False)
                self.push_url = monitoring_config.get("push_url", "")
                self.interval_minutes = monitoring_config.get("interval_minutes", 1)
                self.timeout_seconds = monitoring_config.get("timeout_seconds", 30)
                
                # Validate configuration
                if self.enabled and not self.push_url:
                    print("⚠️ Uptime monitoring is enabled but no push URL configured")
                    self.enabled = False
                elif self.enabled and "YOUR_PUSH_KEY" in self.push_url:
                    print("⚠️ Uptime monitoring is enabled but push URL contains placeholder")
                    self.enabled = False
                    
        except Exception as e:
            print(f"Error loading uptime monitoring config: {e}")
            self.enabled = False
    
    async def start_monitoring(self):
        """Start the uptime monitoring task"""
        if not self.enabled:
            print("📊 Uptime monitoring is disabled")
            return
        
        if self.running:
            print("📊 Uptime monitoring is already running")
            return
        
        print(f"📊 Starting uptime monitoring - pinging every {self.interval_minutes} minute(s)")
        print(f"📊 Push URL: {self.push_url[:50]}{'...' if len(self.push_url) > 50 else ''}")
        
        self.running = True
        self.task = asyncio.create_task(self._monitoring_loop())
    
    async def stop_monitoring(self):
        """Stop the uptime monitoring task"""
        if not self.running:
            return
        
        print("📊 Stopping uptime monitoring...")
        self.running = False
        
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        print(f"📊 Uptime monitoring stopped after {self.ping_count} pings")
    
    async def _monitoring_loop(self):
        """Main monitoring loop that sends periodic pings"""
        try:
            while self.running:
                await self._send_ping()
                await asyncio.sleep(self.interval_minutes * 60)  # Convert minutes to seconds
        except asyncio.CancelledError:
            print("📊 Uptime monitoring task cancelled")
        except Exception as e:
            print(f"📊 Uptime monitoring loop error: {e}")
            self.last_error = str(e)
    
    async def _send_ping(self):
        """Send a single ping to the uptime monitoring service"""
        if not self.enabled or not self.push_url:
            return
        
        try:
            async with aiohttp.ClientSession() as session:
                # Send GET request to push URL
                async with session.get(
                    self.push_url,
                    timeout=aiohttp.ClientTimeout(total=self.timeout_seconds)
                ) as response:
                    
                    self.ping_count += 1
                    self.last_ping_time = datetime.now()
                    
                    if response.status == 200:
                        response_text = await response.text()
                        if self.ping_count % 10 == 0:  # Log every 10th ping to avoid spam
                            print(f"📊 Uptime ping #{self.ping_count} successful: {response_text.strip()}")
                    else:
                        error_msg = f"HTTP {response.status}"
                        print(f"📊 Uptime ping #{self.ping_count} failed: {error_msg}")
                        self.last_error = error_msg
                        
        except asyncio.TimeoutError:
            self.ping_count += 1
            error_msg = f"Timeout after {self.timeout_seconds}s"
            print(f"📊 Uptime ping #{self.ping_count} failed: {error_msg}")
            self.last_error = error_msg
            
        except aiohttp.ClientError as e:
            self.ping_count += 1
            error_msg = f"Network error: {str(e)}"
            print(f"📊 Uptime ping #{self.ping_count} failed: {error_msg}")
            self.last_error = error_msg
            
        except Exception as e:
            self.ping_count += 1
            error_msg = f"Unexpected error: {str(e)}"
            print(f"📊 Uptime ping #{self.ping_count} failed: {error_msg}")
            self.last_error = error_msg
    
    def get_status(self) -> dict:
        """Get current monitoring status"""
        return {
            "enabled": self.enabled,
            "running": self.running,
            "ping_count": self.ping_count,
            "last_ping_time": self.last_ping_time.isoformat() if self.last_ping_time else None,
            "last_error": self.last_error,
            "interval_minutes": self.interval_minutes,
            "push_url_configured": bool(self.push_url and "YOUR_PUSH_KEY" not in self.push_url)
        }
    
    def reload_config(self):
        """Reload configuration from file"""
        old_enabled = self.enabled
        self._load_config()
        
        if old_enabled != self.enabled:
            print(f"📊 Uptime monitoring config changed: enabled={self.enabled}")
        
        return self.enabled


# Global instance
uptime_monitor = UptimeMonitor()


async def test_uptime_monitor():
    """Test function for the uptime monitor"""
    print("Testing Uptime Monitor...")
    
    monitor = UptimeMonitor()
    status = monitor.get_status()
    
    print(f"Enabled: {status['enabled']}")
    print(f"Push URL configured: {status['push_url_configured']}")
    print(f"Interval: {status['interval_minutes']} minutes")
    
    if status['enabled'] and status['push_url_configured']:
        print("Sending test ping...")
        await monitor._send_ping()
        print(f"Test ping sent. Count: {monitor.ping_count}")
    else:
        print("Uptime monitoring not properly configured")


if __name__ == "__main__":
    # Run test if this file is executed directly
    asyncio.run(test_uptime_monitor())