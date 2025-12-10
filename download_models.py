"""Script to download Stanza English models into `stanza_models/` directory.

Run before building an executable to include models in the distribution.
"""
import os
import stanza


def main() -> None:
    """Download required Stanza models into local `stanza_models` directory."""
    target_dir = os.path.join(os.path.dirname(__file__), "stanza_models")
    os.makedirs(target_dir, exist_ok=True)
    print(f"Downloading Stanza English models into: {target_dir}")
    stanza.download("en", processors="tokenize,ner", model_dir=target_dir)
    print("Download complete.")


if __name__ == "__main__":
    main()
