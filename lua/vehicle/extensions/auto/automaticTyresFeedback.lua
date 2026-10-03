-- Enhance native, spatial tyre sounds only while loaded tyres are slipping.
-- No new sound sources and no modifications to contact or thermal physics.
local M = {}
local records = {}
local function finite(x) return type(x)=='number' and x==x and math.abs(x)<math.huge end
local function clamp(x) return math.max(0,math.min(1,x)) end
local function restore()
  for _,r in pairs(records) do
    if r.wheel.tireSoundVolumeCoef==r.applied then r.wheel.tireSoundVolumeCoef=r.base end
  end
  records={}
end
local function updateGFX(dt)
  if not finite(dt) or dt<=0 or not wheels or not wheels.wheels then return end
  for id,w in pairs(wheels.wheels) do
    if w.hasTire and finite(w.tireSoundVolumeCoef) then
      local r=records[id]
      if not r or r.wheel~=w then r={wheel=w,base=w.tireSoundVolumeCoef,gain=1};records[id]=r end
      -- Respect another module's coefficient changes and intentionally muted tyres.
      if r.applied and w.tireSoundVolumeCoef~=r.applied then r.base=w.tireSoundVolumeCoef end
      local slip=finite(w.lastSlip) and math.abs(w.lastSlip) or 0
      local side=finite(w.lastSideSlip) and math.abs(w.lastSideSlip) or 0
      local speed=finite(w.angularVelocity) and finite(w.radius) and math.abs(w.angularVelocity*w.radius) or 0
      local load=finite(w.downForceRaw) and w.downForceRaw or 0
      local target=1
      if not w.isTireDeflated and not w.isPunctured and not w.isBroken then
        target=1+0.8*clamp(math.max(side,slip*0.5)/0.8)*clamp(speed/3)*clamp((load-100)/500)
      end
      r.gain=r.gain+(target-r.gain)*(1-math.exp(-math.min(dt,0.1)/0.08))
      r.applied=r.base*r.gain
      w.tireSoundVolumeCoef=r.applied
    end
  end
end
M.updateGFX=updateGFX
M.onReset=restore
M.onExtensionUnloaded=restore
M.getDiagnostics=function()
  local data={}
  for id,r in pairs(records) do data[id]={name=r.wheel.name,base=r.base,gain=r.gain,applied=r.applied} end
  return data
end
return M
