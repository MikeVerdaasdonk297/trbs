# Ignore PEP8 protected-access to client class | pylint: disable=W0212
"""
This module contains all tests for the CaseImporter() class.
NOTE: only functions that
"""
import warnings
from pathlib import Path
import pytest
import pandas as pd
from core.case_importer import CaseImporter, TemplateError


@pytest.fixture(name="import_beerwiser_json")
def fixture_import_beerwiser_json():
    """
    This fixture initialises a CaseImporter for the beerwiser case.
    :return: an CaseImporter class for the beerwiser case.
    """
    return CaseImporter(Path.cwd() / "data", "beerwiser", "json")


@pytest.fixture(name="import_beerwiser_csv")
def fixture_import_beerwiser_csv():
    """
    This fixture initialises a CaseImporter for the beerwiser case.
    :return: an CaseImporter class for the beerwiser case.
    """
    return CaseImporter(Path.cwd() / "data", "beerwiser", "csv")


@pytest.fixture(name="import_beerwiser_xlsx")
def fixture_import_beerwiser_xlsx():
    """
    This fixture initialises a CaseImporter for the beerwiser case.
    :return: an CaseImporter class for the beerwiser case.
    """
    return CaseImporter(Path.cwd() / "data", "beerwiser", "xlsx")


def test_build_template_validators(import_beerwiser_json):
    """
    This function tests _build_template_validators() to return a dictionary containing the 'table' and necessary
    columns within that table.
    Note: the file extension (here: json) is not relevant for this test, so only one needs to be tested
    :param import_beerwiser_json: an CaseImporter class for the beerwiser case
    """
    result = import_beerwiser_json._build_template_validators()
    expected_result = {
        "configurations": ["configuration", "value"],
        "key_outputs": [
            "key_output",
            "theme",
            "minimum",
            "maximum",
            "monetary",
            "smaller_the_better",
            "linear",
            "automatic",
            "start",
            "end",
            "threshold",
        ],
        "decision_makers_options": ["internal_variable_input", "decision_makers_option", "value"],
        "scenarios": ["external_variable_input", "scenario", "value"],
        "fixed_inputs": ["fixed_input", "value"],
        "dependencies": [
            "destination",
            "argument_1",
            "argument_2",
            "operator",
            "maximum_effect",
            "accessibility",
            "probability_of_success",
            "saturation_point",
        ],
        "theme_weights": ["theme", "weight"],
        "key_output_weights": ["key_output", "weight"],
        "scenario_weights": ["scenario", "weight"],
    }
    assert result == expected_result


@pytest.mark.parametrize(
    "dataframe, table, expected_result",
    [
        (
            pd.DataFrame(columns=["theme", "weight", "EXTRA COL"]),
            "theme_weights",
            pd.DataFrame(columns=["theme", "weight"]),
        ),
        (
            pd.DataFrame(columns=["external_variable_input", "scenario", "value"]),
            "scenarios",
            pd.DataFrame(columns=["external_variable_input", "scenario", "value"]),
        ),
    ],
)
def test_check_data_columns(import_beerwiser_json, dataframe, table, expected_result):
    """
    This function tests _check_data_columns to return the same pd.DataFrame with ONLY the necessary columns. Warnings
    are tested separately below.
    Note: the file extension (here: json) is not relevant for this test, so only one needs to be tested
    :param import_beerwiser_json: an CaseImporter class for the beerwiser case
    :param dataframe: dataframe where the columns need to be checked
    :param table: table name of the dataframe
    :expected_result: dataframe that should be returned by _check_data_columns
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = import_beerwiser_json._check_data_columns(dataframe, table)

    pd.testing.assert_frame_equal(result, expected_result)


def test_check_data_columns_warning(import_beerwiser_json):
    """
    This function tests _check_data_columns to raise a warning when extra columns are provided.
    Note: the file extension (here: json) is not relevant for this test, so only one needs to be tested
    :param import_beerwiser_json: an CaseImporter class for the beerwiser case
    """
    with warnings.catch_warnings(record=True) as warning_list:
        import_beerwiser_json._check_data_columns(
            pd.DataFrame(columns=["fixed_input", "value", "EXTRA COL"]), "fixed_inputs"
        )
    expected_result = "column(s) 'EXTRA COL' are not used for 'fixed_inputs'"
    assert str(warning_list[0].message) == expected_result


def test_check_data_columns_error(import_beerwiser_json):
    """
    This function tests _check_data_column to raise a TemplateError when necessary columns are missing
    Note: the file extension (here: json) is not relevant for this test, so only one needs to be tested
    :param import_beerwiser_json: an CaseImporter class for the beerwiser case
    """
    with pytest.raises(TemplateError) as template_error:
        import_beerwiser_json._check_data_columns(
            pd.DataFrame(columns=["internal_variable_input", "value"]), "decision_makers_options"
        )
    expected_result = "Template Error: column(s) 'decision_makers_option' are missing for 'decision_makers_options'"
    assert str(template_error.value) == expected_result


@pytest.mark.parametrize(
    "fixture_name, table",
    [
        ("import_beerwiser_csv", "dependencies"),
        ("import_beerwiser_json", "key_outputs"),
        ("import_beerwiser_xlsx", "scenarios"),
    ],
)
def test_create_dataframes_dict(fixture_name, table, request):
    """
    This function tests _create_dataframes to update self.dataframes_dict with a new {key: pd.DataFrame} pair.
    Only the structure of the output is tested.
    :param fixture_name: used version of the CaseImporer class. Fixtures differ in used extension / file format
    :param table: name of the table
    :param request: needed to transform fixture_name to a fixture value
    """
    case_importer = request.getfixturevalue(fixture_name)
    case_importer._create_dataframes_dict(table)
    result_structure = {key: type(value) for key, value in case_importer.dataframes_dict.items()}
    expected_structure = {table: pd.DataFrame}
    assert result_structure == expected_structure
