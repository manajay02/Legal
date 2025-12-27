import pandas as pd

# STEP 1: Load merged dataset
df = pd.read_csv("merged_dataset.csv")

# STEP 2: Standardize column name (optional but recommended)
# Rename 'Lable' → 'Label'
df.rename(columns={"Lable": "Label"}, inplace=True)

# STEP 3: Clean label values
df["Label"] = df["Label"].str.upper().str.strip()

# STEP 4: Shuffle dataset
df = df.sample(frac=1, random_state=42).reset_index(drop=True)

# STEP 5: Define split ratios
train_ratio = 0.7
val_ratio = 0.15
test_ratio = 0.15

# STEP 6: Calculate split indices
train_end = int(train_ratio * len(df))
val_end = int((train_ratio + val_ratio) * len(df))

# STEP 7: Split dataset
train_df = df.iloc[:train_end]
val_df = df.iloc[train_end:val_end]
test_df = df.iloc[val_end:]

# STEP 8: Save split datasets
train_df.to_csv("train_dataset.csv", index=False)
val_df.to_csv("validation_dataset.csv", index=False)
test_df.to_csv("test_dataset.csv", index=False)

# STEP 9: Verify label distribution
print("Train label distribution:\n", train_df["Label"].value_counts())
print("Validation label distribution:\n", val_df["Label"].value_counts())
print("Test label distribution:\n", test_df["Label"].value_counts())

print("\n✅ Dataset split completed and saved successfully!")
