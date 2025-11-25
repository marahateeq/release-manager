"""
Manifest Helper
CRUD operations for release manifests
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Check for required dependencies
try:
    import yaml
except ImportError:
    print("❌ Error: PyYAML is not installed")
    print("Please install it with: pip install -r requirements.txt")
    sys.exit(1)

class ManifestHelper:
    """Helper class for manifest operations"""

    def __init__(self, manifests_dir='releases', index_file='releases_index.json'):
        """Initialize manifest helper"""
        self.manifests_dir = Path(manifests_dir)
        self.index_file = Path(index_file)

        # Ensure directories exist
        self.manifests_dir.mkdir(parents=True, exist_ok=True)

        # Initialize index if it doesn't exist
        if not self.index_file.exists():
            self._save_index([])

    def create_manifest(self, manifest: Dict) -> Path:
        """Create a new release manifest"""
        version = manifest.get('version', '0.0.0')

        # Generate filename
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"release_{version}_{timestamp}.yaml"
        filepath = self.manifests_dir / filename

        # Save manifest
        with open(filepath, 'w') as f:
            yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)

        # Update index
        self._add_to_index(version, str(filepath), manifest)

        return filepath

    def get_manifest(self, version: str) -> Optional[Dict]:
        """Get a specific manifest by version"""
        index = self._load_index()

        for entry in index:
            if entry.get('version') == version:
                filepath = entry.get('path')
                return self._read_manifest(filepath)

        return None

    def get_latest_manifest(self) -> Optional[Dict]:
        """Get the latest release manifest"""
        index = self._load_index()

        if not index:
            return None

        # Get most recent entry
        latest = sorted(index, key=lambda x: x.get('created_at', ''), reverse=True)[0]
        filepath = latest.get('path')

        return self._read_manifest(filepath)

    def get_all_manifests(self) -> List[Dict]:
        """Get all release manifests"""
        index = self._load_index()

        manifests = []
        for entry in index:
            filepath = entry.get('path')
            manifest = self._read_manifest(filepath)
            if manifest:
                manifests.append(manifest)

        return manifests

    def delete_manifest(self, version: str) -> bool:
        """Delete a release manifest"""
        index = self._load_index()

        for i, entry in enumerate(index):
            if entry.get('version') == version:
                filepath = Path(entry.get('path'))

                # Delete file
                if filepath.exists():
                    filepath.unlink()

                # Remove from index
                index.pop(i)
                self._save_index(index)

                return True

        return False

    def _read_manifest(self, filepath: str) -> Optional[Dict]:
        """Read manifest from file"""
        try:
            with open(filepath, 'r') as f:
                return yaml.safe_load(f)
        except Exception:
            return None

    def _load_index(self) -> List[Dict]:
        """Load the releases index"""
        try:
            with open(self.index_file, 'r') as f:
                return json.load(f)
        except Exception:
            return []

    def _save_index(self, index: List[Dict]):
        """Save the releases index"""
        with open(self.index_file, 'w') as f:
            json.dump(index, f, indent=2)

    def _add_to_index(self, version: str, filepath: str, manifest: Dict):
        """Add entry to releases index"""
        index = self._load_index()

        # Check for duplicates
        for entry in index:
            if entry.get('version') == version:
                # Update existing entry
                entry['path'] = filepath
                entry['updated_at'] = datetime.utcnow().isoformat()
                self._save_index(index)
                return

        # Add new entry
        index.append({
            'version': version,
            'path': filepath,
            'environment': manifest.get('environment'),
            'created_at': manifest.get('created_at'),
            'services': list(manifest.get('services', {}).keys())
        })

        self._save_index(index)
