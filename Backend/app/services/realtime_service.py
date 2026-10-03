import asyncio
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class RealtimeSafetyManager:
    """
    Manages real-time SSE (Server-Sent Events) connections for safety updates.
    Routes events from synchronous backend services (like TelemetryService)
    to asynchronous FastAPI streaming endpoints.
    """
    def __init__(self):
        # Maps device_id -> List of active asyncio.Queue instances
        self.active_connections: Dict[str, List[asyncio.Queue]] = {}
        # Stores the main FastAPI event loop, captured when the first client connects
        self.loop: Optional[asyncio.AbstractEventLoop] = None

    async def subscribe(self, device_id: str) -> asyncio.Queue:
        """Called by the async SSE endpoint to create a new subscription."""
        if self.loop is None:
            self.loop = asyncio.get_running_loop()
            
        if device_id not in self.active_connections:
            self.active_connections[device_id] = []
            
        queue = asyncio.Queue()
        self.active_connections[device_id].append(queue)
        logger.info(f"Client subscribed to real-time safety updates for device {device_id}. Total connections: {len(self.active_connections[device_id])}")
        return queue

    def unsubscribe(self, device_id: str, queue: asyncio.Queue):
        """Removes a subscription when the SSE connection drops."""
        if device_id in self.active_connections:
            if queue in self.active_connections[device_id]:
                self.active_connections[device_id].remove(queue)
            if not self.active_connections[device_id]:
                del self.active_connections[device_id]
                logger.info(f"No more active real-time connections for device {device_id}.")

    def publish_safety_update(self, device_id: str, payload: dict):
        """
        Called by sync services (like TelemetryService) to broadcast an update.
        Safely schedules the event queue `put` onto the main async event loop.
        """
        if device_id in self.active_connections and self.loop and self.loop.is_running():
            for q in self.active_connections[device_id]:
                try:
                    asyncio.run_coroutine_threadsafe(q.put(payload), self.loop)
                except Exception as e:
                    logger.error(f"Failed to enqueue real-time event for device {device_id}: {e}")

realtime_manager = RealtimeSafetyManager()
