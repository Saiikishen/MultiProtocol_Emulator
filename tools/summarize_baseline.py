"""Validate and summarize artifacts downloaded from one CMOS5L baseline run.

Download all artifacts with ``gh run download RUN_ID --dir ARTIFACTS``, then:
  python tools/summarize_baseline.py ARTIFACTS --expected-sha FULL_SHA --run-url URL

The output defaults to reports/baseline_results_8x4.json in this repository.
JUnit files must come from that same download; their format has no source SHA.
This script does not establish protocol functionality or sequential Fmax.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from urllib.parse import urlparse
import xml.etree.ElementTree as ET


REQUIRED_ZERO_METRICS = (
    "route__drc_errors",
    "magic__drc_error__count",
    "design__lvs_error__count",
    "route__antenna_violation__count",
)
SELECTED_METRICS = (
    "design__die__bbox", "design__die__area", "design__core__area",
    "design__instance__count__stdcell", "design__instance__area__stdcell",
    "design__instance__area__class:fill_cell", "design__instance__area__macros",
    "design__instance__utilization__stdcell", "timing__setup__ws",
    "timing__hold__ws", *REQUIRED_ZERO_METRICS,
)


def read_json(path):
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def numeric_metric(metrics, key):
    value = metrics.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Physical metric missing or non-numeric: {key}={value!r}")
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"Physical metric invalid: {key}={value!r}")
    return value


def junit(path):
    root = ET.parse(path).getroot()
    tag = lambda node: node.tag.rsplit("}", 1)[-1]
    if tag(root) not in ("testsuite", "testsuites"):
        raise ValueError(f"Unexpected JUnit root: {path}")
    nodes = list(root.iter())
    cases = [node for node in nodes if tag(node) == "testcase"]
    result = {
        "cases": len(cases),
        "failures": sum(tag(node) == "failure" for node in nodes),
        "errors": sum(tag(node) == "error" for node in nodes),
        "skipped": sum(tag(node) == "skipped" for node in nodes),
    }
    if not cases or any(result[key] for key in ("failures", "errors", "skipped")):
        raise ValueError(f"Incomplete or failing JUnit: {path}: {result}")
    # Some runners report failed/skipped tests only in summary attributes.
    for node in nodes:
        if tag(node) in ("testsuite", "testsuites"):
            for key in ("failures", "errors", "skipped", "disabled"):
                if key in node.attrib and int(node.attrib[key]) != 0:
                    raise ValueError(f"Nonzero JUnit {key}: {path}")
            if "tests" in node.attrib:
                actual = sum(tag(child) == "testcase" for child in node.iter())
                if int(node.attrib["tests"]) != actual:
                    raise ValueError(f"Incomplete JUnit case count: {path}")
        if tag(node) == "testcase" and node.get("status", "").lower() in (
            "skipped", "disabled", "notrun", "failed", "error"
        ):
            raise ValueError(f"Non-passing JUnit case status: {path}")
    return result


def summarize(args):
    if not re.fullmatch(r"[0-9a-fA-F]{40}", args.expected_sha):
        raise ValueError("--expected-sha must be a full 40-character commit SHA.")
    parsed = urlparse(args.run_url)
    if (parsed.scheme != "https" or parsed.netloc != "github.com"
            or not re.fullmatch(r"/[^/]+/[^/]+/actions/runs/[0-9]+", parsed.path)
            or parsed.query or parsed.fragment):
        raise ValueError("--run-url must be https://github.com/OWNER/REPO/actions/runs/ID.")
    expected_repo = args.run_url.split("/actions/runs/")[0]
    run = args.artifacts / "GDS_logs/runs/wokwi"
    states = list(run.glob("*-misc-reportmanufacturability/state_out.json"))
    if len(states) != 1:
        raise ValueError("Expected exactly one completed manufacturability state.")
    source = read_json(run / "final/commit_id.json")
    if source.get("commit", "").lower() != args.expected_sha.lower():
        raise ValueError(f"Artifact source SHA mismatch: {source.get('commit')!r}")
    if source.get("workflow_url") != args.run_url:
        raise ValueError(f"Artifact workflow URL mismatch: {source.get('workflow_url')!r}")
    if source.get("repo", "").rstrip("/").lower() != expected_repo.lower():
        raise ValueError(f"Artifact repository mismatch: {source.get('repo')!r}")

    # Read the built submission's metadata, not the mutable local info.yaml.
    metadata = (args.artifacts / "tt_submission/info.yaml").read_text(encoding="utf-8")
    tile_values = re.findall(r'''(?m)^  tiles:\s*["']?(\d+x\d+)["']?\s*(?:#.*)?$''', metadata)
    if tile_values != [args.footprint]:
        raise ValueError(f"Built submission footprint mismatch: {tile_values!r}")

    pdk = read_json(run / "pdk.json")
    if pdk.get("PDK") != "ihp-sg13cmos5l":
        raise ValueError(f"Unexpected baseline PDK: {pdk.get('PDK')!r}")
    metrics = read_json(states[0]).get("metrics")
    if not isinstance(metrics, dict):
        raise ValueError("Manufacturability state has no metrics object.")
    for key in REQUIRED_ZERO_METRICS:
        if numeric_metric(metrics, key) != 0:
            raise ValueError(f"Physical check failed: {key}={metrics[key]}")
    logic_area = numeric_metric(metrics, "design__instance__area__stdcell")
    filler_area = numeric_metric(metrics, "design__instance__area__class:fill_cell")
    macro_area = numeric_metric(metrics, "design__instance__area__macros")
    if logic_area == 0:
        raise ValueError("Baseline has zero standard-cell area.")

    precheck = junit(args.artifacts / "precheck_reports/results.xml")
    gatelevel = junit(args.artifacts / "gatelevel_test_results/results.xml")
    gds = run / "final/gds/tt_um_example.gds"
    if not gds.is_file() or gds.stat().st_size == 0:
        raise ValueError("Final baseline GDS is missing or empty.")
    warning_path = run / "warning.log"
    warnings = (list(dict.fromkeys(warning_path.read_text(encoding="utf-8").splitlines()))
                if warning_path.is_file() else ["warning.log was not present in the download."])
    return {
        "footprint": args.footprint,
        "design": "Unmodified combinational template adder; no emulator cores or SRAM",
        "expected_source_sha": args.expected_sha.lower(),
        "run_url": args.run_url,
        "source": source,
        "pdk": pdk,
        "precheck": precheck,
        "gatelevel": gatelevel,
        "area_breakdown_um2": {
            "logic_and_buffer_standard_cells": logic_area,
            "filler_cells": filler_area,
            "macros": macro_area,
        },
        "metrics": {key: metrics.get(key) for key in SELECTED_METRICS},
        "units": {"area": "um^2", "slack": "ns", "utilization": "fraction"},
        "gds_sha256": hashlib.sha256(gds.read_bytes()).hexdigest(),
        "warnings": warnings,
        "interpretation": [
            "Standard-cell logic/buffer cost is separate from filler and macro area.",
            "The combinational adder has no sequential clock path; no Fmax is claimed.",
            "A passing precheck includes its own checks; review the saved case list and warnings.",
            "This validates the baseline flow/footprint, not dual-core or SRAM feasibility.",
            "JUnit files carry no source SHA; download all artifacts from the specified single run.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifacts", type=Path)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--run-url", required=True)
    parser.add_argument("--footprint", choices=("1x1", "6x4", "8x4"), default="8x4")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        report = summarize(args)
        destination = args.output or (Path(__file__).resolve().parents[1] / "reports"
                                     / f"baseline_results_{args.footprint}.json")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    except (OSError, ValueError, TypeError, ET.ParseError) as exc:
        print(f"Baseline validation failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"output": str(destination), "source_sha": report["expected_source_sha"],
                      "run_url": report["run_url"], "precheck": report["precheck"],
                      "gatelevel": report["gatelevel"], "area_um2": report["area_breakdown_um2"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
