import sys
import os
import psutil  # To list processes
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QFileDialog, QMessageBox, QInputDialog
)
from PyQt6.QtCore import Qt, QDir
from src import pythonInjector

# --- Configuration ---
CONFIG_DIR = "config"
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.txt")

class InjectorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Genma DLL Injector") # Changed Title
        self.setGeometry(100, 100, 600, 400) # x, y, width, height

        self.current_dll_path = ""
        self.current_app_name = ""

        # Ensure the config directory exists
        if not os.path.exists(CONFIG_DIR):
            try:
                os.makedirs(CONFIG_DIR)
            except OSError as e:
                # Changed MessageBox content
                QMessageBox.critical(self, "Error", f"Could not create configuration directory: {e}")
                # We could choose to exit here, but let's continue so the UI shows up
                # sys.exit(1) # Uncomment to exit if directory creation fails

        self.load_config()
        self.init_ui()
        self.update_ui_labels() # Update UI with loaded values

    def load_config(self):
        """Load configuration from config/config.txt."""
        self.current_dll_path = "" # Reset in case the file doesn't exist or is corrupt
        self.current_app_name = ""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("dll="):
                            self.current_dll_path = line[len("dll="):].strip()
                        elif line.startswith("exe="):
                            self.current_app_name = line[len("exe="):].strip()
            else:
                # If the file doesn't exist, create it empty or with defaults
                self.save_config() # Creates an empty/default file
                # Changed print message
                print(f"Configuration file '{CONFIG_FILE}' not found. Creating a default file.")

        except IOError as e:
            # Changed MessageBox content
            QMessageBox.warning(self, "Read Error", f"Could not read configuration file: {e}")
        except Exception as e:
             # Changed MessageBox content
             QMessageBox.warning(self, "Unexpected Error", f"Error loading configuration: {e}")


    def save_config(self):
        """Save the current configuration to config/config.txt."""
        try:
            # Ensure the directory exists before writing
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                # Write an empty string if None or ""
                f.write(f"dll={self.current_dll_path or ''}\n")
                f.write(f"exe={self.current_app_name or ''}\n")
        except IOError as e:
            # Changed MessageBox content
            QMessageBox.critical(self, "Write Error", f"Could not save configuration file: {e}")
        except Exception as e:
             # Changed MessageBox content
             QMessageBox.critical(self, "Unexpected Error", f"Error saving configuration: {e}")

    def init_ui(self):
        """Initialize the graphical user interface components."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Configuration Display Section ---
        info_layout = QVBoxLayout()
        # Changed Label text
        self.dll_label = QLabel("Selected DLL: <Not Set>")
        self.app_label = QLabel("Selected Application: <Not Set>")
        info_layout.addWidget(self.dll_label)
        info_layout.addWidget(self.app_label)
        main_layout.addLayout(info_layout)

        # --- Button Section ---
        button_layout = QHBoxLayout()
        # Button text was already English, kept as is
        self.browse_dll_button = QPushButton("Browse DLL")
        self.browse_app_button = QPushButton("Browse App")
        self.inject_button = QPushButton("Inject")

        self.browse_dll_button.clicked.connect(self.browse_dll)
        self.browse_app_button.clicked.connect(self.browse_app)
        self.inject_button.clicked.connect(self.inject)

        button_layout.addWidget(self.browse_dll_button)
        button_layout.addWidget(self.browse_app_button)
        button_layout.addWidget(self.inject_button)
        main_layout.addLayout(button_layout)

        # --- Output/Log Section ---
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True) # To only display messages (read-only)
        main_layout.addWidget(self.output_area)

    def update_ui_labels(self):
        """Update labels displaying the selected DLL and App."""
        # Changed display text for unset values
        dll_display = self.current_dll_path if self.current_dll_path else "<Not Set>"
        app_display = self.current_app_name if self.current_app_name else "<Not Set>"
        # Changed Label f-string text
        self.dll_label.setText(f"Selected DLL: {dll_display}")
        self.app_label.setText(f"Selected Application: {app_display}")

    def browse_dll(self):
        """Open a dialog box to select a DLL file."""
        # Suggest the current directory or the directory of the current DLL if it exists
        start_dir = os.path.dirname(self.current_dll_path) if self.current_dll_path and os.path.exists(os.path.dirname(self.current_dll_path)) else ""

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select DLL File", # Changed Dialog Title
            start_dir, # Initial directory
            "DLL Files (*.dll);;All Files (*.*)" # Changed Filter text
        )
        if file_path: # If the user selected a file
            self.current_dll_path = file_path
            self.update_ui_labels()
            self.save_config() # Save the change immediately
            # Changed output message
            self.output_area.append(f"DLL selected: {self.current_dll_path}")

    def browse_app(self):
        """Display running processes and allow selection."""
        process_names = set() # Use a set to avoid duplicates
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    # Keep only names ending with .exe (or other executables if needed)
                    # and that are not empty
                    proc_name = proc.info['name']
                    if proc_name and proc_name.lower().endswith(".exe"):
                         process_names.add(proc_name)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    # Ignore processes that have disappeared or that we don't have access to
                    pass
                except Exception as e:
                     # Changed print message
                    print(f"Minor error iterating over process {proc.info.get('pid', '?')}: {e}")


            if not process_names:
                 # Changed MessageBox content
                 QMessageBox.information(self, "Information", "No .exe processes found or accessible.")
                 return

            # Convert to a sorted list for display
            sorted_process_list = sorted(list(process_names))

            # Show a dialog for selection
            item, ok = QInputDialog.getItem(
                self,
                "Select Application", # Changed Dialog Title
                "Running Processes (.exe):", # Changed Prompt text
                sorted_process_list,
                0, # Initially selected index
                False # Not editable
            )

            if ok and item: # If the user clicked OK and selected an item
                self.current_app_name = item
                self.update_ui_labels()
                self.save_config() # Save the change immediately
                # Changed output message
                self.output_area.append(f"Application selected: {self.current_app_name}")

        except Exception as e:
             # Changed MessageBox content
             QMessageBox.critical(self, "Process Error", f"Error retrieving processes: {e}")


    def inject(self):
        """Simulate injection by displaying a message in the text area."""
        if not self.current_dll_path:
             # Changed MessageBox content
            QMessageBox.warning(self, "Action Required", "Please select a DLL file first.")
            return
        if not self.current_app_name:
             # Changed MessageBox content
             QMessageBox.warning(self, "Action Required", "Please select an application first.")
             return

        # Check if the DLL file actually exists before displaying the message
        if not os.path.exists(self.current_dll_path):
             # Changed MessageBox content
             QMessageBox.warning(self, "File Error", f"The specified DLL file does not exist:\n{self.current_dll_path}")
             return

        #Manage injection
        myInjector = pythonInjector.myDllInjector(self.current_dll_path)
        myInjector.setTarget(self.current_app_name)
        if myInjector.pid:
            print(f'Injecting {myInjector.dll_name} to {myInjector.target_process_name}. PID: {myInjector.pid}')
            # Close Dll
            ret = myInjector.inject_dll()
            if ret:
                message = f"'{self.current_dll_path}' injected into '{self.current_app_name}'"
                self.output_area.append(message)
                print(message)  # Also print to the console
            else:
                message = f"'Error: {self.current_dll_path}' NOT injected into '{self.current_app_name}'"
                self.output_area.append(message)
                print(message)  # Also print to the console
            # Close process
            myInjector.close_process()


# --- Application Entry Point ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = InjectorApp()
    window.show()
    sys.exit(app.exec())