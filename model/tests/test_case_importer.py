# Ignore PEP8 protected-access to client class | pylint: disable=W0212
"""
This module contains all tests for the CaseImporter() class
"""
import pytest
from core.case_importer import CaseImporter


@pytest.fixture(name="import_beerwiser")
def fixture_import_beerwiser():
    """
    This fixture initialises a CaseImporter for the Beerwiser case.
    :return: an CaseImporter class for Beerwiser
    """
    return CaseImporter(...)
