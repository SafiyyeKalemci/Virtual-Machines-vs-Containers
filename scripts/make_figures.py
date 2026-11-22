"""
make_figures.py - builds Fig. 2, Fig. 3 and Fig. 4 for the SEN421 report
(Virtual Machines vs. Containers) from the raw files in results/.

Run from the repository root:

    python scripts/make_figures.py

Output: figures/*.pdf (vector, for LaTeX) and figures/*.png
"""

import csv
import json
import re
import statistics
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results"
OUT = ROOT / "figures"
OUT.mkdir(exist_ok=True)

# Measured by hand, not stored in a results file:
DOCKER_FS_MIB = 70.0  # docker exec portfolio sh -c "du -xsm /"
VM_FS_MIB = 5.0 * 1024  # df -h / inside the VM: 5.0 GiB used

NAMES = ("Docker", "VM")
FILL = {"Docker": "#9ecae1", "VM": "#fdae6b"}
HATCH = {"Docker": "", "VM": "//"}
UNIT = {"KiB": 1 / 1024, "MiB": 1.0, "GiB": 1024.0}

plt.rcParams.update(
    {
        "font.size": 8,
        "axes.labelsize": 8,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "font.family": "serif",
    }
)


# ---------------------------------------------------------------- reading
def read_text(path):
    """Read a text file. PowerShell's Tee-Object may write UTF-16."""
    raw = Path(path).read_bytes()
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16")
    return raw.decode("utf-8-sig")


def mean_sd(values):
    sd = statistics.stdev(values) if len(values) > 1 else 0.0
    return statistics.mean(values), sd


def k6_stats(path):
    """Throughput (req/s), median and p95 response time (ms) of one k6 run."""
    metrics = json.loads(read_text(path))["metrics"]

    def get(metric, key):
        entry = metrics[metric]
        entry = entry.get("values", entry)
        if key not in entry:
            raise SystemExit(
                f"{Path(path).name}: key {key!r} not found; "
                f"available keys: {list(entry)}"
            )
        return entry[key]

    return {
        "rps": get("http_reqs", "rate"),
        "med": get("http_req_duration", "med"),
        "p95": get("http_req_duration", "p(95)"),
    }


def startup_times(path):
    """Startup times in seconds; rows marked INVALID in the note are skipped."""
    values = []
    for row in csv.DictReader(read_text(path).splitlines()):
        if "INVALID" in (row.get("note") or "").upper():
            continue
        values.append(float(row["seconds"]))
    return values


def mem_vm(path):
    """Rows 'HH:MM:SS used_MiB cpu_busy_percent' -> [(MiB, cpu %), ...]."""
    rows = []
    for line in read_text(path).splitlines():
        parts = line.split()
        if len(parts) == 3:
            rows.append((float(parts[1]), float(parts[2])))
    return rows


def mem_docker(path):
    """Rows 'HH:MM:SS 16.5MiB / 2GiB 19.4%' -> [(MiB, cpu %), ...]."""
    rows = []
    for line in read_text(path).splitlines():
        m = re.match(r"^\S+\s+([\d.]+)(KiB|MiB|GiB)\s*/\s*\S+\s+([\d.]+)%", line)
        if m:
            rows.append((float(m.group(1)) * UNIT[m.group(2)], float(m.group(3))))
    return rows


def idle_and_peak(rows, cpu_threshold, name):
    """Idle = first sample (before the load); peak = highest sample while
    the CPU figure shows that the load test was running."""
    if not rows:
        raise SystemExit(f"{name}: no readable samples")
    loaded = [mem for mem, cpu in rows if cpu > cpu_threshold]
    if not loaded:
        raise SystemExit(
            f"{name}: no sample above CPU {cpu_threshold}% - "
            "the measurement did not overlap with the load test"
        )
    return rows[0][0], max(loaded)


# --------------------------------------------------------------- plotting
def save(fig, name):
    fig.tight_layout()
    fig.savefig(OUT / f"{name}.pdf")
    fig.savefig(OUT / f"{name}.png", dpi=300)
    plt.close(fig)


def bars(ax, groups, ylabel, log=False, show_points=True, texts=None, bottom=1):
    """Bar = mean, error bar = standard deviation, dots = individual values."""
    stats = {n: mean_sd(groups[n]) for n in groups}
    top_of_all = max(m for m, _ in stats.values())
    for x, n in enumerate(groups):
        m, s = stats[n]
        ax.bar(
            x,
            m,
            0.55,
            yerr=s if s > 0 else None,
            capsize=3,
            color=FILL[n],
            edgecolor="black",
            hatch=HATCH[n],
            linewidth=0.8,
        )
        vals = groups[n]
        if show_points and len(vals) > 1:
            offsets = [(-0.12 + 0.24 * k / (len(vals) - 1)) for k in range(len(vals))]
            ax.scatter([x + o for o in offsets], vals, s=9, color="black", zorder=3)
        label = texts[n] if texts else f"{m:.1f}"
        y_top = max([m + s] + list(vals))
        if log:
            ax.text(x, y_top * 1.1, label, ha="center", va="bottom", fontsize=7)
        else:
            ax.text(
                x,
                y_top + top_of_all * 0.02,
                label,
                ha="center",
                va="bottom",
                fontsize=7,
            )
    if log:
        ax.set_yscale("log")
        ax.set_ylim(bottom, top_of_all * 6)
    else:
        ax.set_ylim(0, top_of_all * 1.25)
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels(list(groups))
    ax.set_ylabel(ylabel)


