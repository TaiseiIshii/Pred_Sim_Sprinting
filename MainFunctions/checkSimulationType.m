function file_ext = checkSimulationType(simulation_type)

if strcmp(simulation_type,'_Nominal')
    file_ext = simulation_type  ;
    
elseif strcmp(simulation_type,'_HTD_Plus_1')
    file_ext = simulation_type;
elseif strcmp(simulation_type,'_HTD_Plus_2')
    file_ext = simulation_type;
elseif strcmp(simulation_type,'_HTD_Plus_3')
    file_ext = simulation_type;
elseif strcmp(simulation_type,'_HTD_Plus_4')
    file_ext = simulation_type;
elseif strcmp(simulation_type,'_HTD_Plus_5')
    file_ext = simulation_type;
elseif strcmp(simulation_type,'_HTD_Plus_6')
    file_ext = simulation_type;
elseif strcmp(simulation_type,'_HTD_Plus_7')
    file_ext = simulation_type;
elseif strcmp(simulation_type,'_HTD_Plus_8')
    file_ext = simulation_type;
elseif strcmp(simulation_type,'_HTD_Plus_9')
    file_ext = simulation_type;
elseif strcmp(simulation_type,'_HTD_Plus_10')
    file_ext = simulation_type;

elseif strcmp(simulation_type,'_HTD_Minus_1')
    file_ext = simulation_type;
elseif strcmp(simulation_type,'_HTD_Minus_2')
    file_ext = simulation_type;
elseif strcmp(simulation_type,'_HTD_Minus_3')
    file_ext = simulation_type;
elseif strcmp(simulation_type,'_HTD_Minus_4')
    file_ext = simulation_type;
elseif strcmp(simulation_type,'_HTD_Minus_5')
    file_ext = simulation_type;
elseif strcmp(simulation_type,'_HTD_Minus_6')
    file_ext = simulation_type;
elseif strcmp(simulation_type,'_HTD_Minus_8')
    file_ext = simulation_type;     
elseif strcmp(simulation_type,'_HTD_Minus_7')
    file_ext = simulation_type;  
elseif strcmp(simulation_type,'_HTD_Minus_9')
    file_ext = simulation_type;     
elseif strcmp(simulation_type,'_HTD_Minus_10')
    file_ext = simulation_type;    

elseif strcmp(simulation_type,'_IKTD_Plus_1')
    file_ext = simulation_type;
elseif strcmp(simulation_type,'_IKTD_Plus_2')
    file_ext = simulation_type;
elseif strcmp(simulation_type,'_IKTD_Plus_3')
    file_ext = simulation_type;
elseif strcmp(simulation_type,'_IKTD_Plus_4')
    file_ext = simulation_type;
elseif strcmp(simulation_type,'_IKTD_Plus_5')
    file_ext = simulation_type;
elseif strcmp(simulation_type,'_IKTD_Plus_6')
    file_ext = simulation_type;
elseif strcmp(simulation_type,'_IKTD_Plus_7')
    file_ext = simulation_type;
elseif strcmp(simulation_type,'_IKTD_Plus_8')
    file_ext = simulation_type;
elseif strcmp(simulation_type,'_IKTD_Plus_9')
    file_ext = simulation_type;    
elseif strcmp(simulation_type,'_IKTD_Plus_10')
    file_ext = simulation_type;    

elseif strcmp(simulation_type,'_IKTD_Minus_1')
    file_ext = simulation_type;
elseif strcmp(simulation_type,'_IKTD_Minus_2')
    file_ext = simulation_type;
elseif strcmp(simulation_type,'_IKTD_Minus_3')
    file_ext = simulation_type;
elseif strcmp(simulation_type,'_IKTD_Minus_4')
    file_ext = simulation_type;
elseif strcmp(simulation_type,'_IKTD_Minus_5')
    file_ext = simulation_type;
elseif strcmp(simulation_type,'_IKTD_Minus_6')
    file_ext = simulation_type;
elseif strcmp(simulation_type,'_IKTD_Minus_7')
    file_ext = simulation_type;
elseif strcmp(simulation_type,'_IKTD_Minus_8')
    file_ext = simulation_type;
elseif strcmp(simulation_type,'_IKTD_Minus_9')
    file_ext = simulation_type;    
elseif strcmp(simulation_type,'_IKTD_Minus_10')
    file_ext = simulation_type;    

elseif ~isempty(strfind(simulation_type,'PelvisTilt'))
    % Pelvic Tilt strain study conditions (e.g. _PelvisTilt_m13, _PelvisTilt_p00)
    file_ext = simulation_type;

elseif ~isempty(strfind(simulation_type,'PelvisShift'))
    % Pelvic tilt CAUSAL study v2 (e.g. _PelvisShift_m06, _PelvisShift_p00).
    % Rigid per-node offset of the pelvis_tilt waveform (Method B). m=minus
    % (more anterior in this model), p=plus (more posterior); number = degrees.
    file_ext = simulation_type;

end
