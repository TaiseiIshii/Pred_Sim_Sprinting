function analyze_pelvic_shift()
% ANALYZE_PELVIC_SHIFT  Causal-study v2 analysis for the rigid pelvis_tilt
% offset sweep (_PelvisShift_*). For every converged condition (+ the N=50
% Nominal reference at offset 0) this computes hamstring strain/eccentric
% metrics, MTU-length metrics, the mechanism pathway (touchdown & peak hip
% flexion -> hamstring MTU length -> eccentric loading), and the DOSE-RESPONSE
% slope of each metric vs imposed offset. Outputs a CSV, a slopes CSV, and
% figures under Results/PelvicShift_Study/.
%
% Run headless: matlab -nosplash -nodesktop -wait -r "analyze_pelvic_shift; exit"

scriptDir = fileparts(mfilename('fullpath'));     % analysis
projRoot  = fileparts(scriptDir);
resDir    = fullfile(projRoot,'Results');
outDir    = fullfile(resDir,'PelvicShift_Study');
if ~exist(outDir,'dir'); mkdir(outDir); end

diary(fullfile(outDir,'analysis_log.txt')); diary on;
fprintf('=== analyze_pelvic_shift %s ===\n', datestr(now));

% ---- Hamstring rows in the 92-row muscleValues arrays -----------------
% Rows 1-46 = LEFT, 47-92 = RIGHT; within a side, order follows muscleNames
% with semimem, semiten, bifemlh, bifemsh at positions 7,8,9,10.
hamNames = {'semimem','semiten','bifemlh','bifemsh'};
hamL = [7 8 9 10];
hamR = [53 54 55 56];

% jointi (right side) used for the mechanism pathway
JI.pelvis_tilt = 1;
JI.hip_flex_r  = 7;     % hip_flexion_r in the 37-DOF q
JI.knee_r      = 10;    % knee_angle_r

% ---- Gather condition files (newest per offset token) -----------------
shFiles = dir(fullfile(resDir,'pred_sprinting_data_*PelvisShift*.mat'));
tokens  = containers.Map('KeyType','char','ValueType','char');
tokTime = containers.Map('KeyType','char','ValueType','double');
for i=1:numel(shFiles)
    tk = regexp(shFiles(i).name,'PelvisShift_[mp]\d+','match','once');
    if isempty(tk); continue; end
    if ~isKey(tokTime,tk) || shFiles(i).datenum > tokTime(tk)
        tokTime(tk) = shFiles(i).datenum;
        tokens(tk)  = fullfile(shFiles(i).folder,shFiles(i).name);
    end
end
shList = values(tokens);

% Newest N=50 Nominal as offset-0 reference
nomFiles = dir(fullfile(resDir,'pred_sprinting_data_*Nominal.mat'));
refList = {};
if ~isempty(nomFiles)
    bestIx=0; bestT=-inf; fbIx=0; fbT=-inf;
    for i=1:numel(nomFiles)
        if nomFiles(i).datenum>fbT; fbT=nomFiles(i).datenum; fbIx=i; end
        try
            tmp=load(fullfile(nomFiles(i).folder,nomFiles(i).name),'optimumOutput');
            if isfield(tmp,'optimumOutput') && isfield(tmp.optimumOutput,'options') ...
                    && isfield(tmp.optimumOutput.options,'N') && tmp.optimumOutput.options.N==50 ...
                    && nomFiles(i).datenum>bestT
                bestT=nomFiles(i).datenum; bestIx=i;
            end
        catch
        end
    end
    if bestIx==0; bestIx=fbIx; end
    refList = {fullfile(nomFiles(bestIx).folder,nomFiles(bestIx).name)};
end

allFiles = [refList, shList];
if isempty(shList)
    fprintf('No _PelvisShift_* results found in %s\n', resDir);
end

