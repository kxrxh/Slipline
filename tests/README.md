# Grip lifecycle checks

Install `lupa==2.8`, then run `python tests/test_native_grip.py` from the source checkout. This uses LuaJIT and original mock fixtures; it does not require BeamNG files.

Physics-object access or an extension-order change fails the fixture. It checks native and Redux readings, a replaced Redux grip table, an unknown Redux interface, removal, reset, unload and diagnostic snapshot isolation. These checks establish read-only behaviour; visible driving tests provide separate handling evidence.
