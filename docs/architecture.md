# Architecture contract: initial draft

Status: **planned architecture, 19 November 2026**. This document records the
agreed direction and the decisions still needed before implementing the cores.
The current RTL remains the Tiny Tapeout adder baseline. It implements none of
the engines, loader, protocol firmware or diagnostic features described here.
Passing the baseline flow does not establish this architecture's feasibility.

## Purpose and agreed structure

Build a protocol emulator whose pin behavior is controlled by reloadable
firmware. Initial examples cover UART, SPI, I2C and Modbus RTU. The intended
advantage is useful concurrent operation with bounded recovery and inspectable
fault evidence. Core count alone is not a performance or novelty result.

| Element | Agreed design requirement |
| --- | --- |
| Engines | Two instances of one reusable core design, with independent PCs, registers, timers and working state. Both use a common system clock. |
| Program access | Private, independently writable program banks with independent fetch access sufficient for the documented instruction timing. No hidden shared-memory stall may invalidate that timing. |
| Host interface | SPI loading/control with explicit core selection. Program writes are allowed only to the selected stopped core; prohibited writes are rejected. The loader is distinct from firmware SPI emulation. |
| Coordination | Two directional mailboxes/FIFOs, independent run/stop control, a simultaneous-start operation and a shared timestamp. |
| Pin ownership | One engine owns each driven output. Both may observe inputs. Ownership changes require the affected engines to be stopped; conflicts are rejected. |
| I2C pins | Open-drain behavior through output enables, with external pull-ups. The design must never actively drive the bus high. |
| Diagnostics | Per-core wait and failure logic, plus an independent two-signal timing monitor with its own failure record. |

The timing-isolation requirement applies to independent programs using private
state and disjoint driven pins, under a defined host-access policy. Starting,
stopping or stalling the peer must not change scheduled pin transitions. Shared
mailbox interactions have their own explicitly documented timing. This remains
a requirement to verify, not a demonstrated property.

## Reset, loading and restart

`rst_n` must establish a known control state and safe pin behavior without
assuming initialized flip-flops or memory. Reset invalidates loaded-program
status and stops execution. Starting an unloaded core must not execute stale
memory or drive pins unexpectedly.

After power loss or deselection/reselection, the host must reset/reinitialize
the design, configure ownership and reload both images before starting them.
Ordinary stop/start behavior and program-valid transitions need a precise host
contract. Reset, stop, timeout recovery and fatal-fault output behavior must be
specified separately. Tests must cover a running peer during permitted host
access and reject programming attempts against an active core.

## Four priority features

**F1: native event-or-timeout.** A wait resolves to EVENT or TIMEOUT for a
selected pin condition or supported FIFO/mailbox-ready condition. Firmware
chooses the recovery path. One core's wait must not stall its peer. Define
sampling, deadline ties, already-satisfied events, wrap and result-to-branch
latency before implementing the instruction. Backpressure must not introduce
an indefinite stall that defeats a promised bound.

**F2: coherent first-failure records.** Each core and the monitor have separate
records. Capture cause/source, relevant execution context, timestamp, pin levels
and FIFO occupancy on a defined clock. Monitor records also identify the rule
and measured interval. Freeze the first record until explicit acknowledgment;
clearing one source must not clear another. Same-source cause priority,
acknowledgment/capture races and wrap behavior remain to be specified.

**F3: independent two-signal timing monitor.** Observe selected synchronized
signals while the engines execute. Planned rules cover pulse widths,
cross-signal timing windows and missing events. Define arming, phase exclusions,
boundaries, latency and observable pulse limits. The monitor must distinguish
I2C START/STOP from data-phase checks. It is not an analog measurement tool or
a complete protocol-compliance checker.

**F4: stateful I2C sensor/fault profile.** Firmware on either engine implements
a register pointer, readable data and writable configuration. Host-loaded
settings control NACK-first-N and bounded clock stretching. Define qualifying
accesses, counter resets and state across partial transactions, repeated START,
STOP and reset. Profile changes must not require changing RTL.

## Decisions still open

No instruction encoding, datapath width or storage capacity is frozen by this
document. Resolve the following from models and implementation evidence:

- Opcode set, instruction/register/address widths, instruction-cycle semantics
  and illegal-instruction behavior, including arithmetic needed for CRC/parsing.
- Program/data capacities and whether storage uses flip-flops or CMOS5L SRAM
  macros; actual ports, read latency, power connections and physical views.
- Mailbox/FIFO widths and depths, timer/timestamp widths, monitor rule count,
  snapshot layout, priority rules and maximum bounded-wait durations.
- Host command encodings, register map, allowed concurrent reads, program-valid
  rules, synchronization latency and the complete pin map.
- Supported system clock, protocol rates and timing tolerance. Planning targets
  become supported specifications only after cycle budgets and physical checks.

Memory-bank names do not prove independent access. A Verilog array does not
prove SRAM inference. The complete design must fit and route within the 8x4
CMOS5L boundary using the real memories and constraints.

## Acceptance experiments

1. Load different images through real host pins; exercise fetch, branches,
   working-state access and GPIO. Check unloaded start, invalid selection,
   reset, lost-memory/reload and prohibited active-core writes.
2. Run each disjoint workload alone and concurrently. Compare scheduled edges,
   throughput and latency while the peer runs, waits, stops or reloads.
3. Demonstrate full-duplex UART with one engine transmitting and the other
   receiving against independent external models; inject errors and recover.
4. Demonstrate the I2C fault fixture: one engine emulates the sensor while the
   other observes the controller's UART recovery report. Correlate both with
   monitor records and the shared timestamp.
5. Test wait and monitor boundaries, absent events and counter wrap. Inject
   adjacent/simultaneous failures and delay host reads; prove record stability
   and supported safety properties under explicit assumptions.
6. Compare one-core, dual-core and diagnostics-inclusive implementations with
   identical footprint, flow and clock constraints. Inspect retained hardware,
   real memory placement, routing and extracted timing; account for missing
   logic before making a feasibility decision.

## Next decision sequence

First write cycle-level semantics and a provisional host/pin map. Implement an
executable model and minimal assembler, then model representative UART, I2C and
Modbus work to estimate instruction/data needs. Select candidate storage from
those measurements and available memory views; feed its latency back into the
ISA. Only then build the loader/core feasibility skeleton and run the matched
physical comparisons. Freeze numeric contracts after reviewing those results.

Follow the [development checklist](development.md) and attach source revisions,
assumptions and evidence to every claimed result.
