# rescue-bot/apps/rescue_bot/ml_risk_strategy/feature_engineer.py
import pandas as pd
import numpy as np
# from ta import add_all_ta_features # Example for technical indicators

class FeatureEngineer:
    def __init__(self):
        pass

    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generates predictive features from preprocessed time series data.
        This includes lag features, rolling window statistics, time-based features,
        and potentially technical indicators and custom risk ratios.[19, 20, 21, 22, 24]
        """
        df_fe = df.copy()

        # Lag Features: Explicitly incorporating past values to provide context.[19, 24]
        # These capture short-term dependencies and cyclical patterns.
        df_fe['collateral_value_lag_1'] = df_fe['collateral_value'].shift(1)
        df_fe['debt_value_lag_1'] = df_fe['debt_value'].shift(1)
        df_fe['collateral_value_lag_7'] = df_fe['collateral_value'].shift(7) # Example for weekly patterns
        df_fe['debt_value_lag_7'] = df_fe['debt_value'].shift(7)

        # Rolling Window Statistics: Capturing trends and volatility over time.[19, 24]
        # Higher rolling standard deviation can signal increased market uncertainty.[19]
        df_fe['collateral_rolling_mean_7d'] = df_fe['collateral_value'].rolling(window=7).mean()
        df_fe['collateral_rolling_std_7d'] = df_fe['collateral_value'].rolling(window=7).std()
        df_fe['debt_rolling_mean_7d'] = df_fe['debt_value'].rolling(window=7).mean()
        df_fe['debt_rolling_std_7d'] = df_fe['debt_value'].rolling(window=7).std()
        # Additional rolling features like min, max, median, or sum can be added.

        # Time-Based Features (Sine-Cosine Encoding for cyclicality).[19, 20]
        # This preserves the cyclical nature of time and ensures models recognize adjacency.
        if isinstance(df_fe.index, pd.DatetimeIndex):
            df_fe['hour_sin'] = np.sin(2 * np.pi * df_fe.index.hour / 24)
            df_fe['hour_cos'] = np.cos(2 * np.pi * df_fe.index.hour / 24)
            df_fe['day_of_week_sin'] = np.sin(2 * np.pi * df_fe.index.dayofweek / 7)
            df_fe['day_of_week_cos'] = np.cos(2 * np.pi * df_fe.index.dayofweek / 7)
            df_fe['day_of_month_sin'] = np.sin(2 * np.pi * df_fe.index.day / 31)
            df_fe['day_of_month_cos'] = np.cos(2 * np.pi * df_fe.index.day / 31)
            df_fe['month_sin'] = np.sin(2 * np.pi * df_fe.index.month / 12)
            df_fe['month_cos'] = np.cos(2 * np.pi * df_fe.index.month / 12)
            df_fe['is_weekend'] = ((df_fe.index.dayofweek == 5) | (df_fe.index.dayofweek == 6)).astype(int)
            # Holiday features could also be added if a holiday calendar is available.

        # Custom Risk Ratio: Directly derived from contract logic, provides immediate risk signals.
        if 'collateral_value' in df_fe.columns and 'debt_value' in df_fe.columns:
            # Add a small epsilon to debt_value to avoid division by zero
            epsilon = 1e-9
            df_fe['collateral_to_debt_ratio'] = df_fe['collateral_value'] / (df_fe['debt_value'] + epsilon)
            # Handle potential inf values that might arise from very small debt values
            df_fe['collateral_to_debt_ratio'].replace([np.inf, -np.inf], np.nan, inplace=True)
            df_fe['collateral_to_debt_ratio'].fillna(df_fe['collateral_to_debt_ratio'].mean(), inplace=True) # Or a domain-specific fill

        # Technical Indicators (Conceptual): Requires specific financial data like price or volume.[22, 24]
        # If 'price' data is available for the underlying assets:
        # df_fe = add_all_ta_features(df_fe, open="open", high="high", low="low", close="price", volume="volume", fillna=True)
        # For example, Relative Strength Index (RSI) or Moving Average Convergence Divergence (MACD) can be calculated.

        # Drop rows with NaN values resulting from lagging or rolling operations, as these cannot be used for training.
        return df_fe.dropna()