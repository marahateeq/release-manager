#!/usr/bin/env python3
"""
Service Tag Fetcher
Fetches available tags/versions from service repositories
"""

import sys
import os
import argparse
import subprocess
import json
from datetime import datetime
import yaml

class ServiceTagFetcher:
    """Fetches available tags from service repositories"""

    def __init__(self, config_path='config/release-config.yaml'):
        """Initialize tag fetcher"""
        self.config = self.load_config(config_path)
        self.service_repos = self.get_service_repos()

    def load_config(self, config_path):
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            sys.exit(1)

    def get_service_repos(self):
        """Get service repository URLs from config"""
        repos = {}

        service_repos = self.config.get('service_repositories', {})

        for service_name, service_config in service_repos.items():
            if isinstance(service_config, dict):
                repos[service_name] = service_config.get('url', '')
            else:
                # Fallback: assume it's just a URL string
                repos[service_name] = service_config

        return repos

    def fetch_tags_from_github(self, service_name, limit=20):
        """Fetch tags from GitHub repository using git ls-remote"""
        repo_url = self.service_repos.get(service_name)

        if not repo_url:
            print(f"❌ Service '{service_name}' not found in configuration")
            return []

        try:
            print(f"Fetching tags for {service_name} from {repo_url}...")

            # Use git ls-remote to list tags without cloning
            result = subprocess.run(
                ['git', 'ls-remote', '--tags', '--refs', repo_url],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                print(f"❌ Failed to fetch tags: {result.stderr}")
                return []

            # Parse output
            tags = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue

                # Format: <commit_hash>\trefs/tags/<tag_name>
                parts = line.split('\t')
                if len(parts) == 2:
                    tag_ref = parts[1]
                    tag_name = tag_ref.replace('refs/tags/', '')

                    # Skip tags that end with ^{} (annotated tag references)
                    if not tag_name.endswith('^{}'):
                        tags.append({
                            'tag': tag_name,
                            'commit': parts[0][:8]
                        })

            # Sort tags (semantic version aware if possible)
            tags = self.sort_tags(tags)

            # Limit results
            return tags[:limit]

        except subprocess.TimeoutExpired:
            print(f"❌ Timeout fetching tags from {repo_url}")
            return []
        except Exception as e:
            print(f"❌ Error fetching tags: {e}")
            return []

    def sort_tags(self, tags):
        """Sort tags in descending order (newest first)"""
        def version_key(tag_info):
            tag = tag_info['tag']

            # Remove 'v' prefix if present
            version_str = tag.lstrip('v')

            # Try to parse as semantic version
            try:
                parts = version_str.split('.')
                if len(parts) >= 3:
                    major = int(parts[0])
                    minor = int(parts[1])
                    patch = int(parts[2].split('-')[0])  # Handle pre-release versions
                    return (major, minor, patch)
            except:
                pass

            # Fallback to string comparison
            return (0, 0, 0, tag)

        try:
            return sorted(tags, key=version_key, reverse=True)
        except:
            # If sorting fails, return as-is
            return tags

    def fetch_docker_tags_from_registry(self, service_name, registry_url='localhost:5000', limit=20):
        """Fetch tags from Docker registry (alternative method)"""
        try:
            # This requires the registry API to be accessible
            import requests

            url = f"http://{registry_url}/v2/{service_name}/tags/list"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                tags = data.get('tags', [])

                # Convert to dict format
                tag_list = [{'tag': tag, 'commit': ''} for tag in tags]

                # Sort and limit
                tag_list = sorted(tag_list, key=lambda x: x['tag'], reverse=True)
                return tag_list[:limit]
            else:
                print(f"❌ Failed to fetch from registry: HTTP {response.status_code}")
                return []

        except ImportError:
            print("⚠️  requests library not available for registry API")
            return []
        except Exception as e:
            print(f"❌ Error fetching from registry: {e}")
            return []

    def display_tags(self, service_name, tags, output_format='text'):
        """Display tags in specified format"""
        if not tags:
            print(f"No tags found for {service_name}")
            return

        if output_format == 'json':
            print(json.dumps({
                'service': service_name,
                'tags': tags,
                'count': len(tags)
            }, indent=2))
        else:
            print(f"\nAvailable tags for {service_name}:")
            print("=" * 60)
            for i, tag_info in enumerate(tags, 1):
                tag = tag_info['tag']
                commit = tag_info.get('commit', '')
                if commit:
                    print(f"{i:3d}. {tag:30s} (commit: {commit})")
                else:
                    print(f"{i:3d}. {tag}")
            print("=" * 60)
            print(f"Total: {len(tags)} tags")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Fetch available tags for a service')
    parser.add_argument('--service', required=True,
                       help='Service name')
    parser.add_argument('--source', choices=['github', 'registry'], default='github',
                       help='Source to fetch tags from')
    parser.add_argument('--registry', default='localhost:5000',
                       help='Docker registry URL (for registry source)')
    parser.add_argument('--limit', type=int, default=20,
                       help='Maximum number of tags to return')
    parser.add_argument('--format', choices=['text', 'json'], default='text',
                       help='Output format')

    args = parser.parse_args()

    # Initialize fetcher
    fetcher = ServiceTagFetcher()

    # Fetch tags
    if args.source == 'github':
        tags = fetcher.fetch_tags_from_github(args.service, args.limit)
    else:
        tags = fetcher.fetch_docker_tags_from_registry(args.service, args.registry, args.limit)

    # Display results
    fetcher.display_tags(args.service, tags, args.format)

    sys.exit(0 if tags else 1)


if __name__ == '__main__':
    main()
