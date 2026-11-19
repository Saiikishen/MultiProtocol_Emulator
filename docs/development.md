# Development checklist

Status at repository initialization: 19 November 2026.

## 1. Establish the 8x4 toolchain baseline

- [x] Run the unchanged adder test locally; save simulator/tool versions.
- [x] Pass Verilator lint and the Yosys structural check.
- [x] Pass the new repository's RTL test and documentation workflows.
- [ ] Complete 8x4 GDS generation with the pinned CMOS5L flow.
- [ ] Pass Tiny Tapeout precheck and gate-level simulation on that build.
- [ ] Save the run ID, source SHA, artifacts, warnings and physical results.

A passing combinational example validates the flow, not the proposed emulator.
Do not infer a core frequency or SRAM feasibility from this result.

The completed checks used source `6327d96528f02c483ecdad33ee30d942260b8e52`.
Cloud evidence: [RTL test](https://github.com/Saiikishen/MultiProtocol_Emulator/actions/runs/44458164499)
and [documentation](https://github.com/Saiikishen/MultiProtocol_Emulator/actions/runs/44458164455).
The [physical workflow](https://github.com/Saiikishen/MultiProtocol_Emulator/actions/runs/44458164500)
was still running when this progress record was written. Its downstream precheck
and gate-level results are pending. Check the live run before updating this record.

## 2. Define the programmable engine before RTL expansion

- Write instruction encodings and cycle-by-cycle behavior, including memory
  read latency, arithmetic, shifts/XOR, branches, pin reads and writes.
- Define reset/program-valid behavior and host load/start/stop/readback commands.
- Define output ownership, open-drain behavior and synchronization assumptions.
- Model small UART, I2C and Modbus workloads to estimate instruction/data storage.
- Choose memory views, capacities and ports from actual available CMOS5L macros
  or measured flip-flop implementations; do not assume automatic SRAM inference.

Deliverable: architecture/ISA v0.1, pin/register maps, executable model and a
minimal assembler, with explicit unresolved choices.

## 3. Build and measure the feasibility skeleton

- Implement one parameterized core, then instantiate two copies with private
  state, a real loader and observable outputs.
- Load different programs through the host pins; exercise branch, memory and I/O.
- Compare one core, two cores and diagnostics-inclusive builds using identical
  8x4 boundaries, flow versions and clock constraints.
- Inspect retained netlist state, memory views, placement, routing and timing.
- Record missing logic and its budget before deciding whether the complete
  dual-core architecture remains feasible.

Only after this gate should protocol and diagnostic implementation expand.

## Evidence rules

Each result identifies its source SHA, parameters, tool versions and exact
commands. Keep simulation, formal, FPGA and silicon results distinct. The final
submission includes a verification write-up describing AI use and independent
checks. Do not mark checklist items complete based only on plans or old runs.
