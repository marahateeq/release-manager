#!/usr/bin/env python3
"""
Release Manager
Main orchestrator for release detection and creation
"""

import sys
import os
import argparse
import json
from pathlib import Path
from datetime import datetime

# Check for required dependencies
try:
    import yaml
except ImportError:
    print("❌ Error: PyYAML is not installed")
    print("Please install it with: pip install -r requirements.txt")
    sys.exit(1)

# Add utils directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'utils'))

from manifest_helper import ManifestHelper
from version_manager import VersionManager

class ReleaseManager:
    """Main release manager class"""

    def __init__(self, config_path='config/release-config.yaml'):
        """Initialize release manager"""
        self.config = self.load_config(config_path)
        self.manifest_helper = ManifestHelper('releases', 'releases_index.json')
        self.version_manager = VersionManager()

    def load_config(self, config_path):
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            sys.exit(1)

    def detect_changes(self, environment='qa', config_repo_path=None):
        """Detect if a new release is needed"""
        print(f"\n{'='*60}")
        print(f"Detecting changes for {environment.upper()} environment")
        print(f"{'='*60}\n")

        env_config = self.config['environments'].get(environment, {})

        if not env_config.get('release_tracking', True):
            print(f"Release tracking disabled for {environment}")
            return {'new_release_needed': False}

        # Get current service versions from deployment config
        current_versions = self.get_current_versions(environment, config_repo_path)

        # Get latest release
        latest_release = self.manifest_helper.get_latest_manifest()

        if not latest_release:
            print("No previous releases found - new release needed")
            return {
                'new_release_needed': True,
                'current_versions': current_versions,
                'previous_versions': {},
                'changes': list(current_versions.keys())
            }

        # Compare versions
        previous_versions = latest_release.get('services', {})
        changes = []

        for service, version in current_versions.items():
            prev_version = previous_versions.get(service)
            if prev_version != version:
                changes.append(service)
                print(f"Change detected: {service} ({prev_version} → {version})")

        if changes:
            print(f"\nChanges detected in {len(changes)} service(s)")
            return {
                'new_release_needed': True,
                'current_versions': current_versions,
                'previous_versions': previous_versions,
                'changes': changes
            }
        else:
            print("No changes detected")
            return {
                'new_release_needed': False,
                'current_versions': current_versions,
                'previous_versions': previous_versions,
                'changes': []
            }

    def create_release(self, environment='qa', version_bump='patch', config_repo_path=None):
        """Create a new release"""
        print(f"\n{'='*60}")
        print(f"Creating release for {environment.upper()} environment")
        print(f"{'='*60}\n")

        # Get current service versions
        current_versions = self.get_current_versions(environment, config_repo_path)

        # Determine next version
        latest_release = self.manifest_helper.get_latest_manifest()
        if latest_release:
            current_version = latest_release.get('version', '0.0.0')
        else:
            current_version = '0.0.0'

        next_version = self.version_manager.bump_version(current_version, version_bump)

        print(f"Version: {current_version} → {next_version}")
        print(f"Services: {len(current_versions)}")

        # Create release manifest
        manifest = {
            'version': next_version,
            'environment': environment,
            'created_at': datetime.utcnow().isoformat(),
            'services': current_versions,
            'metadata': {
                'bump_type': version_bump,
                'previous_version': current_version
            }
        }

        # Save manifest
        manifest_path = self.manifest_helper.create_manifest(manifest)

        print(f"\n✅ Release {next_version} created successfully!")
        print(f"Manifest: {manifest_path}")

        return {
            'version': next_version,
            'manifest_path': str(manifest_path),
            'services': current_versions
        }

    def get_current_versions(self, environment, config_repo_path=None):
        """Get current service versions from deployment config"""
        services = {}

        # If config_repo_path is provided, read from there
        if config_repo_path:
            from pathlib import Path
            config_path = Path(config_repo_path)

            # First try to read from environment-specific vars file
            vars_file = config_path / 'vars' / f'{environment}-vars.yml'

            if vars_file.exists():
                try:
                    with open(vars_file, 'r') as f:
                        vars_data = yaml.safe_load(f) or {}

                    service_versions = vars_data.get('service_versions', {})

                    if service_versions:
                        print(f"✅ Loaded versions from {vars_file.name}")
                        for service in self.config.get('services', []):
                            version = service_versions.get(service)
                            if version:
                                services[service] = version
                                print(f"  {service}: {version}")

                        return services

                except Exception as e:
                    print(f"⚠️  Error reading vars file: {e}")

            # Fallback: Parse docker-compose.yaml.j2 files
            print(f"Reading versions from docker-compose files...")

            for service in self.config.get('services', []):
                # Try standard services directory
                compose_file = config_path / 'services' / service / 'docker-compose.yaml.j2'

                if not compose_file.exists():
                    # Try system-services directory
                    compose_file = config_path / 'system-services' / service / 'docker-compose.yaml.j2'

                if compose_file.exists():
                    version = self._extract_version_from_compose(compose_file, service)
                    if version:
                        services[service] = version
                        print(f"  {service}: {version}")
                else:
                    print(f"  ⚠️  Compose file not found for {service}")
        else:
            # Fallback to placeholder versions
            print("⚠️  No config repo path provided, using placeholder versions")
            for service in self.config.get('services', []):
                services[service] = '1.0.0'

        return services

    def _extract_version_from_compose(self, compose_file, service_name):
        """Extract version from docker-compose file"""
        try:
            with open(compose_file, 'r') as f:
                content = f.read()

            # Look for image line and extract version
            import re

            # Pattern 1: default('version') in Jinja2 template
            pattern1 = rf"default\(['\"]([^'\"]+)['\"]\)"
            match = re.search(pattern1, content)
            if match:
                version = match.group(1)
                if version != 'latest':
                    return version

            # Pattern 2: hardcoded version in image tag
            pattern2 = rf"{service_name}:([^\s\"'}}]+)"
            match = re.search(pattern2, content)
            if match:
                return match.group(1)

            return None

        except Exception as e:
            print(f"Error extracting version from {compose_file}: {e}")
            return None

    def list_releases(self, limit=10):
        """List recent releases"""
        print(f"\n{'='*60}")
        print(f"Recent Releases")
        print(f"{'='*60}\n")

        manifests = self.manifest_helper.get_all_manifests()

        if not manifests:
            print("No releases found")
            return []

        # Sort by version (newest first)
        manifests.sort(key=lambda x: x.get('version', '0.0.0'), reverse=True)

        releases = []
        for manifest in manifests[:limit]:
            version = manifest.get('version', 'unknown')
            created_at = manifest.get('created_at', 'unknown')
            environment = manifest.get('environment', 'unknown')
            services = manifest.get('services', {})

            print(f"Version: {version}")
            print(f"  Environment: {environment}")
            print(f"  Created: {created_at}")
            print(f"  Services: {len(services)}")
            print()

            releases.append({
                'version': version,
                'environment': environment,
                'created_at': created_at,
                'services': services
            })

        return releases

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Release Manager')
    parser.add_argument('command', choices=['detect', 'create', 'list'],
                       help='Command to execute')
    parser.add_argument('--env', default='qa',
                       help='Environment (dev/qa/prod)')
    parser.add_argument('--bump', default='patch',
                       choices=['patch', 'minor', 'major'],
                       help='Version bump type')
    parser.add_argument('--config-repo',
                       help='Path to deployment config repository')
    parser.add_argument('--config-branch',
                       help='Branch of deployment config to use')
    parser.add_argument('--json', action='store_true',
                       help='Output as JSON')
    parser.add_argument('--limit', type=int, default=10,
                       help='Limit for list command')

    args = parser.parse_args()

    # Initialize manager
    manager = ReleaseManager()

    # Execute command
    if args.command == 'detect':
        result = manager.detect_changes(args.env, args.config_repo)

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if result['new_release_needed']:
                print("\n✅ New release needed!")
                print(f"Changes: {', '.join(result['changes'])}")
            else:
                print("\n⏭️  No new release needed")

        sys.exit(0 if result['new_release_needed'] else 1)

    elif args.command == 'create':
        result = manager.create_release(args.env, args.bump, args.config_repo)

        if args.json:
            print(json.dumps(result, indent=2))

        sys.exit(0)

    elif args.command == 'list':
        result = manager.list_releases(args.limit)

        if args.json:
            print(json.dumps(result, indent=2))

        sys.exit(0)

if __name__ == '__main__':
    main()
