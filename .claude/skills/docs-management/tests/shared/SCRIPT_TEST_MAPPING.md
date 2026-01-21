# Script to Test File Mapping

This document maps all scripts to their corresponding test files (if they exist).

## Scripts with Tests

| Script | Test File | Coverage |
| --- | --- | --- |
| check_dependencies.py | test_check_dependencies.py | ✓ |
| cleanup_drift.py | test_cleanup_drift.py | ✓ |
| cleanup_old_anthropic_docs.py | test_cleanup_old_anthropic_docs.py | ✓ |
| cleanup_scrape.py | test_cleanup_scrape.py | ✓ |
| cli_utils.py | test_cli_utils.py | ✓ |
| config_helpers.py | test_config_helpers.py | ✓ |
| config_loader.py | test_config_loader.py | ✓ |
| config_registry.py | test_config_registry.py | ✓ |
| detect_changes.py | test_detect_changes.py | ✓ |
| http_utils.py | test_http_utils.py | ✓ |
| index_manager.py | test_index_manager.py | ✓ |
| logging_utils.py | test_logging_utils.py | ✓ |
| path_config.py | test_path_config.py | ✓ |
| publication_utils.py | test_publication_utils.py | ✓ |
| script_utils.py | test_script_utils.py | ✓ |
| official_docs_api.py | test_official_docs_api.py | ✓ |
| (integration tests) | test_integration.py | ✓ |
| (drift detection) | test_drift_detection.py | ✓ |
| (utils) | test_utils.py | ✓ |

## Scripts Without Tests

| Script | Priority | Notes |
| --- | --- | --- |
| audit_performance.py | LOW | Utility script, less critical |
| check_dependencies.py | MEDIUM | ✓ test_check_dependencies.py - Basic tests |
| check_spacy_model_location.py | LOW | Diagnostic script |
| cleanup_old_anthropic_docs.py | MEDIUM | ✓ test_cleanup_old_anthropic_docs.py - Basic tests |
| cleanup_scrape.py | MEDIUM | ✓ test_cleanup_scrape.py - Basic tests |
| cleanup_stale.py | MEDIUM | ✓ test_cleanup_stale.py - Basic tests |
| common_paths.py | LOW | ✓ Re-exports path_config, covered by test_path_config.py |
| discover_categories.py | MEDIUM | ✓ test_discover_categories.py - Basic tests |
| doc_resolver.py | HIGH | ✓ test_doc_resolver.py - Comprehensive tests |
| extract_metadata.py | HIGH | ✓ test_extract_metadata.py - Comprehensive tests |
| extract_publication_dates.py | MEDIUM | ✓ Tested via test_publication_utils.py |
| extract_subsection.py | HIGH | ✓ test_extract_subsection.py - Comprehensive tests |
| find_docs.py | HIGH | ✓ test_find_docs.py - Comprehensive tests |
| generate_report.py | LOW | - Reporting script, less critical |
| keyword_stats.py | LOW | - Analysis script, less critical |
| manage_index.py | HIGH | ✓ test_manage_index.py - Comprehensive tests |
| quick_validate.py | MEDIUM | ✓ test_quick_validate.py - Basic tests |
| rebuild_index.py | HIGH | ✓ test_rebuild_index.py - Comprehensive tests |
| refresh_index.py | HIGH | ✓ test_refresh_index.py - Comprehensive tests |
| scrape_all_sources.py | HIGH | ✓ test_scrape_all_sources.py - Comprehensive tests |
| scrape_docs.py | HIGH | ✓ test_scrape_docs.py - Comprehensive tests |
| setup_dependencies.py | MEDIUM | ✓ test_check_dependencies.py - Basic tests |
| setup_references.py | LOW | - Setup script, less critical |
| validate_filtering.py | LOW | - Validation script, less critical |
| validate_index_vs_docs.py | MEDIUM | ✓ test_validate_index_vs_docs.py - Basic tests |
| validate_scraped_docs.py | MEDIUM | ✓ test_validate_scraped_docs.py - Basic tests |
| verify_index.py | MEDIUM | ✓ test_verify_index.py - Basic tests |

## Test Coverage Summary

- **Total Scripts:** 36 (excluding utils)
- **Scripts with Tests:** 17 (direct) + 10 (HIGH priority) + 3 (via integration/utils) = 30 total
- **Scripts without Tests:** 6 (mostly LOW priority)
- **High Priority Missing Tests:** 0 scripts (all HIGH priority scripts have tests)
- **Medium Priority Missing Tests:** 0 scripts (all MEDIUM priority scripts now have tests)
- **Low Priority Missing Tests:** 6 scripts
- **Test Status:** ✅ 294 tests passing, 1 skipped (as of latest run)

## Next Steps

1. ✅ Create tests for HIGH priority scripts without tests - COMPLETE
2. ✅ Create tests for MEDIUM priority scripts without tests - COMPLETE
3. Enhance existing tests for scripts tested via integration/utils (optional)
4. ✅ Run full test suite and fix any failures - COMPLETE (all tests passing)
5. ✅ Verify Windows compatibility - COMPLETE
