#!/usr/bin/env python3
# tests/test_ltspice_processing.py

import os
import sys
import logging
import platform
import time
import cProfile
import pstats
import io
from dotenv import load_dotenv

# Add parent directory to path to allow imports from the project
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Import from electroninja
from electroninja.config.settings import Config
from electroninja.core.ltspice.interface import LTSpiceInterface

# Load environment variables
load_dotenv()

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_separator(title=None):
    """Print a formatted separator line with an optional title."""
    width = 80
    if title:
        print("\n" + "=" * 20 + f" {title} " + "=" * (width - len(title) - 22) + "\n")
    else:
        print("\n" + "=" * width + "\n")

def test_ltspice_processing(asc_code, prompt_id=1, iteration=0):
    """
    Test the LTSpice processing workflow:
      - Saves the ASC file to data/output/prompt{prompt_id}/output{iteration}/code.asc.
      - Launches LTSpice GUI, prints to PDF, and converts the PDF to a cropped square PNG.
      - Verifies that the expected files and folder structure are created.
    
    Returns:
        Tuple (asc_path, image_path) on success, or None on failure.
    """
    config = Config()
    ltspice = LTSpiceInterface(config)

    print_separator("TEST: LTSPICE PROCESSING")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"LTSpice path: {config.LTSPICE_PATH}")
    print(f"Output directory: {config.OUTPUT_DIR}\n")

    if not os.path.exists(config.LTSPICE_PATH):
        print(f"WARNING: LTSpice not found at {config.LTSPICE_PATH}")
        print("This may cause the test to fail. Please update the path in your .env file.")

    print("ASC Code to Process:\n-------------------")
    if len(asc_code) < 1000:
        print(asc_code)
    else:
        print(asc_code[:1000] + "...")
    print("-------------------\n")

    print_separator("PROCESSING WITH LTSPICE")
    print("Starting LTSpice processing...")
    print(f"Time: {time.strftime('%H:%M:%S')}")

    result = ltspice.process_circuit(asc_code, prompt_id=prompt_id, iteration=iteration)
    finish_time = time.strftime('%H:%M:%S')
    print(f"Processing completed at: {finish_time}\n")

    if not result:
        print_separator("TEST FAILED")
        print("LTSpice processing failed: No result returned.")
        return None

    asc_path, image_path = result
    print_separator("LTSPICE PROCESSING RESULTS")
    print(f"ASC file path: {asc_path}")
    print(f"Image file path: {image_path}")

    if not os.path.exists(asc_path):
        print("Error: ASC file does not exist!")
        return None
    if not os.path.exists(image_path):
        print("Error: Image file does not exist!")
        return None

    print("Successfully processed circuit through LTSpice!\n")

    # Verify file details
    print("Verifying file details:")
    print(f"ASC file exists: {os.path.exists(asc_path)}")
    print(f"Image file exists: {os.path.exists(image_path)}")
    if os.path.exists(image_path):
        print(f"Image file size: {os.path.getsize(image_path)} bytes")

    # Verify folder structure
    output_dir = os.path.dirname(asc_path)
    print("\nVerifying folder structure:")
    print(f"Output directory exists: {os.path.exists(output_dir)}")
    print(f"ASC file named 'code.asc': {asc_path.endswith('code.asc')}")
    print(f"Image file named 'image.png': {image_path.endswith('image.png')}")

    # List files in the output directory
    print("\nListing files in output directory:")
    if os.path.exists(output_dir):
        for file in os.listdir(output_dir):
            file_path = os.path.join(output_dir, file)
            size = os.path.getsize(file_path)
            print(f"  - {file} ({size} bytes)")

    print_separator("TEST COMPLETED SUCCESSFULLY")
    return (asc_path, image_path)

def main():
    test_asc_code = """Version 4
SHEET 1 880 680
WIRE 224 80 80 80
WIRE 336 80 224 80
WIRE 80 128 80 80
WIRE 224 128 224 80
WIRE 336 128 336 80
WIRE 80 240 80 208
WIRE 224 240 224 208
WIRE 224 240 80 240
WIRE 336 240 336 208
WIRE 336 240 224 240
SYMBOL voltage 80 112 R0
SYMATTR InstName V1
SYMATTR Value 50
SYMBOL res 208 112 R0
SYMATTR InstName R1
SYMATTR Value 200
SYMBOL res 320 112 R0
SYMATTR InstName R2
SYMATTR Value 100
TEXT 136 264 Left 2 !.op
"""
    prompt_id = "1"
    iteration = "0"

    result = test_ltspice_processing(test_asc_code, prompt_id, iteration)
    if result:
        asc_path, image_path = result
        print(f"\nTest completed successfully.\nASC file: {asc_path}\nImage file: {image_path}")
    else:
        print("\nTest failed.")

if __name__ == "__main__":
    pr = cProfile.Profile()
    pr.enable()
    main()
    pr.disable()
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('tottime')
    ps.print_stats(10)
    print(s.getvalue())
