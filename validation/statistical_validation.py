"""
Statistical Validation Metrics for Expert-Algorithm Concordance

This module computes validation metrics comparing algorithm scores
with expert panel ratings.

Metrics computed:
- Agreement rate (with tolerance)
- Cohen's Kappa
- Pearson correlation
- Fleiss' Kappa (inter-rater reliability)
- Mean Absolute Error (MAE)
- Confusion matrices and disagreement analysis

Usage:
    from validation.statistical_validation import compute_metrics

    metrics = compute_metrics(algo_scores, expert_scores)
    print(f"Agreement: {metrics['agreement_rate']:.1%}")
    print(f"Cohen's kappa: {metrics['cohens_kappa']:.3f}")
"""

import pandas as pd
import numpy as np
from sklearn.metrics import cohen_kappa_score, confusion_matrix
from scipy.stats import pearsonr, spearmanr
from typing import Dict, List, Tuple

def compute_agreement_rate(algo_scores: pd.DataFrame,
                           expert_scores: pd.DataFrame,
                           tolerance: float = 0.5) -> float:
    """
    Compute percentage agreement within tolerance

    Args:
        algo_scores: DataFrame with columns [CaseID, Model, Indicator, Score]
        expert_scores: DataFrame with columns [ExpertID, CaseID, Model, Indicator, Score]
        tolerance: Maximum difference to count as agreement (default 0.5 on 0-10 scale)

    Returns:
        Agreement rate as proportion (0-1)
    """
    # Compute expert consensus (mean across experts)
    expert_consensus = expert_scores.groupby(['CaseID', 'Model', 'Indicator'])['Score'].mean().reset_index()
    expert_consensus.rename(columns={'Score': 'ExpertScore'}, inplace=True)

    # Merge with algorithm scores
    merged = algo_scores.merge(expert_consensus, on=['CaseID', 'Model', 'Indicator'])

    # Compute agreement
    merged['agree'] = (np.abs(merged['Score'] - merged['ExpertScore']) <= tolerance).astype(int)

    return merged['agree'].mean()

def compute_cohens_kappa(algo_scores: pd.DataFrame,
                         expert_scores: pd.DataFrame,
                         bins: int = 3) -> float:
    """
    Compute Cohen's Kappa after discretizing scores

    Args:
        algo_scores: Algorithm scores
        expert_scores: Expert panel scores (will use mean consensus)
        bins: Number of bins for discretization (default 3: Low/Medium/High)

    Returns:
        Cohen's kappa coefficient
    """
    # Expert consensus
    expert_consensus = expert_scores.groupby(['CaseID', 'Model', 'Indicator'])['Score'].mean().reset_index()

    # Merge
    merged = algo_scores.merge(expert_consensus, on=['CaseID', 'Model', 'Indicator'], suffixes=('_algo', '_expert'))

    # Discretize into bins
    algo_discrete = pd.cut(merged['Score_algo'], bins=bins, labels=False)
    expert_discrete = pd.cut(merged['Score_expert'], bins=bins, labels=False)

    return cohen_kappa_score(expert_discrete, algo_discrete)

def compute_pearson_correlation(algo_scores: pd.DataFrame,
                                expert_scores: pd.DataFrame) -> Tuple[float, float]:
    """
    Compute Pearson correlation coefficient

    Returns:
        (correlation coefficient, p-value)
    """
    expert_consensus = expert_scores.groupby(['CaseID', 'Model', 'Indicator'])['Score'].mean().reset_index()

    merged = algo_scores.merge(expert_consensus, on=['CaseID', 'Model', 'Indicator'], suffixes=('_algo', '_expert'))

    r, p = pearsonr(merged['Score_algo'], merged['Score_expert'])

    return r, p

def compute_mae(algo_scores: pd.DataFrame,
                expert_scores: pd.DataFrame) -> float:
    """
    Compute Mean Absolute Error

    Returns:
        MAE value
    """
    expert_consensus = expert_scores.groupby(['CaseID', 'Model', 'Indicator'])['Score'].mean().reset_index()

    merged = algo_scores.merge(expert_consensus, on=['CaseID', 'Model', 'Indicator'], suffixes=('_algo', '_expert'))

    return np.abs(merged['Score_algo'] - merged['Score_expert']).mean()

def compute_fleiss_kappa(expert_scores: pd.DataFrame) -> float:
    """
    Compute Fleiss' Kappa for inter-rater reliability among experts

    Args:
        expert_scores: Expert panel scores with ExpertID column

    Returns:
        Fleiss' kappa coefficient
    """
    # Pivot to matrix format: rows = (CaseID, Model, Indicator), columns = Experts
    pivot = expert_scores.pivot_table(
        index=['CaseID', 'Model', 'Indicator'],
        columns='ExpertID',
        values='Score',
        aggfunc='first'
    )

    n_items = len(pivot)  # Number of items rated
    n_raters = len(pivot.columns)  # Number of raters

    # Discretize scores into categories (0-3 = Low, 4-6 = Medium, 7-10 = High)
    pivot_discrete = pivot.apply(lambda col: pd.cut(col, bins=[0, 3.5, 6.5, 10], labels=[0, 1, 2]))

    # Compute category counts for each item
    categories = [0, 1, 2]
    category_counts = np.zeros((n_items, len(categories)))

    for i, (idx, row) in enumerate(pivot_discrete.iterrows()):
        for j, cat in enumerate(categories):
            category_counts[i, j] = (row == cat).sum()

    # Compute P_i (agreement proportion for each item)
    P_i = np.sum(category_counts ** 2, axis=1) - n_raters
    P_i = P_i / (n_raters * (n_raters - 1))

    # Mean agreement
    P_mean = P_i.mean()

    # Compute expected agreement
    p_j = category_counts.sum(axis=0) / (n_items * n_raters)  # Proportion in each category
    P_e = np.sum(p_j ** 2)

    # Fleiss' Kappa
    if P_e == 1:
        return 1.0  # Perfect agreement

    kappa = (P_mean - P_e) / (1 - P_e)

    return kappa

