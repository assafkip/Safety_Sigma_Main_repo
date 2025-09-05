from __future__ import annotations

def score_from_metrics(fp_rate: float, tp_rate: float, samples: int) -> float:
    """Calculate confidence score from backtest metrics with transparent composite scoring.
    
    Args:
        fp_rate: False positive rate (0.0-1.0)
        tp_rate: True positive rate (0.0-1.0) 
        samples: Number of samples tested
        
    Returns:
        Confidence score (0.0-1.0) rounded to 3 decimal places
    """
    # Simple, transparent composite: penalize FPR and low samples
    base = max(0.0, min(1.0, 1.0 - fp_rate))  # Invert FPR for base score
    sample_factor = min(1.0, samples / 100.0)  # Full credit at 100+ samples
    
    # Weighted combination: 80% FPR penalty, 20% TPR bonus, scaled by sample confidence
    score = (base * 0.8 + tp_rate * 0.2) * sample_factor
    
    return round(score, 3)