import click

from zhaomu.cli import handle_api_errors, json_output, pass_client
from zhaomu.client import ZhaomuClient


@click.group()
def region():
    """Manage regions / availability zones."""


@region.command("list")
@pass_client
@handle_api_errors
def region_list(client: ZhaomuClient):
    """List all regions."""
    result = client.region.list()
    if json_output([{"id": r.id, "city": r.city, "cityEn": r.cityEn,
                     "continent": r.continent, "country": r.country, "zone": r.zone}
                    for r in result]):
        return
    click.echo(f"{'ID':<6} {'City':<16} {'Country':<14} {'Continent':<12} {'Zone':<6}")
    for r in result:
        click.echo(f"{r.id:<6} {r.city:<16} {r.country:<14} {r.continent:<12} {r.zone:<6}")


@region.command("info")
@click.argument("region_id")
@pass_client
@handle_api_errors
def region_info(client: ZhaomuClient, region_id):
    """Show region details."""
    from zhaomu.cli.resolvers import resolve_region
    rid = resolve_region(client, region_id)
    result = client.region.info(rid)
    if json_output({"id": result.id, "city": result.city, "cityEn": result.cityEn,
                    "continent": result.continent, "continentEn": result.continentEn,
                    "country": result.country, "countryEn": result.countryEn,
                    "area": result.area, "areaEn": result.areaEn,
                    "province": result.province, "provinceEn": result.provinceEn,
                    "zone": result.zone}):
        return
    click.echo(f"ID:         {result.id}")
    click.echo(f"City:       {result.city} ({result.cityEn})")
    click.echo(f"Country:    {result.country} ({result.countryEn})")
    click.echo(f"Continent:  {result.continent} ({result.continentEn})")
    click.echo(f"Area:       {result.area} ({result.areaEn})")
    click.echo(f"Province:   {result.province} ({result.provinceEn})")
    click.echo(f"Zone:       {result.zone}")