% ---- Build results table ----------------------------------------------
R = struct([]); n = 0;
for i=1:numel(allFiles)
    f = allFiles{i};
    S = load(f); o = S.optimumOutput;
    tk = regexp(f,'PelvisShift_[mp]\d+','match','once');
    if isempty(tk)
        offset = 0; label = 'Nominal(0)';
    else
        sgn = 1; if tk(13)=='m'; sgn=-1; end
        offset = sgn*str2double(tk(14:end));
        label = sprintf('%+d deg', offset);
    end

    q     = o.optVars_nsc.q;            % [37 x nCol] rad
    ptilt = rad2deg(q(JI.pelvis_tilt,:));
    hipR  = rad2deg(q(JI.hip_flex_r,:));
    kneeR = rad2deg(q(JI.knee_r,:));
    mv    = o.muscleValues;
    ncol  = size(mv.lMtilde,2);

    % time step for work integration (half-stride duration / (nodes-1))
    try; T = o.optVars_nsc.totalTime; catch; T = NaN; end
    dt = T / max(ncol-1,1);

    try; status = o.stats.return_status; catch; status = 'unknown'; end
    try; gv = max(o.GRFs.R(:,2)); catch; gv = NaN; end

    n = n+1;
    R(n).file=f; R(n).label=label; R(n).offset=offset; R(n).status=status;
    R(n).speed=o.ave_speed; R(n).time=T;
    R(n).ptMean=mean(ptilt); R(n).ptMin=min(ptilt); R(n).ptMax=max(ptilt);
    R(n).grfVpeak=gv;
    % mechanism upstream: touchdown (node 1) & peak hip flexion
    R(n).hipR_TD=hipR(1); R(n).hipR_peak=max(hipR);
    R(n).kneeR_TD=kneeR(1); R(n).kneeR_min=min(kneeR);

    % effort proxy: mean of sum of squared activations
    try; R(n).effort = mean(sum(o.optVars_nsc.act.^2,1)); catch; R(n).effort = NaN; end

    for s=1:2
        if s==1; rows=hamL; side='L'; else; rows=hamR; side='R'; end
        for h=1:4
            r=rows(h);
            lM   = mv.lMtilde(r,:);
            vM   = mv.vMtilde(r,:);
            Fpe  = mv.Fpetilde(r,:);
            Fce  = mv.Fce(r,:);
            FMv  = mv.FMvtilde(r,:);
            ecc  = max(0,vM);
            if isfield(mv,'Fiso'); FceN = Fce./max(mv.Fiso(r,:),eps);
            else; FceN = Fce./max(max(abs(Fce)),eps); end
            % MTU length (musculotendon) if available
            if isfield(mv,'lMTk_lr'); lMT = mv.lMTk_lr(r,:); else; lMT = nan(1,ncol); end

            eccLoad = ecc .* FMv;              % active force during lengthening
            comp    = lM .* ecc .* FceN;       % composite strain-force risk
            % eccentric (negative) work proxy: integral of Fce*max(0,vM) over stride
            % (vMtilde is normalized; this is a dimensionless eccentric impulse)
            eccWork = sum(Fce .* ecc) * dt;

            [peakLM, ix] = max(lM);
            fld = sprintf('%s_%s',hamNames{h},side);
            R(n).([fld '_peakLM'])     = peakLM;
            R(n).([fld '_tPeakPct'])   = 100*(ix-1)/max(ncol-1,1);
            R(n).([fld '_peakVMecc'])  = max(ecc);
            R(n).([fld '_peakEccLoad'])= max(eccLoad);
            R(n).([fld '_peakFpe'])    = max(Fpe);
            R(n).([fld '_peakComp'])   = max(comp);
            R(n).([fld '_eccWork'])    = eccWork;
            R(n).([fld '_peakLMT'])    = max(lMT);
            R(n).([fld '_LMTexc'])     = max(lMT)-min(lMT);   % MTU excursion
        end
    end
end

% ---- Sort by offset ---------------------------------------------------
offs = [R.offset];
[~,ord] = sort(offs); R = R(ord); offs = [R.offset];

