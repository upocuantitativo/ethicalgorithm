"""
Adaptive Ethical Evaluation Algorithm - Modules Package
"""

from .case_loader import CaseLoader
from .query_generator import AdaptiveQueryGenerator
from .model_api import ModelAPIHandler
from .nlp_analyzer import NLPAnalyzer
from .scoring import ScoringModule
from .output_saver import OutputSaver

__all__ = [
    'CaseLoader',
    'AdaptiveQueryGenerator',
    'ModelAPIHandler',
    'NLPAnalyzer',
    'ScoringModule',
    'OutputSaver'
]

__version__ = '1.0.0'
