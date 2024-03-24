
CUDA_VISIBLE_DEVICES_CARLA=0
CUDA_VISIBLE_DEVICES_PYLOT=0

export CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES_CARLA
nohup zsh -c $PYLOT_HOME/scripts/run_simulator.sh > /tmp/carla.log 2>&1 &
sleep 5s

#num=0
#for error in 0.2 0.4 0.6 0.8; do
for error in 0.2; do
    sed -i "s/--obstacle_error=.*/--obstacle_error=${error}/" $PYLOT_HOME/configs/myconf.conf
    #sed -i "s/--simulation_recording_file=data\/sc[0-9]*.log/--simulation_recording_file=data\/sc${num}.log/" $PYLOT_HOME/configs/myconf.conf
    #((num++))
    #echo "obstacle_error=${error}" >> $PYLOT_HOME/script_exp/event.txt
    zsh $PYLOT_HOME/script_exp/get_event.sh -c $CUDA_VISIBLE_DEVICES_CARLA -p $CUDA_VISIBLE_DEVICES_PYLOT -n "obstacle_error=${error}"
    echo "${error} done"
done

kill -9 $(ps -ef|grep carla|gawk '$0 !~/grep/ {print $2}' |tr -s '\n' ' ')