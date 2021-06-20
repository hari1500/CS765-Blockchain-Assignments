import sqlite3
import os
import hashlib
import time

class Block:
    """ Block which is inserted into database files """
    def __init__(self, prevHash=None, merkelRoot=None, timestamp=None, height=None, blockHash=None, minedBy=0):
        self.prevHash = prevHash
        self.merkelRoot = (0).to_bytes(2, byteorder='big') if (merkelRoot == None) else merkelRoot
        self.timestamp = int(time.time()) if (timestamp == None) else timestamp
        self.height = -1 if (height == None) else height
        self.blockHash = self.getBlockHash() if (blockHash == None) else blockHash
        self.minedBy = minedBy
    
    def __eq__(self, block1):
        """ Checks if blocks are equal """
        if block1 == None:
            return False
        else:
            return self.prevHash == block1.prevHash and self.merkelRoot == block1.merkelRoot and int(self.timestamp) == int(block1.timestamp)
    
    def getBlockHash(self):
        """ gives hash of entire block """
        combined = self.getByteArray()
        obj = hashlib.sha3_256()
        obj.update(combined)
        return obj.digest()[-2:]
    
    def getByteArray(self):
        """ generates byte array of entire block """
        return self.prevHash + self.merkelRoot + (self.timestamp).to_bytes(4, byteorder='big')

    def getTuple(self):
        """ get entire block in tuple """
        return (self.prevHash, self.merkelRoot, self.timestamp, self.height, self.blockHash, self.minedBy)

def initDB(dbName="blockchain.db"):
    """ initialiazes database """
    try:
        if (os.path.exists(dbName)): os.remove(dbName)

        connection = sqlite3.connect(dbName, check_same_thread=False)
        
        cursor = connection.cursor()
        cursor.execute(
            """ CREATE TABLE blocks (prevhash BLOB, merkelroot BLOB, timestamp INT, height INT, blockhash BLOB, minedby INT); """
        )

        connection.commit()
        return connection
    except Exception as err:
        print("Unable to create DB")
        print(err)
        exit()

def closeDB(connection):
    """ closes database """
    try:
        connection.close()
    except Exception as err:
        print("Unable to close connection")
        print(err)
    
def insertBlock(connection, block):
    """ inserts a block into database """
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM blocks WHERE blockhash = ?", (block.blockHash,))
        data = cursor.fetchone()
        if data:
            return False
        else:
            cursor.execute('INSERT INTO blocks VALUES (?, ?, ?, ?, ?, ?)', block.getTuple())
            connection.commit()
            return True
    except Exception as err:
        print("Error while inserting block", err)
        exit()

def getByteArrayAllBlocks(connection):
    """ returns all blocks of database as byte array """
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM blocks")
        rows = cursor.fetchall()
        outputByteArray = bytearray(0)
        for row in rows:
            outputByteArray += row[0] + row[1] + (row[2]).to_bytes(4, byteorder='big')
        return outputByteArray
    except Exception as err:
        print(err)
        exit()

def verifyBlock(connection, block):
    """ verifies each block """
    def verifyTimestamp(blockTime):
        currTime = int(time.time())
        return (blockTime < currTime + 3600) and (blockTime > currTime - 3600)

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT height FROM blocks WHERE blockhash = ?", (block.getTuple()[0],))
        data = cursor.fetchone()
        if (data and verifyTimestamp(block.getTuple()[2])):
            # print(data)
            return data[0]
        return -1
    except Exception as err:
        print("while verifying block", err)
        exit()

def initializeHeights(connection):
    """ initializes heights of all blocks in the database """
    try:
        cursor = connection.cursor()
        depth = 1
        currentDepth = [bytearray.fromhex('9e1c')]
        while len(currentDepth) > 0:
            nextDepth = []
            for blob in currentDepth:
                cursor.execute("UPDATE blocks SET height = ? WHERE prevhash = ?",(depth, blob))
                cursor.execute("SELECT blockhash from blocks WHERE prevhash = ?", (blob,))
                data = cursor.fetchall()
                nextDepth = nextDepth+[x[0] for x in data]
            depth += 1
            currentDepth=nextDepth[:] 
    except Exception as err:
        print("while initializing heights", err)
        exit()

def currState(connection):
    """ returns blockhash and height of max height block in the blockchain """
    try :
        cursor = connection.cursor()
        cursor.execute("SELECT MAX(height) FROM blocks")
        topHeight = cursor.fetchone()[0]
        cursor.execute("SELECT blockhash FROM blocks WHERE height = ?",(topHeight,))
        topHash = cursor.fetchone()[0]
        return topHash, topHeight
    except Exception as err:
        print("while fetching current state", err)
        exit()
    