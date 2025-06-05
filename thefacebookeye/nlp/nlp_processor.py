import time # Corrected from 'ሰዓት' to 'time'
import langdetect
from langdetect.lang_detect_exception import LangDetectException
import os
import sys

# Conditional import for argostranslate
try:
    import argostranslate.package
    import argostranslate.translate
    ARGOS_AVAILABLE = True
    package_dir = os.path.join(os.path.expanduser('~'), '.local', 'share', 'argos-translate', 'packages')
    os.environ['ARGOS_TRANSLATE_PACKAGE_DIR'] = package_dir
    if not os.path.exists(package_dir):
        try:
            os.makedirs(package_dir)
            print(f"Created Argos Translate package directory: {package_dir}")
        except Exception as e:
            print(f"Warning: Could not create Argos Translate package directory {package_dir}: {e}")

except ImportError:
    print("Warning: argostranslate module not found. Translation functionality will be disabled.")
    ARGOS_AVAILABLE = False

def install_argos_package_if_needed(from_code, to_code):
    if not ARGOS_AVAILABLE:
        return False
    try:
        installed_packages = argostranslate.package.get_installed_packages()
    except Exception as e:
        print(f"Error getting installed Argos Translate packages: {e}")
        try:
            print("Attempting to update package index before checking installed packages again...")
            argostranslate.package.update_package_index()
            installed_packages = argostranslate.package.get_installed_packages()
            print("Successfully updated index and retrieved installed packages.")
        except Exception as e_update:
            print(f"Failed to update index or get installed packages again: {e_update}")
            return False

    for pkg in installed_packages:
        if pkg.from_code == from_code and pkg.to_code == to_code:
            print(f"Translation package {from_code}->{to_code} is already installed.")
            return True

    print(f"Translation package {from_code}->{to_code} not found directly among {len(installed_packages)} installed package(s).")

    package_to_install = None
    try:
        available_packages = argostranslate.package.get_available_packages()
        print(f"Found {len(available_packages)} available packages in index.")
    except Exception as e:
        print(f"Error getting available Argos Translate packages: {e}")
        return False

    for pkg_info in available_packages:
        if pkg_info.from_code == from_code and pkg_info.to_code == to_code:
            package_to_install = pkg_info
            break

    if package_to_install:
        print(f"Found available package: {package_to_install}. Attempting to download and install...")
        try:
            download_path = package_to_install.download()
            print(f"Package downloaded to {download_path}")
            argostranslate.package.install_from_path(download_path)
            print(f"Successfully installed package {from_code}->{to_code}.")
            updated_installed_packages = argostranslate.package.get_installed_packages()
            for pkg in updated_installed_packages:
                if pkg.from_code == from_code and pkg.to_code == to_code:
                    print(f"Verified: Package {from_code}->{to_code} is now installed.")
                    return True
            print(f"Warning: Package {from_code}->{to_code} was installed but not found in verification.")
            return False
        except Exception as e:
            print(f"Error installing package {from_code}->{to_code}: {e}")
            return False
    else:
        print(f"No installable package found for {from_code}->{to_code} in the current index.")
        return False

def detect_language(text):
    if not text or not isinstance(text, str) or not text.strip():
        return None
    try:
        if len(text.split()) < 3 and len(text) < 20:
             print(f"Warning: Text is very short ('{text[:30].replace(chr(10), ' ')}...'), language detection might be unreliable.")
        lang_code = langdetect.detect(text)
        return lang_code
    except LangDetectException as e:
        print(f"Language detection failed for text: '{text[:50].replace(chr(10), ' ')}...'. Error: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during language detection: {e}")
        return None

