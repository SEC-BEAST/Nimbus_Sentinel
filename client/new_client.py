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

# Clear the terminal before starting the client.
def clearTerminal() -> None:
    '''
    Clears the terminal.
    '''
    osName = os.name
    if osName == 'nt':
        os.system('cls')
    else:
        os.system('clear')

# Check for required libraries before starting the client.
def checkRequiredLibraries(libraries: list) -> tuple[bool, list]:
    '''
    Checks whether all the required libraries are installed or not.
    Returns True and an empty list if all required libraries are installed.
    Returns False and a list of missing libraries to be installed.
    '''
    missing = []
    for library in libraries:
        try:
            importlib.metadata.version(library)
        except importlib.metadata.PackageNotFoundError:
            missing.append(library)

    return (not missing), missing

# Print the banner for the server cli.
def printBanner() -> None:
    '''
    Prints the banner for the server on the cli. Uses ascii art library for printing the banner.
    '''
    banner = text2art("OPENSTACK CLIENT", font="usa_flag")
    print(banner)


# Display the choice table
def displayChoice() -> int:
    print("\nSELECT YOUR TASK")
    print("1. LIST IMAGES.")
    print("2. LIST INSTANCES.")
    print("3. CREATE INSTANCES.")
    print("4. EXIT.")
    while True:
        try:
            choice = int(input("ENTER YOUR TASK: "))
            if choice in [1, 2, 3, 4]:
                return choice
        except ValueError:
            print("Invalid input. Please enter a valid choice.")

# Function to list images
async def listImages(websocket):
    try:
        await websocket.send("lsimage")
        images = await websocket.recv()

        # Ensure the response is valid and contains expected data
        if not images.strip():
            print("No images found.")
            return

        # Process the image entries
        imageEntries = images.split("\n")
        imageList = []
        for entry in imageEntries:
            entry = entry.strip()
            if entry:
                parts = entry.split(" : ")
                if len(parts) == 2:
                    imageList.append([parts[0].strip(), parts[1].strip()])

        # Check if the list is empty after processing
        if imageList:
            print(tabulate(imageList, headers=["IMAGE ID", "IMAGE NAME"], tablefmt="psql"))
        else:
            print("No valid image data received.")
    except Exception as error:
        print(f"An error occurred while listing images: {error}")

# Function to list instances
async def listInstances(websocket):
    try:
        await websocket.send("lsinstances")
        instances = await websocket.recv()

        # Ensure the response is valid and contains expected data
        if not instances.strip():
            print("No instances found.")
            return

        # Process the instance entries
        instanceEntries = instances.split("\n")
        instanceList = []
        for entry in instanceEntries:
            entry = entry.strip()
            if entry:
                parts = entry.split(" : ")
                if len(parts) == 3:  # Expecting ID, Name, and Status
                    instanceList.append([parts[0].strip(), parts[1].strip(), parts[2].strip()])

        # Display the instances in a tabular format
        if instanceList:
            print(tabulate(instanceList, headers=["INSTANCE ID", "INSTANCE NAME", "STATUS"], tablefmt="psql"))
        else:
            print("No valid instance data received.")
    except Exception as error:
        print(f"An error occurred while listing instances: {error}")

# Function to create an instance
async def createInstance(websocket):
    try:
        await websocket.send("createInstance")

        # Fetch and display flavors
        flavors = await websocket.recv()
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
            print("No flavors found.")

        # Fetch and display networks
        networks = await websocket.recv()
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
            print("No networks found.")
    except Exception as error:
        print(f"An error occurred while creating an instance: {error}")

# Authenticate with the server and perform tasks.
async def authenticateWithServer():
    serverURI = "wss://172.16.110.8:8090"  # Update with the actual server URI
    sslContext = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    sslContext.check_hostname = False
    sslContext.verify_mode = ssl.CERT_NONE

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
            while True:  # Wrap task selection in a loop to allow repeated execution
                try:
                    userChoice = displayChoice()
                    if userChoice == 1:
                        await listImages(websocket)
                    elif userChoice == 2:
                        await listInstances(websocket)
                    elif userChoice == 3:
                        await createInstance(websocket)
                    elif userChoice == 4:
                        print("Exiting the program.")
                        break  # Break the loop when exiting
                except Exception as error:
                    print(f"An error occurred while performing the task: {error}")
                    print("Returning to the main menu...\n")
    except websockets.exceptions.ConnectionClosed:
        print("Server connection was closed.")
    except Exception as error:
        print(f"An error occurred: {str(error)}")


# Main driver function
def main():
    clearTerminal()
    required = ["art", "asyncio", "websockets", "pwinput", "tabulate"]
    isInstalled, missing = checkRequiredLibraries(required)
    if not isInstalled:
        print("The following libraries are missing:", ", ".join(missing))
        return

    printBanner()
    asyncio.run(authenticateWithServer())

# Execute the main entry point
if __name__ == "__main__":
    main()
