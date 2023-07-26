"""
This module contains the CaseImporter() class. This class deals with importing and validating an RBS case.
"""
from pathlib import Path
import warnings
import pandas as pd
import numpy as np


class TemplateError(Exception):
    """
    This class deals with the error handling of our CaseImporter().
    """

    def __init__(self, message):  # ignore warning about super-init | pylint: disable=W0231
        self.message = message

    def __str__(self):
        return f"Template Error: {self.message}"


class CaseImporter:
    """
    This class deals with import and validation of an RBS case, either as csv, xlsx or json.
    :param file_path: Path to folder that contains a folder structure of at least "name" - "file_format"
    """

    def __init__(self, file_path, name, extension):
        self.path_base = Path(file_path) / name / extension
        self.file_path = file_path
        self.name = name
        self.extension = extension
        self.importers = {
            "csv": lambda table: pd.read_csv(self.path_base / f"{table}.csv", sep=";"),
            "json": lambda table: pd.read_json(self.path_base / f"{table}.json", orient="table"),
            "xlsx": lambda table: pd.read_excel(self.path_base / f"{self.name}.xlsx", sheet_name=table),
        }
        self.dataframes_dict = {}
        self.input_dict = {}

        # -- Build template validators based on template.xlsx
        self.validate_dict = self._build_template_validators()

    @staticmethod
    def _build_template_validators():
        template = pd.read_excel(Path(__file__).parent.parent / "data/template.xlsx", sheet_name=None)
        return {key: value.columns.values.tolist() for key, value in template.items()}

    def _check_data_columns(self, to_check, table):
        column_list = to_check.values.tolist()

        # 1. Validate all necessary columns are there
        missing_cols = [col for col in self.validate_dict[table] if col not in column_list]
        if missing_cols:
            raise TemplateError(f"column(s) '{', '.join(missing_cols)}' are missing for '{table}'")
        # 2. Warn the user about columns that will not be used
        extra_cols = [col for col in column_list if col not in self.validate_dict[table]]
        if extra_cols:
            warnings.warn(f"column(s) '{', '.join(extra_cols)}' are not used for '{table}'")

    def _create_dataframes_dict(self, table):
        try:
            table_data = self.importers[self.extension](table)
        except ValueError as value_error:
            raise TemplateError(f"Sheet '{table}' is missing") from value_error
        self._check_data_columns(table_data.columns, table)
        self.dataframes_dict[table] = table_data

    def _convert_to_numpy_arrays_2d(self, table, data):
        print(data.columns)
        target_column = [col for col in data.columns if col.endswith("_variable_input")]
        if len(target_column) != 1:
            raise TemplateError(f"Too many '_variable_input' columns in {table}")

        # prepare and store data
        pivoted_data = data.pivot(index=table[:-1], columns=target_column[0], values="value")
        self.input_dict[table] = pivoted_data.index.to_numpy()
        self.input_dict[f"{target_column[0]}s"] = pivoted_data.columns.to_numpy()
        self.input_dict[f"{table[:-1]}_value"] = pivoted_data.values

    @staticmethod
    def _apply_first_level_hierarchy_to_row(row, all_inputs):
        if row["argument_1"] in all_inputs and row["argument_2"] in all_inputs:
            return 1
        return 2

    @staticmethod
    def _apply_second_level_hierarchy_to_row(row, data):
        # The order of calculation for hierarchies of level 1 is not important
        if row["hierarchy"] == 1:
            return row["hierarchy"]

        for _, dep in data.iterrows():
            if dep["destination"] == row["argument_1"]:
                row["hierarchy"] += 1
            elif dep["destination"] == row["argument_2"]:
                row["hierarchy"] += 1
        return row["hierarchy"]

    def _convert_to_ordered_dependencies(self, data):
        data[["argument_1", "argument_2"]] = data[["argument_1", "argument_2"]].fillna("")
        all_inputs = np.hstack(
            (
                self.input_dict["fixed_inputs"],
                self.input_dict["internal_variable_inputs"],
                self.input_dict["external_variable_inputs"],
                "",
            )
        ).ravel()

        data["hierarchy"] = data.apply(self._apply_first_level_hierarchy_to_row, all_inputs=all_inputs, axis=1)
        data["hierarchy"] = data.apply(
            self._apply_second_level_hierarchy_to_row, data=data[data["hierarchy"] != 1], axis=1
        )
        data = data.sort_values("hierarchy")

        for col in self.validate_dict["dependencies"]:
            self.input_dict[col] = data[col].to_numpy()
        self.input_dict["dependencies_order"] = data.index.to_numpy()

    def _convert_to_numpy_arrays_weights(self, table, data):
        option, weight = self.validate_dict[table]
        if f"{option}s" not in self.input_dict:
            self.input_dict[f"{option}s"] = data[option].to_numpy()

        ordered_data = pd.DataFrame(self.input_dict[f"{option}s"], columns=[option]).merge(data)
        self.input_dict[f"{option}_{weight}"] = ordered_data[weight].to_numpy()

    def _convert_to_numpy_arrays(self, table, data):
        columns = self.validate_dict[table]
        for col in columns:
            key_name = table if col == table[:-1] else f"{table[:-1]}_{col}"
            self.input_dict[key_name] = data[col].to_numpy()

    def _create_input_dict(self):
        two_dim = ["decision_makers_options", "scenarios"]
        for table, data in self.dataframes_dict.items():
            print(table)
            # Option 1: data is transformed to a matrix
            if table in two_dim:
                self._convert_to_numpy_arrays_2d(table, data)
            # Option 2: data contains dependencies and hierarchy needs to be calculated
            elif table == "dependencies":
                self._convert_to_ordered_dependencies(data)
            # Option 3: data is about weights and need to match order of previously added data
            elif table.endswith("_weights"):
                self._convert_to_numpy_arrays_weights(table, data)
            # Option 4: data is transformed to a vector
            else:
                self._convert_to_numpy_arrays(table, data)

    def import_case(self) -> dict:
        """
        This function creates the input dictionary. It wraps other functions that deal with reading and validating
        the data.
        :return: dictionary with all necessary inputs for a case
        """
        for table in self.validate_dict:
            self._create_dataframes_dict(table)
        self._create_input_dict()
        return self.input_dict
