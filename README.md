# ElectroNinja - Electrical Engineer Agent

ElectroNinja is an interactive circuit design assistant built with Python and PyQt5. Leveraging OpenAI’s language models and a FAISS-based vector database, ElectroNinja helps electrical engineers generate LTSpice schematic files (.asc) based on user requests, provides a chat interface for design assistance, and integrates with LTSpice for simulation and circuit preview.

## Features

- **Interactive GUI:**  
  A PyQt5-based interface that includes a chat panel, code editor, and circuit preview pane for a seamless design experience.
  
- **LLM-Powered Circuit Generation:**  
  Uses OpenAI models (e.g., `o3-mini` for circuit code generation and `gpt-4o-mini` for chat responses) to generate valid LTSpice (.asc) files based on natural language requests.

- **Semantic Example Retrieval:**  
  Implements a FAISS vector database to store and retrieve circuit examples, which are used to inform and guide the code generation process.

- **LTSpice Integration:**  
  Provides functionality to compile, save, and even launch circuit designs in LTSpice.

- **Image Analysis:**  
  Includes a vision module that can analyze circuit images to verify whether they match the user’s requirements.

## Project Structure

- **ingest_examples.py**  
  Ingests and indexes circuit examples into the FAISS vector database.

- **main.py**  
  The primary application entry point for the full ElectroNinja experience, which integrates the chat manager, vector DB, and GUI components.

- **retrieve.py**  
  A command-line tool to perform semantic searches over stored circuit examples.

- **chat_manager.py**  
  Handles LLM interactions for generating both LTSpice circuit code and friendly chat responses.

- **vector_db.py**  
  Manages document embedding and storage using a FAISS index for semantic search.

- **vision.py**  
  Analyzes circuit images by interfacing with an OpenAI model that supports image inputs.

- **circuit_saver.py**  
  Automates saving and exporting circuit designs from LTSpice, including conversion of schematics to PNG.

- **chat_panel.py**  
  Implements a scrollable chat panel for displaying conversation history with adaptive bubble sizing.

## Prerequisites

### LTSpice Installation

Ensure that LTSpice is installed on your system. You can download it from the [Analog Devices LTSpice page](https://www.analog.com/en/design-center/design-tools-and-calculators/ltspice-simulator.html). This tool is required for simulating and previewing circuit designs. Change the ltspice_path varible in \circuit\circuit_saver.py and \gui\middle_panel.py to the path of LT SPICE .exe file

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/electroninja.git
   cd electroninja

2. **Install the dependencies**
 
   ```bash
   pip install -r requirements.txt
## ⚠️ Note for macOS Users

Some dependencies in this project require additional installation steps on macOS:

- **`pyautogui`** requires the Quartz framework. Install it using:
  ```sh
  pip install pyobjc-framework-Quartz
`pywinauto` and `pygetwindow` are Windows-only libraries. These should be skipped on macOS as they are not required for macOS users.
`faiss-cpu` may require installation via Homebrew before using pip.


3. **Set Up Environment Variables**

  Create a file named `.env` in the root directory of the project and add your OpenAI API key:

  ```bash
  OPENAI_API_KEY=your_openai_api_key_here
  ```
  
## Usage

### Running the Application

Launch the full ElectroNinja interface with:

```bash
python main.py
```
Give instructions for designing circuit in the right panel.

Once asc file has been generated in the left panel, click "Compile Circuit" button to visualize ciruit.

The circuit would be displayed in the central panel, click the "Edit with LT SPICE" button to edit circuit in LT SPICE.






