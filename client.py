import asyncio
import json
import subprocess
import websockets
import os
import sys
import uuid

terminal_log = "Client started\n"
async def listen(uri):
    global terminal_log
    client_id = sys.argv[2] or uuid.uuid4()
    
    uri_with_id = uri if not client_id else f"{uri}?client_id={client_id}"
    while True:
        try:
            async with websockets.connect(uri_with_id) as websocket:
                print(f"Connected to {uri_with_id}")
                
                if not client_id:
                    init_msg = await websocket.recv()
                    try:
                        data = json.loads(init_msg)
                        if data.get("type") == "id":
                            client_id = data.get("content")
                            print(f"Assigned client id: {client_id}")
                            with open(CLIENT_ID_FILE, "w") as f:
                                f.write(client_id)
                    except Exception as e:
                        print("Error parsing init message:", e)
                        
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        msg_type = data.get('type')
                        content = data.get('content')
                        if msg_type == "execute":
                            print(f"Executing command: {content}")
                            
                            result = subprocess.run(content, shell=True, capture_output=True, text=True)
                            output = f"$ {content}\n" + result.stdout
                            if result.stderr:
                                output += result.stderr
                            
                            terminal_log += output + "\n"
                            print("Updated terminal log:")
                            print(terminal_log)
                            
                            response = json.dumps({"type": "output", "content": terminal_log})
                            await websocket.send(response)
                    except Exception as e:
                        print(f"Error processing message: {e}")
        except Exception as e:
            print(f"Connection error: {e}. Retrying in 5 seconds.")
            await asyncio.sleep(5)

if __name__ == '__main__':
    uri = f"ws://{sys.argv[1]}/ws"
    asyncio.get_event_loop().run_until_complete(listen(uri))
