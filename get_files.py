import os
import subprocess

# Project description to be added at the top of the output file.
project_description = """
This project is an AI-driven electrical engineering assistant designed to autonomously generate, evaluate, and refine electrical circuits. The workflow begins when a user provides a high-level prompt describing a desired circuit. A language model (LLM) processes the prompt and generates a corresponding LTSpice .asc file, which represents the circuit schematic. This file is then fed into LTSpice, where the circuit is visualized and simulated. Once the simulation is complete, the circuit is extracted as a PDF, which is subsequently converted into a .png image. This image is passed into a vision model that analyzes the circuit for correctness, compliance with design specifications, and potential errors. The model's evaluation serves as feedback, guiding the refinement process by informing the LLM of necessary modifications to the .asc file, such as correcting wiring errors, improving component placement, or optimizing circuit performance. This loop—comprising prompt processing, circuit generation, simulation, evaluation, and refinement—continues iteratively until a fully functional circuit is achieved. The project integrates multiple components, including LLM-based text generation, vector databases for knowledge retrieval, LTSpice for simulation, computer vision for schematic analysis, and a feedback-driven improvement loop to enhance circuit accuracy over time. The existing implementation is structured into a monolithic set of scripts but can be improved through modularization, ensuring better debugging, maintainability, and scalability. Refinements should focus on breaking down tasks into dedicated modules, such as separate handling for file management, circuit generation, vision processing, simulation control, and feedback mechanisms, ultimately making the agent more robust and efficient.
"""

def is_meaningful_file(file_name):
    """
    Check if a file is meaningful based on its extension or specific filename.
    Adjust allowed_extensions and allowed_no_extension as needed.
    """
    allowed_extensions = {".py", ".txt", ".json", ".env", ".ini", ".md", ".cfg", ".pyw"}
    allowed_no_extension = {"gitignore", ".gitignore"}
    name, ext = os.path.splitext(file_name)
    if ext:
        return ext.lower() in allowed_extensions
    else:
        return file_name in allowed_no_extension

def write_file_contents(output_file, base_path, ignore_dirs=None):
    """
    Walk through the directory and write file titles and content
    to the provided output_file handle, ignoring specified directories.
    """
    if ignore_dirs is None:
        ignore_dirs = []
    for root, dirs, files in os.walk(base_path):
        # Remove directories we want to ignore.
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for file in files:
            if not is_meaningful_file(file):
                continue  # Skip files that are not considered meaningful.
            file_path = os.path.join(root, file)
            header = f"\nFile: {file_path}\n{'-' * (len(file_path) + 6)}\n"
            output_file.write(header)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    output_file.write(f.read() + "\n")
            except Exception as e:
                output_file.write(f"Error reading {file_path}: {e}\n")

if __name__ == "__main__":
    base_directory = "."
    ignore_dirs = ["data", "logs", "__pycache__"]
    output_filename = "output.txt"

    with open(output_filename, "w", encoding="utf-8") as out:
        # Write the project description at the top.
        out.write("Project Description:\n")
        out.write("=" * 20 + "\n")
        out.write(project_description.strip() + "\n\n")

        # Write the directory tree structure.
        out.write("Directory Tree Structure (from 'tree /F'):\n")
        out.write("=" * 40 + "\n")
        try:
            # Execute the 'tree /F' command (Windows only).
            tree_output = subprocess.check_output("tree /F", stderr=subprocess.STDOUT, shell=True)
            # Decode using the OEM code page (commonly cp437 on Windows).
            tree_output = tree_output.decode("cp437")
            out.write(tree_output + "\n")
        except Exception as e:
            out.write(f"Error retrieving tree structure: {e}\n")

        # Write the detailed file titles and contents.
        out.write("\nDetailed File Contents:\n")
        out.write("=" * 30 + "\n")
        write_file_contents(out, base_directory, ignore_dirs)
    
    print(f"Output successfully written to {output_filename}")
