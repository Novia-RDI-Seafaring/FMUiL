## Example 2: Lube oil cooling system
A lube oil cooling (LOC) system regulates the lubrication oil temperature at a constant setpoint at the engine inlet using a PI controller and a control valve. The lube oil cooler transfers heat from the lubrication oil to the cooling water circuit.

As with the water tank system, this model is divided into two parts: the physical system and the control system. Further details about the models and FMUs can be found [here](https://github.com/Novia-RDI-Seafaring/fmu-library/tree/main/models/loc).

This is already setup on the file `exp2_loc.yaml`, to run this simply just call:

```
uv run fmuil -d "examples\Lube oil cooling" run "exp2_loc.yaml"
```