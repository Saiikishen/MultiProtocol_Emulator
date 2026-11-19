# MultiProtocol Emulator

[![GDS](https://github.com/Saiikishen/MultiProtocol_Emulator/actions/workflows/gds.yaml/badge.svg)](https://github.com/Saiikishen/MultiProtocol_Emulator/actions/workflows/gds.yaml)
[![Tests](https://github.com/Saiikishen/MultiProtocol_Emulator/actions/workflows/test.yaml/badge.svg)](https://github.com/Saiikishen/MultiProtocol_Emulator/actions/workflows/test.yaml)
[![Docs](https://github.com/Saiikishen/MultiProtocol_Emulator/actions/workflows/docs.yaml/badge.svg)](https://github.com/Saiikishen/MultiProtocol_Emulator/actions/workflows/docs.yaml)

A programmable dual-core protocol emulator for the Jane Street ASIC competition,
targeting Tiny Tapeout's **IHP CMOS5L, 8x4-tile** allocation.

## Current stage

Development started on **19 November 2026**. The current RTL is the unchanged Tiny Tapeout combinational adder,
used to validate the toolchain. **The emulator cores and protocol firmware are
not implemented yet.** Local simulation/lint/structural checks and cloud RTL/docs
validation have passed. The first 8x4 physical workflow has been launched;
GDS/precheck/gate-level acceptance is still pending.

Only this repository's own Actions runs establish its validation status.
Results from the deleted repository are historical and are not current evidence.
See [the baseline manifest](reports/baseline_manifest.json) and
[the development checklist](docs/development.md). The
[architecture contract](docs/architecture.md) records agreed behavior and open
decisions for the next development stage.

## Planned architecture

- Two identical programmable engines with private program/working state,
  cycle-defined I/O and static output-pin ownership.
- A host SPI loader, stopped-core programming, mailboxes and a shared timestamp.
- Firmware examples for UART, SPI, I2C and Modbus RTU.
- Bounded event waits, first-failure records, an independent two-signal timing
  monitor and a stateful I2C sensor/fault profile.

These are planned features. Memory capacity, protocol rates and physical
feasibility must be measured before they become supported claims.

## Local validation

Use Ubuntu/WSL with Icarus Verilog, Verilator, Yosys, Make and Python installed.
Keep the Python environment in a Linux path without spaces:

```sh
python3 -m venv "$HOME/.venvs/multiprotocol-emulator"
"$HOME/.venvs/multiprotocol-emulator/bin/python" -m pip install -r test/requirements.txt
bash tools/run_baseline.sh
```

The helper runs the unchanged cocotb example, checks its result, lints the RTL
and runs a technology-independent structural check. Outputs are saved under
`reports/local/` and are not committed. Set `ASIC_VENV` to use another environment.

The GitHub `gds` workflow separately runs physical implementation, Tiny Tapeout
precheck and gate-level simulation. It pins the GDS action, support tools and
LibreLane versions. The layout viewer is optional and requires GitHub Pages
plus the repository variable `ENABLE_LAYOUT_VIEWER=true`.

The adder has no sequential clock path. Passing its physical checks does not
demonstrate 50 MHz core timing, SRAM integration or dual-core feasibility.

## Summarize a physical baseline

Download all artifacts from one completed GDS workflow run into a new directory.
Use that run's full source SHA and URL:

```sh
gh run download RUN_ID --repo Saiikishen/MultiProtocol_Emulator --dir reports/local/cloud/8x4
python tools/summarize_baseline.py reports/local/cloud/8x4 --expected-sha FULL_SHA --run-url RUN_URL
```

The tool rejects mismatched provenance, missing/failed test reports and missing
or nonzero required physical-error metrics. It writes
`reports/baseline_results_8x4.json`, keeping filler area separate from logic.
Do not mix artifacts from different runs in the same directory.

## Source attribution

This project incorporates the Tiny Tapeout IHP Verilog template. The original
Apache-2.0 [license](LICENSE), source notices and [attribution](ATTRIBUTION.md)
are retained. The fresh Git history does not include upstream commit ancestry;
it does not claim the template as original work.

AI-assisted setup and documentation are checked through explicit source review
and test results. Later implementation and verification write-ups will document
how AI was used and what independent checks were performed.

## References

- [Competition and FAQ](https://blog.janestreet.com/protocol-emulator-asic-competition/#faq)
- [Tiny Tapeout IHP template](https://github.com/TinyTapeout/ttihp-verilog-template)
- [Tiny Tapeout documentation](https://tinytapeout.com/)
- [Baseline datasheet](docs/info.md)
