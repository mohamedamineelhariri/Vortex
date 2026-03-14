# 🌌 VORTEX
> **AI-Powered Workspace Organizer**

Vortex is a powerful, intelligent desktop manager that automatically categorizes and organizes your files using AI. It keeps your workspace clean so you can focus on what matters.

<img width="1097" height="746" alt="image" src="https://github.com/user-attachments/assets/b37f46ff-ff93-4a44-a960-f7e7f54b8b9e" />


## ✨ Features

*   **🧠 Direct AI Brain**: Connects directly to **OpenAI** (Cloud) or **Ollama** (Local). No middleware like n8n required.
*   **🔐 Secure Storage**: API keys are stored securely using the **OS Credential Manager** (Windows Credential Locker, macOS Keychain).
*   **🏢 Multi-Model Support**: Swap between models like `gpt-4o-mini`, `phi-4`, or `qwen2.5` on the fly.
*   **🛡️ Suggest Mode**: Review AI suggestions before they happen. Approve or Reject actions with a click.
*   **🚀 Auto-Pilot**: Real-time background monitoring. Drop a file, and watch it categorized instantly.
*   **📂 Smart Branding**: Shortcuts are "branded" with categories (e.g., `[Gaming]-Discord.lnk`) to keep the desktop organized and searchable.
*   **⏪ Undo Capability**: Revert any organizational action instantly with a single button.
*   **🎨 Premium UI**: Modern "Deep Space" dark mode interface built with PyQt6.

## 🛠️ Tech Stack

*   **Frontend**: Python (PyQt6)
*   **Backend**: Python (Watchdog, Keyring)
*   **Intelligence**: OpenAI API / Ollama (Local LLM)

## 🚀 Getting Started

### Prerequisites
*   Python 3.10+
*   An OpenAI API Key **OR** [Ollama](https://ollama.com/) installed locally.

### Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/mohamedamineelhariri/Vortex.git
    cd Vortex
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run VORTEX**
    ```bash
    python src/ui/gui_main.py
    ```

4.  **Configuration**
    *   Enter your **OpenAI API Key** in the UI (it will be saved securely).
    *   Or switch to **Ollama** and hit the **Detect** button to use local models.

## 🏭 FabLab / Makerspace Edition
Vortex includes specialized support for shared institution machines and maker spaces.

### Features
*   **CAD/CAM Support**: Deep recognition for `.stl`, `.obj`, `.dxf`, `.step`, `.gcode`, `.ino` (Arduino), and `.f3d` (Fusion 360).
*   **Project Grouping**: Automatically groups files by project context rather than just extension.

## 🎮 Usage

*   **Quick Scan**: Scans existing files on your Desktop/Downloads and queues them for review.
*   **AI Engine**: Use the dashboard panel to swap providers or models without restarting.
*   **Pending Actions**: Hover over suggestions in the table and click **✔** to approve or **✘** to reject.
*   **Undo**: Reverses the last file rename or move operation.

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.

