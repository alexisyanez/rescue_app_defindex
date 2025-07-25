# rescue-bot/apps/rescue_bot/ml_risk_strategy/risk_predictor.py
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier # [1, 4, 26]
from sklearn.metrics import classification_report, roc_auc_score, precision_recall_curve, auc
# from tensorflow.keras.models import Sequential # For LSTM
# from tensorflow.keras.layers import LSTM, Dense # For LSTM
# from tensorflow.keras.preprocessing.sequence import TimeseriesGenerator # For LSTM input formatting

class RiskPredictor:
    def __init__(self, model_type: str = 'RandomForest'):
        self.model_type = model_type
        self.model = None
        # This column needs to be explicitly labeled in historical data,
        # indicating whether a rescue was needed or occurred.[1, 32]
        self.target_column = 'is_rescue_needed' 
        self.feature_columns = {} # To be set after feature engineering

    def train_model(self, data: pd.DataFrame):
        """
        Trains the selected machine learning model using the provided data.
        The data should contain both engineered features and the 'is_rescue_needed' target column.[1, 4, 23, 25, 26]
        """
        if self.target_column not in data.columns:
            raise ValueError(f"Target column '{self.target_column}' not found in data. "
                             "Ensure historical data is properly labeled.")
        
        # Identify feature columns (all columns except the target)
        self.feature_columns = [col for col in data.columns if col!= self.target_column]
        X = data[self.feature_columns]
        y = data[self.target_column]

        # Chronological split for time series data [7, 12]
        # Reserve the most recent data for testing to avoid data leakage.
        train_size = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:train_size], X.iloc[train_size:]
        y_train, y_test = y.iloc[:train_size], y.iloc[train_size:]

        if self.model_type == 'RandomForest':
            self.model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
            # 'balanced' class_weight is important if 'is_rescue_needed' is imbalanced (common in risk data)
        # elif self.model_type == 'LSTM':
        #     # LSTM model setup requires specific input shape for time series (samples, timesteps, features)
        #     # This would involve TimeseriesGenerator or manual reshaping.
        #     # Example: generator = TimeseriesGenerator(X_train.values, y_train.values, length=10, batch_size=32)
        #     self.model = Sequential(, 1)), # Adjust input_shape
        #         Dense(1, activation='sigmoid')
        #     ])
        #     self.model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}. Choose 'RandomForest' or implement 'LSTM'.")

        print(f"Training {self.model_type} model...")
        self.model.fit(X_train, y_train)
        print("Model training complete.")
        self.evaluate_model(X_test, y_test)

    def predict_risk(self, X_new: pd.DataFrame) -> float:
        """
        Predicts the risk score or probability of rescue for new data.
        Returns a probability (0-1) or a classification (0 or 1).
        """
        if self.model is None:
            raise RuntimeError("Model not trained. Call train_model first.")
        
        # Ensure new data has the same features as training data
        X_new_processed = X_new[self.feature_columns]

        # For classification, predict_proba gives probabilities
        if hasattr(self.model, 'predict_proba'):
            # Probability of class 1 (rescue needed)
            risk_probability = self.model.predict_proba(X_new_processed)[:, 1] 
            return risk_probability if len(risk_probability) > 0 else 0.0
        else: # For regression models or direct classification
            return self.model.predict(X_new_processed)

    def evaluate_model(self, X_test: pd.DataFrame, y_test: pd.Series):
        """
        Evaluates the trained model's performance on the test set.[5, 7]
        In financial risk, minimizing false negatives (missed rescues) is crucial.
        """
        if self.model is None:
            raise RuntimeError("Model not trained. Call train_model first.")

        y_pred = self.model.predict(X_test)
        y_proba = self.model.predict_proba(X_test)[:, 1] if hasattr(self.model, 'predict_proba') else None

        print("\n--- Model Evaluation ---")
        print(classification_report(y_test, y_pred))
        if y_proba is not None:
            print(f"AUC-ROC: {roc_auc_score(y_test, y_proba):.4f}")
            # Consider Precision-Recall AUC for imbalanced datasets
            precision, recall, _ = precision_recall_curve(y_test, y_proba)
            print(f"AUC-PR: {auc(recall, precision):.4f}")
        print("------------------------\n")