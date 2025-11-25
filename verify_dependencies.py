#!/usr/bin/env python3
"""
Dependency Verification Script
Checks if all required dependencies are installed and working
"""

import sys

def check_python_version():
    """Check Python version"""
    print("Checking Python version...")
    version = sys.version_info
    print(f"  Python {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("  ❌ Python 3.8 or higher is required")
        return False
    else:
        print("  ✅ Python version OK")
        return True

def check_yaml():
    """Check PyYAML installation"""
    print("\nChecking PyYAML...")
    try:
        import yaml
        print(f"  ✅ PyYAML {yaml.__version__} is installed")

        # Test basic functionality
        test_data = {'test': 'value', 'number': 123}
        yaml_str = yaml.dump(test_data)
        parsed = yaml.safe_load(yaml_str)

        if parsed == test_data:
            print("  ✅ PyYAML functionality verified")
            return True
        else:
            print("  ❌ PyYAML functionality test failed")
            return False

    except ImportError:
        print("  ❌ PyYAML is not installed")
        print("  Install with: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"  ❌ PyYAML test failed: {e}")
        return False

def check_pathlib():
    """Check pathlib availability"""
    print("\nChecking pathlib...")
    try:
        from pathlib import Path
        test_path = Path('.')
        print(f"  ✅ pathlib is available")
        return True
    except ImportError:
        print("  ❌ pathlib is not available")
        return False

def check_config_file():
    """Check if configuration file exists"""
    print("\nChecking configuration file...")
    try:
        from pathlib import Path
        config_path = Path('config/release-config.yaml')

        if config_path.exists():
            print(f"  ✅ Configuration file found: {config_path}")

            # Try to load it
            import yaml
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)

            print(f"  ✅ Configuration is valid YAML")

            # Check key sections
            required_keys = ['environments', 'services', 'versioning']
            missing = [key for key in required_keys if key not in config]

            if missing:
                print(f"  ⚠️  Missing configuration sections: {', '.join(missing)}")
                return False
            else:
                print(f"  ✅ All required configuration sections present")
                return True
        else:
            print(f"  ❌ Configuration file not found: {config_path}")
            return False

    except Exception as e:
        print(f"  ❌ Configuration check failed: {e}")
        return False

def check_directories():
    """Check if required directories exist"""
    print("\nChecking directories...")
    from pathlib import Path

    dirs_to_check = [
        ('scripts', True),
        ('scripts/utils', True),
        ('config', True),
        ('templates', True),
        ('releases', False)  # Will be created automatically
    ]

    all_ok = True
    for dir_name, required in dirs_to_check:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"  ✅ {dir_name}/ exists")
        elif required:
            print(f"  ❌ {dir_name}/ not found (required)")
            all_ok = False
        else:
            print(f"  ⚠️  {dir_name}/ not found (will be created automatically)")

    return all_ok

def check_scripts():
    """Check if required scripts exist and are importable"""
    print("\nChecking scripts...")

    scripts_to_check = [
        ('scripts/release_manager.py', 'ReleaseManager'),
        ('scripts/utils/manifest_helper.py', 'ManifestHelper'),
        ('scripts/utils/version_manager.py', 'VersionManager')
    ]

    from pathlib import Path
    all_ok = True

    for script_path, class_name in scripts_to_check:
        path = Path(script_path)
        if path.exists():
            print(f"  ✅ {script_path} exists")
        else:
            print(f"  ❌ {script_path} not found")
            all_ok = False

    # Try to import the main modules
    try:
        sys.path.insert(0, 'scripts/utils')
        from manifest_helper import ManifestHelper
        from version_manager import VersionManager
        print(f"  ✅ Utility modules can be imported")
    except ImportError as e:
        print(f"  ❌ Cannot import utility modules: {e}")
        all_ok = False

    return all_ok

def main():
    """Run all checks"""
    print("=" * 60)
    print("Release Manager - Dependency Verification")
    print("=" * 60)

    checks = [
        ("Python Version", check_python_version),
        ("PyYAML", check_yaml),
        ("pathlib", check_pathlib),
        ("Configuration", check_config_file),
        ("Directories", check_directories),
        ("Scripts", check_scripts)
    ]

    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"\n❌ Unexpected error in {name} check: {e}")
            results[name] = False

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")

    print("\n" + "=" * 60)
    print(f"Result: {passed}/{total} checks passed")
    print("=" * 60)

    if passed == total:
        print("\n✅ All checks passed! Release Manager is ready to use.")
        return 0
    else:
        print("\n❌ Some checks failed. Please fix the issues above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())

