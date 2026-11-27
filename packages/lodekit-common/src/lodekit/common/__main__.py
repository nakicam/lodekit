"""Print the RunContext JSON schema: ``python -m lodekit.common``."""

import json

from lodekit.common.run_context import run_context_json_schema


def main() -> None:
    """Write the schema as indented, key-sorted JSON to stdout."""
    print(json.dumps(run_context_json_schema(), indent=2, sort_keys=True))


if __name__ == "__main__":  # pragma: no cover
    main()
