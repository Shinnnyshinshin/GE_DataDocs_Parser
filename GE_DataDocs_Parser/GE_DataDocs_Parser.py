import ast
import json
import logging
import os
import re
import great_expectations as ge
from typing import Iterator, Union, List, Dict, Type

# code to make sure this work

logger = logging.getLogger(__name__)

# REGEX that is used to extract annotation information from DataDocs
ANNOTATION_REGEX = ""
ANNOTATION_REGEX += "[ ]*(id:.*)[\n]"
ANNOTATION_REGEX += "[ ]*(title:.*)[\n]"
ANNOTATION_REGEX += "[ ]*(icon:.*)[\n]"
ANNOTATION_REGEX += "[ ]*(short_description:.*)[\n]"
ANNOTATION_REGEX += "[ ]*(description:.*)[\n]"
ANNOTATION_REGEX += "[ ]*(how_to_guide_url:.*)[\n]"
ANNOTATION_REGEX += "[ ]*(maturity:.*)[\n]"
ANNOTATION_REGEX += "[ ]*(maturity_details:.*)[\n]"
ANNOTATION_REGEX += "[ ]*(api_stability:.*)[\n]"
ANNOTATION_REGEX += "[ ]*(implementation_completeness:.*)[\n]"
ANNOTATION_REGEX += "[ ]*(unit_test_coverage:.*)[\n]"
ANNOTATION_REGEX += "[ ]*(integration_infrastructure_test_coverage:.*)[\n]"
ANNOTATION_REGEX += "[ ]*(documentation_completeness:.*)[\n]"
ANNOTATION_REGEX += "[ ]*(bug_risk:.*)[\n]"
annotation_regex_compiled = re.compile(ANNOTATION_REGEX)

# for extracting nested dict that contains maturity details
maturity_details_keys = ["api_stability", "implementation_completeness", "unit_test_coverage", "integration_infrastructure_test_coverage", "documentation_completeness", "bug_risk"]

# all annotation fields are stored as a global dict
full_annotation = Dict[str, str]


def build_annotations(folder_to_annotate: object, in_json: object) -> object:
    """
    Entry-point into parser script from CLI

    Args:
        folder_to_annotate: PATH to Great Expectations folder
        in_json: TOC file for all Feature Maturity Grid annotations

    Returns:
        JSON that can be used as input for the Feature Maturity Grid
    """
    _build_full_annotation_dict(folder_to_annotate)
    return _process_toc(in_json)


def _build_full_annotation_dict(path: str) -> None:
    """
    Args:
        path: PATH to Great Expectations folder (passed in from build_annotations function)

    Returns:
        None: will modify global full_annotation dict directly

    """
    logger.info(f"working through path {path}")
    path = os.path.abspath(path)
    directory_iter = _walk_directory(path)  # iterator(filepath of python file, ast object)
    for filepath, ast_tree in directory_iter:
        _walk_tree(filepath, ast_tree)


def _process_toc(in_json: str) -> Dict[str, str]:
    """
        Updates the TOC JSON file to include the annotations we have parsed from DataDocs
    Args:
        in_json: TOC file for all Feature Maturity Grid annotations (passed in from build_annotations)

    Returns:
        dictionary that is the updated TOC JSON
    """
    with open(in_json) as json_file:
        loaded_json = json.load(json_file)
        for title in loaded_json:
            for section_features in title["section_features"]:
                all_cases = section_features["cases"]
                for index in range(len(all_cases)):
                    if all_cases[index]["id"] in full_annotation.keys():
                        all_cases[index] = full_annotation[all_cases[index]["id"]]
                section_features["cases"] = all_cases
    return loaded_json


def _walk_directory(path: str) -> Iterator[ast.AST]:
    """
    Does an os.walk through the input PATH to read all .py files and load them as abstract syntax tree (AST) objects, which can be parsed
    Args:
        path: path of great_expectations folder

    Returns:
        Iterator of resulting AST objects
    """
    logger.info(f"Beginning to parse path {path}")
    for root, dirs, files in os.walk(path):
        for file in files:
            if not file.endswith(".py"):
                logger.info(f"skipping file {file}")
                continue
            filepath = os.path.join(root, file)
            with open(filepath, 'r') as srcfile:
                logger.info(f"parsing file {file}")
                yield os.path.relpath(filepath, path), ast.parse(srcfile.read())


def _walk_tree(tree: ast.AST) -> None:
    """

    Args:
        tree: ast.AST tree for each .py file in Great Expectations directory

    Returns:
        None: modifies global full_annotation dict directly.
    """
    annotation_list = None
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef)):
            continue
        annotation_list = _parse_feature_annotation(ast.get_docstring(node))
        if annotation_list is not None:
            for annotation in annotation_list:
                # key is annotation["id"] and
                full_annotation[annotation["id"]] = annotation



def _parse_feature_annotation(docstring: Union[str, List[str], None]) -> List[Type[Dict[any, any]]]:
    """

    Args:
        docstring: docstring object that is parsed from ast.get_docstring(node) (passed in from _walk_tree method)

    Returns:
        list_of_annotations: list of dictionaries that contain one annotation per dictionay
    """

    list_of_annotations = []
    id_val = ""
    if docstring is None:
        return
    if isinstance(docstring, str):
        for matches in re.findall(annotation_regex_compiled, docstring):
            annotation_dict = Dict[str, str] # create new dictionary for each match
            maturity_details_dict = Dict[str, str]
            for matched_line in matches:
                # split matched line_fields
                matched_line_fields = matched_line.split(":")
                this_key = matched_line_fields[0].strip()
                this_val = matched_line_fields[1].strip()

                if this_key == "id":
                    id_val = this_val

                if this_key in maturity_details_keys:
                    maturity_details_dict[this_key] = this_val
                elif this_key == "icon": # icon is a special case
                    if this_val is "":
                        annotation_dict[this_key] = f"https://great-expectations-web-assets.s3.us-east-2.amazonaws.com/feature_maturity_icons/{id_val}.png"
                    else:
                        annotation_dict[this_key] = this_val
                else:
                    annotation_dict[this_key] = this_val

            annotation_dict["maturity_details"] = maturity_details_dict
            if annotation_dict is not None:
                list_of_annotations.append(annotation_dict)

    return list_of_annotations
