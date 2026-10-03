"""Regression checks for bounded grip and reversible native audio coefficients."""
from pathlib import Path
import math
import random
import unittest
from lupa.luajit21 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]

class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)

    def module(self, path):
        return self.lua.execute((ROOT / path).read_text(encoding='utf-8'))

    def test_grip_is_finite_and_bounded_across_driving_inputs(self):
        grip = self.module('lua/common/autotyres/grip.lua')
        rng = random.Random(22)
        states = [self.lua.table() for _ in range(4)]
        for _ in range(10000):
            factor = grip.step(rng.choice(states), rng.uniform(.001, .25), rng.uniform(-100, 100), rng.uniform(-40, 40), rng.uniform(-150, 150), rng.uniform(.03, .25), rng.random(), rng.uniform(0, 18000))
            self.assertTrue(math.isfinite(factor))
            self.assertGreaterEqual(factor, .92)
            self.assertLessEqual(factor, 1)
        stationary = self.lua.table()
        for _ in range(120):
            factor = grip.step(stationary, 1/60, 0, 0, 0, .1, .5, 3000)
        self.assertAlmostEqual(factor, .98)
        for bad in (float('nan'), float('inf'), -1, 0):
            self.assertEqual(grip.step(stationary, bad, 0, 0, 0, .1, .5, 3000), factor)
        untouched = self.lua.table()
        grip.step(states[0], 1/60, 10, 4, 30, .1, .5, 3000)
        self.assertIsNone(untouched.memory)

    def test_audio_gain_handles_rest_damage_external_changes_and_unload(self):
        self.lua.execute('wheels={wheels={}}')
        feedback = self.module('lua/vehicle/extensions/auto/automaticTyresFeedback.lua')
        wheel = self.lua.table_from(dict(hasTire=True, tireSoundVolumeCoef=1, lastSlip=0, lastSideSlip=0, angularVelocity=0, radius=.3, downForceRaw=3000, name='FL'))
        self.lua.globals().wheels.wheels[0] = wheel
        def step():
            for _ in range(120):
                feedback.updateGFX(1/60)
        step()
        self.assertEqual(wheel.tireSoundVolumeCoef, 1)
        wheel.angularVelocity, wheel.lastSlip, wheel.lastSideSlip = 30, 2, 1
        step()
        self.assertGreater(wheel.tireSoundVolumeCoef, 1.79)
        self.assertLessEqual(wheel.tireSoundVolumeCoef, 1.8)
        wheel.downForceRaw = 0
        step()
        self.assertAlmostEqual(wheel.tireSoundVolumeCoef, 1)
        wheel.downForceRaw, wheel.isTireDeflated = 3000, True
        step()
        self.assertAlmostEqual(wheel.tireSoundVolumeCoef, 1)
        wheel.isTireDeflated, wheel.tireSoundVolumeCoef = False, 2
        step()
        self.assertGreater(wheel.tireSoundVolumeCoef, 3.59)
        self.assertLessEqual(wheel.tireSoundVolumeCoef, 3.6)
        feedback.onExtensionUnloaded()
        self.assertEqual(wheel.tireSoundVolumeCoef, 2)
        wheel.tireSoundVolumeCoef = 0
        step()
        self.assertEqual(wheel.tireSoundVolumeCoef, 0)
        feedback.onReset()
        self.assertEqual(wheel.tireSoundVolumeCoef, 0)

if __name__ == '__main__':
    unittest.main()
