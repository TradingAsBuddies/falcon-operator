#!/usr/bin/env python3
"""
Falcon Canary - Health Monitoring and Auto-Recovery System

Monitors service health, network connectivity, and can automatically
restart services or repair IP configurations when issues are detected.

Usage:
    python3 canary.py                    # Run once (for cron/systemd timer)
    python3 canary.py --daemon           # Run continuously
    python3 canary.py --check-only       # Check only, no repairs
    python3 canary.py --status           # Show current status
"""

import os
import sys
import time
import json
import socket
import logging
import argparse
import subprocess
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/var/log/falcon/canary.log', mode='a')
    ] if os.path.exists('/var/log/falcon') else [logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Configuration
CONFIG = {
    # Check intervals (seconds)
    'check_interval': 60,
    'network_check_interval': 30,

    # Thresholds
    'max_restart_attempts': 3,
    'restart_cooldown': 300,  # 5 minutes between restart attempts
    'consecutive_failures_alert': 3,

    # Services to monitor
    'services': [
        'falcon-trader',
        'falcon-feedback-loop',
    ],

    # Health endpoints (empty if no HTTP services to check)
    'health_endpoints': [],

    # Web endpoints to verify (host, port, path, expected_status)
    'web_endpoints': [
        ('192.168.1.162', 443, '/health', 200),
        ('192.168.1.162', 443, '/strategies', 200),
        ('192.168.1.162', 443, '/strategies.html', 200),
        ('192.168.1.162', 443, '/orchestrator', 200),
        ('192.168.1.162', 443, '/orchestrator.html', 200),
        ('192.168.1.162', 443, '/api/account', 200),
        ('192.168.1.162', 443, '/api/positions', 200),
        ('192.168.1.162', 443, '/api/recommendations', 200),
        ('192.168.1.162', 443, '/api/trades/summary', 200),
        ('192.168.1.162', 443, '/api/bot/status', 200),
    ],

    # Network targets for connectivity checks
    'network_targets': [
        ('8.8.8.8', 53),        # Google DNS
        ('1.1.1.1', 53),        # Cloudflare DNS
    ],

    # Expected network interface and IP (set via environment or config file)
    # Auto-detect: tries common interfaces if not specified
    'expected_interface': os.getenv('FALCON_NETWORK_INTERFACE', ''),
    'expected_ip_prefix': os.getenv('FALCON_EXPECTED_IP_PREFIX', '192.168.'),

    # State file for tracking
    'state_file': '/var/lib/falcon/canary_state.json',

    # Alert command (optional - e.g., send notification)
    'alert_command': os.getenv('FALCON_ALERT_COMMAND', ''),
}


@dataclass
class ServiceState:
    """Track state for a single service"""
    name: str
    last_check: str = ''
    is_healthy: bool = True
    consecutive_failures: int = 0
    last_restart: str = ''
    restart_count: int = 0
    last_error: str = ''


@dataclass
class CanaryState:
    """Overall canary state"""
    last_run: str = ''
    services: Dict[str, dict] = field(default_factory=dict)
    network_healthy: bool = True
    network_failures: int = 0
    last_network_repair: str = ''
    ip_address: str = ''
    alerts_sent: int = 0

    def get_service(self, name: str) -> ServiceState:
        if name not in self.services:
            self.services[name] = asdict(ServiceState(name=name))
        return ServiceState(**self.services[name])

    def set_service(self, state: ServiceState):
        self.services[state.name] = asdict(state)


class FalconCanary:
    """Health monitoring and auto-recovery for Falcon services"""

    def __init__(self, config: dict = None):
        self.config = config or CONFIG
        self.state = self._load_state()

    def _load_state(self) -> CanaryState:
        """Load persisted state from file"""
        state_file = Path(self.config['state_file'])
        if state_file.exists():
            try:
                with open(state_file) as f:
                    data = json.load(f)
                return CanaryState(**data)
            except Exception as e:
                logger.warning(f"Could not load state file: {e}")
        return CanaryState()

    def _save_state(self):
        """Persist state to file"""
        state_file = Path(self.config['state_file'])
        state_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(state_file, 'w') as f:
                json.dump(asdict(self.state), f, indent=2)
        except Exception as e:
            logger.error(f"Could not save state file: {e}")

    def _run_command(self, cmd: List[str], timeout: int = 30) -> Tuple[bool, str]:
        """Run a shell command and return success status and output"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)

    def _send_alert(self, message: str, severity: str = 'warning'):
        """Send alert notification"""
        logger.log(
            logging.ERROR if severity == 'critical' else logging.WARNING,
            f"ALERT [{severity.upper()}]: {message}"
        )

        self.state.alerts_sent += 1

        # Run custom alert command if configured
        alert_cmd = self.config.get('alert_command')
        if alert_cmd:
            try:
                subprocess.run(
                    [alert_cmd, severity, message],
                    timeout=10,
                    capture_output=True
                )
            except Exception as e:
                logger.error(f"Alert command failed: {e}")

    # -------------------------------------------------------------------------
    # Network Checks
    # -------------------------------------------------------------------------

    def check_network_connectivity(self) -> bool:
        """Check if we have network connectivity"""
        for host, port in self.config['network_targets']:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((host, port))
                sock.close()
                if result == 0:
                    return True
            except Exception:
                continue
        return False

    def get_current_ip(self, interface: str = None) -> Optional[str]:
        """Get current IP address for interface (auto-detects if not specified)"""
        interface = interface or self.config['expected_interface']

        # If interface specified, use it directly
        if interface:
            interfaces = [interface]
        else:
            # Auto-detect: try common interfaces
            interfaces = ['eth0', 'wlan0', 'enp0s3', 'ens3', 'ens192']

        for iface in interfaces:
            try:
                success, output = self._run_command(['ip', 'addr', 'show', iface])
                logger.debug(f"Interface {iface}: success={success}, output_len={len(output)}")
                if success:
                    for line in output.split('\n'):
                        if 'inet ' in line and 'inet6' not in line:
                            # Extract IP: "inet 192.168.1.100/24 ..."
                            parts = line.strip().split()
                            if len(parts) >= 2:
                                ip = parts[1].split('/')[0]
                                logger.debug(f"Found IP {ip} on {iface}")
                                # Skip localhost and docker IPs
                                if not ip.startswith('127.') and not ip.startswith('172.'):
                                    return ip
            except Exception as e:
                logger.debug(f"Interface {iface} error: {e}")
                continue

        logger.error("Could not get IP address from any interface")
        return None

    def check_ip_configuration(self) -> Tuple[bool, str]:
        """Check if IP configuration is correct"""
        current_ip = self.get_current_ip()
        self.state.ip_address = current_ip or ''

        if not current_ip:
            return False, "No IP address found"

        expected_prefix = self.config['expected_ip_prefix']
        if expected_prefix and not current_ip.startswith(expected_prefix):
            return False, f"IP {current_ip} does not match expected prefix {expected_prefix}"

        return True, current_ip

    def _detect_active_interface(self) -> str:
        """Detect the active network interface"""
        # Check configured interface first
        if self.config['expected_interface']:
            return self.config['expected_interface']

        # Try to find an active interface
        for iface in ['wlan0', 'eth0', 'enp0s3', 'ens3', 'ens192']:
            success, output = self._run_command(['ip', 'link', 'show', iface])
            if success and 'UP' in output:
                return iface

        # Fallback to eth0
        return 'eth0'

    def repair_network(self) -> bool:
        """Attempt to repair network configuration"""
        logger.info("Attempting network repair...")

        interface = self._detect_active_interface()
        logger.info(f"Using interface: {interface}")
        repairs_attempted = []

        # Step 1: Bring interface down and up
        logger.info(f"Restarting interface {interface}...")
        self._run_command(['sudo', 'ip', 'link', 'set', interface, 'down'])
        time.sleep(2)
        self._run_command(['sudo', 'ip', 'link', 'set', interface, 'up'])
        time.sleep(5)
        repairs_attempted.append('interface_restart')

        # Check if that helped
        if self.check_network_connectivity():
            logger.info("Network restored after interface restart")
            return True

        # Step 2: Request new DHCP lease
        logger.info("Requesting new DHCP lease...")
        # Try dhclient
        success, _ = self._run_command(['sudo', 'dhclient', '-r', interface], timeout=10)
        time.sleep(1)
        success, _ = self._run_command(['sudo', 'dhclient', interface], timeout=30)
        repairs_attempted.append('dhcp_renew')

        time.sleep(5)
        if self.check_network_connectivity():
            logger.info("Network restored after DHCP renewal")
            return True

        # Step 3: Try NetworkManager if available
        success, _ = self._run_command(['which', 'nmcli'])
        if success:
            logger.info("Restarting NetworkManager connection...")
            self._run_command(['sudo', 'nmcli', 'connection', 'down', interface])
            time.sleep(2)
            self._run_command(['sudo', 'nmcli', 'connection', 'up', interface])
            repairs_attempted.append('networkmanager_restart')

            time.sleep(5)
            if self.check_network_connectivity():
                logger.info("Network restored via NetworkManager")
                return True

        # Step 4: Restart networking service
        logger.info("Restarting networking service...")
        self._run_command(['sudo', 'systemctl', 'restart', 'networking'], timeout=60)
        repairs_attempted.append('networking_service_restart')

        time.sleep(10)
        if self.check_network_connectivity():
            logger.info("Network restored after networking service restart")
            return True

        logger.error(f"Network repair failed. Attempted: {repairs_attempted}")
        return False

    # -------------------------------------------------------------------------
    # Service Checks
    # -------------------------------------------------------------------------

    def check_service_status(self, service: str) -> Tuple[bool, str]:
        """Check if a systemd service is running"""
        success, output = self._run_command(['systemctl', 'is-active', service])
        is_active = 'active' in output.strip().lower() and 'inactive' not in output.strip().lower()
        return is_active, output.strip()

    def check_service_health(self, service: str) -> Tuple[bool, str]:
        """Check service health including endpoint checks"""
        # First check systemd status
        is_running, status = self.check_service_status(service)
        if not is_running:
            return False, f"Service not running: {status}"

        # For services with HTTP endpoints, also check those
        for host, port, path in self.config.get('health_endpoints', []):
            if service in path or (service == 'falcon-dashboard' and port == 5000):
                try:
                    import urllib.request
                    url = f'http://{host}:{port}{path}'
                    req = urllib.request.Request(url, method='GET')
                    with urllib.request.urlopen(req, timeout=10) as response:
                        if response.status == 200:
                            return True, "healthy"
                        return False, f"Health endpoint returned {response.status}"
                except Exception as e:
                    return False, f"Health endpoint unreachable: {e}"

        return True, status

    def check_web_endpoints(self) -> Dict[str, dict]:
        """Check configured web endpoints are accessible"""
        import ssl
        import urllib.request

        results = {}
        # Create SSL context that doesn't verify certificates (for self-signed)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        for endpoint in self.config.get('web_endpoints', []):
            host, port, path, expected_status = endpoint
            url = f"https://{host}:{port}{path}" if port == 443 else f"http://{host}:{port}{path}"

            try:
                req = urllib.request.Request(url, method='GET')
                req.add_header('User-Agent', 'FalconCanary/1.0')
                with urllib.request.urlopen(req, timeout=10, context=ssl_context) as response:
                    actual_status = response.status
                    healthy = actual_status == expected_status
                    results[f"{host}{path}"] = {
                        'url': url,
                        'healthy': healthy,
                        'status_code': actual_status,
                        'expected': expected_status,
                        'error': None if healthy else f"Expected {expected_status}, got {actual_status}"
                    }
            except Exception as e:
                results[f"{host}{path}"] = {
                    'url': url,
                    'healthy': False,
                    'status_code': None,
                    'expected': expected_status,
                    'error': str(e)
                }
                logger.warning(f"Web endpoint {url} check failed: {e}")

        return results

    def restart_service(self, service: str) -> bool:
        """Restart a systemd service"""
        logger.info(f"Restarting service: {service}")
        success, output = self._run_command(['sudo', 'systemctl', 'restart', service], timeout=60)

        if success:
            # Wait for service to start
            time.sleep(5)
            is_running, _ = self.check_service_status(service)
            if is_running:
                logger.info(f"Service {service} restarted successfully")
                return True
            logger.error(f"Service {service} failed to start after restart")
        else:
            logger.error(f"Failed to restart {service}: {output}")

        return False

    def check_and_repair_service(self, service: str, repair: bool = True) -> bool:
        """Check service health and optionally repair"""
        svc_state = self.state.get_service(service)
        svc_state.last_check = datetime.now().isoformat()

        is_healthy, message = self.check_service_health(service)

        if is_healthy:
            svc_state.is_healthy = True
            svc_state.consecutive_failures = 0
            svc_state.last_error = ''
            self.state.set_service(svc_state)
            return True

        # Service is unhealthy
        svc_state.is_healthy = False
        svc_state.consecutive_failures += 1
        svc_state.last_error = message
        logger.warning(f"Service {service} unhealthy: {message} (failures: {svc_state.consecutive_failures})")

        # Check if we should attempt repair
        if repair and svc_state.consecutive_failures >= 2:
            # Check cooldown
            if svc_state.last_restart:
                last_restart = datetime.fromisoformat(svc_state.last_restart)
                cooldown = timedelta(seconds=self.config['restart_cooldown'])
                if datetime.now() - last_restart < cooldown:
                    logger.info(f"Service {service} in restart cooldown, skipping")
                    self.state.set_service(svc_state)
                    return False

            # Check max attempts
            if svc_state.restart_count >= self.config['max_restart_attempts']:
                if svc_state.consecutive_failures == self.config['consecutive_failures_alert']:
                    self._send_alert(
                        f"Service {service} failed {svc_state.consecutive_failures} times, "
                        f"max restart attempts ({svc_state.restart_count}) exceeded",
                        'critical'
                    )
                self.state.set_service(svc_state)
                return False

            # Attempt restart
            if self.restart_service(service):
                svc_state.last_restart = datetime.now().isoformat()
                svc_state.restart_count += 1
                svc_state.consecutive_failures = 0
                svc_state.is_healthy = True
                self.state.set_service(svc_state)
                return True
            else:
                svc_state.restart_count += 1
                self._send_alert(f"Failed to restart service {service}", 'warning')

        self.state.set_service(svc_state)
        return False

    # -------------------------------------------------------------------------
    # Main Check Loop
    # -------------------------------------------------------------------------

    def run_checks(self, repair: bool = True) -> dict:
        """Run all health checks"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'network': {'healthy': False, 'ip': ''},
            'services': {},
            'web_endpoints': {},
            'repairs_attempted': [],
            'overall_healthy': True,
        }

        # Network checks
        logger.info("Checking network connectivity...")
        network_ok = self.check_network_connectivity()
        ip_ok, ip_info = self.check_ip_configuration()

        results['network']['healthy'] = network_ok and ip_ok
        results['network']['ip'] = self.state.ip_address
        results['network']['connectivity'] = network_ok
        results['network']['ip_valid'] = ip_ok

        if not network_ok:
            self.state.network_healthy = False
            self.state.network_failures += 1
            results['overall_healthy'] = False
            logger.error("Network connectivity check failed")

            if repair and self.state.network_failures >= 2:
                # Check cooldown
                should_repair = True
                if self.state.last_network_repair:
                    last_repair = datetime.fromisoformat(self.state.last_network_repair)
                    if datetime.now() - last_repair < timedelta(seconds=self.config['restart_cooldown']):
                        should_repair = False
                        logger.info("Network repair in cooldown")

                if should_repair:
                    results['repairs_attempted'].append('network')
                    if self.repair_network():
                        self.state.last_network_repair = datetime.now().isoformat()
                        self.state.network_failures = 0
                        results['network']['healthy'] = True
                    else:
                        self._send_alert("Network repair failed", 'critical')
        else:
            self.state.network_healthy = True
            self.state.network_failures = 0

        # Service checks (only if network is up)
        if network_ok:
            logger.info("Checking services...")
            for service in self.config['services']:
                healthy = self.check_and_repair_service(service, repair=repair)
                svc_state = self.state.get_service(service)
                results['services'][service] = {
                    'healthy': healthy,
                    'consecutive_failures': svc_state.consecutive_failures,
                    'restart_count': svc_state.restart_count,
                    'last_error': svc_state.last_error,
                }
                if not healthy:
                    results['overall_healthy'] = False

            # Web endpoint checks
            if self.config.get('web_endpoints'):
                logger.info("Checking web endpoints...")
                results['web_endpoints'] = self.check_web_endpoints()
                for endpoint, status in results['web_endpoints'].items():
                    if not status['healthy']:
                        logger.warning(f"Web endpoint unhealthy: {endpoint} - {status['error']}")
                        results['overall_healthy'] = False
        else:
            logger.warning("Skipping service checks - network is down")
            for service in self.config['services']:
                results['services'][service] = {
                    'healthy': False,
                    'skipped': True,
                    'reason': 'network_down'
                }
            results['overall_healthy'] = False

        # Update and save state
        self.state.last_run = results['timestamp']
        self._save_state()

        return results

    def get_status(self) -> dict:
        """Get current status without running checks"""
        return {
            'last_run': self.state.last_run,
            'network_healthy': self.state.network_healthy,
            'ip_address': self.state.ip_address,
            'services': {
                name: self.state.get_service(name).__dict__
                for name in self.config['services']
            },
            'alerts_sent': self.state.alerts_sent,
        }

    def run_daemon(self, interval: int = None):
        """Run continuously as a daemon"""
        interval = interval or self.config['check_interval']
        logger.info(f"Starting canary daemon (interval: {interval}s)")

        while True:
            try:
                results = self.run_checks(repair=True)
                status = "HEALTHY" if results['overall_healthy'] else "DEGRADED"
                logger.info(f"Check complete: {status}")
            except Exception as e:
                logger.error(f"Check failed with error: {e}")

            time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description='Falcon Canary - Health Monitoring')
    parser.add_argument('--daemon', action='store_true', help='Run continuously')
    parser.add_argument('--check-only', action='store_true', help='Check only, no repairs')
    parser.add_argument('--status', action='store_true', help='Show current status')
    parser.add_argument('--interval', type=int, default=60, help='Check interval in seconds')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    args = parser.parse_args()

    canary = FalconCanary()

    if args.status:
        status = canary.get_status()
        if args.json:
            print(json.dumps(status, indent=2))
        else:
            print(f"Last Run: {status['last_run'] or 'Never'}")
            print(f"Network: {'OK' if status['network_healthy'] else 'FAILED'} ({status['ip_address']})")
            print(f"Alerts Sent: {status['alerts_sent']}")
            print("\nServices:")
            for name, svc in status['services'].items():
                health = "OK" if svc['is_healthy'] else "FAILED"
                print(f"  {name}: {health} (restarts: {svc['restart_count']}, failures: {svc['consecutive_failures']})")
        return

    if args.daemon:
        canary.run_daemon(interval=args.interval)
    else:
        results = canary.run_checks(repair=not args.check_only)
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            status = "HEALTHY" if results['overall_healthy'] else "DEGRADED"
            print(f"\n{'='*50}")
            print(f"Falcon Canary Check - {status}")
            print(f"{'='*50}")
            print(f"Time: {results['timestamp']}")
            print(f"\nNetwork:")
            print(f"  Connectivity: {'OK' if results['network']['connectivity'] else 'FAILED'}")
            print(f"  IP Address: {results['network']['ip']} ({'valid' if results['network']['ip_valid'] else 'invalid'})")
            print(f"\nServices:")
            for name, svc in results['services'].items():
                health = "OK" if svc['healthy'] else "FAILED"
                print(f"  {name}: {health}")
                if svc.get('last_error'):
                    print(f"    Error: {svc['last_error']}")
            if results.get('web_endpoints'):
                print(f"\nWeb Endpoints:")
                for endpoint, status in results['web_endpoints'].items():
                    health = "OK" if status['healthy'] else "FAILED"
                    code = status.get('status_code', 'N/A')
                    print(f"  {endpoint}: {health} (HTTP {code})")
                    if status.get('error'):
                        print(f"    Error: {status['error']}")
            if results['repairs_attempted']:
                print(f"\nRepairs Attempted: {', '.join(results['repairs_attempted'])}")
            print(f"{'='*50}\n")

        # Exit with appropriate code
        sys.exit(0 if results['overall_healthy'] else 1)


if __name__ == '__main__':
    main()
