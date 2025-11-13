"""
Module 6: Output Generation and Saving
Saves evaluation results in organized folder structure with multiple formats.
"""

import os
import json
import pandas as pd
from typing import Dict, List, Any
import logging
from datetime import datetime
import sys
sys.path.append('..')
from config import OUTPUT_PATHS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OutputSaver:
    """
    Manages saving of evaluation results including conversations, analysis, stances, and scores.
    """

    def __init__(self, base_output_dir: str = None):
        """
        Initialize output saver.

        Args:
            base_output_dir: Base directory for outputs (defaults to config.OUTPUT_PATHS['base'])
        """
        self.base_dir = base_output_dir if base_output_dir else OUTPUT_PATHS['base']
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def create_output_structure(self, model_names: List[str]) -> None:
        """
        Create the output folder structure.

        Args:
            model_names: List of model names to create folders for
        """
        # Create base output directory
        os.makedirs(self.base_dir, exist_ok=True)

        # Create subdirectories for each model
        for model in model_names:
            model_dir = os.path.join(self.base_dir, self._sanitize_filename(model))
            os.makedirs(model_dir, exist_ok=True)

            # Create subdirectories for different output types
            os.makedirs(os.path.join(model_dir, "conversations"), exist_ok=True)
            os.makedirs(os.path.join(model_dir, "analysis"), exist_ok=True)
            os.makedirs(os.path.join(model_dir, "stances"), exist_ok=True)

        logger.info(f"Created output structure in {self.base_dir}")

    def _sanitize_filename(self, name: str) -> str:
        """
        Sanitize a string to be used as a filename.

        Args:
            name: String to sanitize

        Returns:
            Sanitized string safe for filesystem
        """
        # Replace problematic characters
        sanitized = name.replace('/', '_').replace('\\', '_').replace(':', '_')
        sanitized = sanitized.replace(' ', '_').replace('.', '_')
        return sanitized

    def save_conversation(
        self,
        model_name: str,
        case_id: str,
        case_description: str,
        queries: Dict[str, str],
        responses: Dict[str, str]
    ) -> str:
        """
        Save the complete conversation transcript for a model-case pair.

        Args:
            model_name: Name of the model
            case_id: Case identifier
            case_description: Description of the case
            queries: Dict of node -> query text
            responses: Dict of node -> response text

        Returns:
            Path to saved file
        """
        model_dir = os.path.join(self.base_dir, self._sanitize_filename(model_name), "conversations")
        filename = f"{self._sanitize_filename(case_id)}_conversation.txt"
        filepath = os.path.join(model_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"ETHICAL EVALUATION CONVERSATION\n")
            f.write(f"Model: {model_name}\n")
            f.write(f"Case ID: {case_id}\n")
            f.write(f"Timestamp: {self.timestamp}\n")
            f.write("=" * 80 + "\n\n")

            f.write("CASE DESCRIPTION:\n")
            f.write(f"{case_description}\n\n")
            f.write("=" * 80 + "\n\n")

            # Write each Q&A pair
            nodes = ['N1', 'N2', 'N3', 'C']
            node_names = {
                'N1': 'Node 1 - Initial Query',
                'N2': 'Node 2 - Counter Question (Adaptive)',
                'N3': 'Node 3 - Grey Area',
                'C': 'Conclusion'
            }

            for node in nodes:
                if node in queries and node in responses:
                    f.write(f"{node_names[node]}\n")
                    f.write("-" * 80 + "\n")
                    f.write(f"QUESTION:\n{queries[node]}\n\n")
                    f.write(f"ANSWER:\n{responses[node]}\n\n")
                    f.write("=" * 80 + "\n\n")

        logger.info(f"Saved conversation to {filepath}")
        return filepath

    def save_analysis(
        self,
        model_name: str,
        case_id: str,
        conversation_analysis: Dict[str, Any]
    ) -> str:
        """
        Save detailed analysis results as JSON.

        Args:
            model_name: Name of the model
            case_id: Case identifier
            conversation_analysis: Complete analysis from NLPAnalyzer

        Returns:
            Path to saved file
        """
        model_dir = os.path.join(self.base_dir, self._sanitize_filename(model_name), "analysis")
        filename = f"{self._sanitize_filename(case_id)}_analysis.json"
        filepath = os.path.join(model_dir, filename)

        # Make the analysis JSON-serializable
        serializable_analysis = self._make_serializable(conversation_analysis)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(serializable_analysis, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved analysis to {filepath}")
        return filepath

    def save_stance_network(
        self,
        model_name: str,
        case_id: str,
        stances: Dict[str, str],
        transitions: List[Dict[str, Any]]
    ) -> str:
        """
        Save stance progression/network data.

        Args:
            model_name: Name of the model
            case_id: Case identifier
            stances: Dict of node -> stance
            transitions: List of stance transitions

        Returns:
            Path to saved file
        """
        model_dir = os.path.join(self.base_dir, self._sanitize_filename(model_name), "stances")
        filename = f"{self._sanitize_filename(case_id)}_stance.json"
        filepath = os.path.join(model_dir, filename)

        stance_data = {
            'stances': stances,
            'transitions': transitions,
            'summary': self._generate_stance_summary(stances, transitions)
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(stance_data, f, indent=2)

        logger.info(f"Saved stance network to {filepath}")
        return filepath

    def _generate_stance_summary(
        self,
        stances: Dict[str, str],
        transitions: List[Dict[str, Any]]
    ) -> str:
        """
        Generate a text summary of stance progression.

        Args:
            stances: Dict of node -> stance
            transitions: List of stance transitions

        Returns:
            Summary string
        """
        nodes = ['N1', 'N2', 'N3', 'C']
        stance_sequence = [stances.get(n, 'Unknown') for n in nodes if n in stances]

        summary = f"Stance progression: {' -> '.join(stance_sequence)}\n"

        flip_count = sum(1 for t in transitions if t.get('changed', False))
        summary += f"Total stance changes: {flip_count}"

        return summary

    def _make_serializable(self, obj: Any) -> Any:
        """
        Recursively convert object to JSON-serializable format.

        Args:
            obj: Object to convert

        Returns:
            JSON-serializable version
        """
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        else:
            return str(obj)

    def save_score_matrix(
        self,
        score_data: List[Dict[str, Any]],
        filename: str = None
    ) -> str:
        """
        Save the complete score matrix as CSV.

        Args:
            score_data: List of score dictionaries with keys:
                       Model, CaseID, Awareness, Consistency, Ethics_vs_Profit, Contradiction
            filename: Optional custom filename (defaults to score_matrix.csv)

        Returns:
            Path to saved file
        """
        if filename is None:
            filename = f"score_matrix_{self.timestamp}.csv"

        filepath = os.path.join(self.base_dir, filename)

        df = pd.DataFrame(score_data)

        # Reorder columns for clarity
        column_order = ['Model', 'CaseID', 'Awareness', 'Consistency',
                       'Ethics_vs_Profit', 'Contradiction']
        df = df[column_order]

        # Save to CSV
        df.to_csv(filepath, index=False, encoding='utf-8')

        logger.info(f"Saved score matrix to {filepath}")
        logger.info(f"Score matrix shape: {df.shape}")

        # Also save summary statistics
        self._save_summary_statistics(df, filepath.replace('.csv', '_summary.txt'))

        return filepath

    def _save_summary_statistics(self, df: pd.DataFrame, filepath: str) -> None:
        """
        Save summary statistics for the score matrix.

        Args:
            df: Score matrix DataFrame
            filepath: Path to save summary
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("SCORE MATRIX SUMMARY STATISTICS\n")
            f.write("=" * 80 + "\n\n")

            # Overall statistics
            f.write("Overall Statistics (all models, all cases):\n")
            f.write("-" * 80 + "\n")
            score_cols = ['Awareness', 'Consistency', 'Ethics_vs_Profit', 'Contradiction']
            f.write(df[score_cols].describe().to_string())
            f.write("\n\n")

            # Per-model statistics
            f.write("Per-Model Statistics:\n")
            f.write("-" * 80 + "\n")
            for model in df['Model'].unique():
                model_df = df[df['Model'] == model]
                f.write(f"\nModel: {model}\n")
                f.write(model_df[score_cols].describe().to_string())
                f.write("\n")

            # Model rankings
            f.write("\n\nModel Rankings (by average score):\n")
            f.write("-" * 80 + "\n")
            for dimension in score_cols:
                f.write(f"\n{dimension}:\n")
                rankings = df.groupby('Model')[dimension].mean().sort_values(ascending=False)
                for rank, (model, score) in enumerate(rankings.items(), 1):
                    f.write(f"  {rank}. {model}: {score:.3f}\n")

        logger.info(f"Saved summary statistics to {filepath}")

    def save_complete_results(
        self,
        model_name: str,
        case_id: str,
        case_description: str,
        queries: Dict[str, str],
        responses: Dict[str, str],
        conversation_analysis: Dict[str, Any],
        scores: Dict[str, float]
    ) -> Dict[str, str]:
        """
        Save all results for a single model-case evaluation.

        Args:
            model_name: Name of the model
            case_id: Case identifier
            case_description: Description of the case
            queries: Dict of node -> query text
            responses: Dict of node -> response text
            conversation_analysis: Complete analysis from NLPAnalyzer
            scores: Score dictionary

        Returns:
            Dictionary of saved file paths
        """
        saved_files = {}

        # Save conversation
        saved_files['conversation'] = self.save_conversation(
            model_name, case_id, case_description, queries, responses
        )

        # Save analysis
        saved_files['analysis'] = self.save_analysis(
            model_name, case_id, conversation_analysis
        )

        # Save stance network
        saved_files['stance'] = self.save_stance_network(
            model_name,
            case_id,
            conversation_analysis.get('stances', {}),
            conversation_analysis.get('stance_transitions', [])
        )

        return saved_files


# Example usage and testing
if __name__ == "__main__":
    print("OutputSaver module loaded successfully")
    print("\nExample usage:")
    print("saver = OutputSaver()")
    print("saver.create_output_structure(['GPT-4', 'Claude', 'Gemini'])")
    print("saver.save_conversation(model_name, case_id, description, queries, responses)")
    print("saver.save_score_matrix(score_data)")
