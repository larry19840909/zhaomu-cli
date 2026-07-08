import click

from zhaomu.cli import handle_api_errors, json_output, pass_client
from zhaomu.client import ZhaomuClient


@click.command()
@pass_client
@handle_api_errors
def balance(client: ZhaomuClient):
    """Show account balance."""
    result = client.other.balance()
    if json_output({"balance": result.balance}):
        return
    click.echo(f"Balance: {result.balance}")
