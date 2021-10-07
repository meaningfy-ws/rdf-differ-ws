

import pathlib
from typing import List

from werkzeug.exceptions import NotFound

from rdf_differ.config import APPLICATION_PROFILES_ROOT_FOLDER
from rdf_differ.services import list_folders_from_path, list_files_from_path

QUERIES_SUBFOLDER = "queries"
TEMPLATE_VARIANTS_SUBFOLDER = "template_variants"


class ApplicationProfileManager:
    """
    This class will
        * list of ap names
        * path to chosen ap queries
        * list of chosen ap template types
        * path to chosen template type of a chosen ap
    """

    def __init__(self, application_profile: str, template_type: str,
                 root_folder: pathlib.Path = APPLICATION_PROFILES_ROOT_FOLDER):
        self.root_folder = root_folder
        self.application_profile = application_profile
        self.template_type = template_type

    def path_to_ap_folder(self) -> pathlib.Path:
        """
            returns the path to a chosen AP
        """
        if not self.root_folder.exists():
            raise FileNotFoundError(f"The root folder '{self.root_folder}' is not found.")
        return self.root_folder / self.application_profile

    def list_aps(self) -> List[str]:
        """
            returns a set of APs discovered in the root folder
        """
        if not self.root_folder.exists():
            raise FileNotFoundError(f"The root folder '{self.root_folder}' is not found.")
        return list_folders_from_path(self.root_folder)

    def queries_folder(self) -> pathlib.Path:
        """
            returns the path to the queries folder of a chosen AP
        """
        if not self.path_to_ap_folder().exists():
            raise LookupError(f"the AP named '{self.application_profile}' is not found.")
        queries_folder_path = self.path_to_ap_folder() / QUERIES_SUBFOLDER
        if not queries_folder_path.exists():
            raise FileNotFoundError(f"The queries folder '{queries_folder_path}' is not found.")

        return queries_folder_path

    def get_queries_dict(self) -> dict:
        """
            returns a dictionary of the existing queries in the queries folder of the chosen AP
            the dictionary will contain the filename and the path to the file
        """
        if not self.queries_folder().exists():
            raise FileNotFoundError(f"The queries folder '{self.queries_folder()}' is not found.")
        queries_dict = {}
        list_of_query_files = list_files_from_path(self.queries_folder())
        for query in list_of_query_files:
            queries_dict[query] = str(self.queries_folder() / query)

        return queries_dict

    def template_variants_folder(self) -> pathlib.Path:
        """
            returns the path to the template_variants folder of a chosen AP
        """
        if not self.path_to_ap_folder().exists():
            raise LookupError(f"the AP named '{self.application_profile}' is not found.")
        template_variants_folder_path = self.path_to_ap_folder() / TEMPLATE_VARIANTS_SUBFOLDER
        if not template_variants_folder_path.exists():
            raise NotFound(f"The template_variants folder '{template_variants_folder_path}' is not found.")

        return template_variants_folder_path

    def list_template_variants(self) -> List[str]:
        """
            returns the list of discovered template variants for a chosen AP
        """
        if self.application_profile not in self.list_aps():
            raise NotFound(f"the AP named '{self.application_profile}' is not found.")
        if not self.template_variants_folder().exists():
            raise NotFound(f"the template variations folder '{self.template_variants_folder()}' is not found.")
        return list_folders_from_path(self.template_variants_folder())

    def template_folder(self) -> pathlib.Path:
        """
            returns the path to the folder of a chosen template variant for a chosen AP
        """
        if self.template_type not in self.list_template_variants():
            raise NotFound(f"the template type named '{self.template_type}' is not found.")
        template_folder_path = self.template_variants_folder() / self.template_type

        return template_folder_path






