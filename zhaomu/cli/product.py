import click

from zhaomu.cli import handle_api_errors, json_output, pass_client
from zhaomu.cli.resolvers import resolve_region, resolve_product
from zhaomu.client import ZhaomuClient


@click.group()
def product():
    """Manage cloud server products."""


@product.command("list")
@click.option("-r", "--region", required=True, help="Region (city code, name, or ID)")
@pass_client
@handle_api_errors
def product_list(client: ZhaomuClient, region):
    """List products in a region."""
    rid = resolve_region(client, region)
    result = client.product.list(rid)
    if json_output([{"id": p.id, "cpu": p.cpu, "ram": p.ram, "disk": p.disk,
                     "price": p.price, "traffic": p.traffic, "tags": p.tags}
                    for p in result]):
        return
    click.echo(f"{'ID':<6} {'CPU':<6} {'RAM':<8} {'Disk':<10} {'Traffic':<10} {'Monthly':<10} {'Tags'}")
    for p in result:
        ram_label = f"{p.ram // 1024}G" if p.ram >= 1024 else f"{p.ram}M"
        click.echo(f"{p.id:<6} {p.cpu:<6} {ram_label:<8} "
                   f"{f'{p.disk}G':<10} {f'{p.traffic}G':<10} "
                   f"{p.price:<10} {p.tags}")


@product.command("info")
@click.argument("product_id")
@click.option("-r", "--region", default=None, help="Region (needed for name resolution)")
@pass_client
@handle_api_errors
def product_info(client: ZhaomuClient, product_id, region):
    """Show product details."""
    if product_id.isdigit():
        pid = int(product_id)
    elif region:
        rid = resolve_region(client, region)
        pid = resolve_product(client, rid, product_id)
    else:
        raise click.UsageError("use -r/--region to resolve product by name")
    result = client.product.info(pid)
    if json_output({"id": result.id, "cpu": result.cpu, "ram": result.ram, "disk": result.disk,
                    "traffic": result.traffic, "diskMedia": result.diskMedia,
                    "price": result.price, "priceHour": result.priceHour,
                    "priceQuarter": result.priceQuarter, "priceHalfYear": result.priceHalfYear,
                    "priceYear": result.priceYear, "tags": result.tags}):
        return
    ram_label = f"{result.ram // 1024}G" if result.ram >= 1024 else f"{result.ram}M"
    click.echo(f"ID:         {result.id}")
    click.echo(f"CPU:        {result.cpu} core(s)")
    click.echo(f"RAM:        {ram_label}")
    click.echo(f"Disk:       {result.disk}G {result.diskMedia}")
    click.echo(f"Traffic:    {result.traffic}G/mo")
    click.echo(f"Monthly:    {result.price}")
    click.echo(f"Quarterly:  {result.priceQuarter}")
    click.echo(f"Half-year:  {result.priceHalfYear}")
    click.echo(f"Yearly:     {result.priceYear}")
    if result.tags:
        click.echo(f"Tags:       {result.tags}")


@product.command("price")
@click.argument("product_id")
@click.option("-r", "--region", default=None, help="Region (city code, name, or ID)")
@pass_client
@handle_api_errors
def product_price(client: ZhaomuClient, product_id, region):
    """Get product pricing."""
    if product_id.isdigit():
        pid = int(product_id)
    elif region:
        rid = resolve_region(client, region)
        pid = resolve_product(client, rid, product_id)
    else:
        raise click.UsageError("use -r/--region to resolve product by name")
    result = client.product.price(pid)
    if json_output(result):
        return
    cycle_names = {"1": "Monthly", "2": "Quarterly", "3": "Half-year", "4": "Yearly", "5": "Hourly"}
    for k, v in result.items():
        label = cycle_names.get(k, f"Cycle {k}")
        click.echo(f"{label:<12} {v}")


@product.command("compare")
@click.option("-r", "--region", required=True, help="Region (city code, name, or ID)")
@pass_client
@handle_api_errors
def product_compare(client: ZhaomuClient, region):
    """Compare product features in a region."""
    rid = resolve_region(client, region)
    result = client.product.compare(rid)
    if json_output([{"name": r.name, "explain": r.explain} for r in result]):
        return
    click.echo(f"{'Feature':<20} {'Support'}")
    for r in result:
        click.echo(f"{r.name:<20} {r.explain}")
