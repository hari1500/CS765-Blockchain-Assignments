import socket, re, datetime

# Getting the ip
# Source - https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib?page=1&tab=votes#tab-top

def ipaddr():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # need not be reachable
        sock.connect(('10.255.255.255',0))
        ipaddr = sock.getsockname()[0]
    except Exception:
        ipaddr = '127.0.0.1'
    finally:
        sock.close()
    return ipaddr

def getUtcTimestamp():
    return datetime.datetime.utcnow().strftime("%Y-%m-%d-Time-%H-%M-%S.%f")


timestampPattern = '(\d+)-(\d+)-(\d+)-Time-(\d+)-(\d+)-(\d+).(\d+)'
ipPattern = "(\d+).(\d+).(\d+).(\d+)"
portPattern = "(\d+)"
messagePattern = "(\d+)"

gossipMessagePattern = timestampPattern + ":" + ipPattern + ":" + portPattern + ":" + messagePattern
livenessRequestPattern = "Liveness Request:" + timestampPattern + ":" + ipPattern + ":" + portPattern
livenessReplyPattern = "Liveness Reply:" + timestampPattern + ":" + ipPattern + ":" + portPattern + ":" + ipPattern + ":" + portPattern
deadMessagePattern = "Dead Node:" + ipPattern + ":" + portPattern + ":" + timestampPattern + ":" + ipPattern + ":" + portPattern

def checkPattern(message, pattern):
    match = re.search(pattern, message)
    if len(message) == match.end() - match.start():
        return True
    return False








