import os, time, shutil, subprocess, psutil, tempfile
import fitz  # PyMuPDF
from PIL import Image  # pillow
import pygetwindow as gw
from pywinauto import Application

ltspice_path = r"C:\Users\vleou\AppData\Local\Programs\ADI\LTspice\LTspice.exe"

def circuit_saver(original_asc_file, new_window=True):
    """
    Processes an ASC file with LTSpice and produces a PDF and a PNG image.
    Uses a fixed output directory (data/output). If the original file is already in that
    directory, a temporary file is used to avoid SameFileError.
    """
    output_directory = os.path.join(os.getcwd(), "data", "output")
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    print(f"📂 Using fixed output directory: {output_directory}")

    asc_filename = os.path.basename(original_asc_file)
    copied_asc_file = os.path.join(output_directory, asc_filename)

    if os.path.abspath(original_asc_file) == os.path.abspath(copied_asc_file):
        print("Source and destination are the same file. Using a temp file for the LTSpice copy...")
        temp_asc = tempfile.NamedTemporaryFile(delete=False, suffix=".asc", dir=output_directory)
        temp_asc_name = temp_asc.name
        temp_asc.close()
        shutil.copyfile(original_asc_file, temp_asc_name)
        asc_to_use = temp_asc_name
    else:
        shutil.copyfile(original_asc_file, copied_asc_file)
        asc_to_use = copied_asc_file

    print(f"✅ The file to be processed by LTSpice is {asc_to_use}")

    output_pdf = os.path.join(output_directory, "output.pdf")
    png_file = os.path.join(output_directory, "output.png")

    if new_window:
        subprocess.Popen([ltspice_path, asc_to_use], shell=True)
        time.sleep(2)

    ltspice_window = None
    for window in gw.getWindowsWithTitle(""):
        if "ltspice" in window.title.lower():
            ltspice_window = window
            break
    if ltspice_window:
        print(f"✅ Found LTSpice window: {ltspice_window.title}")
        app = Application().connect(handle=ltspice_window._hWnd)
        window = app.window(handle=ltspice_window._hWnd)
        window.type_keys("^s")
        time.sleep(0.5)
        if os.path.exists(asc_to_use):
            # Use UTF-8 with error replacement to read the file.
            with open(asc_to_use, "r", encoding="utf-8", errors="replace") as f:
                new_content = f.read()
            print(new_content)
        window.type_keys("^p")
        print_window = app.window(title_re=".*Print.*")
        print_window.wait("ready", timeout=5)
        print("✅ Print window detected. Sending commands...")
        print_window.type_keys("{TAB 3}")
        print_window.type_keys("{DOWN}")
        print_window.type_keys("~")
        time.sleep(1)
        print_window.type_keys(output_pdf)
        time.sleep(0.1)
        print_window.type_keys("~")
        max_wait_time = 30
        start_time = time.time()
        print("⏳ Waiting for PDF to be created...")
        while not os.path.exists(output_pdf):
            time.sleep(0.5)
            if time.time() - start_time > max_wait_time:
                print("❌ PDF file was not created within the timeout period.")
                return False
        print(f"✅ PDF exported successfully: {output_pdf}")
        # minimize_popups()
        time.sleep(2)
        if os.path.exists(output_pdf):
            doc = fitz.open(output_pdf)
            page = doc[0]
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

        for process in psutil.process_iter(attrs=['pid', 'name']):
            if "LTspice" in process.info['name']:
                print("🛑 Closing LTSpice...")
                subprocess.run(["taskkill", "/F", "/PID", str(process.info['pid'])], shell=True)
                break
        else:
            print("❌ LTSpice process not found.")
            return False

        if os.path.exists(output_pdf):
            os.remove(output_pdf)
            print(f"🗑️ Deleted temporary PDF file: {output_pdf}")

        if os.path.abspath(original_asc_file) != os.path.abspath(asc_to_use):
            print(f"🔄 Copying final schematic from {asc_to_use} to {original_asc_file}")
            shutil.copyfile(asc_to_use, original_asc_file)

        if asc_to_use != copied_asc_file and os.path.exists(asc_to_use):
            try:
                os.remove(asc_to_use)
                print(f"🗑️ Deleted temp file: {asc_to_use}")
            except Exception as e:
                print(f"Could not delete temp file {asc_to_use}: {e}")

        print(f"🎯 All files saved in {output_directory}")
        return (original_asc_file, png_file)
    else:
        print("❌ LTSpice window not found. Make sure LTSpice is open.")
        return False
