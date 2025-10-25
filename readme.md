# 🌟 Crypto Price Real-Time WebSocket Broadcaster

### 🎯 Project Objective

This project implements a robust, real-time data pipeline in Python using the modern, asynchronous ASGI stack. The primary goal is to fetch live cryptocurrency price data from an external WebSocket source (Binance) and efficiently **broadcast it to multiple connected clients** via a local WebSocket server built with FastAPI.

This solution demonstrates proficiency in asynchronous programming (`asyncio`), WebSocket protocol handling, and inter-task communication via message queues.

---

### 🏛️ Architecture & Flow

The application runs as a single, highly concurrent Python process, leveraging `asyncio` to manage the lifecycle of two main background tasks and the core API server.

| Component | Role | Technology Used |
| :--- | :--- | :--- |
| **Binance Listener** (Producer) | Connects to the external Binance stream and extracts raw price data. | `websockets` (Client) |
| **`asyncio.Queue`** | Safely buffers extracted price data between the Listener and the Broadcaster. | `asyncio` |
| **Price Broadcaster** (Consumer) | Consumes data from the queue, updates the snapshot, and broadcasts to all active clients. | `asyncio` |
| **Local WebSocket Server** | Manages client connections on the `/ws` endpoint and handles graceful disconnections. | `FastAPI` |

$$\text{Binance WebSocket} \xrightarrow{\text{Data Extraction}} \text{Your Listener} \xrightarrow{\text{asyncio.Queue}} \text{Price Broadcaster} \xrightarrow{\text{WebSocket Broadcast}} \text{Clients}$$

---

### ⚙️ Local Setup and Installation

Follow these steps to set up and run the project locally.

#### Prerequisites

* Python 3.8+

#### Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/krutarth-t18/crypto-websocket-broadcaster.git
    cd crypto-websocket-broadcaster
    ```

2.  **Install Dependencies:**
    The required packages (`fastapi`, `uvicorn`, `websockets`) are listed in `requirements.txt`.
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Server:**
    ```bash
    python main.py
    ```
    The server will start on `http://0.0.0.0:8000`. You will see console output confirming the Binance Listener and Price Broadcaster tasks have started concurrently.

---

### 🧪 Testing the Real-Time Feed

You can test the WebSocket functionality using the included HTML client file or any dedicated WebSocket testing tool.

#### Option 1: Using the Included HTML Client (Recommended)

1.  Ensure the server is running (`python main.py`).
2.  Open the included file **`/public/index.html`** in your web browser.
3.  Click the **"Connect"** button.
4.  The client will connect to `ws://localhost:8000/ws` and immediately display the live price updates.
5.  Test the **"Disconnect"** button to confirm graceful connection handling on the server side.

#### Option 2: Using the REST API (Bonus Feature)

The application includes a REST endpoint that returns the latest price snapshot.

* **Endpoint:** `GET /price`
* **URL:** `http://localhost:8000/price`
* **Response Example:**
    ```json
    {
      "symbol": "BTCUSDT", 
      "last_price": 60500.5, 
      "change_percent": 1.25, 
      "timestamp_ms": 1678886400000
    }
    ```

---

### ⚠️ Note on Deployment (Vercel/Netlify)

This application is designed as a **long-running Python asynchronous process** to maintain persistent WebSocket connections.

Due to their serverless and function-based architectures, **Vercel and Netlify do not support true, long-running WebSockets.**

For a production deployment, this application would require a dedicated container service or virtual machine environment (e.g., **Render**, AWS EC2, or Azure Container Apps) capable of hosting a long-lived process.