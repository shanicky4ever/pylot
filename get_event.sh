rm pylot.log

docker run --rm -d --name carla_sim \
    -e SDL_VIDEODRIVER=offscreen \
    -e DISPLAY=$DISPLAY\
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    --net=host \
    -it \
    --gpus all \
    carlasim/carla:0.9.10.1 ./CarlaUE4.sh -opengl -carla-server -nosound -benchmark -fps=20

docker start pylot 
nvidia-docker exec -i -t pylot sudo service ssh start
sleep 3

while getopts "f:o:" opt; do
    case $opt in
        f)
            flagfile=$OPTARG
            ;;
        o)
            outputfile=$OPTARG
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            ;;
    esac
done

script="/bin/zsh ~/workspace/run_pylot.sh "$flagfile

timeout 360s ssh -p 20022 erdos@localhost "$script"
#timeout 400s nvidia-docker exec -i -t pylot $script



docker stop carla_sim
docker stop pylot

#ssh -p 20022 erdos@localhost "sudo kill -9 $(ps -ef|grep pylot|gawk '$0 !~/grep/ {print $2}' |tr -s '\n' ' ')"

python3 get_event.py $outputfile

