from click.testing import CliRunner

from zhaomu.cli import cli


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "cloud" in result.output
    assert "accelerator" in result.output
    assert "region" in result.output
    assert "product" in result.output
    assert "balance" in result.output


def test_cloud_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["cloud", "--help"])
    assert result.exit_code == 0
    assert "list" in result.output
    assert "info" in result.output
    assert "order" in result.output
    assert "renew" in result.output
    assert "reboot" in result.output
    assert "shutdown" in result.output
    assert "destroy" in result.output
    assert "rebuild" in result.output


def test_region_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["region", "--help"])
    assert result.exit_code == 0
    assert "list" in result.output
    assert "info" in result.output


def test_product_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["product", "--help"])
    assert result.exit_code == 0
    assert "list" in result.output
    assert "info" in result.output
    assert "price" in result.output
    assert "compare" in result.output


def test_accelerator_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["accelerator", "--help"])
    assert result.exit_code == 0
    assert "order" in result.output
    assert "traffic-usage" in result.output


def test_balance_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["balance", "--help"])
    assert result.exit_code == 0
    assert "balance" in result.output.lower()


def test_deploy_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["deploy", "--help"])
    assert result.exit_code == 0
    assert "Deploy a cloud server" in result.output


def test_json_flag_available():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert "--json" in result.output


def test_config_flag_available():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert "-c" in result.output
    assert "--config" in result.output
