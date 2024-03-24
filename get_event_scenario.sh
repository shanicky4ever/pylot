rm pylot.log
# docker run --rm -d --name carla_sim \
#     -e SDL_VIDEODRIVER=offscreen \
#     -e DISPLAY=$DISPLAY\
#     -v /tmp/.X11-unix:/tmp/.X11-unix \
#     --net=host \
#     -it \
#     --gpus all \
#     carlasim/carla:0.9.10 ./CarlaUE4.sh -opengl -nosound -carla-server -fps=20 --tm_port 8000 -world-port 2000 -RenderOffScreen

#timeout 190s 
nohup $CARLA_ROOT/CarlaUE4.sh -opengl -carla-server -nosound -fps=20 -RenderOffScreen --tm_port 8000 -world-port=2000 > /tmp/car.log 2>&1 &

docker start pylot 
nvidia-docker exec -i -t pylot sudo service ssh start

sleep 5| pv -t

while getopts "f:o:s:" opt; do
    case $opt in
        f)
            flagfile=$OPTARG
            ;;
        o)
            outputfile=$OPTARG
            ;;
        s)
            scenario=$OPTARG
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            ;;
    esac
done

script_scenario="/bin/zsh /home/erdos/workspace/run_sc.sh "$scenario
rm docker_sc_handle.sh
echo "ssh -p 20022 erdos@localhost \"$script_scenario\"" >> docker_sc_handle.sh
chmod +x docker_sc_handle.sh

nohup ./docker_sc_handle.sh > /tmp/sc.log 2>&1 &

script="/bin/zsh /home/erdos/workspace/run_pylot.sh "$flagfile

timeout 180s ssh -p 20022 erdos@localhost "$script"
#timeout 400s nvidia-docker exec -i -t pylot $script
#docker stop carla_sim
kill -9 $(ps -ef|grep UE4|gawk '$0 !~/grep/ {print $2}' |tr -s '\n' ' ')
docker stop pylot

#ssh -p 20022 erdos@localhost "sudo kill -9 $(ps -ef|grep pylot|gawk '$0 !~/grep/ {print $2}' |tr -s '\n' ' ')"

python3 get_event.py $outputfile

sleep 3

