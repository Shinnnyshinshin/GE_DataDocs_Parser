import ast
import os
from collections import namedtuple
import re
from typing import Iterator, Optional, Union, List, Mapping, Tuple, Set
import logging
import json


logger = logging.getLogger(__name__)

ANNOTATION_KEY = "id:"

MaturityDetails = namedtuple("MaturityDetails", ["api_stability", "implementation_completeness", "unit_test_coverage", "integration_infrastructure_test_coverage", "documentation_completeness", "bug_risk"])
FeatureAnnotation = namedtuple("FeatureAnnotation", ["id", "title", "icon", "short_description", "description", "how_to_guide_url", "maturity", "maturity_details"])


FULL_REGEX_MATCH = ""
FULL_REGEX_MATCH += "[ ]*(id:.*)[\n]" # 1
FULL_REGEX_MATCH += "[ ]*(title:.*)[\n]" # 2
FULL_REGEX_MATCH += "[ ]*(icon:.*)[\n]" # 3
FULL_REGEX_MATCH += "[ ]*(short_description:.*)[\n]" # 4
FULL_REGEX_MATCH += "[ ]*(description:.*)[\n]"# 5
FULL_REGEX_MATCH += "[ ]*(how_to_guide_url:.*)[\n]"# 6
FULL_REGEX_MATCH += "[ ]*(maturity:.*)[\n]"# 7
FULL_REGEX_MATCH += "[ ]*(maturity_details:.*)[\n]"# 8
FULL_REGEX_MATCH += "[ ]*(api_stability:.*)[\n]" #9
FULL_REGEX_MATCH += "[ ]*(implementation_completeness:.*)[\n]" #10
FULL_REGEX_MATCH += "[ ]*(unit_test_coverage:.*)[\n]" #11
FULL_REGEX_MATCH += "[ ]*(integration_infrastructure_test_coverage:.*)[\n]" #12
FULL_REGEX_MATCH += "[ ]*(documentation_completeness:.*)[\n]" #13
FULL_REGEX_MATCH += "[ ]*(bug_risk:.*)[\n]" #14



ANNOTATION_REGEX_ONLY = ''



maturitydetails_keys = ["api_stability", "implementation_completeness", "unit_test_coverage", "integration_infrastructure_test_coverage", "documentation_completeness", "bug_risk"]



pattern = re.compile(FULL_REGEX_MATCH)


"""
    id: expectations_store_git
    title: Expectation Store - Git
    icon:
    short_description:
    description:
    how_to_guide_url:
    maturity: Production
    maturity_details:
        api_stability: Stable
        implementation_completeness: Complete
        unit_test_coverage: Complete
        integration_infrastructure_test_coverage: N/A
        documentation_completeness: Complete
        bug_risk: Low





{"id": "expectations_store_s3"
    title: Expectation Store - S3
    icon:
    short_description:
    description:
    how_to_guide_url:
    maturity: Beta
    maturity_details":{
        api_stability: Stable
        implementation_completeness: Complete
        unit_test_coverage: Complete
        integration_infrastructure_test_coverage: Minimal
        documentation_completeness: Complete
        bug_risk: Low}
}

# list of dicts [{s3 *****}, {azureblob *****}, {gcs *****}]

if icon is null :
    https://great-expectations-web-assets.s3.us-east-2.amazonaws.com/feature_maturity_icons/{id}.png"
if not then keep


"""


AnnotatedNode = namedtuple("AnnotatedNode", ["name", "path", "annotation", "type_", "id"])
#AnnotatedEdge = namedtuple("AnnotatedEdge", ["id_1", "id_2", "annotation"])
#EdgeAnnotation = namedtuple("EdgeAnnotation", ["edge_type"])

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
    path = os.path.abspath(path)
    directory_iter = walk_directory(path) # iterator(filepath of python file, ast object)

    for filepath, ast_tree in directory_iter:
        nodes = nodes + walk_tree(filepath, ast_tree)

    nodes = [node for node in nodes if node.annotation is not None]
    #print(nodes)
    feature_types = ""
    #feature_types = set([node.annotation.id for node in nodes])
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
    return feature_types



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
        annotation = _parse_feature_annotation_regex(ast.get_docstring(node))
        print(annotation)

        if isinstance(node, ast.Module):
            name = os.path.basename(basename)
        else:
            name = node.name
        if name.endswith(".py"):
            name = name[:-3]
        if annotation is not None or include_empty:
            nodes.append(AnnotatedNode(name, basename, annotation, type(node).__name__, name))
    return nodes




def _parse_feature_annotation_regex(docstring: Union[str, List[str], None]) -> Optional[FeatureAnnotation]:
    """Parse a docstring and return a feature annotation."""
    list_of_annotation = []
    id_val = ""
    if docstring is None:
        return
    if isinstance(docstring, str):
        for matches in re.findall(pattern, docstring):
            annotation_dict = dict() # create new dictionary for each match
            maturity_details_dict = dict()
            #for key in FeatureAnnotation._fields:
            # reversed so that we bduilg the MAturityDetails first
            for matched_line in matches:
                #print(matched_line)
                # split matched line_fields
                matched_line_fields = matched_line.split(":")
                this_key = matched_line_fields[0].strip()
                this_val = matched_line_fields[1].strip()

                if this_key == "id":
                    id_val = this_val

                #temp_maturity = MaturityDetails()
                if this_key in maturitydetails_keys:
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
                list_of_annotation.append(annotation_dict)
    return(list_of_annotation)



def _parse_feature_annotation_ast(docstring: Union[str, List[str], None]) -> Optional[FeatureAnnotation]:
    """Parse a docstring and return a feature annotation."""
    if docstring is None:
        return
    if isinstance(docstring, str):
        docstring = docstring.splitlines()
    in_annotation = False
    annotation = dict()
    for line in docstring:
        line = line.lstrip()
        if in_annotation and line == "":

            in_annotation = False
            if len(annotation) > 0:
                yield FeatureAnnotation(**annotation)

        elif line[0:3] == ANNOTATION_KEY:
            logger.debug("Found annotation")
            in_annotation = True

        if in_annotation:
            line_fields = line.split(":", 1)
            for key in FeatureAnnotation._fields:
                if line_fields[0] == key:
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



def main():
    res = build_annotations("/Users/work/Development/GE_DataDocs_Parser/test_folder")

if __name__ == "__main__":
    logging.basicConfig(filename='will.log', level=logging.WARNING)
    main()
