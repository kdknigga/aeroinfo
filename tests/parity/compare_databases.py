#!/usr/bin/env python3
"""Compare data row-by-row, table-by-table between two PostgreSQL databases."""

import argparse
import csv
import os
import sys
from collections import defaultdict
from pathlib import Path

import psycopg2
import psycopg2.extras

from .categories import (
    CATEGORIES,
    EXCLUDED_CATEGORIES,
    classify_diff,
    is_excluded,
)

# -- Connection strings (from environment or defaults) -------------------------
# DB_A = TXT-loaded database (reference), DB_B = CSV-loaded database (target)
DB_A = os.environ.get(
    "AEROINFO_DB_A", "host=localhost dbname=aeroinfo_txt user= password="
)
DB_B = os.environ.get(
    "AEROINFO_DB_B", "host=localhost dbname=aeroinfo_csv user= password="
)

OUTPUT_FILE = "db_differences.csv"
FETCH_SIZE = 5000


def print_summary(category_counts: dict[str, int]) -> None:
    """Print a formatted per-category summary table to stdout."""
    excluded_total = sum(
        v for k, v in category_counts.items() if k in EXCLUDED_CATEGORIES
    )
    actionable_total = sum(
        v for k, v in category_counts.items() if k not in EXCLUDED_CATEGORIES
    )
    total = excluded_total + actionable_total

    print("\n=== Difference Summary ===")
    print(f"{'Category':<45} {'Count':>7}  {'Status'}")
    print("-" * 70)
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        if cat in EXCLUDED_CATEGORIES:
            status = "EXCLUDED"
        else:
            req_id = CATEGORIES.get(cat, {}).get("req_id", "")
            status = f"ACTIONABLE ({req_id})" if req_id else "ACTIONABLE"
        print(f"{cat:<45} {count:>7,}  {status}")
    print("-" * 70)
    print(f"{'Total differences':<45} {total:>7,}")
    print(f"{'  Excluded (accepted)':<45} {excluded_total:>7,}")
    print(f"{'  Actionable':<45} {actionable_total:>7,}")

    # Sanity check: all diffs should be accounted for
    computed_total = sum(category_counts.values())
    if computed_total != total:
        print(
            f"\nWARNING: Category sum ({computed_total}) does not match total ({total})"
        )


# -- Database helpers (unchanged) ---------------------------------------------


def get_tables(conn: psycopg2.extensions.connection) -> list[str]:
    """Return sorted list of user tables in the public schema."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_type = 'BASE TABLE' "
            "ORDER BY table_name"
        )
        return [row[0] for row in cur.fetchall()]


def get_primary_key_columns(
    conn: psycopg2.extensions.connection,
    table: str,
) -> list[str]:
    """Return ordered list of primary key column names for a table."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT a.attname "
            "FROM pg_index i "
            "JOIN pg_attribute a ON a.attrelid = i.indrelid "
            "  AND a.attnum = ANY(i.indkey) "
            "JOIN pg_class c ON c.oid = i.indrelid "
            "JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE c.relname = %s AND n.nspname = 'public' AND i.indisprimary "
            "ORDER BY array_position(i.indkey, a.attnum)",
            (table,),
        )
        return [row[0] for row in cur.fetchall()]


