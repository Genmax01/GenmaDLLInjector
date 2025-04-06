# lib/mywinapi.py
import ctypes
import ctypes.wintypes as wintypes
import win32con # Nécessite pywin32

# --- Constantes WinAPI ---

# Accès aux processus
PROCESS_ALL_ACCESS = win32con.PROCESS_ALL_ACCESS
PAGE_EXECUTE_READWRITE = win32con.PAGE_EXECUTE_READWRITE

# Constants
ERROR_NO_MORE_FILES = 18 # Specific error code for Module32Next end
MAX_PATH = 260

# Typedefs
LPVOID = wintypes.LPVOID
HANDLE = wintypes.HANDLE
DWORD = wintypes.DWORD
BOOL = wintypes.BOOL
SIZE_T = ctypes.c_size_t
POINTER = ctypes.POINTER
VOID_P = ctypes.c_void_p

# Allocation mémoire
MEM_COMMIT = win32con.MEM_COMMIT
MEM_RESERVE = win32con.MEM_RESERVE
MEM_RELEASE = win32con.MEM_RELEASE

# Autres
NULL = 0

# --- Fonctions Kernel32 via ctypes ---
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

# Fonctions de gestion de processus et mémoire
OpenProcess = kernel32.OpenProcess
CloseHandle = kernel32.CloseHandle
VirtualAllocEx = kernel32.VirtualAllocEx
WriteProcessMemory = kernel32.WriteProcessMemory
ReadProcessMemory = kernel32.ReadProcessMemory # Ajouté car utilisé dans utility.py
CreateRemoteThread = kernel32.CreateRemoteThread
LoadLibraryA = kernel32.LoadLibraryA # Version ANSI (bytes)
WaitForSingleObject = kernel32.WaitForSingleObject
GetExitCodeThread = kernel32.GetExitCodeThread
VirtualFreeEx = kernel32.VirtualFreeEx

# Définition des types d'arguments et de retour pour plus de robustesse
OpenProcess.argtypes = [DWORD, BOOL, DWORD]
OpenProcess.restype = HANDLE
#
CloseHandle.argtypes = [HANDLE]
CloseHandle.restype = BOOL
#
VirtualAllocEx.argtypes = [HANDLE, LPVOID, SIZE_T, DWORD, DWORD]
VirtualAllocEx.restype = LPVOID
#
WriteProcessMemory.argtypes = [HANDLE, LPVOID, wintypes.LPCVOID, SIZE_T, POINTER(SIZE_T)]
WriteProcessMemory.restype = BOOL
#
ReadProcessMemory.argtypes = [HANDLE, wintypes.LPCVOID, LPVOID, SIZE_T, POINTER(SIZE_T)]
ReadProcessMemory.restype = BOOL
#
CreateRemoteThread.argtypes = [
    HANDLE, # hProcess
    LPVOID, # lpThreadAttributes (LPSECURITY_ATTRIBUTES)
    SIZE_T, # dwStackSize
    LPVOID, # lpStartAddress (LPTHREAD_START_ROUTINE)
    LPVOID, # lpParameter (LPVOID)
    DWORD,  # dwCreationFlags
    LPVOID  # lpThreadId (LPDWORD)
]
CreateRemoteThread.restype = HANDLE
#
GetExitCodeThread.argtypes = [HANDLE, POINTER(DWORD)] # <--- AJOUT ICI
GetExitCodeThread.restype = BOOL                                      # <--- AJOUT ICI
#
VirtualFreeEx.argtypes = [
    HANDLE,    # hProcess
    LPVOID,    # lpAddress (Crucially, LPVOID or c_void_p for 64-bit pointers)
    SIZE_T,    # dwSize    (Crucially, c_size_t for 64-bit sizes)
    DWORD      # dwFreeType
]
VirtualFreeEx.restype = BOOL
#
WaitForSingleObject.argtypes = [VOID_P, DWORD]
WaitForSingleObject.restype = DWORD
#
CloseHandle.argtypes = [VOID_P]
CloseHandle.restype = BOOL
