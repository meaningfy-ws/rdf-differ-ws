from rdf_differ.services.validation import validate_choice


def test_choice_validator():
    choice = "apple"
    invalid_choice = "onion"
    accepted_values = ["apple", "grapes"]
    exception_text = f"The choice f{invalid_choice} is not valid. Accepted values:" \
                     f" {', '.join(accepted_values)}"
    valid_choice = validate_choice(choice=choice, accepted_values=accepted_values)
    invalid_choice = validate_choice(choice=invalid_choice, accepted_values=accepted_values)
    assert valid_choice == (True, "")
    assert invalid_choice == (False, exception_text)
