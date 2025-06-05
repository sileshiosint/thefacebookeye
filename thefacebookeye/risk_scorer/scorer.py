import re

# Initial keyword configuration. Can be expanded and moved to a config file later.
# Scores are subjective and for demonstration.
DEFAULT_KEYWORDS_CONFIG = {
    # High risk
    "kill": 0.9,
    "attack": 0.8,
    "destroy": 0.8,
    "slaughter": 0.95,
    "massacre": 0.95,
    "genocide": 1.0, # Max score directly
    "assassinate": 0.9,
    "execute": 0.85,
    "retaliation": 0.7, # Can be context-dependent
    "call_to_violence": 0.8, # Phrase
    "incite_violence": 0.85,

    # Medium risk
    "mobilize": 0.7,
    "militia": 0.6,
    "armed": 0.65,
    "conflict": 0.5,
    "clashes": 0.55,
    "war": 0.6,
    "protest": 0.4, # Can be peaceful or violent
    "riot": 0.65,
    "uprising": 0.6,
    "revolution": 0.7,
    "coup": 0.75,
    "take_arms": 0.7, # Phrase

    # Lower risk (but still indicative of tension or specific topics)
    "ethnic_tension": 0.5, # Phrase
    "political_instability": 0.4, # Phrase
    "displacement": 0.3,
    "refugees": 0.2,
    "hate_speech_example": 0.7, # Placeholder for more specific hate speech terms
    "extremism_example": 0.65, # Placeholder

    # Example keywords from the issue description
    "tplf": 0.5, # Context-dependent, could be neutral or indicative
    "oromia_clashes": 0.6, # Phrase, more specific
}

# More keywords related to specific contexts (e.g., Ethiopian conflict)
ETHIOPIAN_CONTEXT_KEYWORDS = {
    "fano": 0.55,
    "amhara_militia": 0.6, # phrase
    "oromo_liberation_army": 0.6, # phrase "OLA"
    "tigray_defense_forces": 0.6, # phrase "TDF"
    "abiy_ahmed": 0.1, # Name, low risk by itself
    "addis_ababa": 0.05, # Location, very low risk
    # More specific terms related to incitement or conflict in the region
    # These would require domain expertise to score appropriately.
}

# Combine keyword sets
COMBINED_KEYWORDS_CONFIG = {**DEFAULT_KEYWORDS_CONFIG, **ETHIOPIAN_CONTEXT_KEYWORDS}


def calculate_risk_score(post_text, keywords_config=None):
    """
    Calculates a risk score for a given text based on keyword occurrences.

    Args:
        post_text (str): The text content of the post.
        keywords_config (dict, optional): A dictionary where keys are keywords/phrases
                                          and values are their risk scores (0.0 to 1.0).
                                          Defaults to COMBINED_KEYWORDS_CONFIG.

    Returns:
        float: A risk score between 0.0 and 1.0.
               Currently, this is the sum of scores of unique keywords found, capped at 1.0.
               Or, if a keyword has score 1.0, it returns 1.0 immediately.
    """
    if not post_text or not isinstance(post_text, str):
        return 0.0

    if keywords_config is None:
        keywords_config = COMBINED_KEYWORDS_CONFIG

    lower_text = post_text.lower()

    current_score_sum = 0.0 # Changed variable name for clarity from current_max_score
    found_keywords = set()

    sorted_keywords = sorted(keywords_config.keys(), key=len, reverse=True)

    for keyword_phrase in sorted_keywords:
        score = keywords_config[keyword_phrase]

        term_to_match = keyword_phrase.replace("_", " ")

        pattern = r"\b" + re.escape(term_to_match) + r"\b"

        # Check if this specific keyword_phrase (not just term_to_match) has already been effectively counted
        # This is to handle cases where a longer phrase (e.g. "oromia_clashes") contains a shorter keyword ("clashes")
        # If we find the longer phrase, we use its score. If we later find the shorter one,
        # we should only add its score if the longer one (which contains it) wasn't already found.
        # However, the current `found_keywords.add(keyword_phrase)` handles uniqueness of the *original keyword keys*.
        # The sorting and iterating should mean longer phrases are checked first.
        # If "oromia clashes" is found, "clashes" (if it's a separate key) will be checked later.
        # If "clashes" is part of "oromia_clashes" but "clashes" is also its own keyword:
        #   1. "oromia_clashes" (0.6) is found. current_score_sum = 0.6. found_keywords.add("oromia_clashes")
        #   2. "clashes" (0.55) is found. current_score_sum += 0.55. found_keywords.add("clashes")
        # This sum is what the original test case expected.

        if re.search(pattern, lower_text):
            if keyword_phrase not in found_keywords:
                print(f"  Found keyword: '{term_to_match}' (score: {score})")
                if score >= 1.0:
                    return 1.0
                current_score_sum += score
                found_keywords.add(keyword_phrase)

    return min(current_score_sum, 1.0)


