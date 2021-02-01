@echo on

CALL conda.bat activate base
cd /d "%~dp0"
pythonw pylon_virtual_cam.py
