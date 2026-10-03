-- Original conservative transient grip model; no GGT code is included.
local M = {}
local min, max, abs, exp, sqrt = math.min, math.max, math.abs, math.exp, math.sqrt
local function clamp(x, lo, hi) return min(hi, max(lo, x)) end
local function finite(x) return type(x) == 'number' and x == x and abs(x) < math.huge end
function M.step(state, dt, longitudinal, lateral, rimSpeed, sidewall, softness, load)
  if not (finite(dt) and dt > 0 and finite(longitudinal) and finite(lateral)
      and finite(rimSpeed) and finite(sidewall) and finite(softness) and finite(load)) then
    return state.factor or 0.98
  end
  dt = min(dt, 0.1)
  local speed = sqrt(longitudinal*longitudinal + lateral*lateral)
  local slip = abs(abs(rimSpeed) - abs(longitudinal)) / max(abs(longitudinal), abs(rimSpeed), 3)
  local angle = math.atan2(abs(lateral), max(abs(longitudinal), 2))
  local peakAngle = clamp(0.075 + sidewall * 0.65, 0.10, 0.18)
  local demand = min(8, sqrt((angle / peakAngle)^2 + (slip / 0.16)^2))
  local tau = clamp(0.05 + sidewall * 0.45 + (1-clamp(softness, 0, 1))*0.03, 0.06, 0.18)
  state.memory = (state.memory or 0) + (demand - (state.memory or 0)) * (1-exp(-dt/tau))
  local transient = clamp(demand - state.memory, -1, 1)
  local recovery = clamp(-transient, 0, 1)
  local target = 0.98 + 0.02*clamp(transient, 0, 1) - 0.025*recovery
      - 0.035*clamp((state.memory-1.5)/3, 0, 1)
  -- Below walking speed and off the ground, ease back to the baseline.
  local activity = clamp((speed-0.5)/2.5, 0, 1) * clamp(load/150, 0, 1)
  target = 0.98 + (target-0.98)*activity
  state.factor = clamp((state.factor or 0.98) + (target-(state.factor or 0.98))*(1-exp(-dt/0.045)), 0.92, 1)
  return state.factor
end
return M
