-- Original private recorder/driver. Not included in the mod release.
local M={}
local t,active=0,false
local samples={}
local function clamp(x,a,b) return math.max(a,math.min(b,x)) end
local function up(f,key)
  if type(f)~='function' then return nil end
  for i=1,64 do local n,x=debug.getupvalue(f,i);if n==key then return x end;if not n then break end end
end
function M.start() t=0;active=true;samples={} end
function M.updateGFX(dt)
  if not active or dt<=0 then return end
  t=t+dt
  local speed=obj:getVelocity():length()
  local throttle,steer,brake,parking,phase=0,0,0,0,'rest'
  if t<2 then parking=1
  elseif t<11 then phase='straight';throttle=clamp(.16+(20-speed)*.25,0,.65)
  elseif t<16 then phase='gentle_corner';throttle=clamp(.16+(20-speed)*.25,0,.65);steer=.08*clamp(t-11,0,1)
  elseif t<21 then phase='hard_corner';throttle=clamp(.16+(20-speed)*.25,0,.65);steer=.30
  elseif t<25 then phase='powered_slide';throttle=.8;steer=t<22 and .5 or -.18
  elseif t<29 then phase='brake';brake=1
  else parking=1;active=t<33 end
  input.event('throttle',throttle,1);input.event('steering',steer,1);input.event('brake',brake,1);input.event('parkingbrake',parking,1)
  local ws=up(sounds.updateGFX,'wheelsSounds') or {}
  local data={}
  for id,w in pairs(wheels.wheels) do
    local s=ws[id] or {};local skid=s.rigidSkid or {};local roll=s.rigidRoll or {}
    data[#data+1]={name=w.name,side=w.lastSideSlip,slip=w.lastSlip,load=w.downForceRaw,coef=w.tireSoundVolumeCoef,
      skid=skid.lastVol or 0,roll=roll.lastVol or 0,material=w.contactMaterialID1,otherMaterial=w.contactMaterialID2,
      flat=w.isTireDeflated==true,broken=w.isBroken==true,friction=(v.data.wheels[id] or {}).frictionCoefMiddle}
  end
  local feedback=rawget(_G,'automaticTyresFeedback')
  samples[#samples+1]={t=t,phase=phase,speed=speed,steer=steer,throttle=throttle,brake=brake,
    beta=math.atan2(obj:getVelocity():dot(obj:getDirectionVector():cross(obj:getDirectionVectorUp())),obj:getVelocity():dot(obj:getDirectionVector()))*180/math.pi,
    wheels=data,feedback=feedback and feedback.getDiagnostics(),grip=automaticTyresGrip and automaticTyresGrip.getDiagnostics(),reduxLoaded=luukstyrethermalsandwear~=nil}
end
function M.status() return {active=active,t=t,count=#samples} end
function M.result() return {samples=samples,parts=v.data.activeParts} end
M.onReset=function() active=false;t=0;samples={} end
return M
