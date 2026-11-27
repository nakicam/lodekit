# EX-1 – Synthetic Retail Dataset Specification

**Status:** Draft v0.1 (specification only; the generator is built in DF-2) · **Owner:** examples maintainers · **Date:** 2026-11-27
**Project name:** lodekit (D1). Package names are placeholders (`<pkg>`) until fixed.
**Implemented by:** DF-2 (generator + dlt ingest). **Used by:** EX-2 (data-pipeline), DQ-1…DQ-4 (quality checks), LD-8c/EX-3 (analyst-mini), EX-4 (multi-agent), EX-8 (end-to-end demo).
**Licence of generated data:** CC0-1.0.

---

## 1. Purpose

One small, fully synthetic, deterministic dataset that gives every example a **known correct answer**:
- the data pipeline (M1) must find **exactly** the injected data errors,
- the analyst (M2, M5) must find **exactly** the injected business anomalies,
- all of this works offline in CI with a fake model.

No real persons, companies, addresses, or brands appear in the data. The fictional company is **"Northbridge Supply"** (working name; must stay obviously fictional and must not reference ducks, DuckDB, or real brands).

## 2. Design principles

| # | Principle | Consequence |
|---|---|---|
| P1 | **Bit-identical output** on Linux/macOS/Windows and Python 3.11–3.14 for the same `--seed` | Only stdlib `random.Random(seed)`; **no Faker** (its output changes between versions); `Decimal` with fixed rounding (`ROUND_HALF_EVEN`, 2 places); UTF-8, `\n` line endings, rows sorted by primary key; no dependence on locale, timezone, or current date |
| P2 | **Fixed calendar**, not relative to "today" | Period 2024-01-01 … 2025-12-31 (8 quarters); "last quarter" always means **2025-Q4**; `as_of = 2025-12-31` |
| P3 | **Anomalies by construction** | Each anomaly is a documented multiplier applied by the generator, so the expected answer follows from the spec, and the generator also writes it to `expected_answers.json` from the clean data |
| P4 | **Errors are countable** | Each data error type has a fixed count and only appears in raw files, never in the clean mart |
| P5 | **Small** | Default ≤ 10 MB total, generation < 30 s on a typical laptop |
| P6 | **Incremental-friendly** | Order files are partitioned by month so the dlt `filesystem` source with `incremental("modification_date")` can load only new files |

## 3. CLI contract

```
generate --seed 42 --rows 50000 --out data/ [--until 2025-12] [--format csv|parquet|both]
```

| Option | Default | Meaning |
|---|---|---|
| `--seed` | `42` | PRNG seed; all expected values in this spec refer to seed 42 |
| `--rows` | `50000` | approximate number of **order lines**; dimension sizes scale (see §4) |
| `--out` | `data/` | output directory, created if missing; existing generated files are overwritten |
| `--until` | `2025-12` | last month to write. `--until 2025-09` writes Q1-2024…Q3-2025 only (first load); a second call with `--until 2025-12` adds Oct–Dec files without touching existing ones → incremental story for EX-2 |
| `--format` | `csv` | raw delivery format; `both` additionally writes Parquet |

Exit code 0 on success; prints a one-line summary (`files, rows, bytes, sha256 of manifest`).

## 4. Output layout and schema

```
data/
├── raw/
│   ├── regions.csv
│   ├── customers.csv
│   ├── products.csv
│   ├── orders/
│   │   ├── orders_2024-01.csv        # one file per month, header + rows
│   │   ├── ...
│   │   └── orders_2025-12.csv
│   └── order_lines/
│       ├── order_lines_2024-01.csv   # one file per month
│       ├── ...
│       └── order_lines_2025-12.csv
├── expected_answers.json
├── manifest.json                     # file list, row counts, sha256 per file, seed, generator version
└── DATA_CARD.md                      # licence CC0-1.0, provenance "synthetic", this spec's summary
```

Sizes at `--rows 50000`: 6 regions, 2,000 customers, 120 products, ~20,000 orders, ~50,000 order lines.

### 4.1 `regions`
| Column | Type | Notes |
|---|---|---|
| `region_id` | int | 1–6, PK |
| `region_name` | str | `North`, `North-East`, `East`, `South`, `West`, `Central` |
| `base_share` | decimal(4,3) | share of baseline demand: 0.200, 0.150, 0.180, 0.170, 0.160, 0.140 |

