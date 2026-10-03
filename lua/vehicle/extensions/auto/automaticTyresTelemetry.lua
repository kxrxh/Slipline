local M = {dependencies={'automaticTyresGrip'}}
local elapsed, lastPayload = 0, nil
local function finite(x) return type(x)=='number' and x==x and math.abs(x)<math.huge end
local function updateGFX(dt)
  if not finite(dt) or dt<=0 or not wheels or not wheels.wheelRotators then return end
  elapsed=elapsed+dt
  if elapsed<0.1 then return end
  elapsed=elapsed%0.1
  local grip=rawget(_G,'automaticTyresGrip')
  local diagnostic=grip and grip.getDiagnostics() or {factors={},applied={}}
  local data={}
  for id, wd in pairs(wheels.wheelRotators) do
    if wd.wheelSection=='pressureWheels' and wd.hasTire then
      local initial=v.data.wheels[id] or {}
      local pressure
      local group=wd.pressureGroup and v.data.pressureGroups and v.data.pressureGroups[wd.pressureGroup]
      if group then
        pressure=math.max(0,(obj:getGroupPressure(group)-obj:getEnvPressure())/6894.757293)
      end
      local applied=diagnostic.applied[id] or {}
      data[#data+1]={name=wd.name,pressurePsi=pressure,targetPressurePsi=initial.pressurePSI,
        rays=initial.numRays,gripFactor=diagnostic.factors[id],combinedGrip=applied.combined,
        baseGrip=applied.base,loadN=wd.downForceRaw,
        sideSlipMps=finite(wd.lastSideSlip) and math.abs(wd.lastSideSlip) or nil,
        deflated=wd.isTireDeflated or wd.isPunctured or wd.isBroken,
        refined=initial._automaticTyresPrepared==true}
    end
  end
  lastPayload={data=data,thermalsBridge=diagnostic.thermalsBridge==true,gripPaused=diagnostic.bridgeFailed==true}
  gui.send('AutomaticTyresTelemetry',lastPayload)
end
M.updateGFX=updateGFX
M.onReset=function() elapsed=0; lastPayload=nil end
M.getSnapshot=function() return lastPayload end
return M
