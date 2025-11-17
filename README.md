# Release Manager

Automated release management system for tracking and creating releases across multiple environments.

## Overview

The Release Manager automates the process of:
- Detecting changes in service versions
- Creating release manifests
- Tracking releases across environments
- Managing semantic versioning
- Integrating with Jenkins CI/CD

## Features

- **Change Detection**: Automatically detects service version changes
- **Semantic Versioning**: Supports PATCH, MINOR, and MAJOR version bumps
- **Multi-Environment**: Separate release tracking for Dev/QA/Prod
- **Release Manifests**: YAML-based release documentation
- **Release Index**: JSON index for quick release lookup
- **Jenkins Integration**: Automated release pipeline
- **Version Management**: Full semantic versioning support

## Repository Structure

```
release-manager/
├── scripts/
│   ├── release_manager.py          # Main release manager
│   └── utils/
│       ├── __init__.py
│       ├── manifest_helper.py      # Manifest CRUD operations
│       └── version_manager.py      # Semantic versioning
├── config/
│   └── release-config.yaml         # Configuration
├── templates/
│   └── release-manifest.template.yaml  # Manifest template
├── releases/                       # Release manifests directory
├── releases_index.json             # Release index
├── jenkinsfile-release             # Jenkins pipeline
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## Installation

### Prerequisites
- Python 3.8+
- PyYAML

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Verify installation
python scripts/release_manager.py --help
```

## Usage

### Command Line Interface

The release manager provides three main commands:

#### 1. Detect Changes

Check if a new release is needed:

```bash
python scripts/release_manager.py detect --env qa
```

With JSON output:
```bash
python scripts/release_manager.py detect --env qa --json
```

#### 2. Create Release

Create a new release:

```bash
python scripts/release_manager.py create --env qa --bump patch
```

Version bump types:
- `patch`: Bug fixes, minor updates (1.0.0 → 1.0.1)
- `minor`: New features (1.0.0 → 1.1.0)
- `major`: Breaking changes (1.0.0 → 2.0.0)

#### 3. List Releases

View recent releases:

```bash
python scripts/release_manager.py list --env qa
```

With JSON output:
```bash
python scripts/release_manager.py list --json
```

### Examples

```bash
# Detect changes in QA
python scripts/release_manager.py detect --env qa

# Create patch release
python scripts/release_manager.py create --env qa --bump patch

# Create minor release for production
python scripts/release_manager.py create --env prod --bump minor

# List all releases
python scripts/release_manager.py list
```

## Configuration

### release-config.yaml

```yaml
environments:
  dev:
    release_tracking: false  # No tracking in dev
    auto_release: false

  qa:
    release_tracking: true
    auto_release: true       # Auto-create releases
    default_bump: patch

  prod:
    release_tracking: true
    auto_release: false      # Manual approval
    default_bump: minor

services:
  - user-api
  - product-frontend
  - data-processor

versioning:
  rules:
    patch: "Bug fixes, security patches"
    minor: "New features, new services"
    major: "Breaking changes, rewrites"
```

### Environments

- **Dev**: No release tracking, for active development
- **QA**: Automatic release creation on deployment
- **Prod**: Manual release process with approval

## Release Manifests

### Manifest Structure

```yaml
version: "1.0.0"
environment: "qa"
created_at: "2025-11-09T12:00:00"

services:
  user-api: "1.0.0"
  product-frontend: "1.0.0"
  data-processor: "1.0.0"

metadata:
  bump_type: "patch"
  previous_version: "0.0.9"
  changes:
    - user-api
  notes: "Bug fixes"

build:
  timestamp: "2025-11-09T12:00:00"
  jenkins_build: "123"
  git_commit: "abc123"

deployment:
  dev: false
  qa: true
  prod: false
```

### Manifest Storage

- **Directory**: `releases/`
- **Format**: YAML files named `release_<version>_<timestamp>.yaml`
- **Index**: `releases_index.json` for quick lookups

## Semantic Versioning

### Version Format

```
MAJOR.MINOR.PATCH[-PRERELEASE]
```

Examples:
- `1.0.0` - Standard release
- `1.0.0-beta` - Pre-release
- `2.0.0` - Major version

### Bump Types

| Type | Description | Example |
|------|-------------|---------|
| **PATCH** | Bug fixes, patches | 1.0.0 → 1.0.1 |
| **MINOR** | New features | 1.0.0 → 1.1.0 |
| **MAJOR** | Breaking changes | 1.0.0 → 2.0.0 |

### Version Comparison

```python
from utils.version_manager import VersionManager

vm = VersionManager()

# Compare versions
result = vm.compare_versions('1.0.0', '1.0.1')
# Returns: -1 (1.0.0 < 1.0.1)

# Bump version
new_version = vm.bump_version('1.0.0', 'minor')
# Returns: '1.1.0'

# Validate version
is_valid = vm.is_valid_version('1.0.0')
# Returns: True
```

