#!/usr/bin/env python3

# Library Import
import asyncio
import websockets
import os
import time
from tabulate import tabulate
import pwinput

# Clear the screen after the authentication sequence.
def clearScreen() -> None:
    '''
    Clear the sequence after the authentication sequence is completed successfully.
    '''
    osName = os.name
    if osName == 'nt':
        os.system('cls')
    else:
        os.system('clear')


# Display the choice table
def displayChoice() -> int:
    print("\nSELECT YOUR TASK")
    print("1. LIST IMAGES.")
    print("2. LIST INSTACNES.")
    print("3. CREATE INSTACNES.")
    while True:
        try:
            choice = int(input( "ENTER YOUR TASKS : " ))
        except Exception as error:
            continue
        else:
            return choice


# Authenticate with the server
async def authenticateWithServer() -> None:
    authURI = "ws://192.168.185.1:8090"
    while True:
        async with websockets.connect(authURI) as websocket:
            print(await websocket.recv())
            username = input( "ENTER YOUR USERNAME : " )
            password = pwinput.pwinput( "ENTER YOUR PASSWORD : ", mask = "*" )
            projectID = "0c709dfa06374e16b70a4cb0ed63ae4d"
            authInfo = f"{username},{password},{projectID}"
            await websocket.send( authInfo )
            serverResponse = await websocket.recv()
            print(await websocket.recv())
            if serverResponse == "success":
                time.sleep(2)
                clearScreen()
                while True:
                    userChoice = displayChoice()
                    if userChoice == 1:
                        await websocket.send("lsimage")
                        images = await websocket.recv()
                        imageEntries = images.split("\n")
                        imageList = []
                        for image in imageEntries:
                            image = image.strip()
                            if image:
                                imageParts = image.split(" : ")
                                if len(imageParts) == 2:
                                    imageList.append([imageParts[0].strip(), imageParts[1].strip()])
                        headers = ["IMAGE ID", "IMAGE NAME"]
                        if imageList:
                            print(tabulate(imageList, headers=headers, tablefmt='psql'))
                        else:
                            print(imageList)
                    elif userChoice == 3:
                        await websocket.send("createInstance")
                        flavors = await websocket.recv()
                        flavorEntries = flavors.split("\n")
                        flavorList = []
                        for flavor in flavorEntries:
                            flavor = flavor.strip()
                            if flavor:
                                flavorParts = flavor.split(" : ")
                                if len(flavorParts) == 2:
                                    flavorList.append([flavorParts[0].strip(), flavorParts[1].strip()])
                        headers = ["FLAVOR ID", "FLAVOR NAME"]
                        if flavorList:
                            print(tabulate(flavorList, headers=headers, tablefmt='psql'))
                        else:
                            print(flavorList)  
                        networks = await websocket.recv()
                        networkEntries = networks.split("\n")
                        networkList = []
                        for network in networkEntries:
                            flavor = network.strip()
                            if network:
                                networkParts = network.split(" : ")
                                if len(networkParts) == 3:
                                    networkList.append([networkParts[0].strip(), networkParts[1].strip(), networkParts[2].strip()])
                        headers = ["NETWORK ID", "NETWORK TYPE", "NETWORK MTU"]
                        if networkList:
                            print(tabulate(networkList, headers=headers, tablefmt='psql'))
                        else:
                            print(networkList)   
                        
                        # networkEntries = networks.split("\n")
                        # networkList = []
                        # for network in networkEntries:
                        #     network = network.strip()
                        #     if network:
                        #         networkParts = network.split(" : ")
                        #         if len(networkParts) == 2:
                        #             networkList.append([networkParts[0].strip(), networkParts[1].strip()])
                        # headers = ["NETWORK ID", "NETWORK NAME"]
                        # if networkList:
                        #     print(tabulate(networkList, headers=headers, tablefmt='psql'))
                        # else:
                        #     print(networkList)              
            else:
                continue
            


if __name__ == "__main__":
    asyncio.run(authenticateWithServer()) 
