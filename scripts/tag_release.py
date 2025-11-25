#!/usr/bin/env python3
"""
Tag Release
Creates git tags for aurora releases and pushes them to GitHub
"""

import sys
import os
import argparse
import subprocess
import yaml
from pathlib import Path
from datetime import datetime

class ReleaseTagManager:
    """Manages git tags for aurora releases"""

    def __init__(self, repo_path='.'):
        """Initialize tag manager"""
        self.repo_path = Path(repo_path)

        if not self.is_git_repo():
            print(f"❌ Not a git repository: {self.repo_path}")
            sys.exit(1)

    def is_git_repo(self):
        """Check if current directory is a git repository"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=self.repo_path,
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False

    def configure_git(self, user_name='Jenkins Release Bot', user_email='jenkins@yourorg.com'):
        """Configure git user"""
        try:
            subprocess.run(
                ['git', 'config', 'user.name', user_name],
                cwd=self.repo_path,
                check=True
            )
            subprocess.run(
                ['git', 'config', 'user.email', user_email],
                cwd=self.repo_path,
                check=True
            )
            print(f"✅ Git configured: {user_name} <{user_email}>")
            return True
        except Exception as e:
            print(f"❌ Error configuring git: {e}")
            return False

    def tag_exists(self, tag_name):
        """Check if a tag already exists"""
        try:
            result = subprocess.run(
                ['git', 'tag', '-l', tag_name],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            return bool(result.stdout.strip())
        except:
            return False

    def create_tag(self, version, message=None, annotated=True):
        """Create a git tag"""
        tag_name = f"v{version}"

        # Check if tag already exists
        if self.tag_exists(tag_name):
            print(f"⚠️  Tag {tag_name} already exists")
            return False

        # Default message
        if not message:
            message = f"Aurora Release {version}"

        try:
            if annotated:
                # Create annotated tag
                subprocess.run(
                    ['git', 'tag', '-a', tag_name, '-m', message],
                    cwd=self.repo_path,
                    check=True
                )
            else:
                # Create lightweight tag
                subprocess.run(
                    ['git', 'tag', tag_name],
                    cwd=self.repo_path,
                    check=True
                )

            print(f"✅ Created tag: {tag_name}")
            return True

        except Exception as e:
            print(f"❌ Error creating tag: {e}")
            return False

    def push_tag(self, version, remote='origin'):
        """Push tag to remote repository"""
        tag_name = f"v{version}"

        try:
            subprocess.run(
                ['git', 'push', remote, tag_name],
                cwd=self.repo_path,
                check=True
            )
            print(f"✅ Pushed tag {tag_name} to {remote}")
            return True

        except Exception as e:
            print(f"❌ Error pushing tag: {e}")
            return False

    def push_commits(self, branch='main', remote='origin'):
        """Push commits to remote repository"""
        try:
            subprocess.run(
                ['git', 'push', remote, branch],
                cwd=self.repo_path,
                check=True
            )
            print(f"✅ Pushed commits to {remote}/{branch}")
            return True

        except Exception as e:
            print(f"❌ Error pushing commits: {e}")
            return False

    def commit_release_files(self, version, environment):
        """Commit release manifest and index files"""
        try:
            # Add release files
            subprocess.run(
                ['git', 'add', 'releases/', 'releases_index.json'],
                cwd=self.repo_path,
                check=True
            )

            # Commit
            commit_msg = f"Release {version} for {environment} environment"
            result = subprocess.run(
                ['git', 'commit', '-m', commit_msg],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                print(f"✅ Committed release files")
                return True
            elif 'nothing to commit' in result.stdout:
                print(f"ℹ️  No changes to commit")
                return True
            else:
                print(f"⚠️  Commit failed: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Error committing files: {e}")
            return False

    def list_tags(self, pattern='v*', limit=20):
        """List existing tags"""
        try:
            result = subprocess.run(
                ['git', 'tag', '-l', pattern, '--sort=-version:refname'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )

            tags = result.stdout.strip().split('\n')
            tags = [t for t in tags if t]  # Filter empty strings

            return tags[:limit]

        except Exception as e:
            print(f"❌ Error listing tags: {e}")
            return []

    def get_tag_info(self, tag_name):
        """Get information about a tag"""
        try:
            result = subprocess.run(
                ['git', 'show', tag_name, '--format=%H%n%an%n%ae%n%at%n%s', '--no-patch'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 5:
                    return {
                        'tag': tag_name,
                        'commit': lines[0][:8],
                        'author': lines[1],
                        'email': lines[2],
                        'date': datetime.fromtimestamp(int(lines[3])).isoformat(),
                        'message': lines[4]
                    }

            return None

        except Exception as e:
            print(f"Error getting tag info: {e}")
            return None

    def delete_tag(self, version, remote='origin', delete_remote=False):
        """Delete a tag locally and optionally from remote"""
        tag_name = f"v{version}"

        try:
            # Delete local tag
            subprocess.run(
                ['git', 'tag', '-d', tag_name],
                cwd=self.repo_path,
                check=True
            )
            print(f"✅ Deleted local tag: {tag_name}")

            # Delete remote tag if requested
            if delete_remote:
                subprocess.run(
                    ['git', 'push', remote, '--delete', tag_name],
                    cwd=self.repo_path,
                    check=True
                )
                print(f"✅ Deleted remote tag: {tag_name}")

            return True

        except Exception as e:
            print(f"❌ Error deleting tag: {e}")
            return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Tag and push aurora releases to GitHub')
    parser.add_argument('command', choices=['create', 'push', 'commit-and-tag', 'list', 'info', 'delete'],
                       help='Command to execute')
    parser.add_argument('--version',
                       help='Release version (e.g., 1.0.0)')
    parser.add_argument('--environment',
                       help='Environment (for commit message)')
    parser.add_argument('--message',
                       help='Tag message')
    parser.add_argument('--remote', default='origin',
                       help='Git remote name')
    parser.add_argument('--branch', default='main',
                       help='Git branch name')
    parser.add_argument('--repo-path', default='.',
                       help='Path to git repository')
    parser.add_argument('--limit', type=int, default=20,
                       help='Limit for list command')
    parser.add_argument('--delete-remote', action='store_true',
                       help='Delete tag from remote (for delete command)')

    args = parser.parse_args()

    # Initialize tag manager
    tag_manager = ReleaseTagManager(args.repo_path)

    # Configure git
    tag_manager.configure_git()

    # Execute command
    if args.command == 'create':
        if not args.version:
            print("❌ --version is required for create command")
            sys.exit(1)

        success = tag_manager.create_tag(args.version, args.message)
        sys.exit(0 if success else 1)

    elif args.command == 'push':
        if not args.version:
            print("❌ --version is required for push command")
            sys.exit(1)

        success = tag_manager.push_tag(args.version, args.remote)
        sys.exit(0 if success else 1)

    elif args.command == 'commit-and-tag':
        if not args.version or not args.environment:
            print("❌ --version and --environment are required for commit-and-tag command")
            sys.exit(1)

        print(f"\n{'='*60}")
        print(f"Commit and Tag Release {args.version}")
        print(f"{'='*60}\n")

        # Step 1: Commit release files
        if not tag_manager.commit_release_files(args.version, args.environment):
            print("❌ Failed to commit release files")
            sys.exit(1)

        # Step 2: Create tag
        if not tag_manager.create_tag(args.version, args.message):
            print("❌ Failed to create tag")
            sys.exit(1)

        # Step 3: Push commits
        if not tag_manager.push_commits(args.branch, args.remote):
            print("❌ Failed to push commits")
            sys.exit(1)

        # Step 4: Push tag
        if not tag_manager.push_tag(args.version, args.remote):
            print("❌ Failed to push tag")
            sys.exit(1)

        print(f"\n{'='*60}")
        print(f"✅ Release {args.version} committed and tagged successfully!")
        print(f"{'='*60}")
        sys.exit(0)

    elif args.command == 'list':
        print(f"\n{'='*60}")
        print(f"Recent Release Tags")
        print(f"{'='*60}\n")

        tags = tag_manager.list_tags(limit=args.limit)

        if not tags:
            print("No tags found")
        else:
            for tag in tags:
                info = tag_manager.get_tag_info(tag)
                if info:
                    print(f"{tag:20s} - {info['message']} ({info['date'][:10]})")
                else:
                    print(tag)

        sys.exit(0)

    elif args.command == 'info':
        if not args.version:
            print("❌ --version is required for info command")
            sys.exit(1)

        tag_name = f"v{args.version}"
        info = tag_manager.get_tag_info(tag_name)

        if info:
            print(f"\n{'='*60}")
            print(f"Tag Information: {tag_name}")
            print(f"{'='*60}")
            print(f"Commit:  {info['commit']}")
            print(f"Author:  {info['author']} <{info['email']}>")
            print(f"Date:    {info['date']}")
            print(f"Message: {info['message']}")
            print(f"{'='*60}")
            sys.exit(0)
        else:
            print(f"❌ Tag not found: {tag_name}")
            sys.exit(1)

    elif args.command == 'delete':
        if not args.version:
            print("❌ --version is required for delete command")
            sys.exit(1)

        success = tag_manager.delete_tag(args.version, args.remote, args.delete_remote)
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
