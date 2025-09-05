# Windows Setup Guide for Local LLM Browser Automation

This guide provides instructions for setting up and running the browser automation agent with a local LLM on a Windows machine.

## 1. Install Ollama on Windows

Ollama is the tool used to run the local Large Language Model (LLM).

1.  **Download Ollama for Windows:** Go to the [Ollama website](https://ollama.com/) and download the installer for Windows.
2.  **Run the installer:** Follow the instructions in the installer to set up Ollama on your system.
3.  **Verify installation:** Open a Command Prompt or PowerShell and run the following command to make sure Ollama is running:
    ```bash
    ollama --version
    ```
4.  **Pull the required model:** The examples use the `llama4:scout` model. Pull it by running:
    ```bash
    ollama pull llama4:scout
    ```

## 2. Set up the Python Environment

1.  **Clone the repository:** If you haven't already, clone this repository to your local machine.
2.  **Install Python:** Make sure you have Python 3.8 or higher installed. You can download it from the [official Python website](https://www.python.org/downloads/).
3.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```
4.  **Install dependencies:** Use the `requirements-local.txt` file to install the necessary Python packages.
    ```bash
    pip install -r requirements-local.txt
    ```
5. **Install Playwright browsers:**
    ```bash
    playwright install
    ```

## 3. Configure Environment Variables

The agent needs to know the URL of your local Ollama instance.

1.  **Create a `.env` file:** In the root of the project, create a new file named `.env`.
2.  **Set the `OLLAMA_BASE_URL`:** Add the following line to your `.env` file. The default URL should work for most standard Ollama installations.
    ```
    OLLAMA_BASE_URL=http://localhost:11434/v1
    ```
    If you have configured Ollama to run on a different address or port, update this value accordingly.

## 4. Run the Local Examples

You can now run the example scripts that use your local LLM.

*   **Google Search Example:**
    ```bash
    python examples/google_search_local.py
    ```
*   **Super Bowl Search Example:**
    ```bash
    python examples/superbowl_search_local.py
    ```
*   **Production Visual Agent:**
    ```bash
    python production_visual_agent_local.py
    ```

You are now set up to run the visual browser automation agent with a local LLM on your Windows machine!
