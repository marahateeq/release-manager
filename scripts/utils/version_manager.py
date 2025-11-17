"""
Version Manager
Semantic versioning utilities
"""

import re
from typing import Tuple

class VersionManager:
    """Manager for semantic versioning operations"""

    def __init__(self):
        """Initialize version manager"""
        self.version_pattern = re.compile(r'^(\d+)\.(\d+)\.(\d+)(?:-(.+))?$')

    def parse_version(self, version: str) -> Tuple[int, int, int, str]:
        """
        Parse semantic version string

        Args:
            version: Version string (e.g., "1.2.3" or "1.2.3-beta")

        Returns:
            Tuple of (major, minor, patch, prerelease)
        """
        match = self.version_pattern.match(version)

        if not match:
            raise ValueError(f"Invalid version format: {version}")

        major = int(match.group(1))
        minor = int(match.group(2))
        patch = int(match.group(3))
        prerelease = match.group(4) or ''

        return (major, minor, patch, prerelease)

    def bump_version(self, version: str, bump_type: str = 'patch') -> str:
        """
        Bump version according to semantic versioning

        Args:
            version: Current version string
            bump_type: Type of bump (patch/minor/major)

        Returns:
            New version string
        """
        major, minor, patch, prerelease = self.parse_version(version)

        if bump_type == 'patch':
            patch += 1
        elif bump_type == 'minor':
            minor += 1
            patch = 0
        elif bump_type == 'major':
            major += 1
            minor = 0
            patch = 0
        else:
            raise ValueError(f"Invalid bump type: {bump_type}")

        # Remove prerelease suffix on bump
        return f"{major}.{minor}.{patch}"

    def compare_versions(self, version1: str, version2: str) -> int:
        """
        Compare two semantic versions

        Args:
            version1: First version string
            version2: Second version string

        Returns:
            -1 if version1 < version2
             0 if version1 == version2
             1 if version1 > version2
        """
        v1 = self.parse_version(version1)
        v2 = self.parse_version(version2)

        # Compare major, minor, patch
        for i in range(3):
            if v1[i] < v2[i]:
                return -1
            elif v1[i] > v2[i]:
                return 1

        # If versions are equal up to patch, compare prerelease
        # Version without prerelease is greater than with prerelease
        if not v1[3] and v2[3]:
            return 1
        elif v1[3] and not v2[3]:
            return -1
        elif v1[3] < v2[3]:
            return -1
        elif v1[3] > v2[3]:
            return 1

        return 0

    def is_valid_version(self, version: str) -> bool:
        """Check if version string is valid semantic version"""
        try:
            self.parse_version(version)
            return True
        except ValueError:
            return False

    def sort_versions(self, versions: list) -> list:
        """Sort list of version strings"""
        from functools import cmp_to_key
        return sorted(versions, key=cmp_to_key(self.compare_versions))
