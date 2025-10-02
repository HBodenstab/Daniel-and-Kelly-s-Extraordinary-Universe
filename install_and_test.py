#!/usr/bin/env python3
"""Installation and basic test script for the podcast search system."""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Error: {e.stderr}")
        return False

def main():
    """Main installation and test process."""
    print("🚀 Podcast Search System - Installation & Test")
    print("=" * 50)
    
    # Check Python version
    print(f"🐍 Python version: {sys.version}")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    
    # Create virtual environment if it doesn't exist
    venv_path = Path(".venv")
    if not venv_path.exists():
        if not run_command("python3 -m venv .venv", "Creating virtual environment"):
            return False
    else:
        print("✅ Virtual environment already exists")
    
    # Activate virtual environment and install dependencies
    if os.name == 'nt':  # Windows
        activate_cmd = ".venv\\Scripts\\activate"
        pip_cmd = ".venv\\Scripts\\pip"
    else:  # Unix-like
        activate_cmd = "source .venv/bin/activate"
        pip_cmd = ".venv/bin/pip"
    
    # Install dependencies
    install_cmd = f"{pip_cmd} install -r requirements.txt"
    if not run_command(install_cmd, "Installing dependencies"):
        return False
    
    # Test basic imports
    test_cmd = f"{pip_cmd} run python3 -c \"from app.config import RSS_URL; print('✅ Config module works')\""
    if not run_command(test_cmd, "Testing config module"):
        return False
    
    # Test parse module (doesn't require heavy dependencies)
    test_cmd = f"{pip_cmd} run python3 -m pytest tests/test_parse.py -v"
    if not run_command(test_cmd, "Testing parse module"):
        return False
    
    # Test chunk module
    test_cmd = f"{pip_cmd} run python3 -m pytest tests/test_chunk.py -v"
    if not run_command(test_cmd, "Testing chunk module"):
        return False
    
    # Test rank module
    test_cmd = f"{pip_cmd} run python3 -m pytest tests/test_rank.py -v"
    if not run_command(test_cmd, "Testing rank module"):
        return False
    
    print("\n🎉 Installation and basic tests completed successfully!")
    print("\n📋 Next steps:")
    print("1. Activate virtual environment:")
    if os.name == 'nt':
        print("   .venv\\Scripts\\activate")
    else:
        print("   source .venv/bin/activate")
    print("2. Update podcast data:")
    print("   python -m app.cli update")
    print("3. Start web interface:")
    print("   uvicorn app.api:app --reload --port 8000")
    print("4. Or use CLI search:")
    print('   python -m app.cli search "relativity"')
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
