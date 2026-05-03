"""
Model Accuracy Analysis Script
Evaluates trained Legal NLI models on test data
"""

import pandas as pd
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support,
    classification_report, confusion_matrix, roc_auc_score, roc_curve
)
import os
import json

# ==============================
# Configuration
# ==============================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "training_pairs", "test.csv")

MODELS = {
    "legal_nli_model": os.path.join(BASE_DIR, "models", "legal_nli_model"),
    "legal_nli_model_v2": os.path.join(BASE_DIR, "models", "legal_nli_model_v2"),
}

# Label mapping for 2-class model
LABEL_NAMES = {0: "Compliant", 1: "Violation"}


def load_test_data():
    """Load test dataset"""
    print("\n📊 Loading test data...")
    df = pd.read_csv(DATA_PATH)
    print(f"   Total test samples: {len(df)}")
    print(f"   Label distribution:")
    for label, count in df['Label'].value_counts().items():
        print(f"      {LABEL_NAMES.get(label, label)}: {count} ({count/len(df)*100:.1f}%)")
    return df


def load_model(model_path):
    """Load model and tokenizer"""
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
    model.eval()
    return model, tokenizer


def predict_batch(model, tokenizer, premises, hypotheses, batch_size=8):
    """Run predictions on multiple samples"""
    all_predictions = []
    all_confidences = []
    all_probs = []
    
    with torch.no_grad():
        for i in range(0, len(premises), batch_size):
            batch_premises = premises[i:i+batch_size]
            batch_hypotheses = hypotheses[i:i+batch_size]
            
            inputs = tokenizer(
                batch_premises,
                batch_hypotheses,
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=512
            )
            
            outputs = model(**inputs)
            probs = F.softmax(outputs.logits, dim=1)
            predictions = torch.argmax(probs, dim=1)
            confidences = torch.max(probs, dim=1).values
            
            all_predictions.extend(predictions.tolist())
            all_confidences.extend(confidences.tolist())
            all_probs.extend(probs.tolist())
    
    return all_predictions, all_confidences, all_probs


def evaluate_model(model_name, model_path, test_df):
    """Evaluate a single model"""
    print(f"\n{'='*60}")
    print(f"🔍 Evaluating: {model_name}")
    print(f"   Path: {model_path}")
    print('='*60)
    
    if not os.path.exists(model_path):
        print(f"   ❌ Model not found!")
        return None
    
    # Load model
    model, tokenizer = load_model(model_path)
    print(f"   ✅ Model loaded successfully")
    print(f"   Number of labels: {model.config.num_labels}")
    
    # Run predictions
    print("\n   Running predictions...")
    premises = test_df['Premise'].tolist()
    hypotheses = test_df['Hypothesis'].tolist()
    true_labels = test_df['Label'].tolist()
    
    predictions, confidences, probs = predict_batch(model, tokenizer, premises, hypotheses)

    # Calculate metrics
    accuracy = accuracy_score(true_labels, predictions)
    precision, recall, f1, support = precision_recall_fscore_support(
        true_labels, predictions, average='binary'
    )
    
    # Calculate ROC-AUC (use probability of class 1)
    probs_class1 = [p[1] for p in probs]
    roc_auc = roc_auc_score(true_labels, probs_class1)
    
    # Confusion matrix
    cm = confusion_matrix(true_labels, predictions)
    
    # Print results
    print(f"\n   ✅ Metrics calculated successfully")
    print(f"\n   {'Metric':<20} {'Value':<15}")
    print(f"   {'-'*35}")
    print(f"   {'Accuracy':<20} {accuracy*100:<14.2f}%")
    print(f"   {'Precision':<20} {precision*100:<14.2f}%")
    print(f"   {'Recall':<20} {recall*100:<14.2f}%")
    print(f"   {'F1-Score':<20} {f1*100:<14.2f}%")
    print(f"   {'ROC-AUC':<20} {roc_auc:<14.4f}")
    
    print(f"\n   Confusion Matrix:")
    print(f"   True Negatives (TN):  {cm[0, 0]}")
    print(f"   False Positives (FP): {cm[0, 1]}")
    print(f"   False Negatives (FN): {cm[1, 0]}")
    print(f"   True Positives (TP):  {cm[1, 1]}")
    
    print(f"\n   Classification Report:")
    print(classification_report(true_labels, predictions, target_names=list(LABEL_NAMES.values())))
    
    return {
        'model_name': model_name,
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'roc_auc': roc_auc,
        'confusion_matrix': cm
    }


