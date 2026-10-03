"""Read-only grip lifecycle/Redux compatibility checks using LuaJIT via lupa."""
from pathlib import Path
from lupa.luajit21 import LuaRuntime

root = Path(__file__).resolve().parents[1]
lua = LuaRuntime()
lua.execute('''
function log(...) end
function deepcopy(t)
  if type(t)~='table' then return t end
  local r={};for k,v in pairs(t) do r[k]=deepcopy(v) end;return r
end
function equal(a,b)
  if type(a)~='table' or type(b)~='table' then return a==b end
  for k,x in pairs(a) do if not equal(x,b[k]) then return false end end
  for k in pairs(b) do if a[k]==nil then return false end end
  return true
end
-- Any attempt to own friction, wheel physics or extension ordering fails.
obj=setmetatable({}, {__index=function() error('Unexpected physics access') end})
extensions=setmetatable({}, {__index=function() error('Unexpected order change') end})
wheels={wheelRotators={[0]={wheelSection='pressureWheels',hasTire=true},
  [1]={wheelSection='pressureWheels',hasTire=false}}}
v={data={wheels={[0]={frictionCoefMiddle=0.87}}}}
originalWheels=deepcopy(wheels);originalVehicle=deepcopy(v)
''')
lua.globals().module_source = (root/'lua/vehicle/extensions/auto/automaticTyresGrip.lua').read_text()
lua.execute('''
M=assert(loadstring(module_source))();M.onExtensionLoaded();M.updateGFX(0.02)
local d=M.getDiagnostics()
assert(d.mode=='native' and d.factors[0]==1 and d.factors[1]==nil)
assert(d.applied[0].base==0.87 and d.applied[0].combined==0.87)
d.applied[0].base=99;assert(M.getDiagnostics().applied[0].base==0.87)
M.updateGFX(0/0);M.updateGFX(-1);M.updateGFX(0)
local tyreGripTable={[0]=0.73}
local function CalculateTyreGrip() return tyreGripTable end
luukstyrethermalsandwear={updateGFX=function() return CalculateTyreGrip() end}
M.updateGFX(0.02);d=M.getDiagnostics()
assert(d.thermalsBridge and not d.bridgeFailed and d.applied[0].combined==0.73)
tyreGripTable={[0]=0.61};M.updateGFX(0.02)
assert(M.getDiagnostics().applied[0].base==0.61)
-- A future unknown Redux interface must not fall back to a fictional base.
luukstyrethermalsandwear={updateGFX=function() end};M.updateGFX(0.02);d=M.getDiagnostics()
assert(d.bridgeFailed and not d.thermalsBridge and d.applied[0]==nil and d.factors[0]==1)
luukstyrethermalsandwear=nil;M.updateGFX(0.02)
assert(not M.getDiagnostics().bridgeFailed and M.getDiagnostics().applied[0].base==0.87)
assert(equal(originalWheels,wheels) and equal(originalVehicle,v))
wheels.wheelRotators={};M.updateGFX(0.02);assert(next(M.getDiagnostics().factors)==nil)
M.onReset();M.onExtensionUnloaded();assert(next(M.getDiagnostics().applied)==nil)
assert(equal(originalVehicle,v))
''')
print('PASS: no physics/order writes; native/Redux/unknown/reset/unload/snapshot isolation')
