-- Original test-only recorder/controller. Never included in the released mod.
local M={}
local active=false
local t=0
local samples={}
local maneuver,target
local previousVelocity
local dtMin,dtMax=math.huge,0
local params,previousBeta,controlThrottle
local function clamp(x,a,b) return math.max(a,math.min(b,x)) end
local function upvalue(f,key)
  if type(f)~='function' then return nil end
  for i=1,64 do local name,value=debug.getupvalue(f,i);if name==key then return value end;if not name then break end end
end
local function snapshot(dt,phase,throttle,steer,brake,parking)
  local vel=obj:getVelocity()
  local forward=obj:getDirectionVector()
  local up=obj:getDirectionVectorUp()
  local right=forward:cross(up)
  local p=obj:getPosition()
  local speed=vel:length()
  local ax,ay=0,0
  if previousVelocity and dt>0 then
    local a=(vel-previousVelocity)/dt
    ax=a:dot(forward);ay=a:dot(right)
  end
  previousVelocity=vec3(vel)
  local diag=rawget(_G,'automaticTyresGrip') and automaticTyresGrip.getDiagnostics() or nil
  local redux=rawget(_G,'luukstyrethermalsandwear')
  local calc=redux and upvalue(redux.updateGFX,'CalculateTyreGrip')
  local thermalData=upvalue(calc,'tyreData') or {}
  local reduxGrip=upvalue(calc,'tyreGripTable') or {}
  local tyres={}
  for id,w in pairs(wheels.wheelRotators) do
    local pg=w.pressureGroup and v.data.pressureGroups[w.pressureGroup]
    local f=diag and diag.factors[id] or 1
    local applied=diag and diag.applied[id]
    local thermal=thermalData[id]
    tyres[#tyres+1]={name=w.name,slip=w.lastSlip or 0,side=w.lastSideSlip or 0,load=w.downForceRaw or 0,
      rays=w.rayCount,rimSpeed=w.angularVelocity*w.radius,flat=w.isTireDeflated==true,broken=w.isBroken==true,punctured=w.isPunctured==true,
      pressure=pg and (obj:getGroupPressure(pg)-obj:getEnvPressure())/6894.757293 or nil,
      factor=f,base=applied and applied.base,combined=applied and applied.combined,
      reduxGrip=reduxGrip[id],temps=thermal and {thermal.temp[1],thermal.temp[2],thermal.temp[3],thermal.temp[4]},condition=thermal and thermal.condition}
  end
  samples[#samples+1]={t=t,dt=dt,phase=phase,speed=speed,longSpeed=vel:dot(forward),sideSpeed=vel:dot(right),
    beta=math.atan2(vel:dot(right),vel:dot(forward))*180/math.pi,yawRate=obj:getYawAngularVelocity(),
    ax=ax,ay=ay,x=p.x,y=p.y,z=p.z,throttle=throttle,steer=steer,brake=brake,parking=parking,
    actualSteer=electrics.values.steering,gear=electrics.values.gear,escActive=electrics.values.escActive,tcActive=electrics.values.tcsActive,tyres=tyres}
end
function M.start(kind,speed,settings)
  params=settings or {};previousBeta=0;controlThrottle=.2;
  maneuver=kind;target=speed;t=0;samples={};previousVelocity=nil;active=true;dtMin=math.huge;dtMax=0
end
function M.updateGFX(dt)
  if not active or dt<=0 then return end
  t=t+dt;dtMin=math.min(dtMin,dt);dtMax=math.max(dtMax,dt)
  local speed=obj:getVelocity():length()
  local throttle,steer,brake,parking=0,0,0,0
  local phase='warmup'
  if t<2 then phase='settle';parking=1
  elseif t<12 then throttle=clamp(.16+(target-speed)*.25,0,.65)
  else
    phase='measure'
    throttle=clamp(.16+(target-speed)*.25,0,.65)
    if maneuver=='corner' then
      steer=.12*clamp(t-12,0,1)+.10*clamp(t-17,0,1)
    elseif maneuver=='steering' then
      if t<13 then steer=.18 elseif t<14 then steer=-.18 else steer=0 end
    elseif maneuver=='brake' then
      throttle=0;brake=1
      if speed<.5 then brake=0;parking=1;active=false end
    elseif maneuver=='controlled' then
      local vel=obj:getVelocity();local f=obj:getDirectionVector();local right=f:cross(obj:getDirectionVectorUp())
      local beta=math.atan2(vel:dot(right),vel:dot(f))*180/math.pi
      local rate=clamp((beta-previousBeta)/dt,-150,150);previousBeta=beta
      steer=clamp((params.feedforward or -.06)+(params.kp or .025)*(beta+(params.angle or 20))+(params.kd or .006)*rate,-.7,.7)
      local rear,total=0,0
      for _,w in pairs(wheels.wheelRotators) do
        if w.name=='RL' or w.name=='RR' then rear=rear+math.abs(w.angularVelocity*w.radius);total=total+1 end
      end
      rear=rear/math.max(total,1)
      local desired=math.abs(vel:dot(f))*(params.rimRatio or 1.15)+2.5
      throttle=clamp(.14+(18-speed)*.035+(desired-rear)*.055,0,.7)
      -- Brief identical slide entry, followed by the same feedback rules.
      if t<12.35 then steer=.4;parking=.5;throttle=.65 end
    elseif maneuver=='drift' then
      throttle=t<12.8 and .85 or .65
      steer=t<12.8 and .45 or -.2
      parking=t<12.35 and .6 or 0
    end
  end
  input.event('throttle',throttle,1);input.event('steering',steer,1)
  input.event('brake',brake,1);input.event('parkingbrake',parking,1)
  snapshot(dt,phase,throttle,steer,brake,parking)
  local duration=maneuver=='corner' and 28 or maneuver=='brake' and 23 or maneuver=='controlled' and 24 or 19
  if t>=duration then active=false end
  if not active then
    input.event('throttle',0,1);input.event('steering',0,1);input.event('brake',0,1);input.event('parkingbrake',1,1)
  end
end
function M.status() return {active=active,t=t,count=#samples,dtMin=dtMin,dtMax=dtMax} end
function M.result() return {maneuver=maneuver,targetSpeed=target,driverParameters=params,samples=samples,clock=M.status()} end
M.onReset=function() active=false;samples={};t=0;previousVelocity=nil end
return M
