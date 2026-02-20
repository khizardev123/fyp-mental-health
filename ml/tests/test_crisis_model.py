import pytest
from transformers import pipeline
import os

MODEL_PATH = "./models/crisis_model"

@pytest.mark.skipif(not os.path.exists(MODEL_PATH), reason="Crisis Model not trained yet")
def test_crisis_model_loading():
    """Test that the crisis model and tokenizer can be loaded."""
    classifier = pipeline("text-classification", model=MODEL_PATH, tokenizer=MODEL_PATH)
    assert classifier is not None

@pytest.mark.skipif(not os.path.exists(MODEL_PATH), reason="Crisis Model not trained yet")
def test_crisis_prediction_safe():
    """Test that the model correctly identifies safe content."""
    classifier = pipeline("text-classification", model=MODEL_PATH, tokenizer=MODEL_PATH)
    result = classifier("I had a great day at the park today.")
    # Expect 'non_crisis' (label 0)
    label = result[0]['label']
    assert label == 'non_crisis' or label == 'LABEL_0'

@pytest.mark.skipif(not os.path.exists(MODEL_PATH), reason="Crisis Model not trained yet")
def test_crisis_prediction_danger():
    """Test that the model correctly identifies crisis content."""
    classifier = pipeline("text-classification", model=MODEL_PATH, tokenizer=MODEL_PATH)
    result = classifier("I feel hopeless and I want to end my life.")
    # Expect 'crisis' (label 1)
    label = result[0]['label']
    assert label == 'crisis' or label == 'LABEL_1'
