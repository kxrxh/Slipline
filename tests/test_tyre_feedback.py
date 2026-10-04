"""Skid-event lifecycle, gating and progressive-response checks using LuaJIT via lupa."""
from pathlib import Path
from lupa.luajit21 import LuaRuntime
lua=LuaRuntime()
root=Path(__file__).resolve().parents[1]
lua.globals().source=(root/'lua/vehicle/extensions/auto/automaticTyresFeedback.lua').read_text()
lua.execute('''
local calls={}
function log(...) end
obj={getGroundSpeed=function() return 20 end,inWater=function() return false end}
local method=function(self,vol,pitch,col,tex) self.output=vol;self.pitch=pitch;self.col=col;self.tex=tex end
local clip=setmetatable({obj=1},{__index={setVolumePitch=method}})
local roll={setVolumePitch=method}
local wheelsSounds={[0]={rigidSkid=clip,rigidRoll=roll}}
sounds={updateGFX=function() return wheelsSounds end}
local wheel={hasTire=true,tireSoundVolumeCoef=1,lastSlip=0,lastSideSlip=0,
  downForceRaw=3000,contactMaterialID1=10,contactMaterialID2=4,contactDepth=0,node1=2,name='FL',frictionCoef=1}
wheels={wheels={[0]=wheel}}
local M=assert(loadstring(source))()
local function frame(n)
  for i=1,n or 120 do M.updateGFX(1/60);clip:setVolumePitch(.002,.23,.52,.025) end
end
frame();assert(clip.output==.002 and wheel.tireSoundVolumeCoef==1 and wheel.frictionCoef==1)
assert(roll.setVolumePitch==method)
wheel.lastSideSlip=.7;frame();local quiet=clip.output;assert(quiet>.002 and quiet<.05)
wheel.lastSideSlip=2;frame();local medium=clip.output;assert(medium>quiet and medium<.18)
wheel.lastSideSlip=5;frame();assert(clip.output>medium and clip.output<=.18)
assert(clip.pitch==.23 and clip.col==.52 and clip.tex==.025)
clip:setVolumePitch(1.2,.23,.52,.025);assert(clip.output==1.2)
wheel.angularVelocity=0;frame();assert(clip.output>.01) -- locked-wheel scrub uses road speed
wheel.downForceRaw=0;frame(1);assert(clip.output==.002)
wheel.downForceRaw=3000;wheel.isBroken=true;frame(1);assert(clip.output==.002)
wheel.isBroken=false;wheel.isTireDeflated=true;frame(1);assert(clip.output==.002)
wheel.isTireDeflated=false;wheel.tireSoundVolumeCoef=0;frame(1);assert(clip.output==.002)
wheel.tireSoundVolumeCoef=1;wheel.contactMaterialID1=19;frame(1);assert(clip.output==.002)
wheel.contactMaterialID1=10;wheel.contactDepth=.1;frame(1);assert(clip.output==.002)
wheel.contactDepth=0;obj.inWater=function() return true end;frame(1);assert(clip.output==.002)
obj.inWater=function() return false end;obj.getGroundSpeed=function() return 0 end;frame(1);assert(clip.output==.002)
obj.getGroundSpeed=function() return 20 end;frame();assert(clip.output>.01)
M.updateGFX(0/0);M.updateGFX(-1)
M.onReset();assert(rawget(clip,'setVolumePitch')==nil and clip.setVolumePitch==method and clip.output==.002)
frame();local wrapper=clip.setVolumePitch
local external=function(self,...) return wrapper(self,...) end
clip.setVolumePitch=external;M.onExtensionUnloaded();assert(clip.setVolumePitch==external)
clip:setVolumePitch(.002,.23,.52,.025);assert(clip.output==.002)
clip.setVolumePitch=nil;frame();wheels.wheels={};M.updateGFX(1/60);assert(rawget(clip,'setVolumePitch')==nil)
wheels.wheels={[0]=wheel};frame();sounds.updateGFX=function() end;M.updateGFX(1/60)
assert(rawget(clip,'setVolumePitch')==nil and not M.getDiagnostics().bridgeReady)
assert(wheel.tireSoundVolumeCoef==1 and wheel.frictionCoef==1 and roll.setVolumePitch==method)
''')
print('PASS: progressive skid cue; native parameters/rolling/physics unchanged; rest/airborne/flat/mute/loose/water; reset/unload/replacement/unknown interface')
