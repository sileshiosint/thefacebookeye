import time
import langdetect
from langdetect.lang_detect_exception import LangDetectException
import os
import sys
import nltk # For VADER sentiment analysis

# Conditional import for argostranslate and spacy
ARGOS_AVAILABLE = False
SPACY_AVAILABLE = False
nlp_spacy_en = None # Global for loaded spaCy English model

try:
    import argostranslate.package
    import argostranslate.translate
    ARGOS_AVAILABLE = True
    # Setup Argos package directory
    package_dir_argos = os.path.join(os.path.expanduser('~'), '.local', 'share', 'argos-translate', 'packages')
    os.environ['ARGOS_TRANSLATE_PACKAGE_DIR'] = package_dir_argos
    if not os.path.exists(package_dir_argos):
        try:
            os.makedirs(package_dir_argos)
            print(f"Created Argos Translate package directory: {package_dir_argos}")
        except Exception as e:
            print(f"Warning: Could not create Argos Translate package directory {package_dir_argos}: {e}")
except ImportError:
    print("Warning: argostranslate module not found. Translation functionality will be disabled.")

try:
    import spacy
    SPACY_AVAILABLE = True
    SPACY_MODEL_EN = "en_core_web_sm" # spaCy model name
except ImportError:
    print("Warning: spacy module not found. NER functionality will be disabled.")


# NLTK resources
NLTK_RESOURCES = {
    "sentiment": ["vader_lexicon"]
}

def download_nltk_resource(resource_group_path, resource_name):
    """Downloads an NLTK resource if not already present."""
    # NLTK resource path is typically like 'sentiment/vader_lexicon.zip' or 'tokenizers/punkt.zip'
    # nltk.data.find expects path relative to one of the nltk_data directories, e.g. 'sentiment/vader_lexicon.zip'
    # For vader_lexicon, the actual path it looks for is 'sentiment/vader_lexicon.zip' for the dir, or vader_lexicon inside it.
    """
    Attempts to ensure an NLTK resource is available, downloading if necessary.
    For VADER, the most direct check is to see if SentimentIntensityAnalyzer can be initialized.
    For other resources, nltk.download is the primary mechanism.
    """
    if resource_name == "vader_lexicon": # Specific handling for VADER
        try:
            # Attempt to initialize to see if data is found by NLTK internally
            from nltk.sentiment.vader import SentimentIntensityAnalyzer
            SentimentIntensityAnalyzer() # This will raise LookupError if vader_lexicon is not found
            print(f"NLTK resource '{resource_name}' is available (VADER initialized).")
            return True
        except LookupError:
            print(f"NLTK resource '{resource_name}' not found by VADER init. Attempting to download...")
        except Exception as e_init: # Other errors during init
            print(f"Unexpected error trying to initialize VADER to check for '{resource_name}': {e_init}")
            # Fall through to download attempt as a precaution

    # General download attempt for any resource if specific check failed or not VADER
    try:
        # print(f"Attempting to download NLTK resource '{resource_name}' via nltk.download()...")
        nltk.download(resource_name, quiet=False)
        print(f"NLTK resource '{resource_name}' download attempted successfully (or was already present).")
        # For VADER, re-check by trying to initialize again after download
        if resource_name == "vader_lexicon":
            from nltk.sentiment.vader import SentimentIntensityAnalyzer
            SentimentIntensityAnalyzer() # This should now work
            print(f"NLTK resource '{resource_name}' confirmed available after download (VADER initialized).")
        return True
    except Exception as e_dl:
        print(f"Error during NLTK resource '{resource_name}' download: {e_dl}")
        print(f"Please try: import nltk; nltk.download('{resource_name}') manually in a Python console if issues persist.")
        return False


