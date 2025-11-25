#!/usr/bin/env python3
"""
Update Service Tag
Updates docker-compose files with new service tags/versions
"""

import sys
import os
import argparse
import yaml
from pathlib import Path
import re
import subprocess

class ServiceTagUpdater:
    """Updates service tags in deployment configuration"""

    def __init__(self, config_dir, branch='main'):
        """Initialize tag updater"""
        self.config_dir = Path(config_dir)
        self.branch = branch

        if not self.config_dir.exists():
            print(f"❌ Configuration directory not found: {self.config_dir}")
            sys.exit(1)

    def get_service_compose_path(self, service_name):
        """Get path to service's docker-compose file"""
        # Standard services are in services/<service-name>/
        compose_path = self.config_dir / 'services' / service_name / 'docker-compose.yaml.j2'

        if compose_path.exists():
            return compose_path

        # System services might be in system-services/<service-name>/
        compose_path = self.config_dir / 'system-services' / service_name / 'docker-compose.yaml.j2'

        if compose_path.exists():
            return compose_path

        print(f"❌ Docker compose file not found for service: {service_name}")
        return None

    def get_environment_vars_path(self, environment):
        """Get path to environment-specific variables file"""
        vars_path = self.config_dir / 'vars' / f'{environment}-vars.yml'

        if vars_path.exists():
            return vars_path

        # If environment-specific file doesn't exist, return common vars path
        return self.config_dir / 'vars' / 'common-vars.yml'

    def update_version_in_vars(self, service_name, tag, environment):
        """Update service version in environment variables file"""
        vars_path = self.get_environment_vars_path(environment)

        if not vars_path.exists():
            print(f"⚠️  Variables file not found: {vars_path}")
            print(f"Creating new file...")
            vars_path.parent.mkdir(parents=True, exist_ok=True)
            vars_data = {}
        else:
            try:
                with open(vars_path, 'r') as f:
                    vars_data = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"❌ Error loading variables file: {e}")
                return False

        # Create versions section if it doesn't exist
        if 'service_versions' not in vars_data:
            vars_data['service_versions'] = {}

        # Update version
        old_version = vars_data['service_versions'].get(service_name, 'not set')
        vars_data['service_versions'][service_name] = tag

        # Write back
        try:
            with open(vars_path, 'w') as f:
                yaml.dump(vars_data, f, default_flow_style=False, sort_keys=False)

            print(f"✅ Updated {service_name} version in {vars_path.name}")
            print(f"   {old_version} → {tag}")
            return True

        except Exception as e:
            print(f"❌ Error writing variables file: {e}")
            return False

    def update_version_inline(self, service_name, tag, environment):
        """Update service version directly in docker-compose file (if not using vars)"""
        compose_path = self.get_service_compose_path(service_name)

        if not compose_path:
            return False

        try:
            with open(compose_path, 'r') as f:
                content = f.read()

            # Pattern to match image line with version
            # Example: image: "{{ docker_registry }}/user-api:{{ version | default('latest') }}"
            # We want to update the default value

            # Check if it's using a variable
            if '{{ version' in content or f'{{{{ {service_name}_version' in content:
                print(f"⚠️  Service uses Jinja2 variable for version")
                print(f"   Updating via vars file instead...")
                return self.update_version_in_vars(service_name, tag, environment)

            # Otherwise, update hardcoded version
            patterns = [
                # Pattern: service-name:tag
                (rf"({service_name}:)[^\s\"'\n]+", rf"\g<1>{tag}"),
                # Pattern: image: "registry/service:tag"
                (rf"(image:\s*[\"'].*/{service_name}:)[^\s\"'\n]+", rf"\g<1>{tag}"),
            ]

            original_content = content
            for pattern, replacement in patterns:
                content = re.sub(pattern, replacement, content)

            if content == original_content:
                print(f"⚠️  Could not find version to update in {compose_path.name}")
                print(f"   Consider using Jinja2 variables for version management")
                return False

            # Write back
            with open(compose_path, 'w') as f:
                f.write(content)

            print(f"✅ Updated {service_name} tag in {compose_path.name}")
            print(f"   New tag: {tag}")
            return True

        except Exception as e:
            print(f"❌ Error updating compose file: {e}")
            return False

    def update_service_tag(self, service_name, tag, environment, commit=False):
        """Update service tag in deployment configuration"""
        print(f"\n{'='*60}")
        print(f"Updating {service_name} to tag: {tag}")
        print(f"Environment: {environment}")
        print(f"Branch: {self.branch}")
        print(f"{'='*60}\n")

        # First try updating via vars file (preferred method)
        success = self.update_version_in_vars(service_name, tag, environment)

        if not success:
            # Fallback to inline update
            print("Attempting inline update...")
            success = self.update_version_inline(service_name, tag, environment)

        if success and commit:
            self.commit_changes(service_name, tag, environment)

        return success

    def commit_changes(self, service_name, tag, environment):
        """Commit changes to git repository"""
        try:
            os.chdir(self.config_dir)

            # Configure git
            subprocess.run(['git', 'config', 'user.email', 'jenkins@yourorg.com'], check=True)
            subprocess.run(['git', 'config', 'user.name', 'Jenkins Deployment Bot'], check=True)

            # Add changes
            subprocess.run(['git', 'add', '.'], check=True)

            # Commit
            commit_msg = f"Update {service_name} to {tag} for {environment} environment"
            subprocess.run(['git', 'commit', '-m', commit_msg], check=False)

            print(f"✅ Changes committed to branch {self.branch}")

        except Exception as e:
            print(f"⚠️  Error committing changes: {e}")

    def get_current_version(self, service_name, environment):
        """Get current version of a service"""
        vars_path = self.get_environment_vars_path(environment)

        if not vars_path.exists():
            return None

        try:
            with open(vars_path, 'r') as f:
                vars_data = yaml.safe_load(f) or {}

            return vars_data.get('service_versions', {}).get(service_name)

        except Exception as e:
            print(f"Error reading current version: {e}")
            return None


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Update service tag in deployment config')
    parser.add_argument('--service', required=True,
                       help='Service name')
    parser.add_argument('--tag', required=True,
                       help='New tag/version')
    parser.add_argument('--environment', required=True,
                       help='Target environment')
    parser.add_argument('--config-dir', required=True,
                       help='Path to deployment config directory')
    parser.add_argument('--branch', default='main',
                       help='Git branch being updated')
    parser.add_argument('--commit', action='store_true',
                       help='Commit changes to git')
    parser.add_argument('--show-current', action='store_true',
                       help='Show current version before updating')

    args = parser.parse_args()

    # Initialize updater
    updater = ServiceTagUpdater(args.config_dir, args.branch)

    # Show current version if requested
    if args.show_current:
        current = updater.get_current_version(args.service, args.environment)
        if current:
            print(f"Current version of {args.service}: {current}")
        else:
            print(f"No current version found for {args.service}")
        print()

    # Update tag
    success = updater.update_service_tag(
        args.service,
        args.tag,
        args.environment,
        args.commit
    )

    if success:
        print(f"\n✅ Service tag updated successfully")
        sys.exit(0)
    else:
        print(f"\n❌ Failed to update service tag")
        sys.exit(1)


if __name__ == '__main__':
    main()
