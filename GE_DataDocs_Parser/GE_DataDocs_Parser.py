import ast
import os
from collections import namedtuple
import re
from typing import Iterator, Optional, Union, List, Mapping, Tuple, Set, Dict
import logging
import json

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

AnnotatedNode = namedtuple("AnnotatedNode", ["name", "path", "annotation", "type_"])

def build_annotations(path: str) -> Mapping[str, Mapping]:
    annotation_tree = {
        "store_backend": {
            "title": "Backend stores",
            "description": "Provide connection to storage systems for expectation suites, validation results, " \
                           "data docs, and other Data Context artifacts."
        }
    }

    nodes = []
    print(f"working through path {path}")
    logger.info(f"working through path {path}")
    path = os.path.abspath(path)
    directory_iter = walk_directory(path) # iterator(filepath of python file, ast object)

    for filepath, ast_tree in directory_iter:
        nodes = nodes + walk_tree(filepath, ast_tree)

    #for node in nodes:
    #    print(node)
    #    print("--------")
    #feature_types = ""
    return nodes


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


def walk_tree(basename: str, tree: ast.AST, include_empty: bool = False) -> List[AnnotatedNode]:
    """Parse AST tree, generating nodes and edges."""
    nodes = []
    annotation = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef)):
            continue

        annotation = _parse_feature_annotation(ast.get_docstring(node))
        if isinstance(node, ast.Module):
            name = os.path.basename(basename)
        else:
            name = node.name
        if name.endswith(".py"):
            name = name[:-3]

        if annotation is not None and len(annotation) > 0 or include_empty:
            nodes.append(AnnotatedNode(name, basename, annotation, type(node).__name__))

    return nodes


def _parse_feature_annotation(docstring: Union[str, List[str], None]):
    """Parse a docstring and return a feature annotation."""
    list_of_annotations = []
    id_val = ""
    if docstring is None:
        return
    if isinstance(docstring, str):
        for matches in re.findall(annotation_regex_compiled, docstring):
            print(docstring)

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
                elif this_key == "icon": # icon is a special cases
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






#def main():
    #res = build_annotations("/Users/work/Development/GE_DataDocs_Parser/test_folder")
#    res = build_annotations("/Users/work/Development/great_expectations")


#if __name__ == "__main__":
#    logging.basicConfig(filename='will.log', level=logging.WARNING)
#    main()
