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
        self.session = None  # Persistent aiohttp session
        self.session_reconnects = 0  # Track session reconnections
        
        # Load configuration
        self._load_config()
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        if self.session and not self.session.closed:
            # Note: We can't use await in __del__, so we schedule the cleanup
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self._close_session())
            except:
                pass  # Ignore errors during cleanup
    
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
        
        # Create persistent session
        await self._create_session()
        
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
        
        # Close persistent session
        await self._close_session()
        
        print(f"📊 Uptime monitoring stopped after {self.ping_count} pings")
    
    async def _create_session(self):
        """Create a new aiohttp session"""
        if self.session and not self.session.closed:
            await self._close_session()
        
        try:
            # Create session with optimized settings for uptime monitoring
            timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)
            connector = aiohttp.TCPConnector(
                limit=2,  # Limit connections since we only need one
                ttl_dns_cache=300,  # DNS cache for 5 minutes
                use_dns_cache=True,
                keepalive_timeout=60,
                enable_cleanup_closed=True
            )
            
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers={
                    'User-Agent': 'Discord-Bot-Uptime-Monitor/1.0'
                }
            )
            
            if self.session_reconnects > 0:
                print(f"📊 Created new HTTP session (reconnection #{self.session_reconnects})")
            
        except Exception as e:
            print(f"📊 Failed to create HTTP session: {e}")
            self.session = None
    
    async def _close_session(self):
        """Close the current aiohttp session"""
        if self.session and not self.session.closed:
            try:
                await self.session.close()
            except Exception as e:
                print(f"📊 Error closing HTTP session: {e}")
            finally:
                self.session = None
    
    async def _ensure_session(self):
        """Ensure we have a valid session, create new one if needed"""
        if not self.session or self.session.closed:
            self.session_reconnects += 1
            await self._create_session()
            return True  # Session was recreated
        return False  # Session was already valid
    
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
        
        # Ensure we have a valid session
        session_recreated = await self._ensure_session()
        
        if not self.session:
            self.ping_count += 1
            error_msg = "No HTTP session available"
            print(f"📊 Uptime ping #{self.ping_count} failed: {error_msg}")
            self.last_error = error_msg
            return
        
        try:
            # Send GET request to push URL using persistent session
            async with self.session.get(self.push_url) as response:
                self.ping_count += 1
                self.last_ping_time = datetime.now()
                
                if response.status == 200:
                    response_text = await response.text()
                    # Log every 10th ping or when session was recreated
                    if self.ping_count % 10 == 0 or session_recreated:
                        reconnect_info = f" (after reconnect #{self.session_reconnects})" if session_recreated else ""
                        print(f"📊 Uptime ping #{self.ping_count} successful{reconnect_info}: {response_text.strip()}")
                    self.last_error = None  # Clear error on success
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
            
            # If it's a connection error, mark session for recreation
            if isinstance(e, (aiohttp.ClientConnectionError, aiohttp.ClientConnectorError)):
                print(f"📊 Connection error detected, will recreate session on next ping")
                await self._close_session()
            
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
            "push_url_configured": bool(self.push_url and "YOUR_PUSH_KEY" not in self.push_url),
            "session_active": bool(self.session and not self.session.closed),
            "session_reconnects": self.session_reconnects
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
    print(f"Session active: {status['session_active']}")
    
    if status['enabled'] and status['push_url_configured']:
        print("Creating session and sending test ping...")
        await monitor._create_session()
        
        print(f"Session created: {monitor.session is not None}")
        
        await monitor._send_ping()
        print(f"Test ping sent. Count: {monitor.ping_count}")
        print(f"Reconnects: {monitor.session_reconnects}")
        
        # Clean up
        await monitor._close_session()
        print("Session closed")
    else:
        print("Uptime monitoring not properly configured")


if __name__ == "__main__":
    # Run test if this file is executed directly
    asyncio.run(test_uptime_monitor())