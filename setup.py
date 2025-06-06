#!/usr/bin/env python3
import os
import sys
import subprocess
from shutil import copy2

def setup_environment():
    print("Setting up Binance Trading Bot...")
    
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            copy2('.env.example', '.env')
            print("Created .env file from .env.example")
            print("Please edit .env and add your Binance API credentials")
        else:
            print("Error: .env.example not found")
            return False
    
    print("\nInstalling dependencies...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("Error installing dependencies")
        return False
    
    if not os.path.exists('logs'):
        os.makedirs('logs')
        print("Created logs directory")
    
    if not os.path.exists('data'):
        os.makedirs('data')
        print("Created data directory")
    
    print("\nSetup complete!")
    print("\nNext steps:")
    print("1. Edit .env file and add your Binance API credentials")
    print("2. Run 'python app.py' to start the web interface")
    print("3. Access the trading bot at http://localhost:5000")
    
    return True

if __name__ == "__main__":
    setup_environment()