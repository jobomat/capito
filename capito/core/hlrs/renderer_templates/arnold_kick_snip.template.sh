$ARNOLD_PATH/bin/kick \
-nstdin -dp -dw -v 5 \
-set color_manager_ocio.config $OCIO \
-i $WS_BASE_PATH/{share_name}/hlrs/{job_name}/scenes/{ass_file} \
-o $WS_BASE_PATH/{share_name}/hlrs/{job_name}/output/{jobfile_name}.exr \
-logfile $WS_BASE_PATH/{share_name}/hlrs/{job_name}/logs/{jobfile_name}.log

touch $WS_BASE_PATH/{share_name}/hlrs/{job_name}/transferable/{jobfile_name}
