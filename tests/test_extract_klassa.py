import sys
import pytest
from src.common.utils import determine_project_root
from src.tools.extract_klassa import validate_excel_file

project_root = determine_project_root()
config_dir = project_root / "config"
tests_dir = project_root / "tests"
valid_path = config_dir / "Klassa_2_1.xlsx"




def test_file_exists():
    valid_path = config_dir / "Klassa_2_1.xlsx"
    assert validate_excel_file(valid_path) == True

def test_invalid_extension():
    invalid_file = tests_dir / "invalid_file.txt"
    assert validate_excel_file(invalid_file) == False

def test_file_not_exists():
    non_existent_file = tests_dir / "non_existent_file.xlsx"
    assert validate_excel_file(non_existent_file) == False


