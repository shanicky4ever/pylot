source ~/.bashrc

cd $PYLOT_HOME

# timeout 330s nohup bash /scripts/run_simulator.sh > /tmp/carla.log 2>&1 &
# sleep 3

python3 pylot_with_fake.py --flagfile=$1

#kill -9 $(ps -ef|grep pylot|gawk '$0 !~/grep/ {print $2}' |tr -s '\n' ' ')