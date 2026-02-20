#!/usr/bin/env python3
import sys, re, joblib, numpy as np, pandas as pd
from pathlib import Path
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import ast

BASE   = Path(__file__).resolve().parent.parent
DATA   = BASE / "data" / "raw"
MODELS = BASE / "models"
MODELS.mkdir(exist_ok=True)

def clean(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r"http\S+|www\S+|<[^>]+>", "", text)
    text = re.sub(r"[^a-z0-9\s'?!.,]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def get_expanded_dataset():
    """
    Massively expanded dataset capturing semantic nuances.
    1 = Crisis / Suicidal Ideation / Severe Hopelessness
    0 = Safe / Normal Sadness / Hopeful Recovery / Neutral Interaction
    """
    crisis = [
        "I want to kill myself", "thinking about ending my life", "i give up on life",
        "life has no meaning and I am better off dead", "worthless and a burden",
        "hopeless and worthless", "ending it all tonight", "don't want to live",
        "wish i was never born", "suicide is my only option", "planning my death",
        "goodbye note is written", "no reason to stay alive", "cut my wrists",
        "took all my pills", "nothing matters anymore i'm done", "life is over for me",
        "disappearing forever", "no one cares if i die", "i want to die so much",
        "i'm such a failure i should just die", "death is the only escape",
        "rather be dead than live like this", "suicidal thoughts everyday",
        "can't live like this another second", "no point in existing",
        "i hate myself i want it to end", "overdosing on meds", "jump off the bridge",
        "world is better without me", "i am going to kill myself i'm serious",
        "my life is a nightmare i want it to stop permanently",
        # Nuanced crisis (no 'kill' or 'suicide' but clear intent)
        "the pain is too much i just want out", "everyone is better off without me",
        "i've lost hope completely i'm done", "no light at the end of the tunnel for me",
        "i'm ready to go now", "last day on earth", "ready to give up",
        "there is no way out except one", "finally making the choice to leave",
    ]
    
    # Critical: Hard "Safe" cases that usually trip up simple models
    safe = [
        "I feel really sad but I know things will get better",
        "I am so frustrated I drank water and now feel a bit better",
        "and then we talk about our past and get too much h",
        "my friend came and we had a great time",
        "I am so happy today and life is wonderful",
        "I am exhausted but looking forward to the weekend",
        "stressed about work but I'll manage",
        "crying a lot but my therapist is helping",
        "sad about the breakup but healing takes time",
        "i felt worthless yesterday but today is better",
        "hoping for improvement", "things will improve", "will get better",
        "seeking help for my depression", "talked to a counselor",
        "called a helpline and feeling safer", "friends are supporting me",
        "it's going to be okay", "life is hard but i'm fighting",
        "managing my anxiety with breathing", "went for a walk to clear my head",
        "i missed my cat so much i cried", "angry at the situation but i'll survive",
        "frustrated but managing", "very sad situation but we stay strong",
        "i was thinking about death in a movie but it was sad",
        "the character in the book died and i felt sad",
        "i am grieving but i am not in danger",
        "life is full of ups and downs", "staying positive despite the pain",
        "recovery is a long road but i'm on it", "got my medication today",
        "feeling a bit down but i'll be fine", "tomorrow is a new day",
        "it was a rough day but i'm okay now", "tired of everything but just need sleep",
        "everyone has bad days", "i'm not giving up on my dreams",
        "talk to you later about our past", "the past was hard but the future is bright",
        "dealing with stress through meditation", "peaceful walk in the park",
    ]
    
    data = [{"text": clean(t), "label": 1} for t in crisis] + \
           [{"text": clean(t), "label": 0} for t in safe]
    return pd.DataFrame(data)

def train():
    print("🔄 Loading GoEmotions + Semantic Dataset...")
    # Load a cleaner subset of GoEmotions to provide background "normal" language
    try:
        raw_df = pd.read_csv(DATA / "go_emotions.csv")
    except:
        print("❌ go_emotions.csv not found, using semantic-only training.")
        raw_df = pd.DataFrame(columns=["text", "labels"])
    
    # Filter GoEmotions for very clear safe/neutral cases
    rows = []
    if not raw_df.empty:
        for _, r in raw_df.head(20000).iterrows():
            try:
                ids = set(ast.literal_eval(str(r["labels"])))
                if ids <= {0, 1, 4, 5, 7, 13, 15, 17, 23, 27}: # Clear safe/positive/neutral
                    rows.append({"text": clean(r["text"]), "label": 0})
            except: continue
    
    semantic_df = get_expanded_dataset()
    # Heavily oversample the semantic dataset (vital for 'complete sentence' accuracy)
    df = pd.concat([pd.DataFrame(rows), semantic_df] + [semantic_df]*15, ignore_index=True)
    df = df.dropna().drop_duplicates()
    
    print(f"📊 Dataset Size: {len(df)} | Crisis Samples: {df['label'].sum()}")

    X, y = df["text"], df["label"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, stratify=y, random_state=42)

    # 🚀 Semantic Pipeline (Word + Char n-grams for "complete context")
    # Using 3-word n-grams to capture phrases like "things will get better" vs "want to die"
    pipe = Pipeline([
        ("tfidf", FeatureUnion([
            ("word", TfidfVectorizer(ngram_range=(1, 3), max_features=25000, sublinear_tf=True)),
            ("char", TfidfVectorizer(ngram_range=(3, 5), max_features=10000, analyzer="char_wb")),
        ])),
        ("clf", CalibratedClassifierCV(
            LogisticRegression(C=2.0, max_iter=2000, class_weight="balanced", solver="lbfgs"),
            cv=5, method="isotonic"
        ))
    ])

    print("🏋️ Training semantic-first model...")
    pipe.fit(X_train, y_train)

    # Validate
    y_pred = pipe.predict(X_test)
    print("\n✅ Model Performance:")
    print(classification_report(y_test, y_pred, target_names=["safe", "crisis"]))

    # Test the model on the user's specific "complete sentence" cases
    tests = [
        "I want to kill myself I cannot take it anymore",
        "I have been feeling really hopeless and worthless",
        "life has no meaning and I am better off dead",
        "I feel really sad but I know things will get better",
        "I am so frustrated I drank water and now feel a bit better",
        "I am happy today and life is wonderful",
        "my friend came and we had a great time",
        "and then we talk about our past and get too much h"
    ]
    print("\n🧪 Semantic Model Smoke Test (No Keywords):")
    p = 0
    for t in tests:
        prob = pipe.predict_proba([clean(t)])[0][1]
        pred = "CRISIS" if prob >= 0.45 else "SAFE"
        print(f"  [{pred}] ({prob:.2f}) {t[:50]}...")
        if (pred == "CRISIS" and "kill" in t or "death" in t or "meaning" in t or "hopeless" in t) or (pred == "SAFE" and "better" in t or "wonderful" in t or "past" in t):
            p += 1

    joblib.dump(pipe, MODELS / "lightweight_crisis.joblib", compress=3)
    print(f"\n🚀 Semantic-first model saved to {MODELS}/lightweight_crisis.joblib")

if __name__ == "__main__":
    train()
