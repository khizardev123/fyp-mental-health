import pytest
from transformers import pipeline
import os

# Mock or use a small model for testing if the main one isn't ready
# For this test, we'll try to load the actual model if it exists, otherwise skip/fail gracefully
MODEL_PATH = "./models/emotion_model"

@pytest.mark.skipif(not os.path.exists(MODEL_PATH), reason="Model not trained yet")
def test_emotion_model_loading():
    """Test that the model and tokenizer can be loaded successfully."""
    classifier = pipeline("text-classification", model=MODEL_PATH, tokenizer=MODEL_PATH)
    assert classifier is not None

@pytest.mark.skipif(not os.path.exists(MODEL_PATH), reason="Model not trained yet")
def test_emotion_prediction_joy():
    """Test that the model correctly identifies joy."""
    classifier = pipeline("text-classification", model=MODEL_PATH, tokenizer=MODEL_PATH)
    result = classifier("I am so happy that I passed my exam!")
    # Result is a list of dicts [{'label': 'joy', 'score': ...}]
    label = result[0]['label']
    assert label == 'joy'

@pytest.mark.skipif(not os.path.exists(MODEL_PATH), reason="Model not trained yet")
def test_emotion_prediction_sadness():
    """Test that the model correctly identifies sadness."""
    classifier = pipeline("text-classification", model=MODEL_PATH, tokenizer=MODEL_PATH)
    result = classifier("I feel very lonely and broken today.")
    label = result[0]['label']
    assert label == 'sadness'

@pytest.mark.skipif(not os.path.exists(MODEL_PATH), reason="Model not trained yet")
def test_emotion_prediction_fear():
    """Test that the model correctly identifies fear/anxiety."""
    classifier = pipeline("text-classification", model=MODEL_PATH, tokenizer=MODEL_PATH)
    result = classifier("I am terrified of what might happen next.")
    assert result[0]['label'] == 'fear'
