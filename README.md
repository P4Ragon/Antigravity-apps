# ⚡ Tool Lending Tracker

A modern desktop application for tracking borrowed tools with a sleek **Matrix-inspired** dark UI.

![Platform](https://img.shields.io/badge/Platform-Windows-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

<!-- Add your screenshot here after uploading to GitHub -->
<!-- ![Screenshot](screenshots/main_window.png) -->

## ✨ Features

- **Tool Management** - Add and remove tools from your inventory
- **Borrower Management** - Keep track of people who borrow your tools
- **Lending System** - Record who borrowed what with a single click
- **Currently Borrowed View** - See all active loans at a glance
- **History Logging** - Automatic logging of all lending/return operations
- **Data Persistence** - All data saved locally in JSON format
- **Modern UI** - Dark Matrix-themed interface with neon green accents

## 📦 Installation

### Option 1: Download Pre-built Executable
1. Download `ToolLendingTracker.7z` from [Releases](../../releases)
2. Extract the archive
3. Run `ToolLendingTracker.exe`

### Option 2: Run from Source
```bash
# Clone the repository
git clone https://github.com/yourusername/tool-lending-tracker.git
cd tool-lending-tracker

# Install dependencies (only tkinter required, included with Python)
pip install pyinstaller  # Only if you want to build .exe

# Run the application
python tool_lending_gui.py
```

## 🚀 Usage

1. **Add Tools** - Enter tool name in the TOOLS section and click `+`
2. **Add Borrowers** - Enter person's name in the BORROWERS section and click `+`
3. **Lend a Tool** - Select tool and borrower from dropdowns, click `🔐 LEND`
4. **Return a Tool** - Click `↩ Return` next to the borrowed item
5. **Delete Items** - Select item from list and click `🗑 Delete`

## 📁 Data Files

The application creates these files in its directory:
- `tool_lending_data.json` - Current state (tools, borrowers, active loans)
- `tool_lending_history.log` - Complete history of all lending operations

### Log Format
```
[2026-02-08 14:30:15] LEND: Hammer -> John Smith
[2026-02-08 16:45:22] RETURN: Hammer -> John Smith
```

## 🛠️ Building from Source

```bash
# Create standalone executable
python -m PyInstaller --onefile --noconsole --name ToolLendingTracker tool_lending_gui.py

# Output: dist/ToolLendingTracker.exe
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Made with ⚡ by [Your Name]
