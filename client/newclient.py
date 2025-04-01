#!/usr/bin/env python3

# Required libraries to run the client cli.
import importlib.metadata
from art import text2art
import os
import asyncio
import websockets
import json
import pwinput
import ssl
import time
from tabulate import tabulate
import websockets.exceptions
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# SSL Configuration
def get_ssl_context(secure: bool = False) -> ssl.SSLContext:
    """Create and return an SSL context based on security requirements."""
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    
    if secure:
        # Production secure setup
        ssl_context.check_hostname = True
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context.load_verify_locations('/etc/ssl/certs/ca-certificates.crt')
    else:
        # Development setup (less secure but easier for testing)
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
    
    return ssl_context

# Clear the terminal before starting the client.
def clearTerminal() -> None:
    '''Clears the terminal.'''
    osName = os.name
    if osName == 'nt':
        os.system('cls')
    else:
        os.system('clear')

# Check for required libraries before starting the client.
def checkRequiredLibraries(libraries: list) -> tuple[bool, list]:
    '''Checks whether all the required libraries are installed or not.'''
    missing = []
    for library in libraries:
        try:
            importlib.metadata.version(library)
        except importlib.metadata.PackageNotFoundError:
            missing.append(library)
    return (not missing), missing

# Print the banner for the server cli.
def printBanner() -> None:
    '''Prints the banner for the server on the cli.'''
    banner = text2art("OPENSTACK CLIENT", font="usa_flag")
    print(banner)

# Display the choice table
def displayChoice() -> int:
    '''Display and get user choice for operations.'''
    print("\nSELECT YOUR TASK")
    print("1. LIST IMAGES")
    print("2. LIST INSTANCES")
    print("3. CREATE INSTANCE")
    print("4. LIST FLAVORS")
    print("5. LIST NETWORKS")
    print("6. EXIT")
    
    while True:
        try:
            choice = int(input("ENTER YOUR TASK: "))
            if choice in range(1, 7):
                return choice
            print("Please enter a number between 1 and 6.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")

# Function to list images
async def listImages(websocket):
    '''List all available images.'''
    try:
        await websocket.send("lsimage")
        images = await websocket.recv()

        if not images.strip():
            print("No images found.")
            return

        imageEntries = images.split("\n")
        imageList = []
        for entry in imageEntries:
            entry = entry.strip()
            if entry:
                parts = entry.split(" : ")
                if len(parts) == 2:
                    imageList.append([parts[0].strip(), parts[1].strip()])

        if imageList:
            print(tabulate(imageList, headers=["IMAGE ID", "IMAGE NAME"], tablefmt="psql"))
        else:
            print("No valid image data received.")
    except Exception as error:
        print(f"An error occurred while listing images: {error}")

# Function to list instances
async def listInstances(websocket):
    '''List all running instances.'''
    try:
        await websocket.send("lsinstances")
        instances = await websocket.recv()

        if not instances.strip():
            print("No instances found.")
            return

        instanceEntries = instances.split("\n")
        instanceList = []
        for entry in instanceEntries:
            entry = entry.strip()
            if entry:
                parts = entry.split(" : ")
                if len(parts) == 3:
                    instanceList.append([parts[0].strip(), parts[1].strip(), parts[2].strip()])

        if instanceList:
            print(tabulate(instanceList, headers=["INSTANCE ID", "INSTANCE NAME", "STATUS"], tablefmt="psql"))
        else:
            print("No valid instance data received.")
    except Exception as error:
        print(f"An error occurred while listing instances: {error}")

# Function to list flavors
async def listFlavors(websocket):
    '''List all available flavors.'''
    try:
        await websocket.send("lsflavor")
        flavors = await websocket.recv()

        if not flavors.strip():
            print("No flavors found.")
            return

        flavorEntries = flavors.split("\n")
        flavorList = []
        for entry in flavorEntries:
            entry = entry.strip()
            if entry:
                parts = entry.split(" : ")
                if len(parts) == 2:
                    flavorList.append([parts[0].strip(), parts[1].strip()])

        if flavorList:
            print(tabulate(flavorList, headers=["FLAVOR ID", "FLAVOR NAME"], tablefmt="psql"))
        else:
            print("No valid flavor data received.")
    except Exception as error:
        print(f"An error occurred while listing flavors: {error}")

