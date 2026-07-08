from platform_forge.templates import TemplateRegistry


def test_registry_resolves_gateway_template() -> None:
    template = TemplateRegistry().get_template("gateway")

    assert template.scaffold_type == "gateway"
    assert template.path.exists()
    assert (template.path / "cookiecutter.json").exists()
