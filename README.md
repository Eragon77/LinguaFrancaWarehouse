# 🏭 Warehouse Digital Twin (V2)

A state-of-the-art **Digital Twin** of a vertical automated warehouse. This project implements a hybrid architecture that leverages **Lingua Franca** for deterministic coordination and **Python** for physical logic, now integrated with the **Frost Framework**.

## 🧠 Architecture

The system is designed with a clear separation of concerns, following the Model-Driven Engineering (MDE) approach:

* **Orchestrator (Lingua Franca):** Acts as the "Logical Time" manager. It coordinates the execution of tasks and ensures deterministic behavior across the simulation.
* **Controller (Python):** Manages the "Business Logic" and physical calculations. It computes movement times ($t = d/v$) and updates the internal state of the robotic platform.
* **Data Model (Frost):** Uses a YAML-based representation to define the warehouse state (trays, slots, and positions), enabling a data-driven simulation.



## 📂 Project Structure

```text
LinguaFrancaWarehouse/
├── src/                 # Lingua Franca source files (.lf)
├── python/              # Core physical logic and controller classes
├── models/              # Data Models (YAML) and Flow Graphs
├── frost/               # Frost Framework (Glacier Project)
├── utils/               # Helper scripts and command loaders
└── requirements.txt     # Python dependencies

🚀 Getting Started
Prerequisites
Lingua Franca (LF) compiler (lfc) installed.

Python 3.10+ with a virtual environment.

Installation
Clone the repository and navigate to the folder:

Bash
git clone <your-repo-link>
cd LinguaFrancaWarehouse
Install the required dependencies:

Bash
pip install -r requirements.txt
Running the Simulation
To compile and run the main factory simulation:

Bash
lfc src/FactoryMain.lf
./bin/FactoryMain
🤖 Note on AI Usage
To ensure code clarity and maintainability, code comments, logging messages, and several test cases in this project were generated and refined with the assistance of Artificial Intelligence tools. The core logic, architecture design, and integration with the Frost framework were implemented manually.

📚 Credits & Citations
This project utilizes the Frost Framework, a simulation platform developed by the Glacier Project. If you use this work, please cite the original paper:

Snippet di codice
@inproceedings{frost:indin:2025,
  author    = {Turco, Pietro and Gaiardelli, Sebastiano and Fraccaroli, Enrico and Lora, Michele and Chakraborty, Samarjit and Fummi, Franco},
  booktitle = {2025 IEEE 23rd International Conference on Industrial Informatics (INDIN)},
  title     = {{Frost: A Simulation Platform for Early Validation and Testing of Manufacturing Software}},
  year      = {2025}
}
Developed as part of a Digital Twin research project.