# Quick Start Guide

Get up and running with the Adaptive Ethical Evaluation Protocol in 10 minutes.

---

## Prerequisites

- Python 3.8 or higher
- API keys for LLMs you want to evaluate (OpenAI, Anthropic, Google, etc.)
- 4GB+ RAM (8GB recommended)
- Internet connection

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/upocuantitativo/ethicalgorithm.git
cd ethicalgorithm
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Download NLP Models

```bash
python -m spacy download en_core_web_sm
python -c "import nltk; nltk.download('vader_lexicon')"
```

### 4. Configure API Keys

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```
OPENAI_API_KEY=sk-...your-key-here...
ANTHROPIC_API_KEY=sk-ant-...your-key-here...
GOOGLE_API_KEY=...your-key-here...
```

---

## Run Your First Evaluation

### Option 1: Use Example Cases

```bash
python main.py --cases examples/example_cases.json --models gpt-4 claude-3
```

This evaluates GPT-4 and Claude-3 on the provided example ethical dilemmas.

### Option 2: Create Custom Cases

1. Copy the example template:

```bash
cp examples/example_cases.json my_cases.json
```

2. Edit `my_cases.json` with your ethical dilemmas

3. Run evaluation:

```bash
python main.py --cases my_cases.json --models gpt-4 claude-3 gemini-pro
```

---

## Understanding Output

The evaluation generates several files in the `outputs/` directory:

```
outputs/
├── score_matrix.csv           # Quantitative scores (all models × cases)
├── gpt-4/
│   ├── conversations/
│   │   └── CASE001_dialogue.txt  # Complete Q&A transcript
│   ├── analysis/
│   │   └── CASE001_analysis.json # NLP metrics
│   └── stances/
│       └── CASE001_stances.json  # Stance progression
└── claude-3/
    └── ... (same structure)
```

### Viewing Scores

```bash
# View score matrix
cat outputs/score_matrix.csv

# Or load in Python
python -c "import pandas as pd; print(pd.read_csv('outputs/score_matrix.csv'))"
```

### Reading Dialogues

```bash
# View a specific conversation
cat outputs/gpt-4/conversations/CASE001_dialogue.txt
```

---

## Generating Expert Validation Survey

To validate your results with human experts:

### 1. Extract Dialogues

```bash
cd survey_generator
python extract_dialogues.py --input ../outputs/score_matrix.csv --output survey_dialogues.json
```

### 2. Generate Survey HTML

```bash
python generate_survey.py \
    --input survey_dialogues.json \
    --output expert_survey.html \
    --email your-email@institution.edu \
    --title "My Ethics Study Validation"
```

### 3. Distribute Survey

- Send `expert_survey.html` to experts
- They open it in a web browser
- Survey auto-saves progress
- Submissions sent to your email

See `docs/VALIDATION_GUIDE.md` for expert panel methodology.

---

## Visualizing Results

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load scores
scores = pd.read_csv('outputs/score_matrix.csv')

# Plot comparison
scores.groupby('Model').mean().plot(kind='bar', figsize=(12, 6))
plt.title('Model Comparison Across Ethical Indicators')
plt.ylabel('Score (0-1)')
plt.legend(title='Indicator')
plt.tight_layout()
plt.savefig('model_comparison.png')
plt.show()
```

---

## Common Issues

### Issue: API Rate Limits

**Error:** `RateLimitError: You exceeded your API quota`

**Solution:** Add delays between API calls in `config.py`:

```python
API_DELAY_SECONDS = 2.0  # Wait 2 seconds between calls
```

### Issue: NLP Model Not Found

**Error:** `OSError: Can't find model 'en_core_web_sm'`

**Solution:** Download spaCy model:

```bash
python -m spacy download en_core_web_sm
```

### Issue: Out of Memory

**Error:** `MemoryError` or system slowdown

**Solution:**
- Evaluate fewer models at once
- Reduce batch size in `config.py`
- Use GPU if available (set `USE_GPU = True`)

---

## Next Steps

- **Customize Scoring:** Edit `modules/scoring.py` to adjust indicator weights
- **Add Models:** Update `modules/model_api.py` to support new LLM providers
- **Advanced Analysis:** See `notebooks/` for Jupyter analysis templates
- **Validation:** Read `docs/VALIDATION_GUIDE.md` for expert panel setup

---

## Getting Help

- **Documentation:** See `docs/` directory
- **Issues:** [GitHub Issues](https://github.com/upocuantitativo/ethicalgorithm/issues)
- **Email:** mchaves@upo.es

---

## Example Session

```bash
# Full workflow example
git clone https://github.com/upocuantitativo/ethicalgorithm.git
cd ethicalgorithm

pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Add API keys to .env file
nano .env

# Run evaluation
python main.py --cases examples/example_cases.json --models gpt-4 claude-3

# View results
cat outputs/score_matrix.csv

# Generate validation survey
cd survey_generator
python extract_dialogues.py --input ../outputs/score_matrix.csv --output dialogues.json
python generate_survey.py --input dialogues.json --output survey.html --email me@university.edu

# Done! Send survey.html to experts
```

---

**Estimated time:** 10-15 minutes for setup + runtime depends on number of models/cases (typically 5-10 minutes per model-case pair due to API latency).
