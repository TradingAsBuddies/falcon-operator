#!/usr/bin/env python3
"""
Security tests for Falcon services.

Verifies that services follow security best practices:
- No services run as root
- Proper file permissions
- Privilege separation
"""

import subprocess
import unittest
from pathlib import Path


class TestPrivilegeSeparation(unittest.TestCase):
    """Test that services don't run as root."""

    FALCON_SERVICES = [
        'falcon-trader',
        'falcon-feedback-loop',
        'falcon-canary',
        'falcon-screener@morning',
        'falcon-screener@midday',
        'falcon-screener@evening',
    ]

    def test_no_services_run_as_root(self):
        """Verify no falcon services are configured to run as root."""
        services_as_root = []

        for service in self.FALCON_SERVICES:
            service_file = f'/etc/systemd/system/{service.replace("@", "@.")}.service'
            if '@' in service:
                # Template service
                service_file = f'/etc/systemd/system/{service.split("@")[0]}@.service'

            try:
                result = subprocess.run(
                    ['systemctl', 'show', service, '--property=User'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                user = result.stdout.strip().split('=')[1] if '=' in result.stdout else ''

                if user == 'root' or user == '':
                    # Check the service file directly
                    try:
                        with open(service_file) as f:
                            content = f.read()
                            if 'User=root' in content:
                                services_as_root.append(service)
                            elif 'User=' not in content:
                                # No User= specified, defaults to root
                                services_as_root.append(f"{service} (no User= specified)")
                    except FileNotFoundError:
                        pass  # Service file doesn't exist on this system

            except subprocess.TimeoutExpired:
                pass
            except Exception as e:
                pass  # Service might not be installed

        self.assertEqual(
            services_as_root,
            [],
            f"Services running as root (security violation): {services_as_root}"
        )

    def test_canary_has_sudoers_file(self):
        """Verify falcon-canary has a sudoers file for privileged operations."""
        sudoers_file = Path('/etc/sudoers.d/falcon-canary')

        if not sudoers_file.exists():
            self.skipTest("Sudoers file not found - may not be installed on this system")

        # Read with sudo since sudoers files are protected
        try:
            result = subprocess.run(
                ['sudo', 'cat', str(sudoers_file)],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                self.skipTest("Cannot read sudoers file (sudo required)")
            content = result.stdout
        except (subprocess.TimeoutExpired, PermissionError):
            self.skipTest("Cannot read sudoers file (sudo required)")

        # Check for required sudo permissions
        required_permissions = [
            'systemctl restart falcon-',
            'systemctl restart networking',
            'ip link set',
            'dhclient',
        ]

        for perm in required_permissions:
            self.assertIn(
                perm,
                content,
                f"Missing sudo permission for: {perm}"
            )

    def test_sudoers_file_permissions(self):
        """Verify sudoers file has correct permissions (440)."""
        sudoers_file = Path('/etc/sudoers.d/falcon-canary')

        if not sudoers_file.exists():
            self.skipTest("Sudoers file not found")

        mode = sudoers_file.stat().st_mode & 0o777
        self.assertEqual(
            mode,
            0o440,
            f"Sudoers file has wrong permissions: {oct(mode)} (expected 0o440)"
        )


class TestFilePermissions(unittest.TestCase):
    """Test file and directory permissions."""

    def test_env_files_not_world_readable(self):
        """Verify .env files are not world-readable."""
        env_files = [
            '/etc/falcon/falcon.env',
            '/etc/falcon/secrets.env',
        ]

        for env_file in env_files:
            path = Path(env_file)
            if not path.exists():
                continue

            mode = path.stat().st_mode & 0o777
            world_readable = mode & 0o004

            self.assertFalse(
                world_readable,
                f"{env_file} is world-readable (mode: {oct(mode)})"
            )

    def test_state_files_owned_by_falcon(self):
        """Verify state files are owned by falcon user."""
        state_files = [
            '/var/lib/falcon/canary_state.json',
            '/var/lib/falcon/paper_trading.db',
        ]

        for state_file in state_files:
            path = Path(state_file)
            if not path.exists():
                continue

            import pwd
            owner = pwd.getpwuid(path.stat().st_uid).pw_name

            self.assertEqual(
                owner,
                'falcon',
                f"{state_file} is owned by {owner}, not falcon"
            )


class TestServiceHardening(unittest.TestCase):
    """Test systemd service hardening options."""

    def test_services_have_memory_limits(self):
        """Verify services have MemoryMax limits."""
        services = ['falcon-trader', 'falcon-canary', 'falcon-feedback-loop']

        for service in services:
            try:
                result = subprocess.run(
                    ['systemctl', 'show', service, '--property=MemoryMax'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                memory_max = result.stdout.strip().split('=')[1] if '=' in result.stdout else ''

                # MemoryMax should be set (not infinity)
                if memory_max and memory_max != 'infinity' and memory_max != '':
                    continue  # Has a limit

                # Check service file directly
                service_file = f'/etc/systemd/system/{service}.service'
                try:
                    with open(service_file) as f:
                        if 'MemoryMax=' in f.read():
                            continue  # Has a limit in file
                except FileNotFoundError:
                    continue  # Service not installed

                self.fail(f"{service} has no MemoryMax limit")

            except subprocess.TimeoutExpired:
                pass
            except Exception:
                pass  # Service might not be installed


if __name__ == '__main__':
    unittest.main()
