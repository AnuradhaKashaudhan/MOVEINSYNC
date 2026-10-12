"""
Pipeline Benchmarking Utility
Measures I/O load times, cache throughput, and aggregation computation latency.
"""

import time
import json
import pandas as pd
from pathlib import Path

def benchmark():
    print("=" * 60)
    print("MOVEINSYNC PIPELINE LATENCY BENCHMARK")
    print("=" * 60)

    # 1. Benchmark CSV Ingestion
    t0 = time.perf_counter()
    data_path = Path("data/processed/analyzed_reviews.csv")
    df = pd.read_csv(data_path)
    t_csv = (time.perf_counter() - t0) * 1000
    print(f"1. CSV Ingestion ({len(df):,} rows): {t_csv:.2f} ms")

    # 2. Benchmark Summary JSON Read
    t0 = time.perf_counter()
    summary_path = Path("reports/summary.json")
    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)
    t_json = (time.perf_counter() - t0) * 1000
    print(f"2. Summary JSON Parse: {t_json:.2f} ms")

    # 3. Benchmark Theme Frequency Aggregation
    t0 = time.perf_counter()
    df_12 = df[df['sample_group'] == 'all_1_2_star']
    counts = df_12['primary_theme'].value_counts()
    t_agg = (time.perf_counter() - t0) * 1000
    print(f"3. In-Memory Aggregation ({len(counts)} themes): {t_agg:.2f} ms")

    print("-" * 60)
    print(f"Total Benchmark Execution Time: {(t_csv + t_json + t_agg):.2f} ms")
    print("=" * 60)

if __name__ == "__main__":
    benchmark()
