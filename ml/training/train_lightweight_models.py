#!/usr/bin/env python3
import sys, os, shutil, pandas as pd, numpy as np, joblib, ast, re, time
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

BASE = Path(__file__).resolve().parent.parent
DATA_DIR = BASE / "data" / "raw"
MODEL_DIR = BASE / "models"
REPORTS_DIR = BASE / "reports"
MODEL_DIR.mkdir(exist_ok=True)

plt.style.use('dark_background')
sns.set_theme(style="darkgrid")

def clean(text):
    text = str(text).lower()
    text = re.sub(r"http\S+|www\S+|<[^>]+>", "", text)
    text = re.sub(r"[^a-z0-9\s'?!.,]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def save_metrics(y_true, y_pred, y_prob, labels, title, prefix):
    # 1. Confusion Matrix (Heatmap)
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=labels, yticklabels=labels)
    plt.title(f'Confusion Matrix: {title}')
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / f"{prefix}_cm.png", dpi=200)
    plt.close()

    # 2. Confidence Distribution (Line Graph / Density)
    plt.figure(figsize=(10, 6))
    confidences = np.max(y_prob, axis=1)
    sns.kdeplot(confidences, fill=True, color="#6366f1", bw_adjust=0.5)
    plt.axvline(np.mean(confidences), color='#f87171', linestyle='--', label=f'Mean: {np.mean(confidences):.2f}')
    plt.title(f'Prediction Confidence Distribution: {title}')
    plt.xlabel('Confidence Score')
    plt.ylabel('Density')
    plt.legend()
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / f"{prefix}_dist.png", dpi=200)
    plt.close()

def train_model(name, prefix, data_path, text_col, label_col, label_map=None):
    print(f"Training {name}...")
    df = pd.read_csv(data_path)
    
    if "mental" in prefix:
        df["text"] = df["Context"].apply(clean)
        KWS = {"anxiety": ["anxious", "worry"], "depression": ["depress", "empty"], "stress": ["stress", "pressure"]}
        def lbl(t):
            for s, ks in KWS.items():
                if any(k in t for k in ks): return s
            return "normal"
        df["label"] = df["text"].apply(lbl)
    elif "crisis" in prefix:
        df["text"] = df["text"].apply(clean)
        rows = []
        for _, r in df.iterrows():
            try:
                ids = set(ast.literal_eval(str(r["labels"])))
                if ids & {9,11,14,16,19,24,25}: rows.append({"text": r["text"], "label": 1})
                elif ids & {0,1,4,5,7,13,15,17,20,26}: rows.append({"text": r["text"], "label": 0})
            except: continue
        df = pd.DataFrame(rows)
    else:
        df["text"] = df[text_col].apply(clean)
        df["label"] = df[label_col]
    
    df = df.dropna().sample(min(len(df), 10000)) if len(df) > 10000 else df.dropna()
    X, y = df["text"], df["label"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, stratify=y)
    
    pipe = Pipeline([("tfidf", TfidfVectorizer(ngram_range=(1,2), max_features=20000)), 
                     ("clf", LogisticRegression(C=1.2, max_iter=1000, class_weight="balanced"))])
    pipe.fit(X_train, y_train)
    
    y_pred, y_prob = pipe.predict(X_test), pipe.predict_proba(X_test)
    labels = sorted(list(set(y.astype(str))))
    if label_map: labels = [label_map[int(i)] if i.isdigit() and int(i) in label_map else i for i in labels]
    
    save_metrics(y_test, y_pred, y_prob, labels, name, prefix)
    joblib.dump(pipe, MODEL_DIR / f"lightweight_{prefix}.joblib", compress=3)
    print(f"✅ {name} complete.")

if __name__ == "__main__":
    if REPORTS_DIR.exists(): shutil.rmtree(REPORTS_DIR)
    REPORTS_DIR.mkdir()
    
    train_model("Emotion Classifier", "emotion", DATA_DIR/"emotion_dataset.csv", "text", "label", {0:"sad", 1:"joy", 2:"love", 3:"anger", 4:"fear", 5:"surprise"})
    train_model("Crisis Detector", "crisis", DATA_DIR/"go_emotions.csv", "text", "label", {0:"safe", 1:"crisis"})
    train_model("Mental Health", "mental_health", DATA_DIR/"mental_health_conversations.csv", "Context", "label")
    print(f"🚀 Reports in {REPORTS_DIR}")
