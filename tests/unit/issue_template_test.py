"""Unit tests for GitHub issue templates validation."""

import os

import pytest
import yaml


@pytest.mark.unit
class TestIssueTemplates:
    """Test suite for validating GitHub issue template structure."""

    @pytest.fixture
    def template_dir(self):
        """Return the path to the issue templates directory."""
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        return os.path.join(repo_root, ".github", "ISSUE_TEMPLATE")

    @pytest.fixture
    def advanced_template_path(self, template_dir):
        """Return the path to the advanced issue template."""
        return os.path.join(template_dir, "06_advanced_issue.yml")

    def test_advanced_issue_template_exists(self, advanced_template_path):
        """Test that the advanced issue template file exists."""
        assert os.path.exists(advanced_template_path), (
            f"Advanced issue template not found at {advanced_template_path}"
        )

    def test_advanced_issue_template_is_valid_yaml(self, advanced_template_path):
        """Test that the advanced issue template is valid YAML."""
        with open(advanced_template_path, 'r') as f:
            data = yaml.safe_load(f)
            assert data is not None, "Template YAML is empty or invalid"

    def test_advanced_issue_template_has_required_fields(self, advanced_template_path):
        """Test that the advanced issue template has all required fields."""
        with open(advanced_template_path, 'r') as f:
            data = yaml.safe_load(f)

            # Verify required top-level fields
            assert 'name' in data, "Template must have a 'name' field"
            assert 'description' in data, "Template must have a 'description' field"
            assert 'title' in data, "Template must have a 'title' field"
            assert 'labels' in data, "Template must have a 'labels' field"
            assert 'body' in data, "Template must have a 'body' field"

    def test_advanced_issue_template_has_correct_label(self, advanced_template_path):
        """Test that the advanced issue template has the 'advanced' label."""
        with open(advanced_template_path, 'r') as f:
            data = yaml.safe_load(f)
            labels = data.get('labels', [])
            assert 'advanced' in labels, "Template must include 'advanced' label"

    def test_advanced_issue_template_has_correct_title_prefix(self, advanced_template_path):
        """Test that the advanced issue template has the correct title prefix."""
        with open(advanced_template_path, 'r') as f:
            data = yaml.safe_load(f)
            title = data.get('title', '')
            assert title.startswith('[Advanced]:'), (
                "Template title must start with '[Advanced]:'"
            )

    def test_advanced_issue_template_has_body_sections(self, advanced_template_path):
        """Test that the advanced issue template has expected body sections."""
        with open(advanced_template_path, 'r') as f:
            data = yaml.safe_load(f)
            body = data.get('body', [])

            # Extract all textarea IDs
            textarea_ids = []
            for item in body:
                if item.get('type') == 'textarea' and 'id' in item:
                    textarea_ids.append(item['id'])

            # Verify key sections are present
            expected_sections = ['problem', 'solution', 'acceptance-criteria']
            for section in expected_sections:
                assert section in textarea_ids, (
                    f"Template must include '{section}' section"
                )
