#!/usr/bin/env bash
# Run from Ubuntu/WSL. Keep the upstream example RTL and test unchanged.
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_dir"
venv_dir="${ASIC_VENV:-$HOME/.venvs/multiprotocol-emulator}"
if [[ ! -x "$venv_dir/bin/python" ]]; then
    printf 'Missing environment. Run: python3 -m venv "$HOME/.venvs/multiprotocol-emulator"\n' >&2
    exit 1
fi
export PATH="$venv_dir/bin:$PATH"
mkdir -p reports/local
{
    printf 'Source revision: '
    git rev-parse HEAD
    git status --short
    python --version
    python -m pip freeze
    iverilog -V 2>&1
    verilator --version
    yosys -V
} > reports/local/environment.txt

# The upstream Makefile uses unescaped absolute paths. WSL workspace paths
# containing spaces require relative source paths. Keep that override local.
(
    cd test
    make clean
    make PWD=. SRC_DIR=../src
    python -m cocotb_tools.check_results results.xml
) 2>&1 | tee reports/local/rtl-test.log
cp test/results.xml reports/local/results.xml

verilator --lint-only --top-module tt_um_example src/project.v \
    2>&1 | tee reports/local/lint.log
yosys -p 'read_verilog src/project.v; hierarchy -check -top tt_um_example; proc; opt; check -assert; stat' \
    2>&1 | tee reports/local/structural-check.log
printf '\nBaseline RTL checks passed. Physical implementation is a separate required gate.\n'