def load_spacy_model(model_name="en_core_web_sm"): # Default to constant if not provided
    """Loads a spaCy model, attempting to download if not found."""
    global nlp_spacy_en
    if not SPACY_AVAILABLE:
        print("spaCy not available, cannot load model.")
        return None

    if model_name == SPACY_MODEL_EN and nlp_spacy_en:
        return nlp_spacy_en # Return cached model

    try:
        nlp = spacy.load(model_name)
        print(f"spaCy model '{model_name}' loaded successfully.")
        if model_name == SPACY_MODEL_EN:
            nlp_spacy_en = nlp
        return nlp
    except OSError:
        print(f"spaCy model '{model_name}' not found. Attempting to download...")
        try:
            spacy.cli.download(model_name)
            # After download, attempt to load again
            nlp = spacy.load(model_name)
            print(f"spaCy model '{model_name}' downloaded and loaded successfully.")
            if model_name == SPACY_MODEL_EN:
                nlp_spacy_en = nlp
            return nlp
        except SystemExit:
             print(f"spaCy download command for '{model_name}' completed via SystemExit. Attempting to load again...")
             try:
                nlp = spacy.load(model_name)
                print(f"spaCy model '{model_name}' loaded successfully after SystemExit.")
                if model_name == SPACY_MODEL_EN: nlp_spacy_en = nlp
                return nlp
             except Exception as e_load_after_dl:
                print(f"Failed to load spaCy model '{model_name}' even after download attempt (post-SystemExit): {e_load_after_dl}")
                return None
        except Exception as e:
            print(f"Error downloading or loading spaCy model '{model_name}': {e}")
            return None

def install_argos_package_if_needed(from_code, to_code):
    if not ARGOS_AVAILABLE: return False
    try:
        installed_packages = argostranslate.package.get_installed_packages()
        for pkg in installed_packages:
            if pkg.from_code == from_code and pkg.to_code == to_code: return True

        print(f"Argos Translate: Package {from_code}->{to_code} not installed. Checking available...")
        available_packages = argostranslate.package.get_available_packages()
        package_to_install = next((p for p in available_packages if p.from_code == from_code and p.to_code == to_code), None)

        if package_to_install:
            print(f"Found Argos package {from_code}->{to_code}. Downloading...")
            download_path = package_to_install.download()
            argostranslate.package.install_from_path(download_path)
            print(f"Installed Argos Translate package {from_code}->{to_code}.")
            return True
        else:
            print(f"Argos package {from_code}->{to_code} not found in index.")
            return False
    except Exception as e: print(f"Error with Argos Translate package management ({from_code}->{to_code}): {e}"); return False


def detect_language(text):
    if not text or not isinstance(text, str) or not text.strip(): return None
    try:
        if len(text.split()) < 3 and len(text) < 20: print(f"Warning: Text is short, lang detection may be unreliable: '{text[:30].replace(chr(10),' ')}...'")
        return langdetect.detect(text)
    except Exception as e: print(f"Language detection failed for '{text[:50].replace(chr(10),' ')}...': {e}"); return None

def translate_text(text, target_language="en", source_language=None):
    if not ARGOS_AVAILABLE: return text # Return original if no Argos
    if not text or not isinstance(text, str) or not text.strip(): return text
    src_lang = source_language or detect_language(text)
    if not src_lang: print(f"Could not detect source lang for translation of '{text[:30].replace(chr(10),' ')}...'"); return text
    if src_lang == target_language: return text
    if not install_argos_package_if_needed(src_lang, target_language):
        print(f"Translation {src_lang}->{target_language} unavailable for '{text[:30].replace(chr(10),' ')}...'"); return text
    try: return argostranslate.translate.translate(text, src_lang, target_language)
    except Exception as e: print(f"Error translating '{text[:30].replace(chr(10),' ')}...': {e}"); return text

_vader_analyzer = None

def extract_entities(text, language_code="en"):
    if not SPACY_AVAILABLE or not text or not isinstance(text, str) or not text.strip(): return []
    nlp_model = None
    if language_code == "en": nlp_model = load_spacy_model(SPACY_MODEL_EN)
    if not nlp_model: print(f"spaCy model for '{language_code}' not available. Cannot extract entities."); return []
    try:
        doc = nlp_model(text)
        return [{"text": ent.text, "label": ent.label_, "start_char": ent.start_char, "end_char": ent.end_char} for ent in doc.ents]
    except Exception as e: print(f"Error during entity extraction: {e}"); return []

