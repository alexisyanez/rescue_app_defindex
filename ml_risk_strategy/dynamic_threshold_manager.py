# rescue-bot/apps/rescue_bot/ml_risk_strategy/dynamic_threshold_manager.py
import numpy as np

class DynamicThresholdManager:
    def __init__(self, initial_threshold: float = 0.5):
        self.current_threshold = initial_threshold
        # Stores historical risk scores and outcomes to dynamically adjust the threshold.[2, 3]
        self.historical_risk_scores ={}
        self.historical_outcomes ={} # True if rescue was needed/approved, False otherwise

    def update_threshold(self, new_risk_scores: list[float], new_outcomes: list[bool]):
        """
        Dynamically adjusts the threshold based on recent historical risk scores and actual outcomes.
        This can be a simple percentile-based adjustment or informed by a more complex Reinforcement Learning approach.[2, 3, 27, 29, 36]
        """
        self.historical_risk_scores.extend(new_risk_scores)
        self.historical_outcomes.extend(new_outcomes)

        # Keep a rolling window of recent data for threshold calculation
        window_size = 200 # Example: use last 200 data points
        if len(self.historical_risk_scores) > window_size:
            recent_scores = np.array(self.historical_risk_scores[-window_size:])
            recent_outcomes = np.array(self.historical_outcomes[-window_size:])
        else:
            recent_scores = np.array(self.historical_risk_scores)
            recent_outcomes = np.array(self.historical_outcomes)

        if len(recent_scores) > 0 and len(recent_outcomes) > 0:
            # Simple example: Set threshold as a percentile of risk scores where rescue was actually needed.
            # This is a heuristic. A more advanced approach would involve optimizing this threshold
            # using techniques like Reinforcement Learning to balance false positives/negatives.
            if np.any(recent_outcomes): # Only if there are actual rescue events
                scores_for_needed_rescue = recent_scores
                if len(scores_for_needed_rescue) > 0:
                    # Set threshold at a percentile (e.g., 25th percentile) of scores that historically led to rescue.
                    # This aims to catch similar situations earlier.
                    self.current_threshold = np.percentile(scores_for_needed_rescue, 25)
            else:
                # If no rescue events, perhaps default to a conservative percentile of all scores
                self.current_threshold = np.percentile(recent_scores, 95) # High percentile to be cautious
        else:
            self.current_threshold = self.initial_threshold # Fallback to initial if no data

        print(f"Dynamic threshold updated to: {self.current_threshold:.4f}")

    def get_threshold(self) -> float:
        """Returns the current dynamic risk threshold."""
        return self.current_threshold

    def determine_action(self, predicted_risk_score: float) -> bool:
        """
        Compares the predicted risk score against the dynamic threshold to determine if an alert is needed.
        """
        return predicted_risk_score >= self.current_threshold