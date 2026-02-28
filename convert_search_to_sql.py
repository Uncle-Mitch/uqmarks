from pathlib import Path
from datetime import datetime
import csv

INPUT_FILE = "logs/search_log.txt"
OUTPUT_FILE = "search_logs.csv"



def main():
    input_path = Path(INPUT_FILE)
    output_path = Path(OUTPUT_FILE)

    if not input_path.exists():
        raise FileNotFoundError(f"{INPUT_FILE} not found")

    with input_path.open("r", encoding="utf-8") as infile, \
         output_path.open("w", newline="", encoding="utf-8") as outfile:

        writer = csv.writer(outfile)

        # Optional header (recommended)
        writer.writerow(["ts", "code", "semester", "year"])

        count = 0

        for line_no, line in enumerate(infile, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                unix_ts, code, semester, year = line.split("|")

                ts = datetime.utcfromtimestamp(int(unix_ts))

                writer.writerow([
                    ts.isoformat(sep=" "),
                    code,
                    int(semester),
                    int(year),
                ])

                count += 1

            except Exception as e:
                raise ValueError(f"Line {line_no} invalid: {line}") from e

    print(f"✅ Wrote {count} rows to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()