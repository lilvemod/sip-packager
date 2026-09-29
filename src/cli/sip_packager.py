"""
Runs the full SIP packaging pipeline:

1. csip_structure.py
2. normalize_filenames.py (optional)
3. cits_erms.py
4. mets.py
5. package_to_zip.py
"""

import datetime
import logging
import subprocess

from src.common.utils import (
    setup_logging,
)


def parse_args(argv=None):
    import argparse

    parser = argparse.ArgumentParser(
        description="Runs the full SIP packaging pipeline."
    )

    parser.add_argument(
        "--normalize",
        action="store_true",
        help="Run normalize-filenames.py between csip_structure and cits_erms."
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug logging."
    )

    return parser.parse_args(argv)


def run_step(description: str, module_path: str) -> None:
    """
    Runs a Python module using subprocess and raises an error if it fails.
    Is run for each module in the pipeline. 
    """
    logging.info("Running step: %s", description)

    start = datetime.datetime.now()

    result = subprocess.run(
        ["python", "-m", module_path],
        capture_output=True,
        text=True
    )

    elapsed = datetime.datetime.now() - start

    # If the program returns 0 it means it ran correctly
    if result.returncode != 0:
        logging.error("Step failed: %s", description)
        logging.error(result.stderr)
        # Uses string formatting rather that %-formatting to avoid formatting issues that otherwise would occurs when building 'description'
        raise RuntimeError(f"Pipeline aborted at step: {description}")

    logging.info("Step completed: %s, (%.2f seconds)", description, elapsed.total_seconds())


def main(argv=None) -> int:
    args = parse_args(argv)
    setup_logging(args.verbose)

    logging.info("Starting SIP packaging pipeline...")

    try:
        # 1. CSIP structure
        run_step("Create CSIP structure", "src.generators.csip_structure")

        # 2. Optional filename normalization
        if args.normalize:
            run_step("Normalize filenames", "src.tools.normalize_filenames")
        else:
            while True:
                choice = input("Normalize filenames in SIP? (y/n): ").strip().lower()
                if choice == "y":
                    run_step("Normalize filenames", "src.tools.normalize_filenames")
                    break
                elif choice == "n":
                    logging.info("Filenames will not be normalized.")
                    break
                else:
                    print("Invalid input, 'y' or 'n'.")

        # 3. ERMS XML generation
        run_step("Generate ERMS XML", "src.generators.cits_erms")

        # 4. METS generation
        run_step("Generate METS XML", "src.generators.mets")

        # 5. ZIP packaging
        run_step("Package SIP into ZIP", "src.generators.package_to_zip")

        logging.info("Pipeline completed successfully.")
        return 0

    except Exception as exc:
        logging.error("Pipeline failed: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
