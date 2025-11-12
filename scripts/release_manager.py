#!/usr/bin/env python3
"""
Release Manager
Main orchestrator for release detection and creation
"""

import sys
import os
import argparse
import json
import yaml
from pathlib import Path
from datetime import datetime

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

    def detect_changes(self, environment='qa'):
        """Detect if a new release is needed"""
        print(f"\n{'='*60}")
        print(f"Detecting changes for {environment.upper()} environment")
        print(f"{'='*60}\n")

        env_config = self.config['environments'].get(environment, {})

        if not env_config.get('release_tracking', True):
            print(f"Release tracking disabled for {environment}")
            return {'new_release_needed': False}

        # Get current service versions from deployment config
        current_versions = self.get_current_versions(environment)

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

    def create_release(self, environment='qa', version_bump='patch'):
        """Create a new release"""
        print(f"\n{'='*60}")
        print(f"Creating release for {environment.upper()} environment")
        print(f"{'='*60}\n")

        # Get current service versions
        current_versions = self.get_current_versions(environment)

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

    def get_current_versions(self, environment):
        """Get current service versions from deployment config"""
        # In a real implementation, this would read from deployment-config
        # For this example, we'll use dummy versions

        services = {}

        # Read from config
        for service in self.config.get('services', []):
            # Simulate reading version from deployment config
            # In production, read from docker-compose.yaml.j2 files
            services[service] = '1.0.0'  # Placeholder

        return services

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
    parser.add_argument('--json', action='store_true',
                       help='Output as JSON')

    args = parser.parse_args()

    # Initialize manager
    manager = ReleaseManager()

    # Execute command
    if args.command == 'detect':
        result = manager.detect_changes(args.env)

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
        result = manager.create_release(args.env, args.bump)

        if args.json:
            print(json.dumps(result, indent=2))

        sys.exit(0)

    elif args.command == 'list':
        result = manager.list_releases()

        if args.json:
            print(json.dumps(result, indent=2))

        sys.exit(0)

if __name__ == '__main__':
    main()