def load_training_history(model_path):
    """Load and analyze training history from checkpoint"""
    checkpoint_dirs = [d for d in os.listdir(model_path) if d.startswith('checkpoint-')]
    if not checkpoint_dirs:
        return None
    
    # Get the latest checkpoint
    checkpoint_nums = [int(d.split('-')[1]) for d in checkpoint_dirs]
    latest_checkpoint = f"checkpoint-{max(checkpoint_nums)}"
    trainer_state_path = os.path.join(model_path, latest_checkpoint, "trainer_state.json")
    
    if not os.path.exists(trainer_state_path):
        return None
    
    with open(trainer_state_path, 'r') as f:
        trainer_state = json.load(f)
    
    return trainer_state


def analyze_training_history(model_name, model_path):
    """Analyze training history"""
    print(f"\n{'='*60}")
    print(f"📈 Training History: {model_name}")
    print('='*60)
    
    trainer_state = load_training_history(model_path)
    if trainer_state is None:
        print("   No training history found")
        return
    
    print(f"   Best metric: {trainer_state.get('best_metric', 'N/A')}")
    print(f"   Best checkpoint: {trainer_state.get('best_model_checkpoint', 'N/A')}")
    print(f"   Total epochs: {trainer_state.get('epoch', 'N/A'):.2f}")
    print(f"   Total steps: {trainer_state.get('global_step', 'N/A')}")
    
    # Extract evaluation metrics from log history
    log_history = trainer_state.get('log_history', [])
    eval_logs = [log for log in log_history if 'eval_accuracy' in log]
    
    if eval_logs:
        print("\n   Training Progress (Evaluation Metrics):")
        print(f"   {'Epoch':<8} {'Accuracy':<12} {'F1':<12} {'Precision':<12} {'Recall':<12}")
        print("   " + "-"*56)
        
        for log in eval_logs:
            epoch = log.get('epoch', 0)
            acc = log.get('eval_accuracy', 0) * 100
            f1 = log.get('eval_f1', 0) * 100
            prec = log.get('eval_precision', 0) * 100
            rec = log.get('eval_recall', 0) * 100
            print(f"   {epoch:<8.1f} {acc:<12.2f} {f1:<12.2f} {prec:<12.2f} {rec:<12.2f}")


def main():
    print("\n" + "="*70)
    print("  LEGAL NLI MODEL ACCURACY ANALYSIS")
    print("="*70)
    
    # Load test data
    test_df = load_test_data()
    
    results = []
    
    # Evaluate each model
    for model_name, model_path in MODELS.items():
        # Analyze training history
        analyze_training_history(model_name, model_path)
        
        # Evaluate model
        result = evaluate_model(model_name, model_path, test_df)
        if result:
            results.append(result)
    
    # Summary comparison
    if len(results) > 1:
        print("\n" + "="*70)
        print("  MODEL COMPARISON SUMMARY")
        print("="*70)
        print(f"\n{'Model':<25} {'Accuracy':<12} {'Precision':<12} {'Recall':<12} {'F1':<12} {'ROC-AUC':<10}")
        print("-"*81)
        for r in results:
            print(f"{r['model_name']:<25} {r['accuracy']*100:<12.2f} {r['precision']*100:<12.2f} {r['recall']*100:<12.2f} {r['f1']*100:<12.2f} {r['roc_auc']:<10.4f}")
        
        # Identify best model
        best_model = max(results, key=lambda x: x['accuracy'])
        print(f"\n🏆 Best model by accuracy: {best_model['model_name']} ({best_model['accuracy']*100:.2f}%)")
    elif len(results) == 1:
        print("\n" + "="*70)
        print("  MODEL EVALUATION SUMMARY")
        print("="*70)
        r = results[0]
        print(f"\nModel: {r['model_name']}")
        print(f"  Accuracy:  {r['accuracy']*100:.2f}%")
        print(f"  Precision: {r['precision']*100:.2f}%")
        print(f"  Recall:    {r['recall']*100:.2f}%")
        print(f"  F1-Score:  {r['f1']*100:.2f}%")
        print(f"  ROC-AUC:   {r['roc_auc']:.4f}")
    
    print("\n" + "="*70)
    print("  ANALYSIS COMPLETE")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
    
    # Summary comparison
    if len(results) > 1:
        print("\n" + "="*70)
        print("  MODEL COMPARISON SUMMARY")
        print("="*70)
        print(f"\n{'Model':<25} {'Accuracy':<12} {'F1':<12} {'Precision':<12} {'Recall':<12}")
        print("-"*70)
        for r in results:
            print(f"{r['model_name']:<25} {r['accuracy']*100:<12.2f} {r['f1']*100:<12.2f} {r['precision']*100:<12.2f} {r['recall']*100:<12.2f}")
        
        # Identify best model
        best_model = max(results, key=lambda x: x['accuracy'])
        print(f"\n🏆 Best model by accuracy: {best_model['model_name']} ({best_model['accuracy']*100:.2f}%)")
    
    print("\n" + "="*70)
    print("  ANALYSIS COMPLETE")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
