# 🌌 VORTEX
> **AI-Powered Workspace Organizer**

Vortex is a powerful, intelligent desktop manager that automatically categorizes and organizes your files using AI. It keeps your workspace clean so you can focus on what matters.

<img width="1097" height="746" alt="image" src="https://github.com/user-attachments/assets/b37f46ff-ff93-4a44-a960-f7e7f54b8b9e" />


## ✨ Features

*   **🧠 AI Brain**: Uses OpenAI (via n8n) to intelligently understand file content and context, not just extensions.
*   **🛡️ Suggest Mode**: Reviews changes before they happen. Approve or Reject actions with a click.
*   **🚀 Auto-Pilot**: Real-time background monitoring. Drop a file, and watch it fly to the right folder instantly.
*   **⏪ Undo Capability**: Made a mistake? Revert moves instantly with the Undo button.
*   **🎨 Premium UI**: "Deep Space" dark mode interface built with PyQt6. Frameless, modern design.
*   **📂 Smart Sorting**: Automatically creates subfolders (e.g., `Documents/Invoices`, `Code/Python`, `Images/Screenshots`).

## 🛠️ Tech Stack

*   **Frontend**: Python (PyQt6)
*   **Backend**: Python (Watchdog, Requests)
*   **Intelligence**: n8n (Workflow Automation) + OpenAI GPT-4

## 🚀 Getting Started

### Prerequisites
*   Python 3.10+
*   Git
*   [n8n](https://n8n.io/) (Self-hosted or Cloud)

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

3.  **Setup the Brain (n8n)**
    *   Import `n8n/antigravity_workflow_v6.json` into your n8n instance.
    *   Configure your OpenAI credentials in the n8n node.
    *   Activate the workflow.
    *   Update `config.yaml` with your n8n webhook URL.

4.  **Run VORTEX**
    ```bash
    python src/ui/gui_main.py
    ```

## 🏭 FabLab / Makerspace Edition
**Vortex** is capable of running on shared institution machines.

### Features
*   **CAD/CAM Support**: Recognizes `.stl`, `.obj`, `.dxf`, `.gcode`, `.ino` and more.
*   **Project Grouping**: Designed for shared users. It attempts to group files into Project folders rather than generic timestamps.
*   **Setup**: Import `n8n/fablab_workflow_v1.json` for the specialized logic.

## 🎮 Usage

*   **Quick Scan**: Scans existing files on your Desktop/Downloads and queues them for review.
*   **Auto-Pilot**: Toggles the background watcher. When active (Green), it monitors for *new* files.
*   **Pending Actions**: Review the AI's suggestions. Click **✔** to approve or **✘** to reject.
*   **Undo**: Reverses the last file move operation.

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.
