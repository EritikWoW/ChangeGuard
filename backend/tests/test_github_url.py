import pytest
from app.services.github_service import parse_pr_url


def test_parse_pr_url():
    ref = parse_pr_url('https://github.com/openai/openai-python/pull/123')
    assert ref.owner == 'openai'
    assert ref.repo == 'openai-python'
    assert ref.number == 123


def test_reject_non_pr_url():
    with pytest.raises(ValueError):
        parse_pr_url('https://github.com/openai/openai-python')
