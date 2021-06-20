import csv
import random
import socket
import threading
import datetime
import time
import hashlib
import re
import argparse

configFileName = "config.csv"
outputFileName = "outputpeer.txt"
NUM_GOSSIP_MSGS = 10
GOSSIP_MSGS_SLEEP_TIME = 5
LIVELY_MSGS_SLEEP_TIME = 13

timestampPattern = "(\d+)-(\d+)-(\d+)-Time-(\d+)-(\d+)-(\d+).(\d+)"
ipPattern = "(\d+).(\d+).(\d+).(\d+)"
portPattern = "(\d+)"
messagePattern = "(\d+)"

gossipMessagePattern = timestampPattern + ":" + ipPattern + ":" + portPattern + ":" + messagePattern
livenessRequestPattern = "Liveness Request:" + timestampPattern + ":" + ipPattern + ":" + portPattern
livenessReplyPattern = "Liveness Reply:" + timestampPattern + ":" + ipPattern + ":" + portPattern + ":" + ipPattern + ":" + portPattern
deadMessagePattern = "Dead Node:" + ipPattern + ":" + portPattern + ":" + timestampPattern + ":" + ipPattern + ":" + portPattern

def getMyIPAddr():
    """ Below code is taken from https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib?page=1&tab=votes#tab-top """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(('10.255.255.255', 0))
        ipaddr = sock.getsockname()[0]
    except Exception:
        ipaddr = '127.0.0.1'
    finally:
        sock.close()

    return ipaddr

def getSeedNodes():
    """ Returns the list of seed nodes from config.csv file """
    seedNodes = []
    try:
        with open(configFileName, mode = 'r') as csvFile:
            csvReader = csv.DictReader(csvFile)

            headers = csvReader.fieldnames
            for row in csvReader:
                seedNodes.append([row[headers[0]], int(row[headers[1]])])
    except Exception as e:
        print(e)

    return seedNodes

def flushOutputFile():
    """ Empties output file """
    try:
        open(outputFileName, 'w').close()
    except Exception as e:
        print(e)

def toOutput(text, toFile=True, toCL=True):
    """ Prints output to terminal and outputfile based on arguments """
    if (toCL):
        print(text)
    if (toFile):
        try:
            fileObject = open(outputFileName, 'a')
            fileObject.write(text + "\n")
            fileObject.close()
        except Exception as e:
            print(e)

def getTimestampString():
    return str(datetime.datetime.utcnow().strftime("%Y-%m-%d-Time-%H-%M-%S.%f"))

def getLocalTimestampString():
    return str(datetime.datetime.now())

def checkPattern(message, pattern):
    try:
        match = re.search(pattern, message)
        return (len(message) == match.end() - match.start())
    except Exception:
        return False

def getPattern(message, pattern):
    try:
        match = re.search(pattern, message)
        return message[match.start():match.end()]
    except Exception:
        return message

class ConnectedPeer:
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

    def increaseCounter(self):
        self.counterLock.acquire()
        self.counter += 1
        self.counterLock.release()

    def resetCounter(self):
        self.counterLock.acquire()
        self.counter = 0
        self.counterLock.release()

class ConnectedSeed:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
    
    def __eq__(self, seed):
        return self.ip == seed.ip and self.port == seed.port

class MessageListMember:
    def __init__(self, hashedMsg, b):
        self.hashedMsg = hashedMsg
        self.b = b

    def __eq__(self, message):
        return self.hashedMsg.digest() == message.hashedMsg.digest()

    def __str__(self):
        return self.hashedMsg

class PeerNode:
    def __init__(self, port=None):
        self.ip = getMyIPAddr()
        self.port = 0 if (port == None) else port
        self.peerList = []
        self.messageList = []
        self.listeningSocket = None
        self.seedSockets = []
        self.messageListLock = threading.Lock()
        self.socklock = threading.Lock()
        self.peerListLock = threading.Lock()

    def __str__(self):
        return "IP Addr: %s, Port: %s" % (self.ip, self.port)

    def addSeedSocket(self, seedSocket):
        self.seedSockets.append(seedSocket)

    def setupListeningSocket(self):
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
        self.peerListLock.acquire()
        peer = ConnectedPeer(ip, port, socket, lPort)
        if peer not in self.peerList:
            self.peerList.append(peer)
            self.peerListLock.release()
            return peer
        self.peerListLock.release()
        return None

    def removePeer(self, connectedPeer):
        self.peerListLock.acquire()
        self.peerList.remove(connectedPeer)
        self.peerListLock.release()

    def addMessage(self, hashedMsg, b):
        self.messageListLock.acquire()
        messageListMember = MessageListMember(hashedMsg, True)
        if messageListMember not in peerNode.messageList:
            self.messageList.append(messageListMember)
            self.messageListLock.release()
            return True
        self.messageListLock.release()
        return False

