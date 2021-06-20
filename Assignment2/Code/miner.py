import random
import socket
import threading
import datetime
import time
import hashlib
import re
import argparse

from queue import Queue
from utils import getMyIPAddr, getSeedNodes, flushOutputFile, toOutput
from block import initDB, insertBlock, Block, getByteArrayAllBlocks, verifyBlock, initializeHeights, currState

configFileName = "config.csv"
outputFileName = "outputpeer.txt"
interArrivalTime = None
queueFilled = threading.Event()

class ConnectedPeer:
    """ Each peer connected to miner is stored as ConnectedPeer """
    def __init__(self, ip, port, socket, lPort):
        self.ip = ip
        self.port = port
        self.socket = socket
        self.counter = 0
        self.listeningPort = lPort
        self.socklock = threading.Lock()
        self.counterLock = threading.Lock()

    def __eq__(self, peer):
        if peer == None: 
            return False
        return self.ip == peer.ip and self.port == peer.port

    """ Counter is for checking liveliness """
    def increaseCounter(self):
        self.counterLock.acquire()
        self.counter += 1
        self.counterLock.release()

    def resetCounter(self):
        self.counterLock.acquire()
        self.counter = 0
        self.counterLock.release()

class ConnectedSeed:
    """ Each seed connected to miner is stored as ConnectedSeed """
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
    
    def __eq__(self, seed):
        return self.ip == seed.ip and self.port == seed.port

class Miner:
    def __init__(self, hashingPower=None, databaseName=None, port=None):
        self.ip = getMyIPAddr()
        self.port = 0 if (port == None) else port
        self.peerList = []
        self.listeningSocket = None
        self.seedSockets = []
        self.socklock = threading.Lock()
        self.peerListLock = threading.Lock()
        self.hashingPower = 0.1 if (hashingPower == None) else hashingPower
        self.databaseConnection = initDB(databaseName)
        self.verifyQueue = Queue(maxsize=0)
        self.queueLock = threading.Lock()
        self.totalBlocks = 0
        self.myBlocks = 0


    def __str__(self):
        return "IP Addr: %s, Port: %s" % (self.ip, self.port)

    def addSeedSocket(self, seedSocket):
        self.seedSockets.append(seedSocket)

    def setupListeningSocket(self):
        """ Sets up listensing socket for miner(self) """
        if self.listeningSocket != None:
            return
        try:
            self.listeningSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.listeningSocket.bind((self.ip, self.port))
            self.listeningSocket.listen(5)
        except Exception as e:
            print("Error in creating listening socket --- %s" % e)
            exit()
        _, self.port = self.listeningSocket.getsockname()

    def addPeer(self, ip, port, socket, lPort):
        """ Adds new connectedPeer to peerList """
        self.peerListLock.acquire()
        peer = ConnectedPeer(ip, port, socket, lPort)
        if peer not in self.peerList:
            self.peerList.append(peer)
            self.peerListLock.release()
            return peer
        self.peerListLock.release()
        return None

    def removePeer(self, connectedPeer):
        """ Removes connectedPeer from peerList """
        self.peerListLock.acquire()
        self.peerList.remove(connectedPeer)
        self.peerListLock.release()

    def genWaitingTime(self, interArrivalTime):
        """ Generates Waiting Time (Tow) """
        lam = self.hashingPower / (interArrivalTime * 100.0)
        return random.expovariate(lam)/100

def connectedPeersThreadTask(connectedPeer, miner):
    """ Receives blocks from peers here """
    while True:
        try:
            msg = connectedPeer.socket.recv(10000)
            if (msg == b''):
                continue
            miner.queueLock.acquire()
            miner.verifyQueue.put(msg)
            miner.queueLock.release()
            queueFilled.set()
        except Exception as e:
            print("Error in receiving blocks --- %s" % e)

def broadcastBlock(newBlock):
    """ Broadcasts blocks to peers """
    # print("Broadcasting")
    msg = newBlock.getByteArray()
    for peer in miner.peerList:
        try:
            peer.socklock.acquire()
            peer.socket.send(msg)
            peer.socklock.release()
        except Exception as e:
            peer.socklock.release()
            print("Error in broadcasting block --- %s" % e)

def miningThreadtask(miner):
    """ Mines new blocks """
    while True:
        topHash, topHeight = currState(miner.databaseConnection)
        newBlock = Block(prevHash=topHash, height=topHeight+1, minedBy=1)
        # New block is created, waiting time generated and started waiting 
        queueFilled.wait(miner.genWaitingTime(interArrivalTime))
        if queueFilled.is_set():
            # received blocks while waiting
            try:
                while not miner.verifyQueue.empty():
                    miner.queueLock.acquire()
                    block = miner.verifyQueue.get()
                    miner.queueLock.release()
                    # verifying and inserting block in the queue
                    newBlock = Block(prevHash=block[:2], merkelRoot=block[2:4], timestamp=int.from_bytes(block[4:8], signed=False, byteorder='big'))
                    height = verifyBlock(miner.databaseConnection, newBlock)
                    # print(height, newBlock)
                    if height >= 0:
                        newBlock.height = height+1
                        if insertBlock(miner.databaseConnection, newBlock):
                            toOutput("Inserted new block", outputFileName=outputFileName)
                            miner.totalBlocks = miner.totalBlocks+1
                            broadcastBlock(newBlock)
                queueFilled.clear()
            except Exception as err:
                print("Error while checking Queue --- %s", err)
                exit()
        else:
            # Waiting time completed, broadcasts mined block
            try: 
                if insertBlock(miner.databaseConnection, newBlock):
                    toOutput("Mined new block", outputFileName=outputFileName)
                    miner.myBlocks += 1
                    miner.totalBlocks += 1
                    broadcastBlock(newBlock)
            except Exception as err:
                print("Error while broadcasting mined block --- %s" % err)
                exit()
                        

