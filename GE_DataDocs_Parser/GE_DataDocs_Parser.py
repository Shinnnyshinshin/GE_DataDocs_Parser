import ast
import json
import logging
import os
import re
from typing import Iterator, Union, List, Dict, Type, Any
import docs.feature_annotation_parser
# code to make sure this work
logger = logging.getLogger(__name__)
# all annotation fields are stored as a global dict
full_annotation = {}


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


def _walk_tree(basename: str, tree: ast.AST) -> None:
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
        annotation_list = docs.feature_annotation_parser.parse_feature_annotation(ast.get_docstring(node))
        if annotation_list is not None:
            for annotation in annotation_list:
                # key is annotation["id"] and
                full_annotation[annotation["id"]] = annotation

