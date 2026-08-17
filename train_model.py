import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib

def generate_synthetic_data(num_samples=2500):
    np.random.seed(42)
    
    # 1. Service Type (1: Ordinary, 2: Speed, 3: Registered, 4: Parcel, 5: Express Parcel, 6: International)
    service_type = np.random.choice([1, 2, 3, 4, 5, 6], size=num_samples, p=[0.25, 0.25, 0.15, 0.15, 0.10, 0.10])
    
    # 2. Weight in kg (0.1 to 30.0)
    weight = np.round(np.random.uniform(0.1, 30.0, size=num_samples), 2)
    
    # 3. Distance in km (10 to 2500)
    distance = np.random.randint(10, 2500, size=num_samples)
    
    # 4. Processing Days (1 to 7)
    processing_days = np.random.randint(1, 8, size=num_samples)
    
    # 5. Destination Type (0: Urban, 1: Semi-Urban, 2: Rural, 3: Remote)
    destination_type = np.random.choice([0, 1, 2, 3], size=num_samples, p=[0.4, 0.3, 0.2, 0.1])
    
    # 6. Previous Delay Rate (0.0 to 0.5)
    previous_delay_rate = np.round(np.random.uniform(0.0, 0.5, size=num_samples), 2)
    
    # 7. Workload (1 to 10 score)
    workload = np.random.randint(1, 11, size=num_samples)
    
    # 8. Weather Risk (0: Low, 1: Medium, 2: High)
    weather_risk = np.random.choice([0, 1, 2], size=num_samples, p=[0.6, 0.25, 0.15])
    
    # 9. Holiday Period (0: No, 1: Yes)
    holiday_period = np.random.choice([0, 1], size=num_samples, p=[0.8, 0.2])
    
    # Calculate Delay Risk Score based on realistic domain logic
    delay_score = (
        (distance / 500.0) * 1.5 +
        (weight / 10.0) * 0.8 +
        (destination_type * 1.2) +
        (previous_delay_rate * 4.0) +
        (workload * 0.6) +
        (weather_risk * 2.0) +
        (holiday_period * 2.5) -
        (processing_days * 0.8)
    )
    
    # Fast service types (Speed, Express) lower delay likelihood if processing days is reasonable
    fast_service_mask = np.isin(service_type, [2, 5])
    delay_score[fast_service_mask] -= 1.5
    
    # Threshold for delay
    threshold = np.median(delay_score) + 0.5
    target = (delay_score > threshold).astype(int) # 0: ON TIME, 1: POSSIBLE DELAY
    
    df = pd.DataFrame({
        'service_type': service_type,
        'weight': weight,
        'distance': distance,
        'processing_days': processing_days,
        'destination_type': destination_type,
        'previous_delay_rate': previous_delay_rate,
        'workload': workload,
        'weather_risk': weather_risk,
        'holiday_period': holiday_period,
        'target': target
    })
    
    return df

def train_and_save_model():
    print("Generating synthetic shipment dataset...")
    df = generate_synthetic_data(num_samples=2500)
    
    X = df[['service_type', 'weight', 'distance', 'processing_days', 
            'destination_type', 'previous_delay_rate', 'workload', 
            'weather_risk', 'holiday_period']]
    y = df['target']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    model_dir = os.path.join(os.path.dirname(__file__), 'model')
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, 'delivery_delay_model.pkl')
    
    joblib.dump(model, model_path)
    
    print(f"Training dataset size: {len(X_train)}")
    print(f"Testing dataset size: {len(X_test)}")
    print(f"Model accuracy: {accuracy * 100:.2f}%")
    print(f"Model saved successfully to {model_path}")

if __name__ == '__main__':
    train_and_save_model()