% ---- Write summary CSV ------------------------------------------------
csvFile = fullfile(outDir,'pelvic_shift_summary.csv');
flds = setdiff(fieldnames(R),{'file'},'stable');
fid = fopen(csvFile,'w');
fprintf(fid,'%s,',flds{1:end-1}); fprintf(fid,'%s\n',flds{end});
for i=1:numel(R)
    for j=1:numel(flds)
        v=R(i).(flds{j});
        if ischar(v); fprintf(fid,'%s',v); else; fprintf(fid,'%.6g',v); end
        if j<numel(flds); fprintf(fid,','); end
    end
    fprintf(fid,'\n');
end
fclose(fid);
fprintf('Wrote %s\n', csvFile);

% ---- Dose-response slopes (metric vs offset, linear regression) -------
% Use bilateral mean per muscle for the key metrics.
metricKeys = {'peakLM','peakFpe','peakEccLoad','peakComp','eccWork','peakLMT','LMTexc'};
slopeRows = {};
slopeRows(end+1,:) = {'metric','muscle','slope_per_deg','intercept','R2','pearson_r'};
for mk = 1:numel(metricKeys)
    for h = 1:4
        yL = arrayfun(@(s) s.(sprintf('%s_L_%s',hamNames{h},metricKeys{mk})), R);
        yR = arrayfun(@(s) s.(sprintf('%s_R_%s',hamNames{h},metricKeys{mk})), R);
        y  = (yL+yR)/2;
        [slope,intercept,R2,pr] = lin_fit(offs(:), y(:));
        slopeRows(end+1,:) = {metricKeys{mk}, hamNames{h}, slope, intercept, R2, pr}; %#ok<AGROW>
    end
end
% also slopes for task cost and mechanism upstream
for key = {'speed','effort','hipR_TD','hipR_peak'}
    y = arrayfun(@(s) s.(key{1}), R);
    [slope,intercept,R2,pr] = lin_fit(offs(:), y(:));
    slopeRows(end+1,:) = {key{1}, 'whole-body', slope, intercept, R2, pr}; %#ok<AGROW>
end
slopeFile = fullfile(outDir,'pelvic_shift_slopes.csv');
fid = fopen(slopeFile,'w');
for i=1:size(slopeRows,1)
    row = slopeRows(i,:);
    for j=1:numel(row)
        v=row{j};
        if ischar(v); fprintf(fid,'%s',v); else; fprintf(fid,'%.6g',v); end
        if j<numel(row); fprintf(fid,','); end
    end
    fprintf(fid,'\n');
end
fclose(fid);
fprintf('Wrote %s\n', slopeFile);

% ---- Figures ----------------------------------------------------------
cols = lines(4); mk = {'-o','-s','-^','-d'};

% Fig 1: manipulation check -- realised mean pelvis_tilt vs offset
f1=figure('Visible','off','Position',[100 100 560 470]);
realMean=[R.ptMean];
% reference mean at offset 0 (use the first offset-0 entry; Nominal & p00 share 0)
ix0 = find(offs==0,1,'first');
if isempty(ix0); refMean0 = realMean(1) - offs(1); else; refMean0 = realMean(ix0); end
plot(offs,realMean,'-o','LineWidth',1.6,'MarkerFaceColor','b'); hold on;
plot(offs,refMean0+offs,'k--');
xlabel('Imposed offset (deg)'); ylabel('Realised mean pelvis\_tilt (deg)');
title('操作の成立: 実現平均 vs 指示オフセット'); grid on;
legend('realised','reference+offset','Location','best');
print(f1,'-dpng','-r150',fullfile(outDir,'fig1_manipulation_check.png'));

% Fig 2: peak lMtilde dose-response (bilateral mean)
f2=figure('Visible','off','Position',[100 100 760 470]);
for h=1:4
    yL=arrayfun(@(s) s.(sprintf('%s_L_peakLM',hamNames{h})),R);
    yR=arrayfun(@(s) s.(sprintf('%s_R_peakLM',hamNames{h})),R);
    plot(offs,(yL+yR)/2,mk{h},'Color',cols(h,:),'LineWidth',1.5,'MarkerFaceColor',cols(h,:)); hold on;
