-- Original test-only recorder/controller. Never included in the released mod.
local M={}
local active=false
local t=0
local samples={}
local maneuver,target
local previousVelocity
local dtMin,dtMax=math.huge,0
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
    local alpha,wheelSteer,hubLong,hubSide
    if w.node1 and w.node2 then
      local axis=obj:getNodePosition(w.node2)-obj:getNodePosition(w.node1)
      local direction=axis:cross(up)
      if direction:squaredLength()>1e-10 then
        direction:normalize();if direction:dot(forward)<0 then direction=-direction end
        local wheelRight=direction:cross(up)
        local hubVelocity=(obj:getNodeVelocityVector(w.node1)+obj:getNodeVelocityVector(w.node2))*.5
        hubLong=hubVelocity:dot(direction);hubSide=hubVelocity:dot(wheelRight)
        alpha=math.atan2(hubSide,hubLong)*180/math.pi
        wheelSteer=math.atan2(direction:dot(right),direction:dot(forward))*180/math.pi
      end
    end
    tyres[#tyres+1]={alpha=alpha,wheelSteer=wheelSteer,hubLong=hubLong,hubSide=hubSide,rimSpeed=w.angularVelocity*w.radius,name=w.name,slip=w.lastSlip or 0,side=w.lastSideSlip or 0,load=w.downForceRaw or 0,
      rays=w.rayCount,flat=w.isTireDeflated==true,broken=w.isBroken==true,punctured=w.isPunctured==true,
      pressure=pg and (obj:getGroupPressure(pg)-obj:getEnvPressure())/6894.757293 or nil,
      factor=f,base=applied and applied.base,combined=applied and applied.combined,
      reduxGrip=reduxGrip[id],temps=thermal and {thermal.temp[1],thermal.temp[2],thermal.temp[3],thermal.temp[4]},condition=thermal and thermal.condition}
  end
  samples[#samples+1]={t=t,dt=dt,phase=phase,speed=speed,longSpeed=vel:dot(forward),sideSpeed=vel:dot(right),
    beta=math.atan2(vel:dot(right),vel:dot(forward))*180/math.pi,yawRate=obj:getYawAngularVelocity(),
    ax=ax,ay=ay,x=p.x,y=p.y,z=p.z,throttle=throttle,steer=steer,brake=brake,parking=parking,
    actualSteer=electrics.values.steering,gear=electrics.values.gear,escActive=electrics.values.escActive,tcActive=electrics.values.tcsActive,tyres=tyres}
end
function M.start(kind,speed)
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
    if maneuver=='sweep' then
      steer=.45*clamp((t-12)/8,0,1)-.45*clamp((t-22)/8,0,1)
    else
      local turn=maneuver=='lift_reversal' and .5 or .22
      steer=turn*clamp((t-12)/2,0,1)
      if t>=18 and t<21 then
        if maneuver~='hold' then throttle=0 end
        if maneuver=='lift_reversal' then steer=.5-1.0*clamp((t-18)/.3,0,1) end
        if maneuver=='trail_mild' or maneuver=='trail_hard' then
          local amount=maneuver=='trail_mild' and .25 or .5
          brake=amount*clamp((t-18)/.25,0,1)*(1-clamp(t-20,0,1))
        end
      elseif t>=21 then
        throttle=0;steer=(maneuver=='lift_reversal' and -.5 or .22)*(1-clamp((t-21)/2,0,1))
      end
    end
  end
  input.event('throttle',throttle,1);input.event('steering',steer,1)
  input.event('brake',brake,1);input.event('parkingbrake',parking,1)
  snapshot(dt,phase,throttle,steer,brake,parking)
  local duration=maneuver=='sweep' and 34 or 26
  if t>=duration then active=false end
  if not active then
    input.event('throttle',0,1);input.event('steering',0,1);input.event('brake',0,1);input.event('parkingbrake',1,1)
  end
end
function M.status() return {active=active,t=t,count=#samples,dtMin=dtMin,dtMax=dtMax} end
function M.result() return {protocol='handling_v3',maneuver=maneuver,targetSpeed=target,samples=samples,clock=M.status()} end
M.onReset=function() active=false;samples={};t=0;previousVelocity=nil end
return M
