
carla_device=0
pylot_device=0
name="test"
data_base_dir="data"

while getopts "c:p:d:" opt; do
    case $opt in
        c)
            carla_device=$OPTARG
            ;;
        p)
            pylot_device=$OPTARG
            ;;
        d)
            data_base_dir=$OPTARG
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            ;;
    esac
done

for mutate in zoomout; do
    sed -i "s/--obstacle_mutate=.*/--obstacle_mutate=${mutate}/" $PYLOT_HOME/configs/myconf.conf
    for dt in  depth_camera; do
        sed -i "s/obstacle_location_finder_sensor=.*/obstacle_location_finder_sensor=${dt}/" $PYLOT_HOME/configs/myconf.conf
        #for error in 0.01 0.02 0.04 0.05 0.08 0.1 0.2 0.3 0.4 0.5 0.6; do
        for error in 0.1 ; do
            data_path="${data_base_dir}/${mutate}_${dt}_${error}"
            if [ -d $data_path ]; then
                rm -rf $data_path
            fi
            mkdir -p $data_path
            sed -i "s/--obstacle_error=.*/--obstacle_error=${error}/" $PYLOT_HOME/configs/myconf.conf
            sed -i "s#--data_path=.*#--data_path=${data_path}#" $PYLOT_HOME/configs/myconf.conf
            zsh $PYLOT_HOME/script_exp/get_event.sh -c ${carla_device} -p ${pylot_device} -n "obstacle_error=${error}"
            echo "${mutate} ${dt} ${error} done"
            sleep 5s|pv -t
        done
    done
done
