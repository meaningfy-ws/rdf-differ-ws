from unittest.mock import patch

from rdf_differ.adapters.filesystem import convert_test_data


@patch("rdf_differ.adapters.filesystem.parse_and_serialize")
def test_convert_test_data_pipes_to_turtle(mock_pipe):
    convert_test_data("in.rdf", "out.ttl")

    kwargs = mock_pipe.call_args.kwargs
    assert kwargs["input_files"] == ["in.rdf"]
    assert kwargs["outfile"] == "out.ttl"
    assert kwargs["output_format"] == "ttl"
    # no explicit input_format -> guessing enabled
    assert kwargs["guess"] is True


@patch("rdf_differ.adapters.filesystem.parse_and_serialize")
def test_convert_test_data_merges_additional_bindings(mock_pipe):
    convert_test_data(
        "in.rdf", "out.ttl", input_format="xml", additional_bindings={"ex": "http://ex#"}
    )

    kwargs = mock_pipe.call_args.kwargs
    assert kwargs["ns_bindings"]["ex"] == "http://ex#"
    assert kwargs["guess"] is False
