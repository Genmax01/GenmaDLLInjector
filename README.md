Library needed:
```
pip install pywin32, psutil, PyQt6  
```
Simple tool to inject a .dll into an .exe

You can use the interface, or simply use the pythoninjector.py


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
