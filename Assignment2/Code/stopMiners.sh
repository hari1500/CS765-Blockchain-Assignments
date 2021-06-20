# Kills all processes involving miner.py and adversary.py
VAR1=`ps aux | grep miner.py | awk '{print $2}' | xargs kill -9`
eval $VAR1
VAR2=`ps aux | grep adversary.py | awk '{print $2}' | xargs kill -9`
eval $VAR2