def compute_metrics(algo_scores: pd.DataFrame,
                    expert_scores: pd.DataFrame,
                    tolerance: float = 0.5) -> Dict:
    """
    Compute all validation metrics

    Args:
        algo_scores: DataFrame with columns [CaseID, Model, Indicator, Score]
        expert_scores: DataFrame with columns [ExpertID, CaseID, Model, Indicator, Score]
        tolerance: Agreement tolerance (default 0.5)

    Returns:
        Dictionary with all metrics
    """
    metrics = {}

    # Agreement rate
    metrics['agreement_rate'] = compute_agreement_rate(algo_scores, expert_scores, tolerance)

    # Cohen's Kappa
    metrics['cohens_kappa'] = compute_cohens_kappa(algo_scores, expert_scores)

    # Pearson correlation
    r, p = compute_pearson_correlation(algo_scores, expert_scores)
    metrics['pearson_r'] = r
    metrics['pearson_p'] = p

    # Mean Absolute Error
    metrics['mae'] = compute_mae(algo_scores, expert_scores)

    # Inter-rater reliability (Fleiss' Kappa)
    if 'ExpertID' in expert_scores.columns:
        metrics['irr_kappa'] = compute_fleiss_kappa(expert_scores)
    else:
        metrics['irr_kappa'] = None

    # Per-indicator breakdown
    indicators = algo_scores['Indicator'].unique()
    metrics['per_indicator'] = {}

    for indicator in indicators:
        algo_ind = algo_scores[algo_scores['Indicator'] == indicator]
        expert_ind = expert_scores[expert_scores['Indicator'] == indicator]

        metrics['per_indicator'][indicator] = {
            'agreement': compute_agreement_rate(algo_ind, expert_ind, tolerance),
            'mae': compute_mae(algo_ind, expert_ind)
        }

    return metrics

def print_metrics_report(metrics: Dict):
    """
    Print formatted validation metrics report

    Args:
        metrics: Dictionary from compute_metrics()
    """
    print("=" * 60)
    print("VALIDATION METRICS REPORT")
    print("=" * 60)
    print()

    print(f"Overall Metrics:")
    print(f"  Agreement Rate:       {metrics['agreement_rate']:.1%}")
    print(f"  Cohen's Kappa:        {metrics['cohens_kappa']:.3f}")
    print(f"  Pearson Correlation:  r = {metrics['pearson_r']:.3f} (p = {metrics['pearson_p']:.4f})")
    print(f"  Mean Absolute Error:  {metrics['mae']:.3f}")

    if metrics['irr_kappa'] is not None:
        print(f"  Inter-Rater Kappa:    {metrics['irr_kappa']:.3f}")

    print()
    print("Interpretation (Landis & Koch, 1977):")

    kappa = metrics['cohens_kappa']
    if kappa < 0.20:
        interpretation = "Slight agreement"
    elif kappa < 0.40:
        interpretation = "Fair agreement"
    elif kappa < 0.60:
        interpretation = "Moderate agreement"
    elif kappa < 0.80:
        interpretation = "Substantial agreement"
    else:
        interpretation = "Almost perfect agreement"

    print(f"  Cohen's Kappa ({kappa:.3f}): {interpretation}")

    print()
    print("Per-Indicator Metrics:")
    for indicator, ind_metrics in metrics['per_indicator'].items():
        print(f"  {indicator}:")
        print(f"    Agreement: {ind_metrics['agreement']:.1%}")
        print(f"    MAE:       {ind_metrics['mae']:.3f}")

    print()
    print("=" * 60)

def analyze_disagreements(algo_scores: pd.DataFrame,
                         expert_scores: pd.DataFrame,
                         threshold: float = 2.0) -> pd.DataFrame:
    """
    Identify cases with large disagreements

    Args:
        algo_scores: Algorithm scores
        expert_scores: Expert scores
        threshold: Difference threshold to flag (default 2.0 on 0-10 scale)

    Returns:
        DataFrame of flagged disagreements
    """
    expert_consensus = expert_scores.groupby(['CaseID', 'Model', 'Indicator'])['Score'].mean().reset_index()

    merged = algo_scores.merge(expert_consensus, on=['CaseID', 'Model', 'Indicator'], suffixes=('_algo', '_expert'))

    merged['difference'] = np.abs(merged['Score_algo'] - merged['Score_expert'])

    disagreements = merged[merged['difference'] >= threshold].copy()

    disagreements = disagreements.sort_values('difference', ascending=False)

    return disagreements[['CaseID', 'Model', 'Indicator', 'Score_algo', 'Score_expert', 'difference']]

# Example usage
if __name__ == '__main__':
    # Example data structure
    print("Example usage:")
    print()
    print("1. Load your data:")
    print("   algo_scores = pd.read_csv('outputs/score_matrix.csv')")
    print("   expert_scores = pd.read_csv('outputs/validation/expert_ratings.csv')")
    print()
    print("2. Compute metrics:")
    print("   metrics = compute_metrics(algo_scores, expert_scores)")
    print("   print_metrics_report(metrics)")
    print()
    print("3. Analyze disagreements:")
    print("   disagreements = analyze_disagreements(algo_scores, expert_scores)")
    print("   print(disagreements)")
