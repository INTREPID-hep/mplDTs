"""T-006: station build benchmark.

Baseline (2026-11-08, 2.7.0, WSL2, checkout, median of 3; the millisecond
cases move 50% between runs on WSL, so read them as an order of magnitude):
    import               0.3 s
    XML parse            0.3 s
    Station(-2, 1, 2)    ~3 ms
    Station(2, 14, 4)    ~2 ms
    Station(0, 1, 1)     ~2 ms
    model (build_station on a parsed source) 4-8 ms
Target after Phase 2 (< 20 ms per station): met with room to spare.

Historical baseline (2026-11-06, pre-refactor checkout): import + parse 3.4 s,
stations 1.00 / 0.71 / 0.87 s (installed 2.2.0b0: 1.25 / 2.26 / 1.66 s).

Usage:
    PYTHONPATH=/home/destrada/mplDTs python test/benchmarks/bench_station.py
    PYTHONPATH=/home/destrada/mplDTs python test/benchmarks/bench_station.py --json out.json
    PYTHONPATH=/home/destrada/mplDTs python test/benchmarks/bench_station.py --compare out.json
"""

import argparse
import json
import platform
import statistics
import sys
import time
from pathlib import Path

STATIONS = [(-2, 1, 2), (2, 14, 4), (0, 1, 1)]
REPRESENTATIVE = [(-2, 1, 1), (-1, 3, 2), (0, 5, 3), (1, 3, 4), (2, 14, 4), (0, 1, 1)]
REPEATS = 3


def _best(effort, repeats=REPEATS):
    """Median wall time of 'repeats' runs (seconds)."""
    times = []
    for _ in range(repeats):
        start = time.perf_counter()
        effort()
        times.append(time.perf_counter() - start)
    return statistics.median(times)


def measure(all_chambers=False):
    """Run every case; returns (metadata, {case: median seconds})."""
    start = time.perf_counter()
    import mpldts
    import mpldts.geometry as geometry
    from mpldts.geometry._geometry import DTGeometry
    from mpldts.geometry import Station, build_station
    from mpldts.geometry.sources import CMSXMLSource

    meta = {
        "package": mpldts.__file__,
        "version": getattr(mpldts, "__version__", "unknown"),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "source_checkout": str(Path(mpldts.__file__).resolve()).startswith(
            "/home/destrada/mplDTs/"
        ),
    }
    cases = {"import": time.perf_counter() - start}

    xml = Path(geometry.__file__).parent / "DTGeometry_v3.xml"
    cases["xml_parse"] = _best(lambda: DTGeometry(xml))

    stations = list(STATIONS)
    if all_chambers:
        stations += [key for key in sorted(geometry.DTGEOMETRY._chamber_key_index) if key not in stations]
    # the source parses the XML once, so the model case is the build alone
    source = CMSXMLSource()
    for key in stations:
        # the legacy view over the node tree, and the model path underneath it
        cases["station %s" % (key,)] = _best(lambda key=key: Station(*key))
        cases["model %s" % (key,)] = _best(
            lambda key=key: build_station(source.station(*key))
        )

    return meta, cases


def _print_table(meta, cases, baseline=None):
    print("mplDTs %s  %s" % (meta["version"], meta["package"]))
    print("%s  %s" % (meta["python"], meta["platform"]))
    print()
    print("%-32s %10s %10s" % ("case", "median s", "delta"))
    for name, seconds in cases.items():
        delta = ""
        if baseline and name in baseline:
            delta = "%+.1f%%" % (100.0 * (seconds - baseline[name]) / baseline[name])
        print("%-32s %10.4f %10s" % (name, seconds, delta))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", metavar="PATH", help="write the results as JSON")
    parser.add_argument("--compare", metavar="PATH", help="compare against a JSON baseline")
    parser.add_argument("--all", action="store_true", help="benchmark all 250 chambers")
    args = parser.parse_args(argv)

    meta, cases = measure(all_chambers=args.all)
    baseline = None
    if args.compare:
        baseline = json.loads(Path(args.compare).read_text())["cases"]

    _print_table(meta, cases, baseline)

    if args.json:
        payload = {"meta": meta, "cases": cases}
        Path(args.json).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        print("\nwrote", args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
