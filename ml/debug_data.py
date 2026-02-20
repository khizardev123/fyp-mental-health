import sys
import os

# Add current directory to path so we can import from training
sys.path.append(os.getcwd())

try:
    from training.train_crisis_model import load_crisis_data
    print("🚀 Attempting to load crisis data...")
    data = load_crisis_data()
    
    if data:
        print(f"✅ Data loaded successfully!")
        print(f"Train size: {len(data['train'])}")
        print(f"Test size: {len(data['test'])}")
        print(f"Sample 'text': {data['train'][0]['text']}")
        print(f"Sample 'label': {data['train'][0]['label']}")
    else:
        print("❌ Data loading returned None.")
        sys.exit(1)

except Exception as e:
    print(f"❌ Exception occurred: {e}")
    sys.exit(1)
