#!/usr/bin/env python3
import subprocess
import os

os.chdir(r'C:\Users\Davlat\Desktop\CaryerHub')

# Step 1: Add all files
result = subprocess.run(['git', 'add', '.'], capture_output=True, text=True)
print(f"ADD: returncode={result.returncode}")
if result.stderr:
    print(f"ADD stderr: {result.stderr[:200]}")

# Step 2: Commit
result = subprocess.run(['git', 'commit', '-m', 'Update parsing and backend'], capture_output=True, text=True)
print(f"COMMIT: returncode={result.returncode}")
if result.stderr:
    print(f"COMMIT stderr: {result.stderr[:200]}")

# Step 3: Set up remote and push
result = subprocess.run(['git', 'remote', 'remove', 'origin'], capture_output=True, text=True)
print(f"REMOVE REMOTE: returncode={result.returncode}")

result = subprocess.run(['git', 'remote', 'add', 'origin', 'https://github.com/davlat96/CareerHub.git'], capture_output=True, text=True)
print(f"ADD REMOTE: returncode={result.returncode}")

result = subprocess.run(['git', 'branch', '-M', 'main'], capture_output=True, text=True)
print(f"RENAME BRANCH: returncode={result.returncode}")

result = subprocess.run(['git', 'push', '-u', 'origin', 'main'], capture_output=True, text=True)
print(f"PUSH: returncode={result.returncode}")
print(f"PUSH stdout: {result.stdout[:500]}")
if result.stderr:
    print(f"PUSH stderr: {result.stderr[:500]}")