# Removes and recreates db folder
rm -rf db/
mkdir db

VAR2="python3 miner.py -i 2 -hp 0.022222 -db db/db"
VAR3="python3 adversary.py -i 2 -hp 0.111111 -n 3 -db db/db"
an=" &"

# Creates 30 miners
for i in {1..30}
do
VAR1="$VAR2$i"
VAR1="$VAR1$an"
eval $VAR1
echo $VAR1
sleep .5
done

# Creates 3 adversaries
for i in {31..33}
do
VAR4="$VAR3$i"
VAR4="$VAR4$an"
eval $VAR4
echo $VAR4
sleep .5
done

# Run for 10 mins
sleep 600

# Kill all miners and adversaries
VAR1=`ps aux | grep miner.py | awk '{print $2}' | xargs kill -9`
eval $VAR1
VAR2=`ps aux | grep adversary.py | awk '{print $2}' | xargs kill -9`
eval $VAR2
