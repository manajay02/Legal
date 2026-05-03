import pandas as pd
from sklearn.model_selection import train_test_split

# Load dataset
df = pd.read_csv("data/training_pairs/nli_dataset.csv", encoding="latin1")

# Fix column name if needed
df.columns = df.columns.str.strip()

# Standardize label text (lowercase + strip spaces)
df["Label"] = df["Label"].str.strip().str.lower()

# Map labels
label_mapping = {
    "entailment": 0,
    "contradiction": 1
}

df["Label"] = df["Label"].map(label_mapping)

# Remove rows with missing labels
df = df.dropna(subset=["Label"])

# Convert label to integer
df["Label"] = df["Label"].astype(int)

# Save clean dataset
df.to_csv("data/training_pairs/nli_dataset_clean.csv", index=False)

print("Dataset cleaned.")

# Split dataset
train_df, test_df = train_test_split(
    df,
    test_size=0.2,
    random_state=42,
    stratify=df["Label"]
)
cro
train_df.to_csv("data/training_pairs/train.csv", index=False)
test_df.to_csv("data/training_pairs/test.csv", index=False)

print("Train/Test split completed successfully.")
