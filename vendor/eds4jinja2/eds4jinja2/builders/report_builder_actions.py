#!/usr/bin/python3

# report_generator
# Created:  08/03/2019
# Author: Laurentiu Mandru
# Email: mclaurentiu79@gmail.com
"""This file contains the post-processing methods that you can use in conjunction with the ReportBuilder:

1. make_pdf_from_latex - allows you, after you rendered a ".tex" file from a template, to make a PDF file out of it

2.copy_static_content - it simply does what it says, copies resources from the static resources folder to the output
folder (for example, in case of a more complex rendered HTML, you will need this to copy .css, .js and other files);
the input directory structure is preserved to the output folder during copying

"""
import logging
import pathlib
from distutils.dir_util import copy_tree
from subprocess import Popen, PIPE, TimeoutExpired

logger = logging.getLogger(__name__)


def make_pdf_from_latex(configuration_context: dict = {}) -> None:
    """
    :rtype: None :param configuration_context: the configuration context of the renderer; in this method it is used
    to construct the output PDF file name

    LaTex will have to run 4 times to ensure proper output results (unfortunately this is a multi pass build process)
    """
    LATEX_RUNS = 4  # LaTex will have to run 4 times to ensure proper output results

    output_folder = pathlib.Path(configuration_context["output_folder"])
    input_file_name = pathlib.Path(configuration_context["template"])

    engine = configuration_context["latex_engine"] if "latex_engine" in configuration_context else "pdflatex"
    logger.info(f"Using {configuration_context['latex_engine']} to compile LaTex sources")

    cmd_args = [engine, "-file-line-error", "-interaction=nonstopmode", "-synctex=1",
                "-output-format=pdf", "-output-directory=.", str(input_file_name)]

    output = "LaTex engine logs"
    for _pass in range(LATEX_RUNS):
        logger.info(f"Running pass {_pass} in a multi-pass LaTex build")
        process = Popen(args=cmd_args, stdout=PIPE,
                        cwd=str(output_folder))
        try:
            output, errs = process.communicate(timeout=120)
        except TimeoutExpired:
            process.kill()
            output, errs = process.communicate()

        if process.returncode != 0:
            logger.fatal('pdflatex execution failed.')
            logger.fatal(output)
            raise RuntimeError(output)

        logger.info('LaTex subprocess finished successfully.')

    logger.info('LaTex multi-pass build finished successfully.')
    logger.info(output)

    # deleting all the source and auxiliary files
    file_list = [f for f in list(output_folder.rglob("*.*")) if f.suffix != ".pdf"]
    for file in file_list:
        if file.is_dir():
            file.rmdir()
        else:
            file.unlink(missing_ok=True)


def copy_static_content(configuration_context: dict) -> None:
    """
    :param configuration_context: the configuration context for the currently executing processing pipeline
    :rtype: None
    """

    if pathlib.Path(configuration_context["static_folder"]).is_dir():
        copy_tree(configuration_context["static_folder"], configuration_context["output_folder"])
    else:
        logger.warning(configuration_context["static_folder"] + " is not a directory !")
