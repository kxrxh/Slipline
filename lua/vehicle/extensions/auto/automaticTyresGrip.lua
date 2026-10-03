-- Keep the legacy extension name for telemetry and existing integrations.
-- Grip is owned entirely by BeamNG or the installed thermal mod.
local M = {}
local factors, applied = {}, {}
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
    bridgeFailed, warned = false, false
    return
  end
  if thermalOwner == ttw.updateGFX then return end
  thermalOwner = ttw.updateGFX
  thermalCalculator, thermalTableIndex = nil, nil
  local _, calculator = findUpvalue(thermalOwner, 'CalculateTyreGrip')
  if type(calculator) == 'function' then
    local index, gripTable = findUpvalue(calculator, 'tyreGripTable')
    if index and type(gripTable) == 'table' then
      thermalCalculator, thermalTableIndex = calculator, index
    end
  end
  bridgeFailed = thermalCalculator == nil
  if bridgeFailed and not warned then
    log('W', 'automaticTyresGrip', 'Unknown TTW interface: base grip reading unavailable; tyre physics unchanged')
    warned = true
  end
end
local function reset()
  factors, applied = {}, {}
  thermalOwner, thermalCalculator, thermalTableIndex = nil, nil, nil
  bridgeFailed, warned = false, false
end
local function updateGFX(dt)
  if not finite(dt) or dt <= 0 or not wheels or not wheels.wheelRotators then return end
  attachThermals()
  local gripTable
  if thermalCalculator then
    local _, value = debug.getupvalue(thermalCalculator, thermalTableIndex)
    if type(value) == 'table' then gripTable = value end
  end
  -- Rebuild snapshots so removed or replaced wheels cannot retain stale values.
  factors, applied = {}, {}
  for id, wd in pairs(wheels.wheelRotators) do
    if type(wd) == 'table' and wd.wheelSection == 'pressureWheels' and wd.hasTire ~= false then
      factors[id] = 1
      local base
      if thermalOwner then
        base = gripTable and gripTable[id]
      else
        base = (v.data.wheels[id] or {}).frictionCoefMiddle or 1
      end
      if finite(base) then applied[id] = {base=base, combined=base} end
    end
  end
end
M.updateGFX = updateGFX
M.getDiagnostics = function()
  return {factors=deepcopy(factors), applied=deepcopy(applied), mode='native',
    thermalsBridge=thermalCalculator ~= nil, bridgeFailed=bridgeFailed}
end
M.onReset = reset
M.onExtensionLoaded = function()
  reset()
  log('I', 'automaticTyresGrip', 'Slipline 0.2.4: native grip preserved; grip telemetry is read-only')
end
M.onExtensionUnloaded = reset
return M
