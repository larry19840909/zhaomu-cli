import functools
import json
import sys
from typing import Any

import click

from zhaomu.client import ZhaomuClient
from zhaomu.errors import ZhaomuError


def handle_api_errors(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ZhaomuError as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
    return wrapper


def json_output(data: Any) -> bool:
    ctx = click.get_current_context()
    while ctx:
        if ctx.meta.get("zhaomu_json"):
            click.echo(json.dumps(data, ensure_ascii=False, indent=2, default=str))
            return True
        ctx = ctx.parent
    return False


def pass_client(func):
    @functools.wraps(func)
    @click.pass_context
    def wrapper(ctx, *args, **kwargs):
        config = ctx.meta.get("zhaomu_config", "config.json")
        try:
            client = ZhaomuClient.from_config(config)
        except (ValueError, KeyError, FileNotFoundError, PermissionError, OSError) as e:
            click.echo(f"Config error: {e}", err=True)
            ctx.exit(1)
        return func(client, *args, **kwargs)
    return wrapper


@click.group(invoke_without_command=True)
@click.option("-c", "--config", default="config.json", metavar="PATH",
              help="Path to config.json")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def cli(ctx, config, as_json):
    ctx.meta["zhaomu_config"] = config
    ctx.meta["zhaomu_json"] = as_json
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


from zhaomu.cli.region import region
from zhaomu.cli.product import product
from zhaomu.cli.cloud import cloud
from zhaomu.cli.accelerator import accelerator
from zhaomu.cli.balance import balance

cli.add_command(region)
cli.add_command(product)
cli.add_command(cloud)
cli.add_command(accelerator)
cli.add_command(balance)

try:
    from zhaomu_deploy.cli import register_commands
    register_commands(cloud, cli)
except ImportError:
    pass
