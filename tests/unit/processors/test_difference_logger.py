import textwrap


from gitlabform.processors.util.difference_logger import DifferenceLogger


def test_empty_dict_current():
    current_config = dict()
    config_to_apply = {
        "foo": 123,
        "bar": "whatever",
    }
    result = DifferenceLogger.log_diff(
        "test", current_config, config_to_apply, False, None, True
    )
    # the whitespace after "123" below is required!
    expected = textwrap.dedent(
        """
        test:
        foo: "???" => 123       
        bar: "???" => "whatever"
    """
    ).strip()
    assert result == expected


def test_none_current():
    current_config = None
    config_to_apply = {
        "foo": 123,
        "bar": "whatever",
    }
    result = DifferenceLogger.log_diff(
        "test", current_config, config_to_apply, False, None, True
    )
    # the whitespace after "123" below is required!
    expected = textwrap.dedent(
        """
        test:
        foo: "???" => 123       
        bar: "???" => "whatever"
    """
    ).strip()
    assert result == expected


def test_diff_from_current():
    current_config = {
        "foo": 456,
        "bar": "whatever",
    }
    config_to_apply = {
        "foo": 123,
        "bar": "whatever",
    }
    result = DifferenceLogger.log_diff(
        "test", current_config, config_to_apply, True, None, True
    )
    # the whitespace after "123" below is required!
    expected = textwrap.dedent(
        """
        test:
        foo: 456 => 123       
    """
    ).strip()
    assert result == expected


def test_diff_output_no_changes():
    current_config = {
        "foo": 123,
        "bar": "whatever",
    }
    config_to_apply = {
        "foo": 123,
        "bar": "whatever",
    }
    result = DifferenceLogger.log_diff(
        "test", current_config, config_to_apply, True, None, True
    )

    expected = textwrap.dedent(
        """

    """
    ).strip()
    assert result == expected
