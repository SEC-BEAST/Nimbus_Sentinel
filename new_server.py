#!/usr/bin/env python3

# Required Libraries
import importlib.metadata
import os
import asyncio
import websockets
import json
import logging
from openstack import connection
from art import text2art
from dotenv import load_dotenv
from aiolimiter import AsyncLimiter
from collections import defaultdict
from keystoneauth1 import loading, session
from novaclient import client as nvc
from glanceclient import Client as gnc
from neutronclient.v2_0 import client as ntc
import ssl
from dotenv import load_dotenv


# Load Environment Variables
load_dotenv()
#access the variables 
port = os.getenv("PORT")
cert_path = os.getenv("SSL_CERT_PATH")
key_path = os.getenv("SSL_KEY_PATH")

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Rate Limiter
rateLimiter = AsyncLimiter(10, 60)
attempts = defaultdict(int)
timestamps = defaultdict(float)

# SSL Configuration
#SSL_CERTIFICATE_PATH = os.getenv("SSL_CERT_PATH")
#SSL_KEY_PATH = os.getenv("SSL_KEY_PATH")

# Helper Functions

def clear_terminal() -> None:
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner() -> None:
    """Print server banner."""
    banner = text2art("OPENSTACK SERVER", font="usa_flag")
    print(banner)

def check_required_libraries(libraries: list) -> tuple[bool, list]:
    """Check if required libraries are installed."""
    missing = []
    for library in libraries:
        try:
            importlib.metadata.version(library)
        except importlib.metadata.PackageNotFoundError:
            missing.append(library)
    return not missing, missing

def authenticate_client(credentials: dict) -> tuple[bool, object, object, object]:
    """Authenticate user with OpenStack and return session details."""
    try:
        loader = loading.get_plugin_loader('password')
        auth = loader.load_from_options(
            auth_url="http://localhost/identity",
            username=credentials["username"],
            password=credentials["password"],
            project_name=credentials["project_name"],
            user_domain_name='Default',
            project_domain_name='Default',
        )
        user_session = session.Session(auth=auth)
        nova = nvc.Client('2.0', session=user_session)
        glance = gnc('2', session=user_session)
        neutron = ntc.Client(session=user_session)
        logging.info("Authentication successful for user: %s", credentials["username"])
        return True, nova, glance, neutron
    except Exception as error:
        logging.warning("Authentication failed: %s", str(error))
        return False, None, None, None

async def list_images(websocket: object, glance: object) -> None:
    """Send the list of images to the client."""
    try:
        images = glance.images.list()
        image_info = "\n".join([f"{img.id} : {img.name}" for img in images]) or "No images available."
	#logging.info(f"Images sent to client:{image_info}")
        await websocket.send(image_info)
    except Exception as error:
        await websocket.send(f"Failed to fetch images: {error}")
	#logging.error(f"Errors listing images :{error}")

async def handle_client(websocket: object) -> None:
    """Handle client requests including authentication and resource listing."""
    client_ip = websocket.remote_address[0]
    authenticated = False
    nova, glance, neutron = None, None, None

    try:
        async for message in websocket:
            if not authenticated:
                try:
                    credentials = json.loads(message)
                    current_time = asyncio.get_event_loop().time()
                    if current_time - timestamps[client_ip] >= 900:
                        attempts[client_ip] = 0
                    timestamps[client_ip] = current_time

                    if attempts[client_ip] >= 5:
                        await websocket.send("Too many attempts. Please wait before trying again.")
                        logging.warning("Rate limit exceeded for %s", client_ip)
                        continue

                    async with rateLimiter:
                        authenticated, nova, glance, neutron = authenticate_client(credentials)
                        attempts[client_ip] += 1

                        if authenticated:
                            await websocket.send("Authentication successful.")
                            logging.info("Client %s authenticated successfully.", client_ip)
                        else:
                            await websocket.send("Authentication failed. Check your credentials.")
                            logging.warning("Authentication failed for %s.", client_ip)
                except json.JSONDecodeError:
                    await websocket.send("Invalid request format.")
                    logging.warning("Malformed request from %s", client_ip)
            else:
                if message == "lsimage":
                    await list_images(websocket, glance)
                else:
                    await websocket.send("Unknown command.")

    except websockets.exceptions.ConnectionClosed:
        logging.info("Client %s disconnected.", client_ip)

# Main Execution
async def main() -> None:
    """Run the WebSocket server."""
    required_libraries = ["art", "websockets", "openstacksdk"]
    installed, missing = check_required_libraries(required_libraries)
    if not installed:
        print("Missing libraries:", ", ".join(missing))
        return

    clear_terminal()
    print_banner()

    bind_ip = "0.0.0.0"
    bind_port = int(os.getenv("PORT", 8090))

#    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
#    ssl_context.load_cert_chain(SSL_CERTIFICATE_PATH, SSL_KEY_PATH)

    async with websockets.serve(handle_client, bind_ip, bind_port): #, ssl=ssl_context):
        print(f"Server started on wss://{bind_ip}:{bind_port}")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
