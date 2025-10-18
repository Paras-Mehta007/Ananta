# Ananta - Offline AI Knowledge Server with LAN-based UI

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![LAN](https://img.shields.io/badge/LAN-Offline-orange)
![AI Model](https://img.shields.io/badge/LLaMA3-8B-purple)
![Multithreading](https://img.shields.io/badge/Multithreading-✔️-brightgreen)

Ananta is a **LAN-based AI knowledge server** that allows multiple clients to interact with a high-performance AI model **without internet access**. It combines a **Python backend** hosting **Meta's LLaMA 3:8B model** with a **frontend UI built using HTML, CSS, and JavaScript** for easy client interaction.  

The system integrates advanced **operating system concepts** like multithreading, mutex, semaphores, and caching to provide a **robust, low-latency, offline AI experience**.

---

## 🏗️ Architecture

![Ananta Architecture](assets/architecture.png)

**Flow:**
- Client (HTML/CSS/JS) ↔ Python Server (LAN TCP/UDP)  
- Server handles AI requests, caching, and context saving  
- Multithreading, Mutex, Semaphore ensure concurrency safety  

---

## ✨ Features

| Feature | Icon | Description |
|---------|------|-------------|
| Offline AI | 🤖 | LLaMA 3:8B runs fully offline |
| LAN Networking | 🌐 | TCP/UDP sockets for client-server communication |
| Context Saving | 🧠 | Maintains conversation across multiple queries |
| Multithreading | 🧵 | Handles multiple clients concurrently |
| Caching | ⚡ | Reduces response time for repeated queries |
| Full-stack UI | 💻 | HTML, CSS, JS frontend for user interaction |

---

## 🛠️ Technologies Used

- **Frontend:** HTML, CSS, JavaScript  
- **Backend / Server:** Python 3, Meta LLaMA 3:8B  
- **Networking:** TCP/UDP sockets for LAN  
- **Concurrency & OS Concepts:** Multithreading, mutexes, semaphores  
- **Caching & Context Management**  

---

## 💻 Installation & Usage

1. **Clone the repository**
```bash
git clone https://github.com/Paras-Mehta007/Ananta-.git
cd Ananta-
