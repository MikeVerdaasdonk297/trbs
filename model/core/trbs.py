"""
This module contains the TRBS class. This is the parent class that deals with anything related to a Responsible
Business Simulator Case.
"""
from core.case_importer import CaseImporter
from core.evaluate import Evaluate
from core.appreciate import Appreciate
from core.visualize import Visualize


class TheResponsibleBusinessSimulator:
    """
    This class is the base class of an tRBS-case and contains all necessary information to import data, evaluate
    dependencies and calculate appreciations.
    """

    def __init__(self, file_path, file_extension, name):
        self.file_path = file_path
        self.file_extension = file_extension
        self.name = name
        self.input_dict = {}
        self.output_dict = {}
        self.visualizer = None

    def __str__(self):
        input_data_formatted = (
            "\n\n".join(f"{key}\n\t{value}" for key, value in self.input_dict.items())
            if self.input_dict
            else "First .build() a case to import data"
        )
        return (
            f"Case: {self.name} ({self.file_extension}) \n"
            f"Data location: {self.file_path} \n"
            f"Input data: \n {input_data_formatted}"
        )

    def _get_options(self):
        """
        This function calculates the amount of different options (or calculations) of the model:
        Amount of scenarios x Amount of decision makers options x Amount of key outputs
        """
        return (
            len(self.input_dict["scenarios"])
            * len(self.input_dict["decision_makers_options"])
            * len(self.input_dict["key_outputs"])
        )

    def build(self):
        """This function builds all necessary elements for a generic RBS case"""
        print(f"Creating '{self.name}'")
        case_import = CaseImporter(self.file_path, self.name, self.file_extension)
        self.input_dict = case_import.import_case()

    def evaluate(self):
        """This function deals with the evaluation of all dependencies"""
        case_evaluation = Evaluate(self.input_dict)
        self.output_dict = case_evaluation.evaluate_all_scenarios()

    def appreciate(self):
        """This function deals with the appreciation of the outcomes"""
        case_appreciation = Appreciate(self.input_dict, self.output_dict)
        case_appreciation.appreciate_all_scenarios()

    def visualize(self, visual_request, key, **kwargs):
        """This function deals with the visualizations of the outcomes"""
        # Set a Visualize class only if this has not yet been initialised.
        if not self.visualizer:
            self.visualizer = Visualize(self.output_dict, self._get_options())
        return self.visualizer.create_visual(visual_request, key, **kwargs)
