import os
import time
import shutil
import subprocess
import psutil
import fitz  # PyMuPDF
from PIL import Image #pillow
import pygetwindow as gw
import pyautogui
from pywinauto import Application

# Define file paths
ltspice_path = r"C:\Users\leegj\AppData\Local\Programs\ADI\LTspice\LTspice.exe"

def circuit_saver(original_asc_file, new_window = True):
    base_output_dir = os.path.join(os.getcwd(), "data", "output")
    # Step 1: Create a timestamped directory at the start
    iteration = 0
    while os.path.exists(os.path.join(base_output_dir, f"output-{iteration}")):
        iteration += 1
    output_directory = os.path.join(os.getcwd(), f"data\output\output-{iteration}")
    os.makedirs(output_directory)
    print(f"📂 Created output directory: {output_directory}")

    # Step 2: Copy the original .asc file into the timestamped directory
    asc_filename = os.path.basename(original_asc_file)
    copied_asc_file = os.path.join(output_directory, asc_filename)
    shutil.copy(original_asc_file, copied_asc_file)
    print(f"✅ Copied original .asc file to {copied_asc_file}")

    # Define paths inside the timestamped directory
    output_pdf = os.path.join(output_directory, "output.pdf")
    png_file = os.path.join(output_directory, "output.png")

    if new_window == True:
    # Step 3: Open LTSpice with the copied schematic file (runs in background)
        subprocess.Popen([ltspice_path, copied_asc_file], shell=True)
        time.sleep(2)  # Increased delay for LTSpice to load

    # Step 4: Find LTSpice window (case insensitive search)
    ltspice_window = None
    for window in gw.getWindowsWithTitle(""):
        if "ltspice" in window.title.lower():
            ltspice_window = window
            break


    if ltspice_window:
        print(f"✅ Found LTSpice window: {ltspice_window.title}")

        # Step 5: Connect to LTSpice in background
        app = Application().connect(handle=ltspice_window._hWnd)
        window = app.window(handle=ltspice_window._hWnd)

        # Step 6: Save the schematic using Ctrl + S
        window.type_keys("^s")  # Ctrl + S to save changes
        time.sleep(0.5)
        if os.path.exists(original_asc_file):
            with open(copied_asc_file, "r") as f:       
                new_content = f.read()
        print(new_content)

        # # Read the original content for comparison
        # with open(original_asc_file, "r") as f:
        #     original_content = f.read()

        # max_attempts = 20  # Limit attempts to prevent infinite loops
        # attempt = 0

        # while attempt < max_attempts:
        #     pyautogui.hotkey('ctrl', 's')
        #     time.sleep(0.2)        # Wait a short moment for LTSpice to process and save
        #     with open(copied_asc_file, "r") as f:
        #         copied_content = f.read()
        #     if copied_content != original_content:
        #         print("✅ File updated successfully!")
        #         print(original_content, copied_content)
        #         break
        #     attempt += 1
        # else:
        #     print("❌ File content did not change after multiple attempts.")

        # Step 7: Open Print Dialog and wait for it to be ready
        window.type_keys("^p")  # Ctrl + P for Print

        # Step 8: Ensure the Print window is ready before sending keystrokes
        print_window = app.window(title_re=".*Print.*")  # Match any print dialog
        print_window.wait("ready", timeout=5)

        print("✅ Print window detected. Sending commands...")

        # Step 9: Select the correct printer and enter file name
        print_window.type_keys("{TAB 3}")  # Navigate to printer selection
        print_window.type_keys("{DOWN}")  # Select next available printer

        print_window.type_keys("~")  # Press Enter to confirm print
        time.sleep(1)
        print_window.type_keys(output_pdf)  # Enter file name
        time.sleep(0.1)
        print_window.type_keys("~")  # Press Enter to save

        max_wait_time = 30  # Maximum wait time (in seconds)
        start_time = time.time()

        print("⏳ Waiting for PDF to be created...")
        while not os.path.exists(output_pdf):
            time.sleep(0.5)  # Check every second
            if time.time() - start_time > max_wait_time:
                print("❌ PDF file was not created within the timeout period.")
                exit()

        print(f"✅ PDF exported successfully: {output_pdf}")
        time.sleep(2)

        # Step 10: Convert PDF to Square PNG
        if os.path.exists(output_pdf):
            doc = fitz.open(output_pdf)
            page = doc[0]  # First page
            pix = page.get_pixmap(dpi=300)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            width, height = img.size
            new_size = width
            crop_y = max(0, (height - new_size) // 2)

            square_img = img.crop((0, crop_y, width, crop_y + new_size))
            square_img.save(png_file, "PNG")

            doc.close()
            time.sleep(0.5)

            print(f"✅ Converted {output_pdf} to a square PNG: {png_file}")
        else:
            print("❌ PNG file was not created. Check LTSpice settings.")
            return False

        # Step 11: Close LTSpice
        for process in psutil.process_iter(attrs=['pid', 'name']):
            if "LTspice" in process.info['name']:
                print("🛑 Closing LTSpice...")
                subprocess.run(["taskkill", "/F", "/PID", str(process.info['pid'])], shell=True)
                break
        else:
            print("❌ LTSpice process not found.")
            return False

        # Step 12: Delete the temporary PDF file and update the original file with the most recent changes
        if os.path.exists(output_pdf):
            os.remove(output_pdf)
            print(f"🗑️ Deleted temporary PDF file: {output_pdf}")
        shutil.copy(original_asc_file, copied_asc_file)

        print(f"🎯 All files saved in {output_directory}")

        return (original_asc_file, png_file)

    else:
        print("❌ LTSpice window not found. Make sure LTSpice is open.")
        return False

