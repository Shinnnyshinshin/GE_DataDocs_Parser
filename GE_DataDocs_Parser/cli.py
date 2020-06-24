import click
import os
import json

from .GE_DataDocs_Parser import build_annotations

@click.group()
@click.version_option()
def cli():
    pass

@cli.command(name='parse')
@click.argument('path', type=click.Path(exists=True))
@click.argument('injson', type=click.Path(exists=True))
@click.option('--out', default=None, type=click.Path(exists=False),
              help='The file to which to save the resulting annotations json.')
def annotations_build(path, injson, out):
    """Build annotations from a python project.\n
        PATH: the root directory from which to parse the project\n
        INJSON: json file that will serve as the scaffold for the feature maturity grid
    """
    annotations = build_annotations(path, injson)
    if out is None:
        print(json.dumps(annotations, indent=2))
    else:
        with open(out, "w") as outfile:
            json.dump(annotations, outfile, indent=2)

def main():
    cli()

if __name__ == '__main__':
    main()
