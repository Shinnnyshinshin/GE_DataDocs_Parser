import ast
import os
from collections import namedtuple
import re
from typing import Iterator, Optional, Union, List, Mapping, Tuple, Set
import logging

logger = logging.getLogger(__name__)

ANNOTATION_KEY = "Feature: "

# -> is named Summary
# Expecation Completeness is missing
FeatureAnnotation = namedtuple("FeatureAnnotation", ["Feature", "Summary", "API_Stability", "Implementation_Completeness", "Unit_Test_Coverage", "Infrastructure_Coverage","Documentation_Completeness","Bug_Risk"])
AnnotatedNode = namedtuple("AnnotatedNode", ["name", "path", "annotation", "type_", "id"])
AnnotatedEdge = namedtuple("AnnotatedEdge", ["id_1", "id_2", "annotation"])
EdgeAnnotation = namedtuple("EdgeAnnotation", ["edge_type"])

def build_annotations(path: str) -> Mapping[str, Mapping]:

    annotation_tree = {
        "store_backend": {
            "title": "Backend stores",
            "description": "Provide connection to storage systems for expectation suites, validation results, " \
                           "data docs, and other Data Context artifacts."
        }
    }

    nodes = []
    logger.info(f"working through path {path}")
    #path = os.path.abspath(os.path.expanduser(path))
    path = os.path.abspath(path)
    directory_iter = walk_directory(path) # iterator(filepath of python file, ast object)

    #print(directory_iter)
    for filepath, ast_tree in directory_iter:
        nodes = nodes + walk_tree(filepath, ast_tree)

    nodes = [node for node in nodes if node.annotation is not None]
    print(nodes)

    #feature_types = set([node.annotation.feature_type for node in nodes])
    #for feature_type in feature_types:
    #   if feature_type not in annotation_tree:
    #        annotation_tree[feature_type] = dict()
    #    annotation_tree[feature_type]["cases"] = [
    #        {
    #            "Feature": node.annotation.Feature,
    #            "Summary": node.annotation.Summary,
    #            "API_Stability": node.annotation.API_Stability,
    #        }
    #        for node in nodes if node.annotation.feature_type == feature_type
    #    ]
    #return annotation_tree



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




def walk_tree(basename: str, tree: ast.AST, include_empty: bool = True) -> List[AnnotatedNode]:
    """Parse AST tree, generating nodes and edges."""
    nodes = []
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
        if annotation is not None or include_empty:
            nodes.append(AnnotatedNode(name, basename, annotation, type(node).__name__, name))
    return nodes

def _parse_feature_annotation(docstring: Union[str, List[str], None]) -> Optional[FeatureAnnotation]:
    """Parse a docstring and return a feature annotation."""
    if docstring is None:
        return
    if isinstance(docstring, str):
        docstring = docstring.splitlines()
    in_annotation = False
    annotation = dict()
    for line in docstring:
        if in_annotation and line.strip() == "":
            in_annotation = False
        elif line[0:9] == ANNOTATION_KEY:
            logger.debug("Found annotation")
            in_annotation = True
        # ALL THE KEYS ARE HANDLED : THE -> is not handled yet
        if in_annotation:
            line_fields = line.split(":", 1)
            for key in FeatureAnnotation._fields:
                #print(key)
                if line_fields[0].replace(" ", "_") == key:
                    try:
                        annotation[key] = line_fields[1].strip()
                    except IndexError:
                        logger.warning(f"Found annotation with key {key}, but no value.")
                elif key == "Summary":
                    if line_fields[0].replace(" ", "")[0:2] == "->":
                        try:
                            annotation["Summary"] = line_fields[0].replace(" ", "").split('->')[1]
                        except IndexError:
                            logger.warning(f"Found annotation with key {key}, but no value.")

    if len(annotation) > 0:
        return FeatureAnnotation(**annotation)


def main():
    res = build_annotations("/Users/work/Development/great_expectations")

if __name__ == "__main__":
    logging.basicConfig(filename='will.log', level=logging.WARNING)
    main()