### 4.2 `customers`
| Column | Type | Notes |
|---|---|---|
| `customer_id` | int | PK |
| `customer_name` | str | generated `"<Adjective> <Noun> <Suffix>"` from built-in word lists (e.g. "Quiet Harbor Traders"); no person names |
| `region_id` | int | FK → regions (see error E3) |
| `segment` | str | `consumer` (70 %), `business` (30 %) |
| `signup_date` | date | 2022-01-01 … 2025-12-31 |

### 4.3 `products`
| Column | Type | Notes |
|---|---|---|
| `product_id` | int | PK |
| `product_name` | str | `"<Category> <Adjective> <Item> <n>"` |
| `category` | str | `Outdoor`, `Kitchen`, `Office`, `Garden`, `Toys`, `Electronics` (20 products each) |
| `list_price` | decimal(10,2) | category-specific range, e.g. Office 5–80, Electronics 40–900 |
| `unit_cost` | decimal(10,2) | 45–70 % of `list_price` |

### 4.4 `orders` (monthly files)
| Column | Type | Notes |
|---|---|---|
| `order_id` | int | PK (see error E2) |
| `order_date` | date | within the file's month (see error E5) |
| `customer_id` | int | FK → customers |
| `channel` | str | `online` (60 %), `store` (40 %) |
| `status` | str | `completed` (92 %), `returned` (5 %), `cancelled` (3 %) |

### 4.5 `order_lines` (monthly files)
| Column | Type | Notes |
|---|---|---|
| `order_id` | int | FK → orders |
| `line_no` | int | 1…n per order (1–5 lines) |
| `product_id` | int | FK → products |
| `quantity` | int | 1–10 (see error E1) |
| `unit_price` | decimal(10,2) | `list_price` (see error E4) |
| `discount` | decimal(3,2) | 0.00 (75 %), 0.05, 0.10, 0.20 |

**Revenue definition (used everywhere):** `revenue = quantity × unit_price × (1 − discount)` for order lines of orders with `status = 'completed'`. Region = customer's region.

## 5. Baseline demand model

Number of orders per (month, region) = `N_base × base_share(region) × growth(month) × season(month) × anomaly(...)`, then Poisson-like noise of ±5 % from the seeded PRNG.

| Factor | Value |
|---|---|
| `growth` | +2 % per quarter, compounded (Q1-2024 = 1.00) |
| `season` | Q4 × 1.15, Q1 × 0.95, Q2/Q3 × 1.00 |
| Category mix | uniform across categories, except anomaly A2 |

Without anomalies, every region would show roughly **+17 % revenue QoQ from 2025-Q3 to 2025-Q4** (growth × season).

## 6. Injected business anomalies (the analyst's "correct answers")

| ID | Anomaly | Construction | Expected finding (seed 42, approx.; exact values in `expected_answers.json`) |
|---|---|---|---|
| **A1** | **Regional revenue drop in the last quarter** | `North-East`, 2025-Q4: order count × **0.65** across all categories and channels | North-East is the **only** region with negative QoQ revenue change in 2025-Q4: ≈ **−14 %** (= 1.173 × 0.65 × 1.13 − 1; others ≈ +28 … +38 %) |
| **A2** | **Outlier category growth** | `Outdoor`, 2025-Q4: additional Outdoor lines so that Outdoor line count is × **1.8** in every region (on top of A1) | Outdoor has the highest QoQ revenue growth of all categories in 2025-Q4: ≈ **+110 %** (= 1.173 × 1.8 − 1, slightly lower because of A1); all other categories ≈ +12 … +17 %. Raises every region's total by ≈ +13 % |
| **A3** | **Channel shift (subtle, for M5 only)** | 2025-H2: `online` share 60 % → 70 % in all regions | Online share of revenue 2025-H2 ≈ 70 % vs. ≈ 60 % before; not required for M2 |

Rules: A1 must stay detectable even with A2 active (A2 boosts North-East Outdoor too, but North-East total must still be negative QoQ and at least 25 pp below the next-lowest region). The generator asserts this before writing files and fails otherwise. Approximate values assume similar average revenue per line across categories; the real values come from `expected_answers.json`.

## 7. Injected data errors (the quality checks' "correct answers")

Errors exist **only in raw files**. Counts are exact for every seed (positions vary with the seed).

