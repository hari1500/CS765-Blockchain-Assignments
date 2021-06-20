import csv
import socket
import datetime

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

def getSeedNodes(configFileName):
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

def flushOutputFile(outputFileName):
    """ Empties output file """
    try:
        open(outputFileName, 'w').close()
    except Exception as e:
        print(e)

def toOutput(text, toFile=True, toCL=True, outputFileName=None):
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
    """ generates timestamp string according to below format """
    return str(datetime.datetime.utcnow().strftime("%Y-%m-%d-Time-%H-%M-%S.%f"))

def genLivelinessRequest(ip, port):
    """ generates liveliness requests """
    return "Liveness Request:%s:%s:%s" % (getTimestampString(), ip, port)

def genLivelinessReply(reqMsg, ip, port):
    """ generates liveliness replies """
    reqMsg = reqMsg.split(":")
    if (len(reqMsg) <= 1):
        return ""
    return "Liveness Reply:%s:%s:%s" % (":".join(reqMsg[1:]), ip, port)

def genDeadMessage(d_ip, d_port, s_ip, s_port):
    """ generates dead messages """
    return "Dead Node:%s:%s:%s:%s:%s" % (d_ip, d_port, getTimestampString(), s_ip, s_port)
