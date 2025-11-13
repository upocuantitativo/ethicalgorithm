"""
Main Execution Script for Adaptive Ethical Evaluation Algorithm
Orchestrates the complete evaluation process across multiple models and cases.
"""

import os
import sys
from typing import List, Dict, Any
import logging
from tqdm import tqdm
import pandas as pd

# Add modules directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

from modules.case_loader import CaseLoader
from modules.query_generator import AdaptiveQueryGenerator
from modules.model_api import ModelAPIHandler
from modules.nlp_analyzer import NLPAnalyzer
from modules.scoring import ScoringModule
from modules.output_saver import OutputSaver
from config import MODEL_CONFIGS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EthicalEvaluationPipeline:
    """
    Main pipeline for adaptive ethical evaluation of language models.
    Implements the complete Algorithm 1 from the research paper.
    """

    def __init__(
        self,
        cases_file: str,
        model_list: List[str],
        output_dir: str = "outputs"
    ):
        """
        Initialize the evaluation pipeline.

        Args:
            cases_file: Path to Excel/CSV file containing ethical cases
            model_list: List of model names to evaluate
            output_dir: Directory for output files
        """
        self.cases_file = cases_file
        self.model_list = model_list
        self.output_dir = output_dir

        # Initialize all modules
        logger.info("Initializing evaluation pipeline...")
        self.case_loader = CaseLoader(cases_file)
        self.query_generator = AdaptiveQueryGenerator()
        self.api_handler = ModelAPIHandler()
        self.nlp_analyzer = NLPAnalyzer()
        self.scorer = ScoringModule()
        self.output_saver = OutputSaver(output_dir)

        # Storage for all results
        self.all_responses = {}
        self.all_analyses = {}
        self.all_scores = []

    def load_cases(self) -> List[Dict[str, Any]]:
        """
        Load ethical cases from file.

        Returns:
            List of case dictionaries
        """
        logger.info(f"Loading cases from {self.cases_file}...")
        cases = self.case_loader.load_cases()
        logger.info(f"Loaded {len(cases)} cases successfully")
        return cases

    def evaluate_model_on_case(
        self,
        model_name: str,
        case: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate a single model on a single case using adaptive questioning.
        Implements the core adaptive algorithm (Algorithm 1).

        Args:
            model_name: Name of the model to evaluate
            case: Case dictionary

        Returns:
            Dictionary containing all evaluation results
        """
        case_id = case['CaseID']
        logger.info(f"Evaluating {model_name} on case {case_id}...")

        # Get model configuration
        model_config = MODEL_CONFIGS.get(model_name, {
            "temperature": 0.7,
            "max_tokens": 512
        })

        # Storage for this evaluation
        queries = {}
        responses = {}
        context = []

        try:
            # === NODE 1: Initial Query ===
            logger.info(f"  Node 1: Initial ambiguous query...")
            queries['N1'] = self.query_generator.formulate_query_n1(case)

            responses['N1'] = self.api_handler.call_model_api(
                model_name=model_name,
                prompt=queries['N1'],
                temperature=model_config.get('temperature', 0.7),
                max_tokens=model_config.get('max_tokens', 512)
            )

            # Classify initial stance
            stance1 = self.nlp_analyzer.classify_stance(responses['N1'])
            logger.info(f"  Initial stance: {stance1}")

            # Update context
            context.append(f"Q1: {queries['N1']}")
            context.append(f"A1: {responses['N1']}")

            # === NODE 2: Adaptive Counter-Question ===
            logger.info(f"  Node 2: Adaptive counter-question (path based on {stance1})...")
            queries['N2'] = self.query_generator.formulate_query_n2(case, stance1)

            responses['N2'] = self.api_handler.call_model_api(
                model_name=model_name,
                prompt=queries['N2'],
                context=context.copy(),
                temperature=model_config.get('temperature', 0.7),
                max_tokens=model_config.get('max_tokens', 512)
            )

            stance2 = self.nlp_analyzer.classify_stance(responses['N2'])
            logger.info(f"  Stance after counter: {stance2}")

            # Update context
            context.append(f"Q2: {queries['N2']}")
            context.append(f"A2: {responses['N2']}")

            # === NODE 3: Grey Area ===
            logger.info(f"  Node 3: Grey area exploration...")
            queries['N3'] = self.query_generator.formulate_query_n3(case, stance1)

            responses['N3'] = self.api_handler.call_model_api(
                model_name=model_name,
                prompt=queries['N3'],
                context=context.copy(),
                temperature=model_config.get('temperature', 0.7),
                max_tokens=model_config.get('max_tokens', 512)
            )

            # Update context
            context.append(f"Q3: {queries['N3']}")
            context.append(f"A3: {responses['N3']}")

            # === CONCLUSION ===
            logger.info(f"  Conclusion: Final recommendation...")
            queries['C'] = self.query_generator.formulate_conclusion_query(case)

            responses['C'] = self.api_handler.call_model_api(
                model_name=model_name,
                prompt=queries['C'],
                context=context.copy(),
                temperature=model_config.get('temperature', 0.7),
                max_tokens=model_config.get('max_tokens', 512)
            )

            stance_final = self.nlp_analyzer.classify_stance(responses['C'])
            logger.info(f"  Final stance: {stance_final}")

            # === ANALYSIS ===
            logger.info(f"  Analyzing conversation...")
            conversation_analysis = self.nlp_analyzer.analyze_conversation(responses)

            # === SCORING ===
            logger.info(f"  Computing scores...")
            scores = self.scorer.score_all_dimensions(conversation_analysis)

            # === SAVE RESULTS ===
            logger.info(f"  Saving results...")
            self.output_saver.save_complete_results(
                model_name=model_name,
                case_id=case_id,
                case_description=case['Description'],
                queries=queries,
                responses=responses,
                conversation_analysis=conversation_analysis,
                scores=scores
            )

            # Prepare result summary
            result = {
                'model': model_name,
                'case_id': case_id,
                'queries': queries,
                'responses': responses,
                'analysis': conversation_analysis,
                'scores': scores,
                'success': True
            }

            logger.info(f"  Completed: {scores}")
            return result

        except Exception as e:
            logger.error(f"Error evaluating {model_name} on {case_id}: {e}")
            return {
                'model': model_name,
                'case_id': case_id,
                'success': False,
                'error': str(e)
            }

    def run_evaluation(self) -> pd.DataFrame:
        """
        Run the complete evaluation across all models and cases.

        Returns:
            DataFrame containing the score matrix
        """
        # Load cases
        cases = self.load_cases()

        # Create output structure
        self.output_saver.create_output_structure(self.model_list)

        # Initialize score data storage
        score_data = []

        # Total iterations for progress bar
        total_iterations = len(self.model_list) * len(cases)

        # Evaluate each model on each case
        with tqdm(total=total_iterations, desc="Overall Progress") as pbar:
            for model_name in self.model_list:
                logger.info(f"\n{'='*80}")
                logger.info(f"Evaluating model: {model_name}")
                logger.info(f"{'='*80}\n")

                for case in cases:
                    case_id = case['CaseID']

                    # Run evaluation
                    result = self.evaluate_model_on_case(model_name, case)

                    # Store results
                    if result['success']:
                        scores = result['scores']
                        score_data.append({
                            'Model': model_name,
                            'CaseID': case_id,
                            'Awareness': scores['awareness'],
                            'Consistency': scores['consistency'],
                            'Ethics_vs_Profit': scores['ethics_vs_profit'],
                            'Contradiction': scores['contradiction']
                        })

                        # Store for later access
                        key = f"{model_name}_{case_id}"
                        self.all_responses[key] = result['responses']
                        self.all_analyses[key] = result['analysis']
                    else:
                        # Record failure
                        score_data.append({
                            'Model': model_name,
                            'CaseID': case_id,
                            'Awareness': None,
                            'Consistency': None,
                            'Ethics_vs_Profit': None,
                            'Contradiction': None
                        })

                    pbar.update(1)

        # Save final score matrix
        logger.info("\nSaving final score matrix...")
        score_matrix_path = self.output_saver.save_score_matrix(score_data)

        logger.info(f"\n{'='*80}")
        logger.info("EVALUATION COMPLETE")
        logger.info(f"{'='*80}")
        logger.info(f"Score matrix saved to: {score_matrix_path}")
        logger.info(f"Individual results saved in: {self.output_dir}")

        # Return as DataFrame
        return pd.DataFrame(score_data)


def main():
    """
    Main entry point for the evaluation script.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='Adaptive Ethical Evaluation Algorithm for Language Models'
    )
    parser.add_argument(
        '--cases',
        type=str,
        required=True,
        help='Path to Excel/CSV file containing ethical cases'
    )
    parser.add_argument(
        '--models',
        type=str,
        nargs='+',
        default=['gpt-3.5-turbo'],
        help='List of model names to evaluate (e.g., gpt-4 claude-v1 gemini-pro)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='outputs',
        help='Output directory for results (default: outputs)'
    )

    args = parser.parse_args()

    # Validate cases file exists
    if not os.path.exists(args.cases):
        logger.error(f"Cases file not found: {args.cases}")
        sys.exit(1)

    # Initialize and run pipeline
    pipeline = EthicalEvaluationPipeline(
        cases_file=args.cases,
        model_list=args.models,
        output_dir=args.output
    )

    # Run evaluation
    score_matrix = pipeline.run_evaluation()

    # Display summary
    print("\n" + "="*80)
    print("SCORE MATRIX SUMMARY")
    print("="*80)
    print(score_matrix.groupby('Model').mean())
    print("="*80)


if __name__ == "__main__":
    main()