if __name__ == '__main__':
    print("--- Testing Risk Scorer ---")

    # Recalculate expected scores based on the sum logic for unique keywords
    # Test Case 2: "There are reports of clashes in Oromia and mobilization of militia."
    # "oromia_clashes" (0.6) - found first due to length
    # "clashes" (0.55) - found
    # "mobilization" (0.7) - found
    # "militia" (0.6) - found
    # Expected approx: 0.6 (oromia_clashes) + 0.7 (mobilization) + 0.6 (militia) = 1.9 -> capped 1.0
    # If "clashes" is also counted separately (and it should if it's a distinct keyword):
    # This depends if "oromia_clashes" means "oromia" AND "clashes" or the literal phrase.
    # The code matches literal phrase "oromia clashes".
    # So, "clashes" would be matched separately.
    # "oromia_clashes" (0.6) + "clashes" (0.55) + "mobilization" (0.7) + "militia" (0.6)
    # sum = 0.6 + 0.55 + 0.7 + 0.6 = 2.45 -> capped 1.0

    # Test Case 4: "The TPLF forces are planning an attack."
    # "tplf" (0.5) + "attack" (0.8) = 1.3 -> capped 1.0

    # Test Case 6: "A revolution is needed to overthrow the government. Take arms now!"
    # "take_arms" (0.7) + "revolution" (0.7) = 1.4 -> capped 1.0

    test_cases = [
        ("This is a peaceful message about community.", 0.0),
        ("There are reports of clashes in Oromia and mobilization of militia.", 1.0), # 0.6+0.55+0.7+0.6 = 2.45 -> 1.0
        ("Urgent call to kill all enemies and attack their homes! This is genocide!", 1.0), # "genocide" is 1.0
        ("The TPLF forces are planning an attack.", 1.0), # 0.5 + 0.8 = 1.3 -> 1.0
        ("Let's protest peacefully for our rights.", COMBINED_KEYWORDS_CONFIG.get("protest",0)), # 0.4
        ("A revolution is needed to overthrow the government. Take arms now!", 1.0), # 0.7 + 0.7 = 1.4 -> 1.0
        ("Discussion about ethnic_tension in the region.", COMBINED_KEYWORDS_CONFIG.get("ethnic_tension",0)), # 0.5
        ("The word 'execute' should trigger a high score.", COMBINED_KEYWORDS_CONFIG.get("execute",0)), # 0.85
        ("This talks about the Oromo Liberation Army.", COMBINED_KEYWORDS_CONFIG.get("oromo_liberation_army", 0)), # 0.6
        ("A message about Abiy Ahmed visiting Addis Ababa.",
         COMBINED_KEYWORDS_CONFIG.get("abiy_ahmed",0) + COMBINED_KEYWORDS_CONFIG.get("addis_ababa",0) # 0.1 + 0.05 = 0.15
        )
    ]

    for i, (text, expected_score_val) in enumerate(test_cases): # Renamed expected_score_approx
        print(f"\n--- Test Case {i+1} ---")
        print(f"Text: \"{text}\"")
        score = calculate_risk_score(text)
        print(f"Calculated Score: {score:.4f}")

        # Check if the calculated score is close to the expected score
        if abs(score - expected_score_val) < 0.01 : # Using a small tolerance for float comparison
            print(f"Matches expected score: {expected_score_val:.4f}")
        else:
            print(f"Deviation: Expected {expected_score_val:.4f}, but got {score:.4f}")


    print("\n--- Testing with custom keywords ---")
    custom_config = {"alert": 0.9, "urgent_alert": 1.0, "meeting": 0.1} # Added urgent_alert
    custom_text = "This is an urgent alert for the upcoming meeting."
    # Expected: "urgent_alert" (1.0) should be found first and return 1.0
    print(f"Text: \"{custom_text}\" with custom config")
    score = calculate_risk_score(custom_text, custom_config)
    print(f"Calculated Score (custom config): {score:.4f}") # Expected 1.0
    if abs(score - 1.0) < 0.01:
        print("Matches expected score of 1.0 for custom config.")
    else:
        print(f"Deviation in custom: Expected 1.0, got {score:.4f}")

    print("\n--- Risk Scorer Test Finished ---")
