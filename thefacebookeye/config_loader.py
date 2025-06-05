import json
import os

DEFAULT_CONFIG_PATH = "config.json"
EXAMPLE_CONFIG_PATH = "config.example.json"

def load_config(config_path=DEFAULT_CONFIG_PATH):
    """
    Loads the configuration from a JSON file.

    If config_path doesn't exist, it checks for config.example.json
    and guides the user to set up their config.json.
    """
    if not os.path.exists(config_path):
        if os.path.exists(EXAMPLE_CONFIG_PATH):
            print(f"Configuration file '{config_path}' not found.")
            print(f"An example configuration file exists at '{EXAMPLE_CONFIG_PATH}'.")
            print(f"Please copy it to '{config_path}' and customize it for your needs.")
            print(f"  cp {EXAMPLE_CONFIG_PATH} {config_path}")
            return None
        else:
            print(f"Error: Configuration file '{config_path}' not found, "
                  f"and no example file '{EXAMPLE_CONFIG_PATH}' was found either.")
            return None

    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        print(f"Configuration loaded successfully from '{config_path}'.")
        return config_data
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{config_path}'. "
              "Please ensure it is a valid JSON file.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while loading '{config_path}': {e}")
        return None

if __name__ == '__main__':
    print("Attempting to load configuration...")

    # Scenario 1: config.json does not exist, config.example.json exists
    print("\n--- Scenario 1: Testing with default paths (config.json missing) ---")
    if os.path.exists(DEFAULT_CONFIG_PATH):
        os.rename(DEFAULT_CONFIG_PATH, DEFAULT_CONFIG_PATH + ".backup") # Temporarily move if exists

    config = load_config()
    if config:
        print("Config loaded:")
        # print(json.dumps(config, indent=2)) # Avoid printing potentially sensitive info in logs
        print(f"  Pages: {len(config.get('target_pages', []))}")
        print(f"  Groups: {len(config.get('target_groups', []))}")
        print(f"  Keywords: {len(config.get('target_keywords', []))}")
    else:
        print("Config not loaded (as expected in this scenario if config.json doesn't exist).")

    if os.path.exists(DEFAULT_CONFIG_PATH + ".backup"):
        os.rename(DEFAULT_CONFIG_PATH + ".backup", DEFAULT_CONFIG_PATH)

    # Scenario 2: config.json exists (we'll use config.example.json as a stand-in)
    print("\n--- Scenario 2: Testing with config.example.json as the source ---")
    config_example = load_config(config_path=EXAMPLE_CONFIG_PATH)
    if config_example:
        print(f"Example config loaded successfully from '{EXAMPLE_CONFIG_PATH}'.")
        # print(json.dumps(config_example, indent=2))
        print(f"  Pages: {len(config_example.get('target_pages', []))}")
        print(f"  Groups: {len(config_example.get('target_groups', []))}")
        print(f"  Keywords: {len(config_example.get('target_keywords', []))}")
        print(f"  Search Location: {config_example.get('search_location')}")
        print(f"  Date Filter: {config_example.get('date_filter')}")

    else:
        print(f"Failed to load example config from '{EXAMPLE_CONFIG_PATH}'. This should not happen.")

    # Scenario 3: Neither config.json nor config.example.json exists
    print("\n--- Scenario 3: Testing with no config files ---")
    if os.path.exists(DEFAULT_CONFIG_PATH):
        os.rename(DEFAULT_CONFIG_PATH, DEFAULT_CONFIG_PATH + ".backup")
    if os.path.exists(EXAMPLE_CONFIG_PATH):
        os.rename(EXAMPLE_CONFIG_PATH, EXAMPLE_CONFIG_PATH + ".backup")

    config_none = load_config()
    if config_none is None:
        print("Config not loaded (as expected, no files exist).")

    if os.path.exists(DEFAULT_CONFIG_PATH + ".backup"):
        os.rename(DEFAULT_CONFIG_PATH + ".backup", DEFAULT_CONFIG_PATH)
    if os.path.exists(EXAMPLE_CONFIG_PATH + ".backup"):
        os.rename(EXAMPLE_CONFIG_PATH + ".backup", EXAMPLE_CONFIG_PATH)

    print("\nConfig loader test finished.")
