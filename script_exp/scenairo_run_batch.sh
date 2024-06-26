while getopts "c:p:f:i:" opt; do
    case $opt in
        c)
            carla_device=$OPTARG
            ;;
        p)
            pylot_device=$OPTARG
            ;;
        f)
            flagfile=$OPTARG
            ;;
        i)
            inputfile=$OPTARG
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            ;;
    esac
done

if [[ -f "${inputfile}" ]]; then
    while IFS= read -r line || [[ -n "$line" ]]; do
        zsh ${PYLOT_HOME}/script_exp/run_scenario.sh -c ${carla_device} -p ${pylot_device} -s ${line}
    done < "${inputfile}"
else
    echo "File not found: ${inputfile}"
fi