def get_columns(
    conn: psycopg2.extensions.connection,
    table: str,
) -> list[str]:
    """Return ordered list of column names for a table."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = %s "
            "ORDER BY ordinal_position",
            (table,),
        )
        return [row[0] for row in cur.fetchall()]


def format_pk(
    pk_cols: list[str],
    row_dict: dict[str, object],
) -> str:
    """Format primary key value(s) as a string."""
    if len(pk_cols) == 1:
        return str(row_dict[pk_cols[0]])
    return "({})".format(", ".join(f"{c}={row_dict[c]}" for c in pk_cols))


def pk_tuple(
    pk_cols: list[str],
    row_dict: dict[str, object],
) -> tuple[object, ...]:
    """Extract primary key as a comparable tuple."""
    return tuple(row_dict[c] for c in pk_cols)


def open_sorted_cursor(
    conn: psycopg2.extensions.connection,
    table: str,
    columns: list[str],
    pk_cols: list[str],
    cursor_name: str,
) -> psycopg2.extensions.cursor:
    """Open a named server-side cursor ordered by primary key."""
    col_list = ", ".join(f'"{c}"' for c in columns)
    order_by = ", ".join(f'"{c}"' for c in pk_cols)
    cur = conn.cursor(
        name=cursor_name,
        cursor_factory=psycopg2.extras.RealDictCursor,
    )
    cur.itersize = FETCH_SIZE
    cur.execute(f'SELECT {col_list} FROM "{table}" ORDER BY {order_by}')  # noqa: S608
    return cur


def compare_table(
    conn_a: psycopg2.extensions.connection,
    conn_b: psycopg2.extensions.connection,
    table: str,
    pk_cols: list[str],
    columns: list[str],
    writer: csv.writer,
    category_counts: dict[str, int],
    *,
    show_all: bool = False,
) -> tuple[int, int]:
    """Stream-compare a single table; returns (total_diffs, actionable_diffs)."""
    non_pk_cols = [c for c in columns if c not in pk_cols]
    diff_count = 0
    actionable_count = 0

    cur_a = open_sorted_cursor(conn_a, table, columns, pk_cols, f"cur_a_{table}")
    cur_b = open_sorted_cursor(conn_b, table, columns, pk_cols, f"cur_b_{table}")

    row_a = next(cur_a, None)
    row_b = next(cur_b, None)

    while row_a is not None or row_b is not None:
        if row_a is not None and row_b is not None:
            pk_a = pk_tuple(pk_cols, row_a)
            pk_b = pk_tuple(pk_cols, row_b)

            if pk_a == pk_b:
                # Same row -- compare fields
                pk_str = format_pk(pk_cols, row_a)
                for col in non_pk_cols:
                    val_a = row_a[col]
                    val_b = row_b[col]
                    if val_a != val_b:
                        category = classify_diff(table, col)
                        category_counts[category] += 1
                        if not is_excluded(category):
                            actionable_count += 1
                        if show_all or not is_excluded(category):
                            writer.writerow([table, pk_str, col, val_a, val_b])
                        diff_count += 1
                row_a = next(cur_a, None)
                row_b = next(cur_b, None)

            elif pk_a < pk_b:
                # Row only in A
                pk_str = format_pk(pk_cols, row_a)
                field = "(row missing from B)"
                category = classify_diff(table, field, "missing_from_b")
                category_counts[category] += 1
                if not is_excluded(category):
                    actionable_count += 1
                if show_all or not is_excluded(category):
                    writer.writerow([table, pk_str, field, "", ""])
                diff_count += 1
                row_a = next(cur_a, None)

            else:
                # Row only in B
                pk_str = format_pk(pk_cols, row_b)
                field = "(row missing from A)"
                category = classify_diff(table, field, "missing_from_a")
                category_counts[category] += 1
                if not is_excluded(category):
                    actionable_count += 1
                if show_all or not is_excluded(category):
                    writer.writerow([table, pk_str, field, "", ""])
                diff_count += 1
                row_b = next(cur_b, None)

        elif row_a is not None:
            pk_str = format_pk(pk_cols, row_a)
            field = "(row missing from B)"
            category = classify_diff(table, field, "missing_from_b")
            category_counts[category] += 1
            if not is_excluded(category):
                actionable_count += 1
            if show_all or not is_excluded(category):
                writer.writerow([table, pk_str, field, "", ""])
            diff_count += 1
            row_a = next(cur_a, None)

        else:
            pk_str = format_pk(pk_cols, row_b)
            field = "(row missing from A)"
            category = classify_diff(table, field, "missing_from_a")
            category_counts[category] += 1
            if not is_excluded(category):
                actionable_count += 1
            if show_all or not is_excluded(category):
                writer.writerow([table, pk_str, field, "", ""])
            diff_count += 1
            row_b = next(cur_b, None)

    cur_a.close()
    cur_b.close()

    return diff_count, actionable_count


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Compare two PostgreSQL databases row-by-row.",
    )
    parser.add_argument(
        "--show-all",
        action="store_true",
        help="Write all diffs to CSV including excluded categories "
        "(default: only actionable diffs)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run database comparison with categorization and summary."""
    args = parse_args(argv)

    conn_a = psycopg2.connect(DB_A)
    conn_b = psycopg2.connect(DB_B)
    conn_a.set_session(readonly=True)
    conn_b.set_session(readonly=True)

    tables_a = get_tables(conn_a)
    tables_b = get_tables(conn_b)
    common_tables = sorted(set(tables_a) & set(tables_b))

    only_a = sorted(set(tables_a) - set(tables_b))
    only_b = sorted(set(tables_b) - set(tables_a))
    if only_a:
        print(f"Tables only in A: {', '.join(only_a)}")
    if only_b:
        print(f"Tables only in B: {', '.join(only_b)}")

    total_diffs = 0
    total_actionable = 0
    category_counts: dict[str, int] = defaultdict(int)

    with Path(OUTPUT_FILE).open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["table", "row", "field", "value_a", "value_b"])

        for table in common_tables:
            pk_cols = get_primary_key_columns(conn_a, table)
            if not pk_cols:
                print(f"  SKIP {table} (no primary key)")
                continue

            columns = get_columns(conn_a, table)
            print(f"  Comparing {table}...", end="", flush=True)
            diffs, actionable = compare_table(
                conn_a,
                conn_b,
                table,
                pk_cols,
                columns,
                writer,
                category_counts,
                show_all=args.show_all,
            )
            total_diffs += diffs
            total_actionable += actionable
            print(f" {diffs} difference(s)")

    conn_a.close()
    conn_b.close()

    print_summary(category_counts)

    mode = "all diffs" if args.show_all else "actionable only"
    print(f"\nCSV output ({mode}): {OUTPUT_FILE}")

    return 0 if total_actionable == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
