
for scenario_mode in 1 FollowLeadingVehicle_5 SignalizedJunctionRightTurn_6; do
    if [[ $scenario_mode == 1 ]]; then
        echo "nothing happen"
        continue
    fi
    rm -rf res
    mkdir res
    for attribute in  RGBobdetect RGBlanedetect GNSS depth_tracking ; do
    #for attribute in RGBobdetect RGBlanedetect GNSS; do
        zsh batch_test.sh -a $attribute -c input_mutate -m $scenario_mode
    done
    sleep 1m| pv -t
    for attribute in  depth_tracking RGBobdetect GNSS; do
        zsh batch_test.sh -a $attribute -c mutate_full -m $scenario_mode
    done
    sleep 1m| pv -t

    for attribute in obstacle_detection obstacle_tracking lane_detection ; do
    #for attribute in planning lane_detection; do   
        zsh batch_test.sh -a $attribute -c delay_output -m $scenario_mode
        sleep 1m| pv -t
    done

    mv res res_collect/res_sceanrio_${scenario_mode}

done