
carla_device=0
pylot_device=0
name="test"

while getopts "c:p:" opt; do
    case $opt in
        c)
            carla_device=$OPTARG
            ;;
        p)
            pylot_device=$OPTARG
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            ;;
    esac
done

CUDA_VISIBLE_DEVICES_CARLA=$carla_device
CUDA_VISIBLE_DEVICES_PYLOT=$pylot_device



export CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES_CARLA
nohup zsh -c $PYLOT_HOME/scripts/run_simulator.sh > /tmp/carla.log 2>&1 &
sleep 5s |pv -t

#num=0

for mutate in zoomout xleft yup; do
    sed -i "s/--obstacle_mutate=.*/--obstacle_mutate=${mutate}/" $PYLOT_HOME/configs/myconf.conf
    for dt in depth_camera; do
        sed -i "s/obstacle_location_finder_sensor=.*/obstacle_location_finder_sensor=${dt}/" $PYLOT_HOME/configs/myconf.conf
        #for error in 0.02 0.04 0.08 0.10 0.15; do
        #for error in 0.6; do
        for error in 0.01 0.05 0.2 0.3 0.4 0.5 0.6 0.02 0.04 0.08 0.1 0.15; do
            data_path="data/${mutate}_${dt}_${error}"
            if [ -d $data_path ]; then
                rm -rf $data_path
            fi
            mkdir -p $data_path
            sed -i "s/--obstacle_error=.*/--obstacle_error=${error}/" $PYLOT_HOME/configs/myconf.conf
            sed -i "s#--data_path=.*#--data_path=${data_path}#" $PYLOT_HOME/configs/myconf.conf
            zsh $PYLOT_HOME/script_exp/get_event.sh -c $CUDA_VISIBLE_DEVICES_CARLA -p $CUDA_VISIBLE_DEVICES_PYLOT -n "obstacle_error=${error}"
            echo "${error} done"
            sleep 5s|pv -t
        done
    done
done

kill -9 $(ps -ef|grep carla|gawk '$0 !~/grep/ {print $2}' |tr -s '\n' ' ')
