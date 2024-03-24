#sleep 4h| pv -t
for scenario_mode in 1 DynamicObjectCrossing_4 OppositeVehicleRunningRedLight_1 ; do
    if [[ $scenario_mode == 1 ]]; then
        echo "nothing happen"
        continue
    fi
    rm -rf res
    mkdir res
    for attribute in RGBobdetect RGBlanedetect GNSS depth_tracking ; do
        zsh batch_test.sh -a $attribute -c input_mutate -m $scenario_mode
    done

    for attribute in GNSS RGBobdetect depth_tracking ; do
        zsh batch_test.sh -a $attribute -c mutate_full -m $scenario_mode
    done


    for attribute in obstacle_detection obstacle_tracking lane_detection planning; do
    #for attribute in planning lane_detection; do   
        zsh batch_test.sh -a $attribute -c delay_output -m $scenario_mode
    done

    mv res res_collect/res_sceanrio_${scenario_mode}

done