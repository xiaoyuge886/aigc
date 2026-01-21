#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick script to check spaCy model location and info"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.script_utils import configure_utf8_output, suppress_pydantic_v1_warning
configure_utf8_output()
suppress_pydantic_v1_warning()  # Must be called before spacy import

from utils.logging_utils import get_or_setup_logger
logger = get_or_setup_logger(__file__, log_category="diagnostics")

def main() -> None:
    logger.start()
    exit_code = 0
    try:
        try:
            import en_core_web_sm
            model_path = Path(en_core_web_sm.__file__)
            print(f"Model installed at: {model_path}")
            print(f"Model directory: {model_path.parent}")
            logger.track_metric('model_found', True)
            logger.track_metric('model_path', str(model_path))
        except ImportError:
            print("Model not installed")
            logger.track_metric('model_found', False)
            exit_code = 1
            raise SystemExit(1)

        try:
            from spacy.lang.en.stop_words import STOP_WORDS
            print(f"spaCy available")
            print(f"Stop words count: {len(STOP_WORDS)}")
            print(f"Sample stop words: {list(STOP_WORDS)[:10]}")
            logger.track_metric('spacy_available', True)
            logger.track_metric('stop_words_count', len(STOP_WORDS))
        except ImportError:
            print("spaCy not installed")
            logger.track_metric('spacy_available', False)
        
        logger.end(exit_code=exit_code)
        
    except SystemExit:
        raise
    except Exception as e:
        logger.log_error("Fatal error", error=e)
        exit_code = 1
        logger.end(exit_code=exit_code)
        sys.exit(exit_code)

if __name__ == '__main__':
    main()

