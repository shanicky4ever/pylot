rm pylot.log
rm pylot.csv

export TF_CPP_MIN_LOG_LEVEL=1

carla_device=0
pylot_device=0
name="test"

while getopts "c:p:n:" opt; do
    case $opt in
        c)
            carla_device=$OPTARG
            ;;
        p)
            pylot_device=$OPTARG
            ;;
        n)
            name=$OPTARG
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            ;;
    esac
done


echo $name >> event.txt

# export CUDA_VISIBLE_DEVICES=$carla_device
# timeout 65s nohup zsh -c $PYLOT_HOME/scripts/run_simulator.sh > /tmp/carla.log 2>&1 &
# sleep 2s
#nohup $CARLA_ROOT/CarlaUE4.sh -opengl -carla-server -nosound -fps=20 -RenderOffScreen --tm_port 8000 -world-port=2000 > /tmp/car.log 2>&1 &

export CUDA_VISIBLE_DEVICES=$carla_device
nohup zsh -c $PYLOT_HOME/scripts/run_simulator.sh > /tmp/carla.log 2>&1 &
sleep 5s |pv -t

export CUDA_VISIBLE_DEVICES=$pylot_device
timeout 420s python $PYLOT_HOME/pylot_with_fake.py --flagfile $PYLOT_HOME/configs/myconf.conf

kill -9 $(ps -ef|grep carla|gawk '$0 !~/grep/ {print $2}' |tr -s '\n' ' ')
kill -9 $(ps -ef|grep pylot_with|gawk '$0 !~/grep/ {print $2}' |tr -s '\n' ' ')

#python $PYLOT_HOME/script_exp/get_event.py event.txt $name

unset CUDA_VISIBLE_DEVICES
