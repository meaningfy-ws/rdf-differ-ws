import logging
import click

from eds4jinja2.builders.report_builder import ReportBuilder
from eds4jinja2.builders.report_builder_actions import copy_static_content, make_pdf_from_latex

logger = logging.getLogger(__name__)


@click.command()
@click.option("--target", default=".", required=False, type=str, help="The folder containing the config.json")
@click.option("--config", default="config.json", type=str,
              help="The configuration file if named other than config.json")
@click.option("--output", required=False, type=str, help="The output folder")
@click.option("--latex", is_flag=True, help="If this parameter is specified, after the templates are compiled, "
                                            "the resulting output  compiled using LaTeX engine "
                                            "to generate the PDF output")
@click.option("--xelatex", is_flag=True, help="If this parameter is specified, after the templates are compiled, "
                                              "the resulting output  compiled using XeLaTeX engine "
                                              "to generate the PDF output. Either XeLaTex or LaTex shall be used, "
                                              "but not both.")
def build_report(target, config, output, latex, xelatex):
    report_builder = ReportBuilder(target_path=target, config_file=config, output_path=output)
    if latex or xelatex:
        report_builder.configuration_context["latex_engine"] = "pdflatex" if latex else "xelatex"
        report_builder.add_before_rendering_listener(copy_static_content)
        report_builder.add_after_rendering_listener(make_pdf_from_latex)
    else:
        report_builder.add_after_rendering_listener(copy_static_content)
    report_builder.make_document()


if __name__ == "__main__":
    build_report()
