#!/usr/bin/env python3
"""Quick analysis of test dataset"""

import pandas as pd

print("\n" + "="*70)
print("TEST DATASET ANALYSIS")
print("="*70)

df = pd.read_csv('data/training_pairs/test.csv')

print(f"\nDataset shape: {df.shape}")
print(f"Number of samples: {len(df)}")
print(f"Number of features: {len(df.columns)}")

print(f"\nColumns: {list(df.columns)}")

print(f"\nFirst 5 samples:")
print(df.head())

print(f"\nLabel distribution:")
print(df['Label'].value_counts())

print(f"\nLabel percentages:")
for label, count in df['Label'].value_counts().items():
    print(f"  Label {label}: {count} ({count/len(df)*100:.2f}%)")

print("\n" + "="*70)
