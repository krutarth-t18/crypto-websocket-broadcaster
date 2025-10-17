import asyncio
import json
import uvicorn
import logging
import sys
from typing import Dict, Any, Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import websockets


# The latest price updates from Binance will be stored in this queue.
PRICE_QUEUE: asyncio.Queue = asyncio.Queue()

app = FastAPI()

# Binance WebSocket URI for the BTC/USDT Ticker
BINANCE_URI = "wss://stream.binance.com:9443/ws/btcusdt@ticker"

LAST_PRICE_SNAPSHOT: Dict[str, Any] = {}

#Logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler(stream=sys.stdout)
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    "%(asctime)s %(levelname)s [%(name)s:%(lineno)d] %(message)s"
)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


class ClientConnectionManager:
    """Manages active local WebSocket connections and broadcasting."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        """Accepts a new client connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(msg=f"Client connected. Total active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Removes a disconnected client."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(msg=f"Client disconnected. Total active: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        """Sends a message to ALL connected clients concurrently."""
        # Create a list of send tasks
        send_tasks = [conn.send_text(message) for conn in self.active_connections]

        # Use asyncio.gather to run all sends in parallel.
        # return_exceptions=True ensures that if one client disconnects during broadcast,
        # it doesn't crash the entire broadcaster.
        await asyncio.gather(*send_tasks, return_exceptions=True)

client_connection_manager = ClientConnectionManager()


async def binance_listener():
    """Connects to Binance and puts parsed price data into the queue."""
    logger.info(msg="Starting Binance Listener...")
    while True:
        try:
            async with websockets.connect(BINANCE_URI) as websocket:
                logger.info(msg=f"Successfully connected to Binance at {BINANCE_URI}")
                while True:
                    data = await websocket.recv()
                    price_data = json.loads(data)

                    required_data: Dict[str, Any] = {
                        "symbol": price_data.get('s'),
                        "last_price": float(price_data.get('c', 0)),
                        "change_percent": float(price_data.get('P', 0)),
                        "timestamp_ms": price_data.get('E')
                    }

                    # Put the extracted data into the global queue
                    await PRICE_QUEUE.put(required_data)

        except websockets.exceptions.ConnectionClosedOK:
            logger.exception(msg="Binance connection closed gracefully. Attempting to reconnect...")
        except Exception as e:
            logger.exception(msg=f"Binance connection error: {e}. Reconnecting in 5 seconds...")

        # Wait before attempting a reconnect to avoid rapid-fire attempts
        await asyncio.sleep(5)


async def price_broadcaster():
    """Pulls data from the queue and broadcasts it to all connected clients."""
    logger.info(msg="Starting Price Broadcaster...")
    global LAST_PRICE_SNAPSHOT
    while True:
        latest_price = await PRICE_QUEUE.get()

        LAST_PRICE_SNAPSHOT = latest_price

        message_to_send = json.dumps(latest_price)

        # Broadcast the message using the manager
        await client_connection_manager.broadcast(message_to_send)

        PRICE_QUEUE.task_done()


@app.get("/price")
async def get_latest_price():
    """Returns the latest price snapshot as JSON."""
    if LAST_PRICE_SNAPSHOT:
        return LAST_PRICE_SNAPSHOT
    return {"error": "Price data not yet available. Listener may be connecting."}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """The local endpoint for clients to connect (e.g., ws://localhost:8000/ws)."""
    await client_connection_manager.connect(websocket)
    try:
        while True:
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        # Handle the graceful disconnection
        client_connection_manager.disconnect(websocket)
    except Exception as e:
        logger.exception(msg=f"Unexpected WebSocket Error on /ws: {e}")
        client_connection_manager.disconnect(websocket)


listener_task = None
broadcaster_task = None


@app.on_event("startup")
async def startup_event():
    """Starts the two main background tasks when the FastAPI server begins."""
    global listener_task, broadcaster_task

    listener_task = asyncio.create_task(binance_listener())
    broadcaster_task = asyncio.create_task(price_broadcaster())

    logger.info(msg="Server initialized. Background tasks (Listener & Broadcaster) are running.")


@app.on_event("shutdown")
async def shutdown_event():
    """Gracefully cancels the background tasks when the server stops."""
    if listener_task:
        listener_task.cancel()
    if broadcaster_task:
        broadcaster_task.cancel()
    logger.info(msg="Server shutting down. Background tasks canceled.")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)