## Jenkins Integration

### Pipeline Configuration

The `jenkinsfile-release` defines an automated pipeline with:

1. **Initialize**: Setup environment
2. **Setup Python**: Install dependencies
3. **Detect Changes**: Check for version changes
4. **Create Release**: Generate release manifest
5. **Commit Manifest**: Save to repository
6. **Notify**: Send email notifications

### Pipeline Parameters

- **ENVIRONMENT**: Target environment (qa/prod)
- **ACTION**: Operation to perform (detect/create/list)
- **BUMP_TYPE**: Version bump type (patch/minor/major)
- **FORCE_CREATE**: Force release creation

### Trigger Pipeline

**Manual**:
1. Go to Jenkins → Release Manager job
2. Click "Build with Parameters"
3. Select environment and action
4. Click "Build"

**Automated**:
- Triggered after deployment pipeline
- Auto-creates releases in QA
- Detects changes in production

### Example Jenkins Integration

```groovy
// In deployment-config/jenkinsfile
stage('Create Release') {
    when {
        expression { env.ENVIRONMENT == 'qa' }
    }
    steps {
        build job: 'release-manager',
            parameters: [
                string(name: 'ENVIRONMENT', value: env.ENVIRONMENT),
                string(name: 'ACTION', value: 'create'),
                string(name: 'BUMP_TYPE', value: 'patch')
            ]
    }
}
```

## Workflows

### QA Deployment Workflow

1. Service is deployed to QA
2. Release Manager detects version change
3. Automatically creates new release
4. Manifest is saved and committed
5. Team is notified via email

### Production Deployment Workflow

1. Release is validated in QA
2. Manual trigger of release pipeline
3. Release Manager creates prod release
4. Approval required before deployment
5. Manifest tracks production release

## API Reference

### ReleaseManager Class

```python
from scripts.release_manager import ReleaseManager

# Initialize
manager = ReleaseManager('config/release-config.yaml')

# Detect changes
result = manager.detect_changes(environment='qa')

# Create release
release = manager.create_release(environment='qa', version_bump='patch')

# List releases
releases = manager.list_releases(limit=10)
```

### ManifestHelper Class

```python
from scripts.utils.manifest_helper import ManifestHelper

# Initialize
helper = ManifestHelper('releases', 'releases_index.json')

# Create manifest
manifest = {'version': '1.0.0', 'services': {...}}
path = helper.create_manifest(manifest)

# Get manifest
manifest = helper.get_manifest('1.0.0')

# Get latest
latest = helper.get_latest_manifest()

# Get all
all_manifests = helper.get_all_manifests()
```

### VersionManager Class

```python
from scripts.utils.version_manager import VersionManager

# Initialize
vm = VersionManager()

# Parse version
major, minor, patch, prerelease = vm.parse_version('1.0.0')

# Bump version
new_version = vm.bump_version('1.0.0', 'minor')  # Returns '1.1.0'

# Compare versions
result = vm.compare_versions('1.0.0', '1.0.1')  # Returns -1

# Validate
is_valid = vm.is_valid_version('1.0.0')  # Returns True

# Sort versions
sorted_list = vm.sort_versions(['1.0.0', '1.1.0', '1.0.1'])
```

## Troubleshooting

### No Changes Detected

If changes aren't detected:
1. Verify service is in `services` list in config
2. Check deployment config has updated version
3. Run with `--json` flag to see current vs previous versions

### Invalid Version Format

Versions must follow `MAJOR.MINOR.PATCH` format:
- ✅ Valid: `1.0.0`, `2.1.3`, `1.0.0-beta`
- ❌ Invalid: `1.0`, `v1.0.0`, `1.0.0.0`

### Manifest Creation Fails

Check:
1. Write permissions on `releases/` directory
2. Valid YAML in configuration
3. All required fields in manifest

### Jenkins Pipeline Fails

Common issues:
1. Python not installed on Jenkins agent
2. Missing credentials for Git push
3. Invalid environment parameter

## Best Practices

1. **Use Patch Bumps**: For most releases in QA
2. **Use Minor Bumps**: When adding new services
3. **Use Major Bumps**: Rarely, for breaking changes
4. **Validate in QA**: Before promoting to production
5. **Document Changes**: Add notes to release manifests
6. **Review Manifests**: Before committing to repository
7. **Automate QA**: Let system create releases automatically
8. **Manual Prod**: Require approval for production releases

## Future Enhancements

- [ ] Git integration for automatic version detection
- [ ] JIRA ticket extraction and linking
- [ ] Release notes generation
- [ ] Rollback functionality
- [ ] Multi-region release tracking
- [ ] Slack notifications
- [ ] Release approval workflows
- [ ] API server for programmatic access

## Contributing

1. Create feature branch
2. Make changes
3. Test with all commands
4. Update this README
5. Create pull request

## License

Internal use only - proprietary
