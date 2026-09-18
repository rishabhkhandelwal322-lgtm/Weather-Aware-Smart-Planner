"""
test_api.py - Test script to catch the immediate exit cause
"""
import sys
import os

print("1. Testing basic imports...")

try:
    import storage
    print("   [x] storage imported")
    import weather_fetcher
    print("   [x] weather_fetcher imported")
    import task_manager
    print("   [x] task_manager imported")
    import planner
    print("   [x] planner imported")
    import notifier
    print("   [x] notifier imported")
except Exception as e:
    print(f"❌ Import error: {e}")

print("2. Testing FastAPI application initialization...")
from fastapi import FastAPI
app = FastAPI()

print("3. Everything imported without exiting. Attempting uvicorn start...")