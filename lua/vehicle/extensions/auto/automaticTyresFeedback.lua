-- Enhance only the existing spatial rigid-skid events. Wheel/contact physics and
-- native rolling, loose-surface, kick-up and flat-tyre sounds are never written.
local M = {}
local records, soundTable, soundFunction = {}, nil, nil
local bridgeReady, warned, retryClock = false, false, 0
local abs, min, max, exp = math.abs, math.min, math.max, math.exp
local function finite(x) return type(x)=='number' and x==x and abs(x)<math.huge end
local function clamp(x) return max(0,min(1,x)) end
local function smooth(x) x=clamp(x);return x*x*(3-2*x) end
local function detach(r)
  r.enabled=false
  -- Restore only our own table entry; leave a later owner's method intact.
  if r.clip.setVolumePitch==r.wrapper then
    r.clip.setVolumePitch=r.rawMethod
    if r.pitch~=nil and finite(r.nativeVolume) then r.original(r.clip,r.nativeVolume,r.pitch,r.color,r.texture) end
  end
end
local function restore()
  for _,r in pairs(records) do detach(r) end
  records={};soundTable=nil;soundFunction=nil;bridgeReady=false;retryClock=0
end
local function discover()
  soundTable=nil;bridgeReady=false
  local fn=sounds and sounds.updateGFX
  if type(fn)~='function' or not debug or type(debug.getupvalue)~='function' then return end
  -- Read the known 0.39 sound-object interface; never replace a game upvalue.
  for i=1,64 do
    local name,value=debug.getupvalue(fn,i)
    if not name then break end
    if name=='wheelsSounds' then
      if type(value)=='table' then soundTable=value;soundFunction=fn;bridgeReady=true end
      return
    end
  end
end
local function attach(id,w,clip)
  if type(clip)~='table' or clip.obj==nil or type(clip.setVolumePitch)~='function' then return nil end
  local r={wheel=w,clip=clip,rawMethod=rawget(clip,'setVolumePitch'),original=clip.setVolumePitch,
    enabled=true,active=false,floor=0,gain=1,nativeVolume=0,outputVolume=0,angle=0}
  r.wrapper=function(self,volume,pitch,color,texture)
    r.pitch=pitch;r.color=color;r.texture=texture
    if not r.enabled or not r.active or not finite(volume) or self~=r.clip then
      r.nativeVolume=volume;r.outputVolume=volume
      return r.original(self,volume,pitch,color,texture)
    end
    -- Leave already loud native events intact; raise only the existing skid cue.
    local output=max(volume, min(max(0,volume)*r.gain,.8), r.floor)
    r.nativeVolume=volume;r.outputVolume=output
    return r.original(self,output,pitch,color,texture)
  end
  clip.setVolumePitch=r.wrapper
  records[id]=r
  return r
end
local function updateGFX(dt)
  if not finite(dt) or dt<=0 then return end
  if not wheels or not wheels.wheels then restore();return end
  retryClock=retryClock+dt
  if not soundTable or not sounds or soundFunction~=sounds.updateGFX or retryClock>=1 then
    retryClock=0;discover()
  end
  if not bridgeReady then
    for _,r in pairs(records) do detach(r) end
    records={}
    if not warned and log then log('W','automaticTyresFeedback','Skid audio interface unavailable; retaining native audio.');warned=true end
    return
  end
  local groundSpeed=obj and obj:getGroundSpeed() or 0
  local speed=finite(groundSpeed) and abs(groundSpeed) or 0
  -- Clear removed/replaced wheels and old clips, including reset/reconfiguration.
  for id,r in pairs(records) do
    local w=wheels.wheels[id];local s=soundTable[id]
    if w~=r.wheel or not s or s.rigidSkid~=r.clip then detach(r);records[id]=nil end
  end
  for id,w in pairs(wheels.wheels) do
    local s=soundTable[id]
    local r=records[id]
    if not r and w.hasTire and s then r=attach(id,w,s.rigidSkid) end
    if r then
      local load=finite(w.downForceRaw) and max(0,w.downForceRaw) or 0
      local side=finite(w.lastSideSlip) and abs(w.lastSideSlip) or 0
      local slip=finite(w.lastSlip) and abs(w.lastSlip) or 0
      local mat,other=w.contactMaterialID1,w.contactMaterialID2
      if mat==4 then mat,other=other,mat end
      local road=mat==10 or mat==29 or mat==30 or mat==11
      local coefficient=finite(w.tireSoundVolumeCoef) and w.tireSoundVolumeCoef or 0
      local submerged=obj and type(obj.inWater)=='function' and w.node1 and obj:inWater(w.node1)
      r.active=w.hasTire and coefficient>0 and load>100 and speed>3 and road and other==4
        and w.contactDepth==0 and not submerged and not w.isTireDeflated and not w.isPunctured and not w.isBroken
      r.angle=math.atan(side/max(speed,3))*180/math.pi
      if r.active then
        -- A slip-derived audio cue, not an estimate of the force-curve peak.
        local lateral=smooth((r.angle-1)/7)*smooth((side-.15)/.8)
        local strength=max(lateral,smooth((slip-.5)/5))
        local contact=smooth((load-100)/700)*smooth((speed-3)/5)
        local floorTarget=min(.18,.16*lateral*contact*coefficient*(mat==11 and .45 or 1))
        local gainTarget=1+.5*strength*contact
        local step=min(dt,.1)
        local tau=floorTarget>r.floor and .06 or .16
        r.floor=r.floor+(floorTarget-r.floor)*(1-exp(-step/tau))
        r.gain=r.gain+(gainTarget-r.gain)*(1-exp(-step/.08))
      else
        r.floor=0;r.gain=1
      end
    end
  end
end
M.updateGFX=updateGFX
M.onReset=restore
M.onExtensionUnloaded=restore
M.getDiagnostics=function()
  local data={}
  for id,r in pairs(records) do
    data[id]={name=r.wheel.name,active=r.active==true,angle=r.angle,floor=r.floor,gain=r.gain,
      nativeVolume=r.nativeVolume,outputVolume=r.outputVolume,hookOwned=r.clip.setVolumePitch==r.wrapper}
  end
  return {bridgeReady=bridgeReady,wheels=data}
end
return M
