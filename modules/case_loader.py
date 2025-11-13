"""
Module 1: Input and Case Preparation
Handles loading and preprocessing of ethical cases from Excel/CSV files.
"""

import pandas as pd
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CaseLoader:
    """
    Loads and prepares ethical case studies for evaluation.
    """

    def __init__(self, file_path: str):
        """
        Initialize the CaseLoader with a path to the cases file.

        Args:
            file_path: Path to Excel or CSV file containing ethical cases
        """
        self.file_path = file_path
        self.cases = []

    def load_cases(self) -> List[Dict[str, Any]]:
        """
        Load cases from file and perform basic cleaning.

        Returns:
            List of dictionaries, each containing case information
        """
        try:
            # Determine file type and load accordingly
            if self.file_path.endswith('.xlsx') or self.file_path.endswith('.xls'):
                df = pd.read_excel(self.file_path)
            elif self.file_path.endswith('.csv'):
                df = pd.read_csv(self.file_path)
            else:
                raise ValueError("File must be Excel (.xlsx, .xls) or CSV (.csv)")

            # Basic cleaning
            df = df.fillna('')
            df = df.map(lambda x: x.strip() if isinstance(x, str) else x)

            # Validate required columns
            required_columns = ['CaseID', 'Description']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")

            # Convert to list of dictionaries
            self.cases = df.to_dict(orient='records')

            logger.info(f"Successfully loaded {len(self.cases)} cases from {self.file_path}")
            return self.cases

        except Exception as e:
            logger.error(f"Error loading cases: {e}")
            raise

    def get_case_by_id(self, case_id: str) -> Dict[str, Any]:
        """
        Retrieve a specific case by its ID.

        Args:
            case_id: The case identifier

        Returns:
            Dictionary containing case information
        """
        for case in self.cases:
            if case['CaseID'] == case_id:
                return case
        raise ValueError(f"Case with ID {case_id} not found")

    def get_all_cases(self) -> List[Dict[str, Any]]:
        """
        Get all loaded cases.

        Returns:
            List of all case dictionaries
        """
        return self.cases

    def validate_case(self, case: Dict[str, Any]) -> bool:
        """
        Validate that a case has all required fields.

        Args:
            case: Case dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        required_fields = ['CaseID', 'Description']
        for field in required_fields:
            if field not in case or not case[field]:
                logger.warning(f"Case {case.get('CaseID', 'unknown')} missing field: {field}")
                return False
        return True

    def filter_cases(self, filter_func) -> List[Dict[str, Any]]:
        """
        Filter cases based on a custom function.

        Args:
            filter_func: Function that takes a case dict and returns bool

        Returns:
            Filtered list of cases
        """
        return [case for case in self.cases if filter_func(case)]


# Example usage and testing
if __name__ == "__main__":
    # This would be used for testing the module independently
    print("CaseLoader module loaded successfully")
    print("Example usage:")
    print("loader = CaseLoader('path/to/cases.xlsx')")
    print("cases = loader.load_cases()")
