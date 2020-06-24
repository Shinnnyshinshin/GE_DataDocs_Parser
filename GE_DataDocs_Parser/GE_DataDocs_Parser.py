import ast
import json
import logging
import os
import re
from typing import Iterator, Union, List, Dict

logger = logging.getLogger(__name__)

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

maturity_details_keys = ["api_stability", "implementation_completeness", "unit_test_coverage", "integration_infrastructure_test_coverage", "documentation_completeness", "bug_risk"]

# global dictionary for all annotations that already exist in DataDocs
full_annotation = Dict[str, str]


def build_annotations(folder_to_annotate: str, in_json: str):
    """ Entry-point into parser script. Will return the results of process_toc, whichi """
    build_full_annotation_dict(folder_to_annotate)
    return process_toc(in_json)



def process_toc(in_json: str):
    with open(in_json) as json_file:
        data = json.load(json_file)
        for title in data:
            for section_features in title["section_features"]:
                all_cases = section_features["cases"]
                for index in range(len(all_cases)):
                    if all_cases[index]["id"] in full_annotation.keys():
                        all_cases[index] = full_annotation[all_cases[index]["id"]]
                section_features["cases"] = all_cases
    return data


def build_full_annotation_dict(path: str) -> Dict[str, str]:
    logger.info(f"working through path {path}")
    path = os.path.abspath(path)
    directory_iter = walk_directory(path) # iterator(filepath of python file, ast object)
    for filepath, ast_tree in directory_iter:
        walk_tree(filepath, ast_tree)
    return full_annotation


def walk_directory(path: str) -> Iterator[ast.AST]:
    """Walk a directory and provide AST trees for each item."""
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


def walk_tree(basename: str, tree: ast.AST, include_empty: bool = False):
    """Parse AST tree, generating dictionary of annotations"""
    annotation = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef)):
            continue
        annotation = _parse_feature_annotation(ast.get_docstring(node))
        if annotation:
            for annot in annotation:
                full_annotation[annot["id"]] = annot


def _parse_feature_annotation(docstring: Union[str, List[str], None]):
    """Parse a docstring and return a feature annotation."""
    list_of_annotations = []
    id_val = ""
    if docstring is None:
        return
    if isinstance(docstring, str):
        for matches in re.findall(annotation_regex_compiled, docstring):
            annotation_dict = dict() # create new dictionary for each match
            maturity_details_dict = dict()
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
    return(list_of_annotations)
