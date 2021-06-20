import socket
import threading
import re
import argparse

outputFileName = "outputseed.txt"
socketReceivingCapacity = 10000

timestampPattern = "(\d+)-(\d+)-(\d+)-Time-(\d+)-(\d+)-(\d+).(\d+)"
ipPattern = "(\d+).(\d+).(\d+).(\d+)"
portPattern = "(\d+)"
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

def checkPattern(message, pattern):
    """ checks if message matches the pattern of liveliness format or dead format etc """
    try:
        match = re.search(pattern, message)
        return (len(message) == match.end() - match.start())
    except Exception:
        return False

class PeerListMember:
    """ element of peerlist """
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

    def __eq__(self, peer):
        return self.ip == peer.ip and self.port == peer.port

class SeedNode:
    def __init__(self, port=None):
        self.ip = getMyIPAddr()
        self.port = 0 if (port == None) else port
        self.peerList = []
        self.socket = None
        self.lock = threading.Lock()

    def __str__(self):
        return "IP Addr: %s, Port: %s" % (self.ip, self.port)

    def addPeer(self, ip, port):
        """ adds peer to peerList """
        if PeerListMember(ip, port) not in self.peerList:
            self.peerList.append(PeerListMember(ip, port))
            return True
        return False

    def removePeer(self, ip, port):
        """ removes peer from peerList """
        self.lock.acquire()
        peer = PeerListMember(ip, port)
        if peer in self.peerList:
            self.peerList.remove(peer)
        self.lock.release()

    def setupSocket(self):
        """ setsup socket for accepting peers """
        if self.socket != None:
            return

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.bind((self.ip, self.port))
            self.socket.listen(5)
        except Exception as e:
            print("Error in creating socket --- %s" % e)
            exit()

        _, self.port = self.socket.getsockname()

def sendPeerList(peerSocket, peerList):
    """ Sending seed's PL for the requested peer node """
    peerListString = ""
    for peer in peerList:
        peerListString += peer.ip + ":" + str(peer.port) + ","
    peerListString += "&"

    peerListEncoded = str.encode(peerListString)

    """ Below code is taken from https://docs.python.org/3/howto/sockets.html """
    try:
        totalSent = 0
        peerListLen = len(peerListEncoded)
        while totalSent < peerListLen:
            sent = peerSocket.send(peerListEncoded[totalSent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalSent += sent
    except Exception as e:
        print("Error in sending PL --- %s" % e)

def peerThreadTask(peerSocket, peerAddr, seedNode):
    """ accepts peer connection and listens for dead nodes in this thread """
    try:
        peerPort = peerSocket.recv(1024)
        peerPort = peerPort.decode()
        peerPort = int(peerPort)
        toOutput("Connected to (%s:%s)" % (peerAddr[0], peerPort))
    except Exception as e:
        print("Error in receiving port --- %s" % e)

    sendPeerList(peerSocket, seedNode.peerList)
    seedNode.addPeer(peerAddr[0], peerPort)

    while True:
        try:
            deadMessage = peerSocket.recv(10000)
            deadMessage = deadMessage.decode()
            if (checkPattern(deadMessage, deadMessagePattern)):
                toOutput("Receiving Dead node message: %s" % (deadMessage))
                deadMessage = deadMessage.split(":")
                seedNode.removePeer(deadMessage[1], int(deadMessage[2]))
        except Exception as e:
            print("Error in receiving message from peer --- %s" % e)

if __name__ == "__main__":
    # Cleaning output file
    flushOutputFile()

    parser = argparse.ArgumentParser()
    parser.add_argument("-o","--outputfile")
    args = parser.parse_args()
    if args.outputfile:
        outputFileName = args.outputfile

    seedNode = SeedNode()
    seedNode.setupSocket()
    toOutput(seedNode, toFile=False)

    # Accepts peer connection and spawns new thread for each peer
    while True:
        try:
            (peerSocket, peerAddr) = seedNode.socket.accept()
            
            threading.Thread(
                target=peerThreadTask,
                args=(peerSocket, peerAddr, seedNode)
            ).start()
        except Exception as e:
            print("Error in accepting peer --- %s" % e)