# Function to list networks
async def listNetworks(websocket):
    '''List all available networks.'''
    try:
        await websocket.send("lsnetwork")
        networks = await websocket.recv()

        if not networks.strip():
            print("No networks found.")
            return

        networkEntries = networks.split("\n")
        networkList = []
        for entry in networkEntries:
            entry = entry.strip()
            if entry:
                parts = entry.split(" : ")
                if len(parts) == 3:
                    networkList.append([parts[0].strip(), parts[1].strip(), parts[2].strip()])

        if networkList:
            print(tabulate(networkList, headers=["NETWORK ID", "NETWORK TYPE", "NETWORK MTU"], tablefmt="psql"))
        else:
            print("No valid network data received.")
    except Exception as error:
        print(f"An error occurred while listing networks: {error}")

# Function to create an instance
async def createInstance(websocket):
    '''Create a new instance with user input.'''
    try:
        await websocket.send("createinstance")
        
        # Get flavor selection
        await listFlavors(websocket)
        flavor_id = input("\nEnter Flavor ID: ").strip()
        await websocket.send(flavor_id)
        
        # Get network selection
        await listNetworks(websocket)
        network_id = input("\nEnter Network ID: ").strip()
        await websocket.send(network_id)
        
        # Get instance name
        instance_name = input("\nEnter Instance Name: ").strip()
        await websocket.send(instance_name)
        
        # Get response
        response = await websocket.recv()
        print(f"\n{response}")
        
    except Exception as error:
        print(f"An error occurred while creating an instance: {error}")

# Authenticate with the server and perform tasks
async def authenticateWithServer():
    '''Main authentication and task execution loop.'''
    serverURI = os.getenv("SERVER_URI", "wss://localhost:8090")
    sslContext = get_ssl_context(secure=False)  # Set to True for production

    try:
        async with websockets.connect(serverURI, ssl=sslContext) as websocket:
            print("Connected to the server.")

            # Authentication Sequence
            username = input("Enter Your Username: ")
            password = pwinput.pwinput("Enter Your Password: ")
            project_name = input("Enter Your Project Name: ")
            credentials = {
                "username": username,
                "password": password,
                "project_name": project_name
            }
            await websocket.send(json.dumps(credentials))
            print("Authentication request sent")

            response = await websocket.recv()
            if response != "Authentication successful.":
                print("Authentication Failed. Please try again.")
                return

            print("Authentication Successful!")
            time.sleep(2)
            clearTerminal()

            # Task Selection and Execution
            while True:
                try:
                    userChoice = displayChoice()
                    if userChoice == 1:
                        await listImages(websocket)
                    elif userChoice == 2:
                        await listInstances(websocket)
                    elif userChoice == 3:
                        await createInstance(websocket)
                    elif userChoice == 4:
                        await listFlavors(websocket)
                    elif userChoice == 5:
                        await listNetworks(websocket)
                    elif userChoice == 6:
                        print("Exiting the program.")
                        break
                    
                    input("\nPress Enter to continue...")
                    clearTerminal()
                    
                except Exception as error:
                    print(f"An error occurred while performing the task: {error}")
                    print("Returning to the main menu...\n")
                    time.sleep(2)
                    
    except websockets.exceptions.ConnectionClosed:
        print("Server connection was closed.")
    except Exception as error:
        print(f"An error occurred: {str(error)}")

# Main driver function
def main():
    '''Main entry point of the program.'''
    clearTerminal()
    required = ["art", "asyncio", "websockets", "pwinput", "tabulate", "python-dotenv"]
    isInstalled, missing = checkRequiredLibraries(required)
    if not isInstalled:
        print("The following libraries are missing:", ", ".join(missing))
        return

    printBanner()
    asyncio.run(authenticateWithServer())

# Execute the main entry point
if __name__ == "__main__":
    main() 