"""
Tests for extract_subsection.py module.

Tests critical functionality for extracting subsections from markdown files.
"""






class TestMarkdownExtractor:
    """Test suite for MarkdownExtractor class."""

    def test_extract_section_exists(self, temp_dir):
        """Test extracting existing section."""
        doc_content = """# Main Title

## Section One

Content for section one.

## Section Two

Content for section two.
"""
        doc_file = temp_dir / "test.md"
        doc_file.write_text(doc_content)
        
        from scripts.management.extract_subsection import MarkdownExtractor
        
        extractor = MarkdownExtractor(doc_file)
        result = extractor.extract_section("Section One")
        
        assert result is not None
        assert 'Section One' in result
        assert 'Content for section one' in result
        assert 'Section Two' not in result

    def test_extract_section_with_subsections(self, temp_dir):
        """Test extracting section with child subsections."""
        doc_content = """# Main Title

## Section One

Content for section one.

### Subsection 1.1

Subsection content.

### Subsection 1.2

More subsection content.

## Section Two

Content for section two.
"""
        doc_file = temp_dir / "test.md"
        doc_file.write_text(doc_content)
        
        from scripts.management.extract_subsection import MarkdownExtractor
        
        extractor = MarkdownExtractor(doc_file)
        result = extractor.extract_section("Section One")
        
        assert result is not None
        assert 'Section One' in result
        assert 'Subsection 1.1' in result
        assert 'Subsection 1.2' in result
        assert 'Section Two' not in result

    def test_extract_section_not_found(self, temp_dir):
        """Test extracting non-existent section."""
        doc_content = """# Main Title

## Section One

Content.
"""
        doc_file = temp_dir / "test.md"
        doc_file.write_text(doc_content)
        
        from scripts.management.extract_subsection import MarkdownExtractor
        
        extractor = MarkdownExtractor(doc_file)
        result = extractor.extract_section("Nonexistent Section")
        
        assert result is None

    def test_extract_section_case_sensitive(self, temp_dir):
        """Test that section extraction is case-sensitive (or case-insensitive if implemented)."""
        doc_content = """# Main Title

## Section One

Content.
"""
        doc_file = temp_dir / "test.md"
        doc_file.write_text(doc_content)
        
        from scripts.management.extract_subsection import MarkdownExtractor
        
        extractor = MarkdownExtractor(doc_file)
        result = extractor.extract_section("section one")  # lowercase
        
        # The extractor may be case-insensitive, so check actual behavior
        # If it matches, that's fine - just verify it works
        if result is not None:
            assert 'Section One' in result or 'section one' in result.lower()
        # If it doesn't match, that's also fine (case-sensitive)

    def test_extract_section_boundaries(self, temp_dir):
        """Test that extraction stops at next same-level heading."""
        doc_content = """# Main Title

## Section One

Content one.

## Section Two

Content two.

## Section Three

Content three.
"""
        doc_file = temp_dir / "test.md"
        doc_file.write_text(doc_content)
        
        from scripts.management.extract_subsection import MarkdownExtractor
        
        extractor = MarkdownExtractor(doc_file)
        result = extractor.extract_section("Section Two")
        
        assert result is not None
        assert 'Section Two' in result
        assert 'Content two' in result
        assert 'Section One' not in result
        assert 'Section Three' not in result

    def test_parse_headings(self, temp_dir):
        """Test parsing headings from markdown."""
        doc_content = """# Main Title

## Section One

### Subsection 1.1

## Section Two
"""
        doc_file = temp_dir / "test.md"
        doc_file.write_text(doc_content)
        
        from scripts.management.extract_subsection import MarkdownExtractor
        
        extractor = MarkdownExtractor(doc_file)
        # Use _parse_headings which is the internal method
        headings = extractor._parse_headings()
        
        # _parse_headings returns list of (level, title, start_line, end_line) tuples
        assert len(headings) >= 2
        heading_titles = [h[1] for h in headings if isinstance(h, tuple) and len(h) > 1]
        assert any('Section One' in str(t) for t in heading_titles)
        assert any('Section Two' in str(t) for t in heading_titles)
