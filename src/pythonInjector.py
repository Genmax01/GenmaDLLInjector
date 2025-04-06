from src import mywinapi as winapi
import ctypes
import ctypes.wintypes as wintypes
import os
import psutil

class myDllInjector():
    def __init__(self, dllName='myDll.dll'):
        self.dll_name = dllName
        self.dll_path = os.path.abspath(self.dll_name)
        self.process_handle = None
        self.target_process_name = None
        self.pid = None

    def _open_process(self):
        """Ouvre un handle vers le processus cible."""
        if not self.pid:
            print("[Erreur] PID non trouvé ou non défini.")
            return False
        self.process_handle = winapi.OpenProcess(winapi.PROCESS_ALL_ACCESS, False, self.pid)
        if not self.process_handle:
            print(f"Echec OpenProcess pour PID {self.pid}")
            self.pid = None # Réinitialiser si l'ouverture échoue
            return False
        print(f"Handle obtenu pour PID {self.pid}: {self.process_handle}")
        return True

    def close_process(self):
        """Ferme le handle du processus."""
        if self.process_handle:
            winapi.CloseHandle(self.process_handle)
            # print(f"Handle fermé pour PID {self.pid}.")
            self.process_handle = None
            # On ne réinitialise pas pid ici, car on pourrait vouloir réinjecter

    def _find_pid(self):
        """Trouve le PID du processus cible."""
        if not self.target_process_name:
            print("[Erreur] Nom du processus cible non défini. Utilisez setTarget().")
            return False
        print(f"Recherche du processus '{self.target_process_name}'...")
        for process in psutil.process_iter(['pid', 'name']):
            try:
                if self.target_process_name.lower() in process.info['name'].lower():
                    self.pid = process.info['pid']
                    print(f"Processus trouvé avec PID: {self.pid}")
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        self.pid = None
        print(f"Processus '{self.target_process_name}' non trouvé.")
        return False

    def setTarget(self, process_name):
        """Définit le nom du processus exécutable cible."""
        self.target_process_name = process_name
        self._find_pid() # Essayer de trouver le PID immédiatement
        self._open_process()

    def _allocate_memory(self, size):
        # print('try to allocate memory')
        # print('handle:', self.process_handle)
        """Alloue de la mémoire dans le processus cible."""
        if not self.process_handle: return None
        address = winapi.VirtualAllocEx(
            self.process_handle, winapi.NULL, size,
            winapi.MEM_COMMIT | winapi.MEM_RESERVE, winapi.PAGE_EXECUTE_READWRITE
        )
        if not address:
            print("Echec VirtualAllocEx")
        return address

    def _write_memory(self, address, data_bytes):
        # print('try to write memory')
        """Écrit des données dans la mémoire du processus cible."""
        if not self.process_handle or not address: return False
        size = len(data_bytes)
        bytes_written = ctypes.c_size_t(0)
        success = winapi.WriteProcessMemory(
            self.process_handle, address, data_bytes, size, ctypes.byref(bytes_written)
        )
        if not success or bytes_written.value != size:
            print("Echec WriteProcessMemory")
            return False
        return True

    def _read_memory(self, address, size):
        """Lit la mémoire du processus cible."""
        if not self.process_handle: return None
        buffer = ctypes.create_string_buffer(size)
        bytes_read = ctypes.c_size_t(0)
        success = winapi.ReadProcessMemory(
            self.process_handle, wintypes.LPCVOID(address), buffer, size, ctypes.byref(bytes_read)
        )
        if not success or bytes_read.value != size:
            # Ne pas printer d'erreur ici systématiquement, car la lecture peut échouer légitimement
            # self._print_error(f"Echec ReadProcessMemory à {hex(address)}")
            return None
        return buffer.raw

    def _create_remote_thread(self, start_address, arg_address=0):
        if not self.process_handle or not start_address: return None
        # print(f"start_address: {hex(start_address)}")
        # print(f"arg_address: {hex(arg_address)}")
        # print(f"process_handle: {self.process_handle}")
        thread_id = wintypes.DWORD(0)  # Variable pour stocker l'ID du thread (optionnel)
        thread_handle = winapi.CreateRemoteThread(
            self.process_handle,
            None,  # lpThreadAttributes
            0,  # dwStackSize
            ctypes.c_void_p(start_address),  # lpStartAddress
            ctypes.c_void_p(arg_address),  # lpParameter
            0,  # dwCreationFlags
            ctypes.byref(thread_id)  # lpThreadId (pointeur vers DWORD)
        )
        if not thread_handle:
            print("Echec CreateRemoteThread")
        else:
            print(f"Thread handle créé: {thread_handle}, Thread ID: {thread_id.value}")
        return thread_handle

    # Modify _wait_for_thread to return the actual exit code or an error indicator
    def _wait_for_thread(self, thread_handle, timeout=10000):
        """Waits for a thread and returns its exit code or an error code."""
        if not thread_handle:
            print("[Erreur] Handle de thread invalide passé à _wait_for_thread.")
            return -999  # Indicate invalid handle input

        thread_handle_value = thread_handle  # Store the value if needed, but use the object directly
        # print(f"Attente du thread avec handle: {thread_handle_value}")
        wait_result = winapi.WaitForSingleObject(thread_handle_value, timeout)
        # print(f"WaitForSingleObject retourné: {wait_result}")

        if wait_result == 0:  # WAIT_OBJECT_0 (Thread finished)
            exit_code = wintypes.DWORD()
            if winapi.GetExitCodeThread(thread_handle_value, ctypes.byref(exit_code)):
                exit_code_value = exit_code.value
                # Interpret common return codes
                # if exit_code_value == 0:
                #     print(f"Code de sortie du thread: 0 (Succès probable)")
                # elif exit_code_value == -1:  # Corresponds to 0xFFFFFFFF if read as unsigned DWORD
                #     print(f"Code de sortie du thread: -1 (0x{exit_code.value:X}) (ERREUR)")
                # else:
                #     print(f"Code de sortie du thread: {exit_code_value} (Inattendu)")
            else:
                print("Echec GetExitCodeThread")
                exit_code_value = -997  # Indicate GetExitCodeThread failure
        elif wait_result == 0x00000102:  # WAIT_TIMEOUT
            print("[Avertissement] Timeout en attendant le thread.")
            exit_code_value = -996  # Indicate Timeout
        else:  # WAIT_FAILED or other error
            print("Echec WaitForSingleObject")
            exit_code_value = -995  # Indicate Wait Failed

        # Ensure the handle is closed even if GetExitCodeThread failed
        winapi.CloseHandle(thread_handle_value)
        print(f"Handle de thread fermé: {thread_handle_value}")

        return exit_code_value

    def inject_dll(self):
        """Injecte la DLL Python dans le processus cible."""
        # print(f"Tentative d'injection de '{self.dll_name}'...")
        dllPathBytes = self.dll_path.encode('utf-8') + b'\x00'
        pathSize = len(dllPathBytes)

        # print(self.dll_path)
        # Allouer mémoire pour le chemin
        dllPathAddress = self._allocate_memory(pathSize)
        # print('dllPathAddress', dllPathAddress)
        if not dllPathAddress: return False

        # Écrire le chemin
        if not self._write_memory(dllPathAddress, dllPathBytes):
            winapi.VirtualFreeEx(self.process_handle, dllPathAddress, 0, winapi.MEM_RELEASE)
            return False
        print("Chemin DLL écrit dans la mémoire distante.")

        # Obtenir l'adresse de LoadLibraryA
        loadLibraryAddr = ctypes.cast(winapi.LoadLibraryA, wintypes.LPVOID).value
        if not loadLibraryAddr:
            winapi.VirtualFreeEx(self.process_handle, dllPathAddress, 0, winapi.MEM_RELEASE)
            print("[Erreur] Adresse LoadLibraryA introuvable.")
            return False

        # Créer le thread pour charger la DLL
        thread_handle = self._create_remote_thread(loadLibraryAddr, dllPathAddress)
        if not thread_handle:
            winapi.VirtualFreeEx(self.process_handle, dllPathAddress, 0, winapi.MEM_RELEASE)
            return False

        # Attendre la fin du chargement
        print("Attente du chargement de la DLL...")
        success = self._wait_for_thread(thread_handle, 15000)  # Timeout un peu plus long

        winapi.VirtualFreeEx(self.process_handle, dllPathAddress, 0, winapi.MEM_RELEASE)

        if success:
            print(f" ==>  Injection de '{self.dll_name}' réussie dans '{self.target_process_name}'.")
            return True
        else:
            print(f" ==>  Echec ou timeout lors de l'injection de '{self.dll_name}' dans '{self.target_process_name}'.")
            return False


if __name__ == '__main__':
    try:
        # Init
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
    except Exception as e:
        print(e)
        try:
            myInjector.close_process()
        except Exception as e:
            pass
