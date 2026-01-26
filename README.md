<div align="center">

# 🎬 Kitsu Project Ingester

<!-- Badges -->

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20|%20macOS%20|%20Linux-lightgrey?style=for-the-badge&logo=linux&logoColor=white)](https://github.com/bharathadolf/Kitsu-Project-Setup)
[![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)](https://github.com/bharathadolf/Kitsu-Project-Setup)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

**A professional tool for managing VFX project structures and ingesting metadata into Kitsu.**

[Getting Started](#-getting-started) • [Features](#-features) • [Auto-Updates](#-auto-updating-system) • [Support](#-support)

</div>

---

## 🚀 Overview

**Kitsu Project Ingester** is a robust desktop application designed to streamline the setup of VFX productions. It allows supervisors and coordinators to visualize, modify, and ingest project hierarchies (Projects -> Sequences -> Shots) directly into the Kitsu production tracking system.

But it's more than just an app—it's a **fully managed ecosystem**. With our custom **Auto-Updating Launcher**, your entire team stays in sync with the latest tools automatically.

## ✨ Features

- **🎨 Intuitive UI**: Built with PySide (Qt) for a responsive, modern experience.
- **🔄 Auto-Updating Launchers**: "Set it and forget it." The launcher monitors the repository for changes and updates the app automatically.
- **📂 Dynamic Hierarchy**: Create complex project structures (Sequences, Shots) with strict rule-based logic.
- **🛠 Kitsu Integration**: Seamlessly syncs your local planning with your remote Kitsu instance.
- **🖥 Cross-Platform**: Works effortlessly on Windows, macOS, and Linux.

---

## 📦 Getting Started

You don't need to manually install Python dependencies or manage git repos. **Just download the launcher.**

### 🖥 For Windows Users

1.  **Download** the `launcher.bat` file from this repository.
    > [!TIP]
    > You can save this file anywhere (e.g., your Desktop).
2.  **Double-click** `launcher.bat`.
3.  **That's it!** The script will:
    - Initialize the environment.
    - Download the latest code.
    - Launch the application.

### 🍎 For macOS / 🐧 Linux Users

1.  **Download** the `launcher.sh` file.
2.  Open your terminal and run:
    ```bash
    chmod +x launcher.sh
    ./launcher.sh
    ```

---

## 🔄 Auto-Updating System

This project features a **Zero-Maintenance** deployment strategy.

### How it works

The `launcher.bat` file runs continuously in the background while you work.

1.  **Monitors**: Checks GitHub every **10 seconds** for updates.
2.  **Detects**: If a developer pushes new code, the launcher sees the change.
3.  **Updates**: It automatically **closes** your running application, **downloads** the new update, and **restarts** the app instantly.

> [!NOTE]
> You will see a log window confirming your connection status:
> `[MONITOR] Check #42 at 14:00:00 - System is up to date ...`

---

## 🛠 Tech Stack

- **Language**: Python 3.10+
- **GUI Framework**: PySide2 / PySide6 (Qt)
- **Deployment**: Batch/Shell Scripting + Git
- **VFX Platform**: Kitsu (Gazu)

---

<div align="center">

**Created by [Bharath Adolf](https://github.com/bharathadolf)**

</div>
