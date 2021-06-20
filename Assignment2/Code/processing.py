import sqlite3
import statistics

miner_dbs = []
adv_dbs = []
n_miners = 30
n_adversaries = 3
for i in range(1,n_miners+1):
    miner_dbs.append('db/db'+str(i))
for i in range(n_miners+1,n_miners+n_adversaries+1):
    adv_dbs.append('db/db'+str(i))

def mining_power():
    """ Calculates mining power utilization """
    mining_power = []
    for db in miner_dbs:
        connection = sqlite3.connect(db)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM blocks")
        rows = cursor.fetchall()
        total_blocks = float(len(rows) + 1)
        cursor.execute("SELECT MAX(height) FROM blocks")
        rows = cursor.fetchall()
        max_height = float(rows[0][0] + 1)
        mining_power.append(max_height / total_blocks)
    for db in adv_dbs:
        connection = sqlite3.connect(db)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM blocks")
        rows = cursor.fetchall()
        total_blocks = float(len(rows) + 1)
        cursor.execute("SELECT MAX(height) FROM blocks")
        rows = cursor.fetchall()
        max_height = float(rows[0][0] + 1)
        mining_power.append(max_height / total_blocks)
    return statistics.mean(mining_power)

def fraction():
    """ Calculates Fraction of main chain blocks mined by the adversary """
    fraction = []
    for db in miner_dbs[0:1]:
        longest_chain = []
        connection = sqlite3.connect(db)
        cursor = connection.cursor()
        cursor.execute("SELECT prevhash, blockhash, MAX(height) FROM blocks")
        rows = cursor.fetchall()
        longest_chain.append(rows[0][1])
        prevhash = rows[0][0]
        while prevhash != bytearray.fromhex('9e1c'):
            cursor.execute("SELECT prevhash, blockhash FROM blocks WHERE blockhash=?", (prevhash,))
            rows = cursor.fetchall()
            longest_chain.append(rows[0][1])
            prevhash = rows[0][0]
        longest_chain = set(longest_chain)
        fraction1 = []
        for db1 in adv_dbs:
            connection = sqlite3.connect(db1)
            cursor = connection.cursor()
            cursor.execute("SELECT blockhash FROM blocks WHERE minedby=?", (1,))
            rows = cursor.fetchall()
            adv_blocks = set([row[0] for row in rows])
            common_blocks = longest_chain.intersection(adv_blocks)
            fraction1.append(float(len(common_blocks))/ float(len(longest_chain)))
        fraction.append(statistics.mean(fraction1))
    return statistics.mean(fraction)

# mining power utilization and fraction of longest chain blocks mined by adversary can be calculated by taking db file as input
print("mining power utilization", mining_power())
print("fraction of longest chain blocks mined by adversary", n_adversaries * fraction())