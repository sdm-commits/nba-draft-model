# 🏀 NBA Draft Oracle

An ML-powered NBA draft projection model that predicts future NBA success from college basketball performance data.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![XGBoost](https://img.shields.io/badge/XGBoost-2.0+-green.svg)

## 🎯 Overview

NBA Draft Oracle uses machine learning to project which college basketball players will become NBA stars. The model is trained on 15 years of college data (2010-2024) and validated using walk-forward backtesting against actual NBA career outcomes.

**Live Demo**: [NBA Draft Model]](https://nba-draft-model.streamlit.app/)

## 📊 Model Performance

| Metric | Value |
|--------|-------|
| Average Correlation | 0.41 |
| Mean Absolute Error | 3.7 VORP |
| Top 10 Overlap | 5.2/10 |
| Star Recall | 39% |

### Backtest Results (2015-2023)

The model was validated using strict walk-forward methodology — for each draft year, the model only sees data from previous years (no data leakage).

| Year | Correlation | Top 10 Overlap | Hits | Busts |
|------|-------------|----------------|------|-------|
| 2019 | 0.64 | 5/10 | 4 | 3 |
| 2021 | 0.61 | 5/10 | 2 | 1 |
| 2022 | 0.61 | 7/10 | 0 | 3 |
| 2018 | 0.41 | 6/10 | 5 | 0 |

### High-Profile Predictions

**✅ Hits:**
- Ja Morant (2019): Predicted 12.4, Actual 11.4 VORP
- Trae Young (2018): Predicted 25.0, Actual 18.7 VORP
- Jayson Tatum (2017): Predicted 16.3, Actual 29.1 VORP

**❌ Known Misses:**
- Shai Gilgeous-Alexander: Predicted 2.4, Actual 28.2 VORP
- Donovan Mitchell: Predicted -0.9, Actual 24.7 VORP
- Devin Booker: Predicted -0.5, Actual 17.9 VORP

## 🔬 Methodology

### Target Variable

**Career VORP** (Value Over Replacement Player) — cumulative contribution across a player's NBA career. This captures both star potential and longevity.

### Key Features

| Feature | Correlation | Description |
|---------|-------------|-------------|
| Age-Adjusted BPM | +0.28 | BPM scaled by experience (younger = higher multiplier) |
| Size-Skill Score | +0.21 | Height × BPM interaction |
| BPM Max | +0.21 | Best Box Plus/Minus season |
| Conference-Adjusted BPM | +0.21 | BPM normalized by conference strength |
| Recruit Score | +0.15 | High school recruiting ranking |

### Age Adjustment Formula

Younger players with the same college production are more valuable:

```python
age_adjusted_bpm = bpm_max * (1.4 - (years_exp * 0.15))
# Freshman (1 yr): 1.25x multiplier
# Sophomore (2 yr): 1.10x multiplier
# Junior (3 yr): 0.95x multiplier
# Senior (4 yr): 0.80x multiplier
```

### Model Architecture

1. **Classifier**: XGBoost with calibration → Star probability (VORP > 3)
2. **Regressor**: XGBoost → VORP magnitude prediction
3. **Scout Adjustments**: Rule-based multipliers for archetypes (freshman phenoms, shot creators, etc.)

## 🚀 Features

### Interactive Dashboard

- **Board View**: Card-based display of top prospects with images and key stats
- **Chart View**: Scatter plot of Usage vs Star Probability/Age-Adjusted BPM
- **Results View**: Compare predictions to actual draft outcomes and rookie stats
- **Table View**: Full sortable draft board
- **Model View**: Backtest metrics and methodology explanation

### Filters

- Draft class selection (2024, 2025, 2026)
- Archetype filtering (Elite Producer, Two-Way Wing, etc.)
- Player search

## 📁 Project Structure

```
nba-draft-oracle/
├── app.py                              # Streamlit application
├── all_draft_predictions_2024_2026.csv # Model predictions
├── requirements.txt                    # Python dependencies
├── README.md                           # This file
```

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- pip

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/nba-draft-oracle.git
cd nba-draft-oracle

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

### Requirements

```
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
plotly>=5.18.0
nba_api>=1.4.1
```

## 📈 Data Sources

- **College Stats**: [Barttorvik](https://barttorvik.com/) (2010-2025)
- **NBA Outcomes**: Basketball Reference VORP data
- **Player Images**: NBA.com CDN
- **Draft History**: NBA API

## ⚠️ Known Limitations

1. **Shot-creating guards undervalued**: The model struggles with guards who create their own offense (Edwards, Booker, Mitchell, SGA, Brunson). These players often have lower BPM in college but develop elite scoring ability in the NBA.

2. **Injury risk not modeled**: Predictions assume full health. Players like Zion Williamson show high predicted value but injury concerns aren't captured.

3. **Mid-major translation**: Some mid-major stars (Siakam, Jalen Williams) outperform predictions because their competition level is discounted too heavily.

4. **Rookie stats ≠ career value**: Recent draft classes (2023-2024) only have rookie stats available, which are poor predictors of career outcomes.

## 🔮 Future Improvements

- [ ] Model injury risk separately
- [ ] Ensemble with mock draft consensus
- [ ] Historical player comps (e.g., "plays like young SGA")
- [ ] Add prospect comparison tool
- [ ] Ensemble with mock draft consensus

## 📝 License

MIT License — feel free to use and modify.

## 🙏 Acknowledgments

- [Barttorvik](https://barttorvik.com/) for comprehensive college basketball data
- [nba_api](https://github.com/swar/nba_api) for NBA statistics access
- Basketball analytics community for research and inspiration

---

**Built with** ❤️ **using Python, XGBoost, and Streamlit**