def translate_text(text, target_language="en", source_language=None):
    if not ARGOS_AVAILABLE:
        print("Translation skipped: argostranslate is not available.")
        return text
    if not text or not isinstance(text, str) or not text.strip():
        return text

    original_text_snippet = text[:50].replace(chr(10), ' ') + "..."

    if source_language is None:
        source_language = detect_language(text)
        if source_language is None:
            print(f"Could not detect source language for '{original_text_snippet}'. Skipping translation.")
            return text
        print(f"Detected source language: {source_language} for '{original_text_snippet}'")

    if source_language == target_language:
        print(f"Source and target language ('{source_language}') are the same for '{original_text_snippet}'. No translation needed.")
        return text

    if not install_argos_package_if_needed(source_language, target_language):
        print(f"Translation from {source_language} to {target_language} for '{original_text_snippet}' is not available. Returning original text.")
        return text

    try:
        translation = argostranslate.translate.translate(text, source_language, target_language)
        print(f"Successfully translated '{original_text_snippet}' from {source_language} to {target_language}.")
        return translation
    except Exception as e:
        print(f"Error during translation of '{original_text_snippet}' from {source_language} to {target_language}: {e}")
        return text


if __name__ == '__main__':
    print("--- Testing NLP Processor ---")

    if ARGOS_AVAILABLE:
        print("\n--- Ensuring Argos Translate package directory exists ---")
        if not os.path.exists(package_dir) or not os.access(package_dir, os.W_OK):
            print(f"Warning: Argos Translate package directory {package_dir} is not writable or does not exist. Package installation may fail.")
        else:
            print(f"Argos Translate package directory {package_dir} is accessible.")

        print("\n--- Updating Argos Translate package index (first attempt in main) ---")
        try:
            argostranslate.package.update_package_index()
            print("Argos Translate package index updated successfully.")
        except Exception as e:
            print(f"Could not update Argos Translate package index: {e}")
    else:
        print("\nSkipping Argos Translate specific setup (package dir, index update) as module is not available.")

    print("\n--- Test 1: Language Detection ---")
    texts_to_detect = [
        ("Hello, world!", "en"), ("Hola, mundo!", "es"), ("Bonjour, le monde!", "fr"),
        ("你好，世界！", "zh-cn"), ("வணக்கம் உலகம்", "ta"), ("ይህ የሙከራ ዓረፍተ ነገር ነው።", "am"),
        ("Short", None), ("", None)
    ]
    for text, expected_lang in texts_to_detect:
        detected = detect_language(text)
        print(f"Text: '{text[:30].replace(chr(10), ' ')}...' -> Detected: {detected} (Expected: {expected_lang if expected_lang else 'None/Error'})")
        if text == "ይህ የሙከራ ዓረፍተ ነገር ነው።" and detected != "am":
            print("Note: Amharic detection might be inaccurate with default langdetect models.")

    if ARGOS_AVAILABLE:
        print("\n--- Test 2: Translation (Spanish to English) ---")
        text_es = "Hola, ¿cómo estás?"
        print(f"Original Spanish: {text_es}")
        translated_to_en = translate_text(text_es, target_language="en", source_language="es")
        print(f"Translated to English: {translated_to_en}")

        print("\n--- Test 3: Translation (English to Spanish) ---")
        text_en = "This is a test sentence."
        print(f"Original English: {text_en}")
        translated_to_es = translate_text(text_en, target_language="es", source_language="en")
        print(f"Translated to Spanish: {translated_to_es}")

        print("\n--- Test 4: Translation (Amharic to English if model available) ---")
        text_am = "ይህ የሙከራ ዓረፍተ ነገር ነው።"
        print(f"Original Amharic: {text_am}")
        translated_am_to_en = translate_text(text_am, target_language="en", source_language="am")
        if translated_am_to_en == text_am:
            print("Amharic to English translation did not occur.")
        else:
            print(f"Translated Amharic to English: {translated_am_to_en}")

        print("\n--- Test 5: Translation with Auto-Detection ---")
        auto_translate_text = "Bonjour et bienvenue."
        print(f"Original for auto-detect: {auto_translate_text}")
        translated_auto = translate_text(auto_translate_text, target_language="en")
        print(f"Translated (auto-detected source) to English: {translated_auto}")
    else:
        print("\nSkipping translation tests as argostranslate is not available.")

    print("\n--- NLP Processor Test Finished ---")
