from gitlabform.output import EffectiveConfigurationFile


def test_no_output_file_is_noop():
    # when no output file is set, all methods are no-ops
    effective_configuration = EffectiveConfigurationFile(None)
    effective_configuration.add_configuration("", "settings", {"admin_mode": True})
    assert effective_configuration.config == {}


def test_add_configuration_without_placeholder(tmp_path):
    # the "application" section is processed with an empty string key and without a
    # preceding add_placeholder() call, so add_configuration must create the container
    output_file = tmp_path / "output.yaml"
    effective_configuration = EffectiveConfigurationFile(str(output_file))

    effective_configuration.add_configuration("", "settings", {"admin_mode": True})

    assert effective_configuration.config == {"": {"settings": {"admin_mode": True}}}