def fig2(runs):
    groups = {n: [r["rps"] for r in runs[n]] for n in NAMES}
    fig, ax = plt.subplots(figsize=(3.5, 2.6))
    bars(
        ax,
        groups,
        "Throughput (requests per second)",
        texts={n: f"{mean_sd(groups[n])[0]:.0f}" for n in NAMES},
    )
    save(fig, "fig2_throughput")


def fig3(startup):
    fig, ax = plt.subplots(figsize=(3.5, 2.6))
    for i, n in enumerate(NAMES):
        vals = startup[n]
        count = len(vals)
        xs = [i + (-0.2 + 0.4 * k / max(count - 1, 1)) for k in range(count)]
        ax.scatter(
            xs, vals, s=14, color=FILL[n], edgecolor="black", linewidth=0.7, zorder=3
        )
        med = statistics.median(vals)
        ax.hlines(med, i - 0.3, i + 0.3, colors="black", linewidth=1.6, zorder=4)
        ax.text(
            i + 0.33, med, f"median {med:.2f} s", va="center", ha="left", fontsize=7
        )
    ax.set_yscale("log")
    ax.set_xlim(-0.6, 2.25)
    ax.set_xticks([0, 1])
    ax.set_xticklabels([f"{n}\n(n = {len(startup[n])})" for n in NAMES])
    ax.set_ylabel("Startup time (s, log scale)")
    save(fig, "fig3_startup")


def fig4(mem):
    fig, (a, b) = plt.subplots(1, 2, figsize=(3.5, 2.6))
    peak = {n: mem[n]["peak"] for n in NAMES}
    bars(
        a,
        peak,
        "Memory under load (MiB, log scale)",
        log=True,
        bottom=1,
        texts={n: f"{mean_sd(peak[n])[0]:.1f}" for n in NAMES},
    )
    a.set_title("(a)", fontsize=8)
    bars(
        b,
        {"Docker": [DOCKER_FS_MIB], "VM": [VM_FS_MIB]},
        "Filesystem size (MiB, log scale)",
        log=True,
        show_points=False,
        bottom=10,
        texts={"Docker": "70 MiB", "VM": "5.0 GiB"},
    )
    b.set_title("(b)", fontsize=8)
    save(fig, "fig4_resources")


# ------------------------------------------------------------------- main
def main():
    runs = {
        "Docker": [k6_stats(RES / f"docker_run{i}.json") for i in (1, 2, 3)],
        "VM": [k6_stats(RES / f"vm_run{i}.json") for i in (1, 2, 3)],
    }
    startup = {
        "Docker": startup_times(RES / "docker_startup.csv"),
        "VM": startup_times(RES / "vm_startup.csv"),
    }
    mem = {}
    for n, reader, threshold, prefix in (
        ("Docker", mem_docker, 10, "docker_mem"),
        ("VM", mem_vm, 50, "vm_mem"),
    ):
        idle, peak = [], []
        for i in (1, 2, 3):
            fname = f"{prefix}{i}.txt"
            i_, p_ = idle_and_peak(reader(RES / fname), threshold, fname)
            idle.append(i_)
            peak.append(p_)
        mem[n] = {"idle": idle, "peak": peak}

    print("Throughput and latency (mean +/- SD of 3 runs)")
    for n in NAMES:
        cells = []
        for key, label in (("rps", "req/s"), ("med", "median ms"), ("p95", "p95 ms")):
            m, s = mean_sd([r[key] for r in runs[n]])
            cells.append(f"{label} {m:.1f} +/- {s:.1f}")
        print(f"  {n:6s} " + ", ".join(cells))

    print("\nStartup time in seconds (valid runs only)")
    for n in NAMES:
        v = startup[n]
        print(
            f"  {n:6s} n={len(v)}  median {statistics.median(v):.2f}  "
            f"min {min(v):.2f}  max {max(v):.2f}"
        )

    print("\nMemory in MiB (mean +/- SD of 3 repetitions)")
    for n in NAMES:
        mi, si = mean_sd(mem[n]["idle"])
        mp, sp = mean_sd(mem[n]["peak"])
        print(
            f"  {n:6s} idle {mi:.1f} +/- {si:.1f}   under load {mp:.1f} +/- {sp:.1f}"
            f"   (peaks: {[round(x, 2) for x in mem[n]['peak']]})"
        )

    fig2(runs)
    fig3(startup)
    fig4(mem)
    print(f"\nFigures written to {OUT}")


if __name__ == "__main__":
    main()
