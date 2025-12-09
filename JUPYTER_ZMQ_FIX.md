# Jupyter ZMQ Timeout Fix Guide

## Problem
`zmq.error.ZMQError: timed out` when starting Jupyter kernel in Cursor/VS Code on Windows.

## Root Cause
This is typically caused by Windows Firewall, antivirus software, or system-level blocking of ZMQ socket creation.

## Solutions (Try in Order)

### Solution 1: Windows Firewall Exception
1. Open **Windows Defender Firewall** (or your antivirus firewall)
2. Click **Allow an app or feature through Windows Firewall**
3. Click **Change Settings** → **Allow another app**
4. Add Python executable: `C:\scripting\cellpy\.venv\Scripts\python.exe`
5. Check both **Private** and **Public** networks
6. Restart Cursor

### Solution 2: Run as Administrator
1. Close Cursor completely
2. Right-click Cursor → **Run as administrator**
3. Try starting the Jupyter kernel again

### Solution 3: Reinstall pyzmq with Specific Method
```bash
# In your activated venv
pip uninstall -y pyzmq
pip install --no-binary pyzmq pyzmq
```

If that fails, try installing from conda-forge (if you have conda):
```bash
conda install -c conda-forge pyzmq
```

### Solution 4: Check for Port Conflicts
ZMQ uses dynamic ports. Check if anything is blocking:
```bash
# Check what's using ports
netstat -ano | findstr :49152
```

### Solution 5: Temporarily Disable Antivirus
1. Temporarily disable Windows Defender or your antivirus
2. Try starting the kernel
3. If it works, add Python/Jupyter to antivirus exclusions

### Solution 6: Use Alternative Jupyter Setup
If ZMQ continues to fail, you can try using Jupyter via browser instead:
```bash
# Start Jupyter Lab in browser
jupyter lab
```
Then connect Cursor to the running Jupyter server.

### Solution 7: Environment Variable Workaround
Create a batch file to set environment variables before starting Cursor:
```batch
@echo off
set ZMQ_IOTHREADS=1
set ZMQ_BLOCKY=0
start "" "C:\path\to\Cursor.exe"
```

### Solution 8: Downgrade Jupyter Extension (Cursor-specific)
1. In Cursor, open Extensions (`Ctrl+Shift+X`)
2. Find "Jupyter" extension
3. Click gear icon → **Install Another Version**
4. Try version `2024.9.1` or earlier

### Solution 9: Use Different Python Environment
Create a fresh virtual environment:
```bash
python -m venv .venv_new
.venv_new\Scripts\activate
pip install ipykernel jupyter pyzmq
python -m ipykernel install --user --name cellpy_new
```

## Verification
After applying fixes, test ZMQ:
```python
import zmq
ctx = zmq.Context()
print("Success!")
ctx.term()
```

## Most Likely Fix
**Solution 1 (Firewall)** or **Solution 5 (Antivirus)** are the most common fixes for this issue on Windows.