if __name__ == "__main__":
    # Reading inputs
    parser = argparse.ArgumentParser()
    parser.add_argument("-o","--outputfile")
    parser.add_argument("-c","--configfile")
    parser.add_argument("-i","--interarrivaltime", required=True)
    parser.add_argument("-hp","--hashingpower", required=True)
    parser.add_argument("-db","--database")
    args = parser.parse_args()
    if args.outputfile:
        outputFileName = args.outputfile
    if args.configfile:
        configFileName = args.configfile
    try:
        if args.interarrivaltime:
            interArrivalTime = float(args.interarrivaltime)
    except Exception as err:
        print(err)
        exit()

    # Cleaning output file
    flushOutputFile(outputFileName)

    # Creating miner
    try:
        miner = Miner(
            hashingPower=float(args.hashingpower),
            databaseName=args.database if args.database else "blockchain.db"
        )
        miner.setupListeningSocket()
    except Exception as err:
        print(err)
        print("Miner creation failed")
        exit()
    
    # print(miner.genWaitingTime(interArrivalTime))

    # Getting seed nodes
    seedNodes = getSeedNodes(configFileName)
    random.shuffle(seedNodes)
    
    # Selecting [n/2]+1 seed nodes
    nSeedNodes = len(seedNodes)
    if (nSeedNodes == 0):
        toOutput("No seed nodes available", toFile=False)
        exit()
    chosenSeedNodes = seedNodes[:((nSeedNodes>>1)+1)]

    # Connecting to seeds and getting peerList
    peerList = []
    for seedNode in chosenSeedNodes:
        peerListStr = ""

        try:
            seedConnectionSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            seedConnectionSocket.connect((seedNode[0], seedNode[1]))
            seedConnectionSocket.send(str.encode(str(miner.port)))
            while True:
                peerListData = seedConnectionSocket.recv(10000)
                peerListData = peerListData.decode()
                peerListStr += peerListData
                if (peerListData.endswith("&")):
                    break
            peerListStr = peerListStr[:-1]
            miner.addSeedSocket(seedConnectionSocket)
        except Exception as e:
            print("Error in connecting seed or receiving PL from seed --- %s" % e)

        for i in peerListStr.split(","):
            peerNodeData = i.split(":")
            if (len(peerNodeData) > 1):
                peerList.append((peerNodeData[0], int(peerNodeData[1])))

    peerList = list(set(peerList))
    random.shuffle(peerList)
    toOutput("Peer List: %s" % (peerList), outputFileName=outputFileName)

    # Choosing a max of 4 peers in peerList
    if (len(peerList) > 4):
        peerList = peerList[:4]

    # Receiving local blocklist of connected peers
    blockList = []
    for peer in peerList:
        try:
            peerRequestingSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peerRequestingSocket.connect((peer[0], peer[1]))
            peerRequestingSocket.send(str.encode(str(miner.port)))
            addedPeer = miner.addPeer(peer[0], peer[1], peerRequestingSocket, peer[1])
            blocksByteArray = peerRequestingSocket.recv(10000)
            while (len(blocksByteArray) > 0):
                block_prevHash = blocksByteArray[:2]
                blocksByteArray = blocksByteArray[2:]
                block_merkelRoot = blocksByteArray[:2]
                blocksByteArray = blocksByteArray[2:]
                block_timestamp = blocksByteArray[:4]
                blocksByteArray = blocksByteArray[4:]
                newBlock = Block(prevHash = block_prevHash, merkelRoot = block_merkelRoot, timestamp = int.from_bytes(block_timestamp, signed=False, byteorder='big'))
                if newBlock not in blockList:
                    blockList.append(newBlock)

            if (addedPeer != None):
                threading.Thread(
                    target=connectedPeersThreadTask,
                    args=(addedPeer, miner)
                ).start()
        except Exception as e:
            print("Error in connecting or sending my port to peer --- %s" % e)
    
    toOutput("Received these many blocks %s" % len(blockList), toFile=False)

    # Uppdating database with blocks of connected peers
    for block in blockList:
        # if(verifyBlock(miner.databaseConnection,block)):
        insertBlock(miner.databaseConnection, block)
    if len(blockList) == 0: 
        newBlock = Block(prevHash=bytearray.fromhex('9e1c'), height=0)
        insertBlock(miner.databaseConnection, newBlock)
    initializeHeights(miner.databaseConnection)

    # Starts mining
    threading.Thread(
        target=miningThreadtask,
        args=(miner, )
    ).start()

    # Accepting connections from new peers
    while True:
        try:
            (peerAcceptingSocket, peerAcceptingAddr) = miner.listeningSocket.accept()
            peerListeningPort = peerAcceptingSocket.recv(10000)
            peerListeningPort = int(peerListeningPort.decode())
            addedPeer = miner.addPeer(peerAcceptingAddr[0], int(peerAcceptingAddr[1]), peerAcceptingSocket, peerListeningPort)
            blockByteArray = getByteArrayAllBlocks(miner.databaseConnection)
            toOutput("Sending local database", toFile=False)
            peerAcceptingSocket.send(blockByteArray)
            if (addedPeer != None):
                threading.Thread(
                    target=connectedPeersThreadTask,
                    args=(addedPeer, miner)
                ).start()
        except Exception as e:
            print("Error in accepting or receiving data from peer --- %s" % e)