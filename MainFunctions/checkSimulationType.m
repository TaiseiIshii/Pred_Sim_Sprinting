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

elseif ~isempty(strfind(simulation_type,'PelvisTD'))
    % Pelvic tilt CAUSAL study v3 = Touchdown Pelvic Tilt (TDPT)
    % (e.g. _PelvisTD_m6, _PelvisTD_p6, _PelvisTD_p0). A SINGLE equality at the
    % touchdown node pins pelvis_tilt to (Nominal touchdown tilt + offset);
    % pelvis_tilt is free at every other node and the rest of the motion
    % re-optimises naturally. m=minus (more anterior in this model), p=plus
    % (more posterior); number = degrees.
    file_ext = simulation_type;

elseif ~isempty(strfind(simulation_type,'HamFascicle'))
    % Hamstring muscle-architecture study (RQ2): scales hamstring optimal
    % FIBRE length to model short-fascicle (higher-risk) vs long-fascicle
    % virtual athletes (Timmins 2016: short BFlh fascicles = strongest
    % modifiable HSI risk factor). e.g. _HamFascicle_m20 -> lMo x0.80,
    % _HamFascicle_p20 -> lMo x1.20. Muscle parameters change; the kinematic
    % sprinting task is unchanged.
    file_ext = simulation_type;

elseif ~isempty(strfind(simulation_type,'HamStrength'))
    % Hamstring muscle-architecture study (RQ2): scales hamstring maximal
    % isometric FORCE to model weak (higher-risk) vs strong virtual athletes.
    % e.g. _HamStrength_m30 -> Fmax x0.70, _HamStrength_p30 -> Fmax x1.30.
    file_ext = simulation_type;

elseif ~isempty(strfind(simulation_type,'HamPareto'))
    % Injury-minimising optimal-technique study (RQ3+RQ4): adds a smooth
    % biarticular-hamstring fascicle-overstretch penalty (wJ(13)) to the
    % objective and sweeps its weight to trace the speed<->peak-fascicle-strain
    % Pareto frontier, optionally on an at-risk virtual athlete.
    % e.g. _HamPareto_Nom_w0200 -> nominal athlete, wJ(13)=0.20;
    %      _HamPareto_Sh_w0800  -> short-fascicle athlete (lMo x0.80), wJ(13)=0.80.
    file_ext = simulation_type;

end
