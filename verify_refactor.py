import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'src'))

print("Verifying imports...")

def check_import(module_name):
    try:
        __import__(module_name)
        print(f"[OK] {module_name} imported successfully.")
    except ImportError as e:
        print(f"[FAIL] {module_name} failed to import: {e}")
    except Exception as e:
        print(f"[FAIL] {module_name} failed with error: {e}")

check_import("soniclit.fwh_solver")
check_import("soniclit.signal_processing")
check_import("soniclit.cavity_modes")
check_import("soniclit.audio_generator")
