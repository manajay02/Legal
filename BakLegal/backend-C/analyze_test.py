import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, roc_auc_score

# Load test data
df = pd.read_csv('data/training_pairs/test.csv')

print("\n" + "="*70)
print("TEST DATASET ANALYSIS")
print("="*70)
print(f"\nTotal samples: {len(df)}")
print(f"Columns: {list(df.columns)}")
print(f"\nLabel distribution:")
print(df['Label'].value_counts())
print(f"\nLabel percentages:")
for label, count in df['Label'].value_counts().items():
    print(f"  Label {label}: {count} samples ({count/len(df)*100:.2f}%)")

print("\n" + "="*70)
print("DATA INTEGRITY CHECKS")
print("="*70)
print(f"Missing values:\n{df.isnull().sum()}")
print(f"\nData types:\n{df.dtypes}")
