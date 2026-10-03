local M = {}
local model = require('autotyres/grip')
local states, factors, applied = {}, {}, {}
local thermalOwner, thermalCalculator, thermalTableIndex
local bridgeFailed, warned = false, false
local function finite(x) return type(x) == 'number' and x == x and math.abs(x) < math.huge end
local function findUpvalue(func, target)
  for i=1, 64 do
    local name, value = debug.getupvalue(func, i)
    if not name then break end
    if name == target then return i, value end
  end
end
local function attachThermals()
  local ttw = rawget(_G, 'luukstyrethermalsandwear')
  if not ttw or type(ttw.updateGFX) ~= 'function' then
    thermalOwner, thermalCalculator, thermalTableIndex = nil, nil, nil
    bridgeFailed = false
    return false
  end
  if thermalOwner == ttw.updateGFX then return true end
  local index, original = findUpvalue(ttw.updateGFX, 'CalculateTyreGrip')
  if not index or type(original) ~= 'function' then
    bridgeFailed = true
    if not warned then log('W', 'automaticTyresGrip', 'Unknown TTW interface: grip refinement paused to preserve thermals'); warned = true end
    return true
  end
  local tableIndex, gripTable = findUpvalue(original, 'tyreGripTable')
  if not tableIndex or type(gripTable) ~= 'table' then
    bridgeFailed = true
    if not warned then log('W','automaticTyresGrip','Unknown TTW grip table: refinement paused'); warned=true end
    return true
  end
  thermalOwner, thermalCalculator, thermalTableIndex = ttw.updateGFX, original, tableIndex
  -- Public dependency refresh ensures TTW updates its base grip first.
  -- Only read its computed grip; never alter another module's local state.
  M.dependencies = {'luukstyrethermalsandwear'}
  extensions.refresh('automaticTyresGrip')
  bridgeFailed = false
  log('I', 'automaticTyresGrip', 'TTW bridge active: temperature/wear grip multiplied by transient response')
  return true
end
local function reset() states, factors, applied = {}, {}, {} end
local function updateGFX(dt)
  if not finite(dt) or dt <= 0 or not wheels or not wheels.wheelRotators then return end
  local thermals = attachThermals()
  if bridgeFailed then return end
  -- A replacement GGT with an actual frame hook must not compete for friction.
  local ggt = rawget(_G, 'testMod')
  if ggt and type(ggt.updateGFX) == 'function' then
    if not warned then log('W','automaticTyresGrip','Another GGT frame hook is active: grip refinement paused'); warned = true end
    return
  end
  local up, forward = obj:getDirectionVectorUp(), obj:getDirectionVector()
  for id, wd in pairs(wheels.wheelRotators) do
    if type(wd) == 'table' and wd.wheelSection == 'pressureWheels' and finite(wd.radius) and finite(wd.hubRadius)
        and wd.radius > wd.hubRadius and wd.hasTire ~= false and wd.node1 and wd.node2 then
      local axis = obj:getNodePosition(wd.node2) - obj:getNodePosition(wd.node1)
      local direction = axis:cross(up)
      if direction:squaredLength() > 1e-10 then
        direction:normalize()
        if direction:dot(forward) < 0 then direction = -direction end
        local lateralDirection = direction:cross(up)
        local velocity = (obj:getNodeVelocityVector(wd.node1) + obj:getNodeVelocityVector(wd.node2)) * 0.5
        local state = states[id]
        if not state then state={}; states[id]=state end
        local factor = model.step(state, dt, velocity:dot(direction), velocity:dot(lateralDirection),
            (wd.angularVelocity or 0)*wd.radius, wd.radius-wd.hubRadius,
            wd.softnessCoef or 0.6, wd.downForceRaw or 0)
        factors[id] = factor
        local thermalBase
        if thermals then
          local _, gripTable = debug.getupvalue(thermalCalculator, thermalTableIndex)
          thermalBase = type(gripTable)=='table' and gripTable[id]
        end
        if not thermals or finite(thermalBase) then
          local w = obj:getWheel(id)
          if w then
            -- Preserve the vehicle's configured thermal curve when applying
            -- the standalone multiplier; do not replace it with a flat curve.
            local original = v.data.wheels[id] or {}
            if thermals then
              local combined = thermalBase * factor
              w:setFrictionThermalSensitivity(-300,1e7,1e-10,1e-10,10,combined,combined,combined)
              applied[id] = {base=thermalBase, combined=combined}
            else
              w:setFrictionThermalSensitivity(original.frictionLowTemp or -300,
                  original.frictionHighTemp or 1e7, original.frictionLowSlope or 1e-10,
                  original.frictionHighSlope or 1e-10, original.frictionSlopeSmoothCoef or 10,
                  (original.frictionCoefLow or 1)*factor, (original.frictionCoefMiddle or 1)*factor,
                  (original.frictionCoefHigh or 1)*factor)
              applied[id] = {base=original.frictionCoefMiddle or 1, combined=(original.frictionCoefMiddle or 1)*factor}
            end
          end
        end
      end
    end
  end
end
M.updateGFX = updateGFX
M.getDiagnostics = function()
  return {factors=deepcopy(factors), applied=deepcopy(applied), thermalsBridge=thermalOwner ~= nil, bridgeFailed=bridgeFailed}
end
M.onReset = reset
M.onExtensionLoaded = function() reset(); log('I','automaticTyresGrip','Automatic transient grip active (0.2.1)') end
M.onExtensionUnloaded = function()
  for id, data in pairs(applied) do
    local w = obj:getWheel(id)
    if w then
      local original = v.data.wheels[id] or {}
      if thermalOwner then
        w:setFrictionThermalSensitivity(-300,1e7,1e-10,1e-10,10,data.base,data.base,data.base)
      else
        w:setFrictionThermalSensitivity(original.frictionLowTemp or -300, original.frictionHighTemp or 1e7,
            original.frictionLowSlope or 1e-10, original.frictionHighSlope or 1e-10,
            original.frictionSlopeSmoothCoef or 10, original.frictionCoefLow or 1,
            original.frictionCoefMiddle or 1, original.frictionCoefHigh or 1)
      end
    end
  end
end
return M
