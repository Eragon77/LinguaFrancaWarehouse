🏭 Warehouse Digital Twin (V2)

A Digital Twin of a vertical automated warehouse. This project uses a hybrid architecture that combines Lingua Franca (for time management) and Python (for physical logic).

The system simulates the movement of a robotic platform, handling trays, slots, and queues with realistic timing.

🧠 Architecture

The project separates responsibilities into two main parts:

Orchestrator (Lingua Franca): It manages the "Logical Time". It decides when an action happens but does not know how it happens.

Controller (Python): It manages the "Business Logic". It calculates the time required for physical movements ($Time = Distance / Speed$) and manages the state of the warehouse.








🤖 Note on AI Usage

To ensure code clarity and maintainability, code comments and logging messages in this project were generated and refined with the assistance of Artificial Intelligence tools. The core logic and architecture were designed and implemented manually.
