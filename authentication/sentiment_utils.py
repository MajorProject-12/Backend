# authentication/sentiment_utils.py

from transformers import pipeline

# Load the model only once when the module is imported
classifier = None

def get_classifier():
    global classifier
    if classifier is None:
        # Initialize the sentiment analysis pipeline
        classifier = pipeline("sentiment-analysis")
    return classifier

def analyze_sentiment(text):
    """
    Perform sentiment analysis on the given text.
    Returns a tuple (sentiment_label, confidence_score)
    """
    if not text:
        return None, 0.0

    try:
        classifier = get_classifier()
        result = classifier(text)[0]
        return result['label'], float(result['score'])
    except Exception as e:
        print(f"Error in sentiment analysis: {e}")
        return None, 0.0

if __name__ == "__main__":
    # Get text input from the user
    input_text = input("Enter your text for analysis: \n")
    analyze_sentiment(input_text)

