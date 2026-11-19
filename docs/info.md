<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

This is the unmodified CMOS5L template example used for our first toolchain
baseline. It adds ui_in and uio_in modulo 256 and drives the result on uo_out.
All bidirectional output enables are zero. It is not the dual-core emulator.

## How to test

Run the upstream cocotb test: drive 20 and 30, then check that the output is 50.
The project helper tools/run_baseline.sh runs that test, checks results.xml,
lints the example and performs a technology-independent structural check.
GDS, precheck and gate-level simulation are separate GitHub Actions gates.

## External hardware

None for simulation or physical-flow validation.
