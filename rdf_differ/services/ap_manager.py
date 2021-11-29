

import pathlib
from typing import List


from rdf_differ.config import APPLICATION_PROFILES_ROOT_FOLDER
from rdf_differ.utils.file_utils import dir_exists, list_folders_from_path, list_files_from_path

QUERIES_SUBFOLDER = "queries"
TEMPLATE_VARIANTS_SUBFOLDER = "template_variants"


class ApplicationProfileManager:
    """
    This class will get details about application profiles
    """

    def __init__(self, application_profile: str = None, template_type: str = None,
                 root_folder: pathlib.Path = pathlib.Path(APPLICATION_PROFILES_ROOT_FOLDER)):
        self.root_folder = root_folder
        self.application_profile = application_profile
        self.template_type = template_type

    def get_path_to_ap_folder(self) -> pathlib.Path:
        """
            Method to get the path to the chosen AP folder
            :return:  pathlib.Path
        """
        if not dir_exists(self.root_folder):
            raise FileNotFoundError(f"The root folder '{self.root_folder}' is not found.")
        return self.root_folder / self.application_profile

    def list_aps(self) -> List[str]:
        """
            Method to list the APs discovered in the root folder
            :return: List[APs]
        """
        if not dir_exists(self.root_folder):
            raise FileNotFoundError(f"The root folder '{self.root_folder}' is not found.")
        return list_folders_from_path(self.root_folder)

    def get_queries_folder(self) -> pathlib.Path:
        """
            Method to get the path to the queries folder of a chosen AP
            :return:  pathlib.Path
        """
        if not dir_exists(self.get_path_to_ap_folder()):
            raise LookupError(f"the AP named '{self.application_profile}' is not found.")
        queries_folder_path = self.get_path_to_ap_folder() / QUERIES_SUBFOLDER
        if not dir_exists(queries_folder_path):
            raise FileNotFoundError(f"The queries folder '{queries_folder_path}' is not found.")

        return queries_folder_path

    def get_queries_dict(self) -> dict:
        """
            Method to get a dictionary of the existing queries in the queries folder of the chosen AP
            :return:  Dict {query_filename: path_to_the_query_file}
        """
        if not dir_exists(self.get_queries_folder()):
            raise FileNotFoundError(f"The queries folder '{self.get_queries_folder()}' is not found.")
        queries_dict = {}
        list_of_query_files = list_files_from_path(self.get_queries_folder())
        for query in list_of_query_files:
            queries_dict[query] = str(self.get_queries_folder() / query)

        return queries_dict

    def get_template_variants_folder(self) -> pathlib.Path:
        """
            Method to get the path to the template_variants folder of a chosen AP
            :return:  pathlib.Path
        """
        if not dir_exists(self.get_path_to_ap_folder()):
            raise LookupError(f"the AP named '{self.application_profile}' is not found.")
        template_variants_folder_path = self.get_path_to_ap_folder() / TEMPLATE_VARIANTS_SUBFOLDER
        if not dir_exists(template_variants_folder_path):
            raise FileNotFoundError(f"The template_variants folder '{template_variants_folder_path}' is not found.")

        return template_variants_folder_path

    def list_template_variants(self) -> List[str]:
        """
            Method to list discovered template variants for a chosen AP
            :return: List[template variants]
        """
        if self.application_profile not in self.list_aps():
            raise LookupError(f"the AP named '{self.application_profile}' is not found.")
        if not dir_exists(self.get_template_variants_folder()):
            raise FileNotFoundError(f"the template variations folder '{self.get_template_variants_folder()}' is not found.")
        return list_folders_from_path(self.get_template_variants_folder())

    def get_template_folder(self) -> pathlib.Path:
        """
            Method to get the path template variant folder for a chosen AP
            :return:  pathlib.Path
        """
        if self.template_type not in self.list_template_variants():
            raise LookupError(f"the template type named '{self.template_type}' is not found.")
        template_folder_path = self.get_template_variants_folder() / self.template_type

        return template_folder_path
