
Simple tool to inject a .dll into an .exe

You can use the interface, or simply use the pythoninjector.py

# Setup

# 1. Clone the repository:
   ```bash
   git clone https://github.com/Genmax01/GenmaDLLInjector.git
   cd GenmaDLLInjector
   ```

# 2. Create and activate a virtual environment (recommended)
## Windows
```
python -m venv .venv
.\.venv\Scripts\activate
```
## macOS / Linux
```
python3 -m venv .venv
source .venv/bin/activate
```
# 3. Install requirements
```
pip install -r requirements.txt
```
# 4. Run
```
python genmaDLLInjector.py
```


# Libraries needed (if you don t use the requirements file):
```
pip install pywin32, psutil, PyQt6  
```

## example with pythoninjector.py:
```python
dll_name_to_inject = 'myDll.dll'

myInjector = myDllInjector(dll_name_to_inject)
myInjector.setTarget('notepad++.exe')
# check if target found
if myInjector.pid:
    print(f'Injecting {myInjector.dll_name} to {myInjector.target_process_name}. PID: {myInjector.pid}')
    # Close Dll
    myInjector.inject_dll()
    # Close process
    myInjector.close_process()

```
