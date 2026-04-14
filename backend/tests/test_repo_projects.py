import pytest
from unittest.mock import patch, MagicMock

from repositories.projects import (
    list_projects,
    get_project,
    create_project,
    update_project,
    delete_project,
    compute_scores,
    list_project_candidates,
    get_project_stakeholder_links,
)


def test_compute_scores_all_fives():
    project = {
        "roi_potential": 5,
        "implementation_effort": 5,
        "strategic_alignment": 5,
        "stakeholder_readiness": 5,
    }
    result = compute_scores(project)
    assert result["total_score"] == 20
    assert result["tier"] == 1


def test_compute_scores_all_ones():
    project = {
        "roi_potential": 1,
        "implementation_effort": 1,
        "strategic_alignment": 1,
        "stakeholder_readiness": 1,
    }
    result = compute_scores(project)
    assert result["total_score"] == 4
    assert result["tier"] == 4


def test_compute_scores_missing_values():
    project = {"roi_potential": 4}
    result = compute_scores(project)
    assert result["total_score"] == 4
    assert result["tier"] == 4


def test_compute_scores_tier_boundaries():
    assert compute_scores({"roi_potential": 4, "implementation_effort": 4, "strategic_alignment": 4, "stakeholder_readiness": 4})["tier"] == 1
    assert compute_scores({"roi_potential": 3, "implementation_effort": 3, "strategic_alignment": 3, "stakeholder_readiness": 3})["tier"] == 2
    assert compute_scores({"roi_potential": 2, "implementation_effort": 2, "strategic_alignment": 2, "stakeholder_readiness": 2})["tier"] == 3
    assert compute_scores({"roi_potential": 1, "implementation_effort": 1, "strategic_alignment": 1, "stakeholder_readiness": 1})["tier"] == 4


@patch("repositories.projects.pb")
def test_list_projects(mock_pb):
    mock_pb.get_all.return_value = [
        {"id": "abc", "project_code": "T01", "title": "Test", "roi_potential": 5,
         "implementation_effort": 5, "strategic_alignment": 5, "stakeholder_readiness": 5}
    ]
    result = list_projects()
    mock_pb.get_all.assert_called_once()
    assert len(result) == 1
    assert result[0]["total_score"] == 20
    assert result[0]["tier"] == 1


@patch("repositories.projects.pb")
def test_get_project_not_found(mock_pb):
    mock_pb.get_record.return_value = None
    result = get_project("nonexistent")
    assert result is None