def genGossipMessage(ip, port, msgInd):
    return "%s:%s:%s:%s" % (getTimestampString(), ip, port, msgInd)

def genLivelinessRequest(ip, port):
    return "Liveness Request:%s:%s:%s" % (getTimestampString(), ip, port)

def genLivelinessReply(reqMsg, ip, port):
    reqMsg = reqMsg.split(":")
    if (len(reqMsg) <= 1):
        return ""
    return "Liveness Reply:%s:%s:%s" % (":".join(reqMsg[1:]), ip, port)

def genDeadMessage(d_ip, d_port, s_ip, s_port):
    return "Dead Node:%s:%s:%s:%s:%s" % (d_ip, d_port, getTimestampString(), s_ip, s_port)

def connectedPeersThreadTask(connectedPeer, peerNode):
    """ Receives gossip messages here """
    while True:
        try:
            msg = connectedPeer.socket.recv(10000)
            msg = msg.decode()

            if(checkPattern(msg, livenessReplyPattern)):
                connectedPeer.resetCounter()
            if(checkPattern(msg, livenessRequestPattern)):
                truncatedMsg = getPattern(msg, livenessRequestPattern)
                reply = genLivelinessReply(truncatedMsg, peerNode.ip, peerNode.port)
                try:
                    connectedPeer.socklock.acquire()
                    connectedPeer.socket.send(str.encode(reply))
                    connectedPeer.socklock.release()
                except Exception as e:
                    connectedPeer.socklock.release()
                    print("Error in sending in Liveliness reply --- %s" % e)
            if (checkPattern(msg, gossipMessagePattern)):
                truncatedMsg = getPattern(msg, gossipMessagePattern)
                hashedMsg = hashlib.sha256(truncatedMsg.encode())
                addedMsg = peerNode.addMessage(hashedMsg, True)

                if addedMsg:
                    printMsg = "Gossip Message from (%s:%s), msg: %s at %s" % (connectedPeer.ip, connectedPeer.listeningPort, truncatedMsg, getLocalTimestampString())
                    toOutput(printMsg)
                    for peer in peerNode.peerList:
                        if peer != connectedPeer:
                            try:
                                peer.socklock.acquire()
                                peer.socket.send(str.encode(truncatedMsg))
                                peer.socklock.release()
                            except Exception as e:
                                peer.socklock.release()
                                print("Error in Forwarding gossip messages --- %s" % e)
        except Exception as e:
            print("Error in receiving message --- %s" % e)

def generateLivelyRequestMsgsThreadTask(peerNode):
    while(True):
        for peer in peerNode.peerList:
            if(peer.counter >= 3):
                deadMsg = genDeadMessage(peer.ip, peer.listeningPort, peerNode.ip, peerNode.port)
                for seedSock in peerNode.seedSockets:
                    try:
                        seedSock.send(str.encode(deadMsg))
                    except Exception as e:
                        print("Error in notifying dead message to seed --- %s" % e)

                toOutput("Reporting Dead node message: %s" % deadMsg)
                peerNode.removePeer(peer)
            else:
                peer.increaseCounter()

                try:
                    peer.socklock.acquire()
                    peer.socket.send(str.encode(genLivelinessRequest(peerNode.ip, peerNode.port)))
                    peer.socklock.release()
                except Exception as e:
                    peer.socklock.release()
                    print("Error in sending liveliness request --- %s" % e)

        time.sleep(LIVELY_MSGS_SLEEP_TIME)

