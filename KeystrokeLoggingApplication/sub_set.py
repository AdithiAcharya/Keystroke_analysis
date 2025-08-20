import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
import os

def create_curated_subset(input_filepath):
    """
    Loads a dataset, identifies and removes ambiguous samples, 
    and returns a curated subset.
    """
    try:
        df = pd.read_csv(input_filepath, on_bad_lines='skip')
        print(f"Successfully loaded {input_filepath}.")
        print(f"Original dataset size: {df.shape[0]} rows")
    except FileNotFoundError:
        print(f"Error: The file '{input_filepath}' was not found.")
        return None
    except Exception as e:
        print(f"An error occurred while loading the data: {e}")
        return None

    X = df.drop(columns=['User', 'Target'])
    y = df['Target'].apply(lambda x: 1 if x == 'Genuine' else 0)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    initial_model = LogisticRegression(max_iter=1000, random_state=42)
    initial_model.fit(X_scaled, y)

    probabilities = initial_model.predict_proba(X_scaled)[:, 1]

    CONFIDENCE_MARGIN = 0.25 
    LOWER_BOUND = 0.5 - CONFIDENCE_MARGIN  # 0.25
    UPPER_BOUND = 0.5 + CONFIDENCE_MARGIN  # 0.75

    confident_genuine = (df['Target'] == 'Genuine') & (probabilities > UPPER_BOUND)
    confident_imposter = (df['Target'] == 'Imposter') & (probabilities < LOWER_BOUND)

    curated_df = df[confident_genuine | confident_imposter]
    print(f"Curated dataset size: {curated_df.shape[0]} rows")
    return curated_df

if __name__ == "__main__":
    # Set input and output paths
    input_path = r"C:\Users\Admin\Desktop\Keystroke_analysis\KeystrokeLoggingApplication\src\Keystrokes.csv"
    output_path = os.path.join(
        r"C:\Users\Admin\Desktop\Keystroke_analysis\KeystrokeLoggingApplication", "subset.csv"
    )

    curated_data = create_curated_subset(input_path)

    if curated_data is not None:
        try:
            curated_data.to_csv(output_path, index=False)
            print(f"✅ Success! Curated subset saved to {output_path}")
        except Exception as e:
            print(f"An error occurred while saving the file: {e}")