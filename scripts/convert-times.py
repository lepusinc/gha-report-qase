"""Convert execution.start_time / end_time of Qase result files from seconds to milliseconds.

The Qase reporters (qase-php-commons, qase-javascript-commons) write start_time / end_time in seconds, while
qasectl reads them as milliseconds and recomputes the duration from their difference. Without this conversion every
duration becomes 0 in Qase.

Usage: python3 convert-times.py <results directory>
Prints the number of converted files.
"""

import json
import pathlib
import sys


def convert(result: dict) -> dict:
    execution = result.get("execution") or {}
    for key in ("start_time", "end_time"):
        value = execution.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            execution[key] = value * 1000
    return result


def main(directory: str) -> int:
    count = 0
    for path in sorted(pathlib.Path(directory).glob("*.json")):
        result = json.loads(path.read_text(encoding="utf-8-sig"))
        path.write_text(json.dumps(convert(result), ensure_ascii=False), encoding="utf-8")
        count += 1
    print(count)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
