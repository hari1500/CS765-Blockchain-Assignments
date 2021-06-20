import networkx as nx
import sqlite3
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-o","--outputfile")
parser.add_argument("-db","--inputdatabase", required=True)
args = parser.parse_args()
inputdb = None
outputfile = None
if args.inputdatabase:
    inputdb = args.inputdatabase
if args.outputfile:
    outputfile = args.outputfile

# Reads blocks from database file
connection = sqlite3.connect(inputdb, check_same_thread=False)
cursor = connection.cursor()
height=1
level=[]
cursor.execute("SELECT prevhash, blockhash, height, minedby FROM blocks ORDER BY height ASC")
rows=cursor.fetchall()
for row in rows:
    level.append((bytearray.hex(bytearray(row[0])), bytearray.hex(bytearray(row[1]))))

# Plots blockchain
g = nx.DiGraph()
g.add_edges_from(level)
p = nx.drawing.nx_pydot.to_pydot(g)
for n,row in zip(p.get_node_list()[1:], rows):
    n.set_fillcolor("#00ff00" if row[3] == 1 else "#0000ff")
    n.set_style("filled")

# Saves plot in output file
p.write_png('chain.png' if outputfile == None else outputfile)