def sendGossipMessage(gossipMsg, peerNode):
    for peer in peerNode.peerList:
        hashedMsg = hashlib.sha256(gossipMsg.encode())
        peerNode.addMessage(hashedMsg, True)

        try:
            peer.socklock.acquire()
            peer.socket.send(str.encode(gossipMsg))
            peer.socklock.release()
        except Exception as e:
            peer.socklock.release()
            print("Error in sending gossip message --- %s" % e)

def generateGossipMsgsThreadTask(peerNode):
    time.sleep(GOSSIP_MSGS_SLEEP_TIME)
    for i in range(NUM_GOSSIP_MSGS-1):
        gossipMsg = genGossipMessage(peerNode.ip, peerNode.port, i+1)
        sendGossipMessage(gossipMsg, peerNode)
        time.sleep(GOSSIP_MSGS_SLEEP_TIME)

if __name__ == "__main__":
    # Cleaning output file
    flushOutputFile()

    parser = argparse.ArgumentParser()
    parser.add_argument("-o","--outputfile")
    parser.add_argument("-c","--configfile")
    args = parser.parse_args()
    if args.outputfile:
        outputFileName = args.outputfile
    if args.configfile:
        configFileName = args.configfile

    # Creating peer node
    peerNode = PeerNode()
    peerNode.setupListeningSocket()
    # toOutput(peerNode, toFile=False)

    # Getting seed nodes
    seedNodes = getSeedNodes()
    random.shuffle(seedNodes)
    
    nSeedNodes = len(seedNodes)
    if (nSeedNodes == 0):
        toOutput("No seed nodes available", toFile=False)
        exit()
    chosenSeedNodes = seedNodes[:((nSeedNodes>>1)+1)]

    peerList = []
    for seedNode in chosenSeedNodes:
        peerListStr = ""

        try:
            seedConnectionSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            seedConnectionSocket.connect((seedNode[0], seedNode[1]))
            seedConnectionSocket.send(str.encode(str(peerNode.port)))
            while True:
                peerListData = seedConnectionSocket.recv(10000)
                peerListData = peerListData.decode()
                peerListStr += peerListData
                if (peerListData.endswith("&")):
                    break
            peerListStr = peerListStr[:-1]
            peerNode.addSeedSocket(seedConnectionSocket)
        except Exception as e:
            print("Error in connecting seed or receiving PL from seed --- %s" % e)

        for i in peerListStr.split(","):
            peerNodeData = i.split(":")
            if (len(peerNodeData) > 1):
                peerList.append((peerNodeData[0], int(peerNodeData[1])))

    peerList = list(set(peerList))
    random.shuffle(peerList)
    toOutput("Peer List: %s" % (peerList))

    if (len(peerList) > 4):
        peerList = peerList[:4]

    for peer in peerList:
        try:
            peerRequestingSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peerRequestingSocket.connect((peer[0], peer[1]))
            peerRequestingSocket.send(str.encode(str(peerNode.port)))
            addedPeer = peerNode.addPeer(peer[0], peer[1], peerRequestingSocket, peer[1])
            if (addedPeer != None):
                threading.Thread(
                    target=connectedPeersThreadTask,
                    args=(addedPeer, peerNode)
                ).start()
        except Exception as e:
            print("Error in connecting or sending my port to peer --- %s" % e)

    gossipMsg = genGossipMessage(peerNode.ip, peerNode.port, 0)
    sendGossipMessage(gossipMsg, peerNode)

    threading.Thread(
        target=generateGossipMsgsThreadTask,
        args=(peerNode, )
    ).start()

    threading.Thread(
        target=generateLivelyRequestMsgsThreadTask,
        args=(peerNode, )
    ).start()

    while True:
        try:
            (peerAcceptingSocket, peerAcceptingAddr) = peerNode.listeningSocket.accept()
            peerListeningPort = peerAcceptingSocket.recv(10000)
            peerListeningPort = int(peerListeningPort.decode())
            addedPeer = peerNode.addPeer(peerAcceptingAddr[0], int(peerAcceptingAddr[1]), peerAcceptingSocket, peerListeningPort)
            if (addedPeer != None):
                threading.Thread(
                    target=connectedPeersThreadTask,
                    args=(addedPeer, peerNode)
                ).start()
        except Exception as e:
            print("Error in accepting or receiving data from peer --- %s" % e)