| ID | Error | Where | Count | Expected check (DQ-2 / DQ-3) |
|---|---|---|---|---|
| **E1** | `quantity` is empty (NULL) | `order_lines` | **12** rows | `not_null(order_lines.quantity)` fails with 12 |
| **E2** | duplicated order row (identical copy, same `order_id`) | `orders` | **25** duplicates | `unique(orders.order_id)` fails with 25 |
| **E3** | `region_id = 99` (unknown region) | `customers` | **8** customers | `relationships(customers.region_id → regions)` / `accepted_values` fails with 8 |
| **E4** | negative `unit_price` | `order_lines` | **5** rows | `expression: unit_price >= 0` fails with 5 |
| **E5** | `order_date` after `as_of` (2026-06-30) in `orders_2025-12.csv` | `orders` | **3** rows | freshness/range check `order_date <= as_of` fails with 3 |

**Cleaning rules in the dbt staging layer (DF-3)** so the mart is correct:
E1 → drop line · E2 → keep first occurrence · E3 → map to region `unknown` and exclude from regional marts · E4 → drop line · E5 → drop order.
`expected_answers.json` is computed **after** applying exactly these rules.

M1 acceptance (EX-2, G3): the quality report lists **exactly** E1–E5 with these counts, nothing else; `DataAsset.quality_status = "warning"` for the raw asset and `"passed"` for the mart.

## 8. Expected marts (DF-3) and exports for analyst-mini

| Model | Grain | Columns |
|---|---|---|
| `stg_*` | 1:1 raw, typed, cleaned per §7 | – |
| `fct_order_lines` | order line | order_id, line_no, order_date, quarter (`YYYY-Qn`), region_name, category, channel, quantity, revenue, cost |
| `mart_revenue_region_quarter` | region × quarter | region_name, quarter, revenue, orders, qoq_change_pct |
| `mart_revenue_category_quarter` | category × quarter | category, quarter, revenue, qoq_change_pct |

**Exports for EX-3 (D1b = b, no own DuckDB wrapper):** the pipeline writes `exports/mart_revenue_region_quarter.parquet` and `exports/mart_revenue_category_quarter.parquet` (plus CSV). The analyst-mini's read-only data tool reads only these files via pyarrow/pandas.

## 9. `expected_answers.json`

```json
{
  "seed": 42,
  "as_of": "2025-12-31",
  "last_quarter": "2025-Q4",
  "questions": [
    {
      "id": "Q1",
      "text": "Which region is unusual last quarter?",
      "answer": {"region": "North-East", "qoq_change_pct": -13.8},
      "tolerance": {"qoq_change_pct": 1.0}
    },
    {
      "id": "Q2",
      "text": "Which product category grew fastest last quarter?",
      "answer": {"category": "Outdoor", "qoq_change_pct": 108.7},
      "tolerance": {"qoq_change_pct": 1.0}
    },
    {
      "id": "Q3",
      "text": "What was total revenue last quarter?",
      "answer": {"revenue": 0.0},
      "tolerance": {"revenue_pct": 0.1}
    }
  ],
  "data_errors": {"E1": 12, "E2": 25, "E3": 8, "E4": 5, "E5": 3}
}
```
Numbers above are **illustrative**; the generator writes the real values. CI asserts against the file, not against this document.

## 10. Data contract hints (for DQ-3)

Raw contract (`orders`): `order_id` int unique not null · `order_date` date ≤ as_of · `customer_id` int FK · `channel` in {online, store} · `status` in {completed, returned, cancelled}. Analogous for the other tables. Contract format per spike S6 (e.g. ODCS).

## 11. Acceptance criteria (for DF-2, generator part)

1. `generate --seed 42 --rows 50000 --out data/` finishes in < 30 s and writes ≤ 10 MB (CSV).
2. Running it twice on Linux, macOS and Windows with Python 3.11 and 3.14 yields identical `manifest.json` sha256 values (CI matrix test).
3. Error counts E1–E5 exactly as in §7; anomalies A1/A2 hold per §6 (generator self-check).
4. `--until 2025-09` followed by `--until 2025-12` produces the same final files as a single `--until 2025-12` run, and existing files keep their modification time.
5. `DATA_CARD.md` states CC0-1.0, "synthetic, no real persons or companies", and links this spec.
6. Only stdlib dependencies (Parquet output may use `pyarrow` as an optional extra).

## 12. Non-goals

No realistic geography, currencies, taxes, or time zones · no personal data of any kind · no streaming/CDC simulation · not a benchmark dataset.