def analyze_sentiment_vader(text):
    global _vader_analyzer
    if not text or not isinstance(text, str) or not text.strip():
        return {"neg": 0.0, "neu": 1.0, "pos": 0.0, "compound": 0.0, "error": "Empty input"}
    if not _vader_analyzer: # Only attempt to initialize if not already done
        # Ensure the vader_lexicon is downloaded.
        # The download_nltk_resource for "vader_lexicon" now includes an init check.
        if not download_nltk_resource("sentiment", "vader_lexicon"): # resource_group_path is not used by new logic for vader
            # The error message is now printed by download_nltk_resource
            return {"error": "VADER lexicon missing or download failed"}

        try:
            # If download_nltk_resource returned True for "vader_lexicon", VADER should be initializable.
            from nltk.sentiment.vader import SentimentIntensityAnalyzer
            _vader_analyzer = SentimentIntensityAnalyzer()
            print("VADER SentimentIntensityAnalyzer initialized successfully for use.")
        except Exception as e_init_vader:
            print(f"Error initializing VADER SentimentIntensityAnalyzer after download check: {e_init_vader}")
            _vader_analyzer = None # Ensure it's None if init fails
            return {"error": f"VADER analyzer init failed post-check: {e_init_vader}"}

    if not _vader_analyzer:
        return {"error": "VADER analyzer could not be initialized."} # Should have been caught above

    try:
        return _vader_analyzer.polarity_scores(text)
    except Exception as e:
        print(f"Error during VADER sentiment analysis: {e}")
        return {"error": str(e)}


if __name__ == '__main__':
    print("--- Testing Enhanced NLP Processor ---")
    print("\n--- Ensuring NLP Models ---")
    if SPACY_AVAILABLE: load_spacy_model(SPACY_MODEL_EN)
    else: print("Skipping spaCy model load (spaCy not available).")
    download_nltk_resource("sentiment", "vader_lexicon")

    print("\n--- Test 1: Language Detection (Quick Check) ---")
    print(f"Lang of 'Hello world': {detect_language('Hello world')}")

    if ARGOS_AVAILABLE:
        print("\n--- Test 2: Translation (Quick Check Es->En) ---")
        try: argostranslate.package.update_package_index()
        except Exception as e_argos_update: print(f"Argos update index failed: {e_argos_update}")
        print(f"Translate 'Hola mundo': {translate_text('Hola mundo', 'en', 'es')}")
    else: print("\nSkipping Translation tests (argostranslate not available).")

    if SPACY_AVAILABLE:
        print("\n--- Test 3: Named Entity Recognition (NER) ---")
        ner_text_en = "Apple is looking at buying U.K. startup for $1 billion. Barack Obama visited Paris."
        print(f"NER for: '{ner_text_en}'")
        entities = extract_entities(ner_text_en, "en")
        if entities: [print(f"  Entity: {ent['text']}, Label: {ent['label']}") for ent in entities]
        else: print("  No entities extracted or error occurred.")
    else: print("\nSkipping NER tests (spaCy not available).")

    print("\n--- Test 4: Sentiment Analysis (VADER) ---")
    sentiment_texts = [
        ("I love this product, it's amazing!", "Positive"),
        ("This is the worst experience ever.", "Negative"),
        ("The weather is okay today.", "Neutral")
    ]
    for text, expected_cat in sentiment_texts:
        sentiment_scores = analyze_sentiment_vader(text)
        print(f"Sentiment for: '{text}' -> Scores: {sentiment_scores} (Expected: {expected_cat})")
        if "compound" in sentiment_scores:
            cat = "Positive" if sentiment_scores['compound'] >= 0.05 else "Negative" if sentiment_scores['compound'] <= -0.05 else "Neutral"
            print(f"  VADER determined category: {cat}")
    print("\n--- Enhanced NLP Processor Test Finished ---")
