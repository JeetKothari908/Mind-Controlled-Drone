import asyncio
import json
import websockets

PHONE_WS_URL = "ws://192.168.1.50:8765"  # <-- phone + port (you'll set this)

async def send(cmd: dict):
    async with websockets.connect(PHONE_WS_URL) as ws:
        await ws.send(json.dumps(cmd))
        resp = await ws.recv()
        print("response:", resp)

async def main():
    # Examples
    await send({"type": "connect"})
    await send({"type": "takeoff"})
    await send({"type": "virtual_stick", "roll": 0.0, "pitch": 2.0, "yaw": 0.0, "throttle": 0.0, "duration_ms": 300})
    await send({"type": "land"})

if __name__ == "__main__":
    asyncio.run(main())
