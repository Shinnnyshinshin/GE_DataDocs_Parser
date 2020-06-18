import click
import os
import json

from .GE_DataDocs_Parser import build_annotations

@click.group()
@click.version_option()
def cli():
    pass


@cli.group()
def docstrings():
    pass

@docstrings.command(name='parse')
@click.argument('path', type=click.Path(exists=True))
@click.option('--out', default=None, type=click.Path(exists=False),
              help='The file to which to save the resulting annotations json.')
def annotations_build(path, out):
    """Build annotations from a python project.
        PATH: the root directory from which to parse the project
    """
    annotations = build_annotations(path)
    if out is None:
        print(json.dumps(annotations, indent=2))
    else:
        with open(out, "w") as outfile:
            json.dump(annotations, outfile, indent=2)


def main():
    cli()

if __name__ == '__main__':
    main()