end
xl = [min(offs) max(offs)];
plot(xl,[1.2 1.2],'k:'); text(xl(1),1.205,'strain threshold','FontSize',8);
xlabel('Imposed offset (deg, - = more anterior)'); ylabel('peak lMtilde (bilateral mean)');
title('ハム peak 正規化筋線維長の用量反応'); legend(hamNames,'Location','best'); grid on;
print(f2,'-dpng','-r150',fullfile(outDir,'fig2_dose_peakLM.png'));

% Fig 3: peak passive force + eccentric work
f3=figure('Visible','off','Position',[100 100 1100 470]);
subplot(1,2,1);
for h=1:4
    yL=arrayfun(@(s) s.(sprintf('%s_L_peakFpe',hamNames{h})),R);
    yR=arrayfun(@(s) s.(sprintf('%s_R_peakFpe',hamNames{h})),R);
    plot(offs,(yL+yR)/2,mk{h},'Color',cols(h,:),'LineWidth',1.5,'MarkerFaceColor',cols(h,:)); hold on;
end
xlabel('offset (deg)'); ylabel('peak Fpetilde'); title('受動張力'); legend(hamNames,'Location','best'); grid on;
subplot(1,2,2);
for h=1:4
    yL=arrayfun(@(s) s.(sprintf('%s_L_eccWork',hamNames{h})),R);
    yR=arrayfun(@(s) s.(sprintf('%s_R_eccWork',hamNames{h})),R);
    plot(offs,(yL+yR)/2,mk{h},'Color',cols(h,:),'LineWidth',1.5,'MarkerFaceColor',cols(h,:)); hold on;
end
xlabel('offset (deg)'); ylabel('eccentric impulse \Sigma Fce\cdotmax(0,vM)\cdotdt'); title('伸張性負荷'); grid on;
print(f3,'-dpng','-r150',fullfile(outDir,'fig3_dose_passive_eccwork.png'));

% Fig 4: mechanism pathway + task cost
f4=figure('Visible','off','Position',[100 100 1100 470]);
subplot(1,2,1);
yyaxis left;  plot(offs,[R.hipR_TD],'-o','LineWidth',1.5); ylabel('touchdown hip flexion (deg)');
yyaxis right; bifemMTU=arrayfun(@(s) (s.bifemlh_L_peakLMT+s.bifemlh_R_peakLMT)/2,R);
plot(offs,bifemMTU,'-s','LineWidth',1.5); ylabel('bifemlh peak MTU length (m)');
xlabel('offset (deg)'); title('メカニズム: 接地股屈曲 -> ハムMTU長'); grid on;
subplot(1,2,2);
yyaxis left;  plot(offs,[R.speed],'-o','LineWidth',1.5); ylabel('average speed (m/s)');
yyaxis right; plot(offs,[R.effort],'-s','LineWidth',1.5); ylabel('effort \Sigma act^2 (mean)');
xlabel('offset (deg)'); title('課題コスト: 速度と筋努力'); grid on;
print(f4,'-dpng','-r150',fullfile(outDir,'fig4_mechanism_cost.png'));

fprintf('Figures written to %s\n', outDir);
fprintf('=== analysis done ===\n');
diary off;
end

% ---- helper: simple linear regression -------------------------------------
function [slope,intercept,R2,pr] = lin_fit(x,y)
    ok = isfinite(x) & isfinite(y);
    x = x(ok); y = y(ok);
    if numel(x) < 2
        slope=NaN; intercept=NaN; R2=NaN; pr=NaN; return;
    end
    p = polyfit(x,y,1);
    slope = p(1); intercept = p(2);
    yhat = polyval(p,x);
    ssres = sum((y-yhat).^2);
    sstot = sum((y-mean(y)).^2);
    if sstot <= eps; R2 = NaN; else; R2 = 1 - ssres/sstot; end
    if std(x)<=eps || std(y)<=eps
        pr = NaN;
    else
        c = corrcoef(x,y); pr = c(1,2);
    end
end
