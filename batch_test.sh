while getopts "a:c:m:" opt; do
    case $opt in
        c)
            class=$OPTARG
            ;;
        a)
            attribute=$OPTARG
            ;;
        m)
            mode=$OPTARG
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            ;;
    esac
done

#outputfile="res/batch_res_${class}_${attribute}.txt"
outputfile="tmp_res.txt"
echo $outputfile
#rm $outputfile
configfile="configs/${class}/${attribute}.conf"

echo "Testing ${class} ${attribute} with ${mode}"

if [[ $class == "delay_output" ]]; then
    for fail in {1..3}; do
        for delay in 50 100 200 500; do
            echo "fail_ratio:${fail}, delay:${delay}" >> $outputfile
            sed -i "s/--${attribute}_failure_ratio=[0-9.]*/--${attribute}_failure_ratio=${fail}/" ${configfile}
            sed -i "s/--${attribute}_failure_delay=[0-9.]*/--${attribute}_failure_delay=${delay}/" ${configfile}
            for i in {1..2}; do
                zsh get_event_scenario.sh -f ${configfile} -o ${outputfile} -s ${mode};
            done
        done;
    done
else
    if [[ "$attribute" =~ ^RGB* ]]; then
        for mu in "gaussian" "motion\_blur" "broke\_part" "brightness"; do
            sed -i "s/--mutate_camera_type=[a-z_]*/--mutate_camera_type=${mu}/" ${configfile}
            echo "class: ${class}, attr: ${attribute}, mutate:${mu}" >> $outputfile
            zsh get_event_scenario.sh -f ${configfile} -o ${outputfile} -s ${mode};
        done
    else
        echo "mode:{$mode},class: ${class}, attr: ${attribute} " >> $outputfile
        zsh get_event_scenario.sh -f ${configfile} -o ${outputfile} -s ${mode};
    fi
fi


