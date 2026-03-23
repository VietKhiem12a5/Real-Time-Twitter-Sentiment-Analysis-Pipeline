#!/usr/bin/env python3
"""
Start Script: Unified entry point for starting the sentiment analysis pipeline.

This script provides an interactive menu to start different components of the pipeline:
- Kafka & Zookeeper
- Model Training
- Producer
- Consumer
- API Server

"""

import os
import sys
import subprocess
import time
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str) -> None:
    """Print formatted header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text:^60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.ENDC}\n")


def print_success(text: str) -> None:
    """Print success message."""
    print(f"{Colors.GREEN}✓{Colors.ENDC} {text}")


def print_error(text: str) -> None:
    """Print error message."""
    print(f"{Colors.RED}✗{Colors.ENDC} {text}")


def print_info(text: str) -> None:
    """Print info message."""
    print(f"{Colors.BLUE}ℹ{Colors.ENDC} {text}")


def print_warning(text: str) -> None:
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠{Colors.ENDC} {text}")


def check_prerequisites() -> bool:
    """Check if all prerequisites are met."""
    print_header("Checking Prerequisites")
    
    checks = []
    
    # Check Python version
    if sys.version_info >= (3, 9):
        print_success(f"Python {sys.version.split()[0]} installed")
        checks.append(True)
    else:
        print_error(f"Python 3.9+ required (current: {sys.version.split()[0]})")
        checks.append(False)
    
    # Check Docker
    try:
        subprocess.run(
            ['docker', '--version'],
            capture_output=True,
            timeout=5,
            check=True
        )
        version_output = subprocess.run(
            ['docker', '--version'],
            capture_output=True,
            text=True
        ).stdout.strip()
        print_success(f"{version_output}")
        checks.append(True)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print_error("Docker not installed or not running")
        checks.append(False)
    
    # Check Docker Compose
    try:
        subprocess.run(
            ['docker-compose', '--version'],
            capture_output=True,
            timeout=5,
            check=True
        )
        version_output = subprocess.run(
            ['docker-compose', '--version'],
            capture_output=True,
            text=True
        ).stdout.strip()
        print_success(f"{version_output}")
        checks.append(True)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print_error("Docker Compose not installed")
        checks.append(False)
    
    # Check CSV file
    if Path('sentiment140_clean.csv').exists():
        size_mb = Path('sentiment140_clean.csv').stat().st_size / (1024 * 1024)
        print_success(f"Dataset found (sentiment140_clean.csv, {size_mb:.1f} MB)")
        checks.append(True)
    else:
        print_error("Dataset not found: sentiment140_clean.csv")
        checks.append(False)
    
    # Check Docker running
    try:
        subprocess.run(
            ['docker', 'ps'],
            capture_output=True,
            timeout=5,
            check=True
        )
        print_success("Docker daemon is running")
        checks.append(True)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        print_error("Docker daemon is not running")
        checks.append(False)
    
    return all(checks)


def install_dependencies() -> bool:
    """Install Python dependencies."""
    print_header("Installing Python Dependencies")
    
    try:
        print_info("Installing from requirements.txt...")
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
            check=True
        )
        print_success("Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install dependencies: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False


def train_models() -> bool:
    """Run model training."""
    print_header("Training Machine Learning Models")
    
    if Path('logistic_model.pkl').exists() and Path('tfidf_vectorizer.pkl').exists():
        print_warning("Model files already exist. Skipping training.")
        return True
    
    try:
        print_info("Starting model training (this may take a few minutes)...")
        subprocess.run([sys.executable, 'train_models.py'], check=True)
        print_success("Model training completed")
        return True
    except subprocess.CalledProcessError:
        print_error("Model training failed")
        return False
    except Exception as e:
        print_error(f"Unexpected error during training: {e}")
        return False


def start_kafka() -> bool:
    """Start Kafka and Zookeeper."""
    print_header("Starting Kafka & Zookeeper")
    
    try:
        print_info("Pulling latest images...")
        subprocess.run(
            ['docker-compose', 'pull'],
            timeout=300,
            capture_output=True
        )
        
        print_info("Starting containers...")
        subprocess.run(['docker-compose', 'up', '-d'], check=True)
        
        print_info("Waiting for Kafka to be ready (30 seconds)...")
        time.sleep(30)
        
        # Verify Kafka is running
        result = subprocess.run(
            ['docker-compose', 'ps'],
            capture_output=True,
            text=True
        )
        
        if 'running' in result.stdout.lower():
            print_success("Kafka and Zookeeper are running")
            print_info("Kafka UI available at: http://localhost:8080")
            return True
        else:
            print_error("Containers not running. Check logs: docker-compose logs")
            return False
            
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to start Kafka: {e}")
        print_info("Try: docker-compose logs")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False


def start_component(component: str) -> None:
    """Start a specific component."""
    print_header(f"Starting {component.upper()}")
    
    commands = {
        'consumer': f'{sys.executable} consumer.py',
        'producer': f'{sys.executable} producer.py',
        'api': f'{sys.executable} api.py',
        'train': f'{sys.executable} train_models.py',
    }
    
    if component not in commands:
        print_error(f"Unknown component: {component}")
        return
    
    try:
        print_info(f"Starting {component}...")
        print_info("Press Ctrl+C to stop\n")
        subprocess.run(commands[component], shell=True, check=False)
    except KeyboardInterrupt:
        print_info(f"\n{component.upper()} stopped by user")
    except Exception as e:
        print_error(f"Error running {component}: {e}")


def show_status() -> None:
    """Show current status of all components."""
    print_header("System Status")
    
    # Check Docker
    try:
        result = subprocess.run(
            ['docker-compose', 'ps'],
            capture_output=True,
            text=True,
            timeout=10
        )
        print("Docker Containers:")
        print(result.stdout)
    except Exception as e:
        print_error(f"Could not get Docker status: {e}")
    
    # Check model files
    print("\nModel Files:")
    if Path('logistic_model.pkl').exists():
        size = Path('logistic_model.pkl').stat().st_size / (1024 * 1024)
        print_success(f"logistic_model.pkl ({size:.1f} MB)")
    else:
        print_error("logistic_model.pkl not found")
    
    if Path('tfidf_vectorizer.pkl').exists():
        size = Path('tfidf_vectorizer.pkl').stat().st_size / (1024 * 1024)
        print_success(f"tfidf_vectorizer.pkl ({size:.1f} MB)")
    else:
        print_error("tfidf_vectorizer.pkl not found")
    
    # Check database
    print("\nDatabase:")
    if Path('sentiment_db.sqlite').exists():
        size = Path('sentiment_db.sqlite').stat().st_size / (1024 * 1024)
        print_success(f"sentiment_db.sqlite ({size:.1f} MB)")
    else:
        print_warning("sentiment_db.sqlite not found (will be created by consumer)")
    
    # Check CSV
    print("\nDataset:")
    if Path('sentiment140_clean.csv').exists():
        size = Path('sentiment140_clean.csv').stat().st_size / (1024 * 1024)
        print_success(f"sentiment140_clean.csv ({size:.1f} MB)")
    else:
        print_error("sentiment140_clean.csv not found")


def stop_kafka() -> None:
    """Stop Kafka and Zookeeper."""
    print_header("Stopping Kafka & Zookeeper")
    
    try:
        print_info("Stopping containers...")
        subprocess.run(['docker-compose', 'down'], check=True)
        print_success("Kafka and Zookeeper stopped")
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to stop containers: {e}")
    except Exception as e:
        print_error(f"Unexpected error: {e}")


def show_menu() -> str:
    """Display main menu and get user choice."""
    print_header("Sentiment Analysis Pipeline - Setup & Control")
    
    menu_options = [
        ('1', 'Check Prerequisites', 'check_prerequisites'),
        ('2', 'Install Dependencies', 'install_dependencies'),
        ('3', 'Train ML Models', 'train_models'),
        ('4', 'Start Kafka Infrastructure', 'start_kafka'),
        ('5', 'Start Consumer', 'start_component:consumer'),
        ('6', 'Start Producer', 'start_component:producer'),
        ('7', 'Start API Server', 'start_component:api'),
        ('8', 'Stop Kafka Infrastructure', 'stop_kafka'),
        ('9', 'Show System Status', 'show_status'),
        ('0', 'Exit', 'exit'),
    ]
    
    for key, label, _ in menu_options:
        print(f"  {Colors.BOLD}{key}{Colors.ENDC}. {label}")
    
    print()
    choice = input(f"{Colors.BOLD}Select option (0-9): {Colors.ENDC}").strip()
    return choice


def main():
    """Main entry point."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}Sentiment Analysis Pipeline Launcher{Colors.ENDC}")
    print(f"{Colors.CYAN}Version 1.0.0{Colors.ENDC}\n")
    
    while True:
        choice = show_menu()
        
        if choice == '0':
            print(f"\n{Colors.GREEN}Thank you for using Sentiment Analysis Pipeline!{Colors.ENDC}\n")
            break
        elif choice == '1':
            check_prerequisites()
        elif choice == '2':
            install_dependencies()
        elif choice == '3':
            train_models()
        elif choice == '4':
            start_kafka()
        elif choice == '5':
            start_component('consumer')
        elif choice == '6':
            start_component('producer')
        elif choice == '7':
            start_component('api')
        elif choice == '8':
            stop_kafka()
        elif choice == '9':
            show_status()
        else:
            print_error("Invalid option. Please try again.")
        
        input(f"\n{Colors.BOLD}Press Enter to continue...{Colors.ENDC}")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Program interrupted by user{Colors.ENDC}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Fatal error: {e}{Colors.ENDC}\n")
        sys.exit(1)
