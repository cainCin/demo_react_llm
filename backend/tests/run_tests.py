#!/usr/bin/env python3
"""
Test launcher script for Chatbox App
Provides convenient commands to run tests and launch the application
"""
import sys
import subprocess
import os
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}\n")
    
    result = subprocess.run(cmd, shell=True, cwd=Path(__file__).parent.parent)
    
    if result.returncode != 0:
        print(f"\n❌ Command failed with exit code {result.returncode}")
        return False
    return True


def main():
    """Main test launcher"""
    if len(sys.argv) < 2:
        print("""
🧪 Chatbox App Test Launcher

Usage:
    python run_tests.py <command> [options]

Commands:
    all              Run all tests
    api              Run API endpoint tests only
    database         Run database tests only
    rag              Run RAG system tests only
    unit             Run unit tests (fast)
    integration      Run integration tests
    coverage         Run tests with coverage report
    lint             Run linter checks
    launch           Launch the application (backend + frontend)
    backend          Launch backend only
    frontend         Launch frontend only
    help             Show this help message

Examples:
    python run_tests.py all
    python run_tests.py api
    python run_tests.py coverage
    python run_tests.py launch
        """)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    backend_dir = Path(__file__).parent.parent
    frontend_dir = backend_dir.parent / "frontend"
    
    if command == "all":
        success = run_command(
            "pytest tests/ -v",
            "Running all tests"
        )
        sys.exit(0 if success else 1)
    
    elif command == "api":
        success = run_command(
            "pytest tests/test_api.py -v -m api",
            "Running API endpoint tests"
        )
        sys.exit(0 if success else 1)
    
    elif command == "database":
        success = run_command(
            "pytest tests/test_database.py -v -m database",
            "Running database tests"
        )
        sys.exit(0 if success else 1)
    
    elif command == "rag":
        success = run_command(
            "pytest tests/test_rag.py -v -m rag",
            "Running RAG system tests"
        )
        sys.exit(0 if success else 1)
    
    elif command == "unit":
        success = run_command(
            "pytest tests/ -v -m 'unit and not integration'",
            "Running unit tests"
        )
        sys.exit(0 if success else 1)
    
    elif command == "integration":
        success = run_command(
            "pytest tests/ -v -m integration",
            "Running integration tests"
        )
        sys.exit(0 if success else 1)
    
    elif command == "coverage":
        success = run_command(
            "pytest tests/ --cov=. --cov-report=html --cov-report=term",
            "Running tests with coverage"
        )
        if success:
            print("\n✅ Coverage report generated in htmlcov/index.html")
        sys.exit(0 if success else 1)
    
    elif command == "lint":
        print("\n🔍 Running linter checks...")
        # Add linting commands here if needed
        print("⚠️  Linting not configured yet")
        sys.exit(0)
    
    elif command == "launch":
        print("\n🚀 Launching Chatbox App...")
        print("This will start both backend and frontend servers.")
        print("Press Ctrl+C to stop both servers.\n")
        
        import threading
        import time
        
        def run_backend():
            os.chdir(backend_dir)
            subprocess.run(["python", "main.py"])
        
        def run_frontend():
            time.sleep(2)  # Give backend time to start
            os.chdir(frontend_dir)
            subprocess.run(["npm", "run", "dev"])
        
        backend_thread = threading.Thread(target=run_backend, daemon=True)
        frontend_thread = threading.Thread(target=run_frontend, daemon=True)
        
        backend_thread.start()
        frontend_thread.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping servers...")
            sys.exit(0)
    
    elif command == "backend":
        print("\n🚀 Launching backend server...")
        os.chdir(backend_dir)
        subprocess.run(["python", "main.py"])
    
    elif command == "frontend":
        print("\n🚀 Launching frontend server...")
        os.chdir(frontend_dir)
        subprocess.run(["npm", "run", "dev"])
    
    elif command == "help":
        main()  # Show help
        sys.exit(0)
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Run 'python run_tests.py help' for usage information")
        sys.exit(1)


if __name__ == "__main__":
    main()


