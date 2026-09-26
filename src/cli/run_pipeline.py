"""
Runs the full SIP packaging pipeline:

1. csip_structure.py
2. (optional) normalize_filenames.py
3. cits_erms.py
4. mets.py
5. package_to_zip.py
"""

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
        "--verbose",
        action="store_true",
        help="Enable debug logging."
    )

    return parser.parse_args(argv)


def run_step(description: str, module_path: str) -> None:
    """
    Runs a Python module using subprocess and raises an error if it fails.
    """
    logging.info(f"Running step: {description}")

    result = subprocess.run(
        ["python", "-m", module_path],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        logging.error(f"Step failed: {description}")
        logging.error(result.stderr)
        raise RuntimeError(f"Pipeline aborted at step: {description}")

    logging.info(result.stdout)
    logging.info(f"Step completed: {description}")


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
        logging.error(f"Pipeline failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
