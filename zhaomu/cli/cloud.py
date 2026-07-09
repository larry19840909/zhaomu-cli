import click

from zhaomu.cli import handle_api_errors, json_output, pass_client
from zhaomu.cli.resolvers import resolve_by_ip, resolve_product, resolve_image, resolve_regions_by_city, filter_by_zone
from zhaomu.client import ZhaomuClient
from zhaomu.models.cloud.request import (
    OrderRequest, RenewRequest, UpgradeRequest, UpgradePriceRequest,
    RebuildRequest, ResetPasswordRequest, AutoRenewRequest, NoteRequest,
)

STATUS_NAMES = {1: "Provisioning", 2: "Running", 3: "Stopped", 4: "Disabled", 5: "Preparing"}
PAYMENT_CYCLE_NAMES = {1: "Monthly", 2: "Quarterly", 3: "Half-year", 4: "Yearly", 5: "Hourly"}


@click.group()
def cloud():
    """Manage cloud servers."""


@cloud.command("list")
@pass_client
@handle_api_errors
def cloud_list(client: ZhaomuClient):
    """List all cloud servers."""
    result = client.cloud.list()
    if json_output([{"id": s.id, "ip": s.ip, "cpu": s.cpu, "ram": s.ram,
                     "disk": s.disk, "image": s.image, "status": s.status,
                     "statusName": STATUS_NAMES.get(s.status, "Unknown"),
                     "startTime": s.startTime, "endTime": s.endTime}
                    for s in result]):
        return
    click.echo(f"{'ID':<8} {'IP':<18} {'CPU':<5} {'RAM':<6} {'Status':<14} {'Image'}")
    for s in result:
        ram_gb = f"{s.ram // 1024}G" if s.ram >= 1024 else f"{s.ram}M"
        status = STATUS_NAMES.get(s.status, str(s.status))
        click.echo(f"{s.id:<8} {s.ip:<18} {s.cpu:<5} {ram_gb:<6} {status:<14} {s.image}")


@cloud.command("info")
@click.argument("instance")
@pass_client
@handle_api_errors
def cloud_info(client: ZhaomuClient, instance):
    """Show cloud server details."""
    sid = resolve_by_ip(client, client.cloud.list, instance)
    result = client.cloud.info(sid)
    if json_output({"id": result.id, "ip": result.ip, "root": result.root,
                    "cpu": result.cpu, "ram": result.ram, "disk": result.disk,
                    "diskData": result.diskData, "diskMedia": result.diskMedia,
                    "traffic": result.traffic, "image": result.image,
                    "status": result.status, "startTime": result.startTime,
                    "endTime": result.endTime, "isAutoRenew": result.isAutoRenew,
                    "noteUser": result.noteUser, "region_id": result.region_id}):
        return
    ram_gb = f"{result.ram // 1024}G" if result.ram >= 1024 else f"{result.ram}M"
    status = STATUS_NAMES.get(result.status, str(result.status))
    click.echo(f"ID:           {result.id}")
    click.echo(f"IP:           {result.ip}")
    click.echo(f"User:         {result.root}")
    click.echo(f"CPU:          {result.cpu} core(s)")
    click.echo(f"RAM:          {ram_gb}")
    click.echo(f"Disk:         {result.disk}G {result.diskMedia}")
    click.echo(f"Traffic:      {result.traffic}G/mo")
    click.echo(f"Image:        {result.image}")
    click.echo(f"Status:       {status}")
    click.echo(f"Start:        {result.startTime}")
    click.echo(f"End:          {result.endTime}")
    click.echo(f"Auto-Renew:   {'On' if result.isAutoRenew else 'Off'}")
    if result.noteUser:
        click.echo(f"Note:         {result.noteUser}")


@cloud.command("order")
@click.option("-r", "--region", required=True, help="City name or region ID")
@click.option("--zone", default=None, help="Zone code when city has multiple (e.g. V)")
@click.option("-p", "--product", required=True, help="Product (e.g. 1C-1G, or ID)")
@click.option("--image", required=True, help="Image (name or ID)")
@click.option("--disk", type=int, required=True, help="System disk size (GB)")
@click.option("--disk-data", type=int, default=0, help="Data disk size (GB)")
@click.option("--bandwidth", type=int, default=0, help="Bandwidth (Mbps, 0=unlimited)")
@click.option("--period", type=int, default=1, help="Payment cycle (1=Monthly,2=Quarterly,3=Half-year,4=Yearly,5=Hourly)")
@pass_client
@handle_api_errors
def cloud_order(client: ZhaomuClient, region, zone, product, image, disk, disk_data, bandwidth, period):
    """Order a new cloud server."""
    rids = resolve_regions_by_city(client, region)
    rids = filter_by_zone(client, rids, zone)
    rid = rids[0]
    pid = resolve_product(client, rid, product)
    iid = resolve_image(client, pid, image)
    req = OrderRequest(productId=pid, disk=disk, diskData=disk_data,
                       bandwidth=bandwidth, imageId=iid, paymentCycle=period)
    result = client.cloud.order(req)
    if json_output({"success": result.success, "message": result.message,
                    "info": result.info}):
        return
    if not result.success:
        click.echo(f"Error: {result.message}", err=True)
        raise SystemExit(1)
    if result.info:
        info = result.info
        click.echo(f"Ordered: ID={info.get('id', '?')}, IP={info.get('ip', 'pending')}")
    else:
        click.echo(f"Ordered: {result.message}")


@cloud.command("images")
@click.option("-p", "--product", required=True, help="Product (e.g. 1C-1G, or ID)")
@click.option("-r", "--region", required=True, help="City name or region ID")
@click.option("--zone", default=None, help="Zone code when city has multiple (e.g. V)")
@pass_client
@handle_api_errors
def cloud_images(client: ZhaomuClient, product, region, zone):
    """List available images for a product."""
    rids = resolve_regions_by_city(client, region)
    rids = filter_by_zone(client, rids, zone)
    pid = resolve_product(client, rids[0], product)
    result = client.cloud.images(pid)
    if json_output([{"id": img.id, "name": img.name, "type": img.type} for img in result]):
        return
    click.echo(f"{'ID':<6} {'Name':<30} {'Type'}")
    for img in result:
        click.echo(f"{img.id:<6} {img.name:<30} {img.type}")


@cloud.command("renew")
@click.argument("instance")
@click.option("--period", type=int, default=1, help="Payment cycle (1=Monthly,2=Quarterly,3=Half-year,4=Yearly)")
@pass_client
@handle_api_errors
def cloud_renew(client: ZhaomuClient, instance, period):
    """Renew a cloud server."""
    sid = resolve_by_ip(client, client.cloud.list, instance)
    req = RenewRequest(paymentCycle=period)
    result = client.cloud.renew(sid, req)
    if json_output({"success": result.success, "message": result.message}):
        return
    if not result.success:
        click.echo(f"Error: {result.message}", err=True)
        raise SystemExit(1)
    click.echo(result.message)


@cloud.command("upgrade")
@click.argument("instance")
@click.option("-p", "--product", type=int, default=None, help="Target product ID")
@click.option("--disk", type=int, default=None, help="System disk size (GB)")
@click.option("--disk-data", type=int, default=None, help="Data disk size (GB)")
@click.option("--bandwidth", type=int, default=None, help="Bandwidth (Mbps)")
@pass_client
@handle_api_errors
def cloud_upgrade(client: ZhaomuClient, instance, product, disk, disk_data, bandwidth):
    """Upgrade cloud server configuration."""
    if not any([product, disk, disk_data, bandwidth]):
        raise click.UsageError("specify at least one option to upgrade")
    sid = resolve_by_ip(client, client.cloud.list, instance)
    req = UpgradeRequest(productId=product, disk=disk, diskData=disk_data,
                         bandwidth=bandwidth)
    result = client.cloud.upgrade(sid, req)
    if json_output({"success": result.success, "message": result.message}):
        return
    if not result.success:
        click.echo(f"Error: {result.message}", err=True)
        raise SystemExit(1)
    click.echo(result.message)


@cloud.command("upgrade-price")
@click.argument("instance")
@click.option("-p", "--product", type=int, default=None, help="Target product ID")
@click.option("--disk", type=int, default=None, help="System disk size (GB)")
@click.option("--disk-data", type=int, default=None, help="Data disk size (GB)")
@click.option("--bandwidth", type=int, default=None, help="Bandwidth (Mbps)")
@pass_client
@handle_api_errors
def cloud_upgrade_price(client: ZhaomuClient, instance, product, disk, disk_data, bandwidth):
    """Get upgrade price quote."""
    sid = resolve_by_ip(client, client.cloud.list, instance)
    req = UpgradePriceRequest(productId=product, disk=disk, diskData=disk_data,
                              bandwidth=bandwidth)
    result = client.cloud.upgrade_price(sid, req)
    if json_output({"success": result.success, "message": result.message}):
        return
    click.echo(f"Upgrade price: {result.message}")


@cloud.command("destroy")
@click.argument("instance")
@pass_client
@handle_api_errors
def cloud_destroy(client: ZhaomuClient, instance):
    """Destroy a cloud server."""
    sid = resolve_by_ip(client, client.cloud.list, instance)
    result = client.cloud.destroy(sid)
    if json_output({"success": result.success, "message": result.message}):
        return
    if not result.success:
        click.echo(f"Error: {result.message}", err=True)
        raise SystemExit(1)
    click.echo(f"Destroyed: {result.message}")


@cloud.command("reboot")
@click.argument("instance")
@pass_client
@handle_api_errors
def cloud_reboot(client: ZhaomuClient, instance):
    """Reboot or start a cloud server."""
    sid = resolve_by_ip(client, client.cloud.list, instance)
    result = client.cloud.reboot(sid)
    if json_output({"success": result.success, "message": result.message}):
        return
    if not result.success:
        click.echo(f"Error: {result.message}", err=True)
        raise SystemExit(1)
    click.echo(result.message)


@cloud.command("shutdown")
@click.argument("instance")
@pass_client
@handle_api_errors
def cloud_shutdown(client: ZhaomuClient, instance):
    """Shutdown a cloud server."""
    sid = resolve_by_ip(client, client.cloud.list, instance)
    result = client.cloud.shutdown(sid)
    if json_output({"success": result.success, "message": result.message}):
        return
    if not result.success:
        click.echo(f"Error: {result.message}", err=True)
        raise SystemExit(1)
    click.echo(result.message)


@cloud.command("rebuild")
@click.argument("instance")
@click.option("--image", required=True, help="Image ID")
@pass_client
@handle_api_errors
def cloud_rebuild(client: ZhaomuClient, instance, image):
    """Rebuild (reinstall OS) a cloud server."""
    sid = resolve_by_ip(client, client.cloud.list, instance)
    req = RebuildRequest(imageId=int(image))
    result = client.cloud.rebuild(sid, req)
    if json_output({"success": result.success, "message": result.message}):
        return
    if not result.success:
        click.echo(f"Error: {result.message}", err=True)
        raise SystemExit(1)
    click.echo(result.message)


@cloud.command("rebuild-images")
@click.argument("instance")
@pass_client
@handle_api_errors
def cloud_rebuild_images(client: ZhaomuClient, instance):
    """List available images for rebuilding."""
    sid = resolve_by_ip(client, client.cloud.list, instance)
    result = client.cloud.rebuild_images(sid)
    if json_output([{"id": img.id, "name": img.name, "type": img.type} for img in result]):
        return
    click.echo(f"{'ID':<6} {'Name':<30} {'Type'}")
    for img in result:
        click.echo(f"{img.id:<6} {img.name:<30} {img.type}")


@cloud.command("reset-password")
@click.argument("instance")
@click.option("--password", required=True, prompt=True, hide_input=True, confirmation_prompt=True)
@pass_client
@handle_api_errors
def cloud_reset_password(client: ZhaomuClient, instance, password):
    """Reset cloud server root password."""
    sid = resolve_by_ip(client, client.cloud.list, instance)
    req = ResetPasswordRequest(password=password)
    result = client.cloud.reset_password(sid, req)
    if json_output({"success": result.success, "message": result.message}):
        return
    if not result.success:
        click.echo(f"Error: {result.message}", err=True)
        raise SystemExit(1)
    click.echo(result.message)


@cloud.command("console")
@click.argument("instance")
@pass_client
@handle_api_errors
def cloud_console(client: ZhaomuClient, instance):
    """Get noVNC console URL."""
    sid = resolve_by_ip(client, client.cloud.list, instance)
    result = client.cloud.console(sid)
    if json_output({"success": result.success, "message": result.message}):
        return
    click.echo(result.message)


@cloud.command("auto-renew")
@click.argument("instance")
@click.option("--enable/--disable", default=True, help="Enable or disable auto-renew")
@pass_client
@handle_api_errors
def cloud_auto_renew(client: ZhaomuClient, instance, enable):
    """Set auto-renew for a cloud server."""
    sid = resolve_by_ip(client, client.cloud.list, instance)
    req = AutoRenewRequest(enable=1 if enable else 0)
    result = client.cloud.auto_renew(sid, req)
    if json_output({"success": result.success, "message": result.message}):
        return
    if not result.success:
        click.echo(f"Error: {result.message}", err=True)
        raise SystemExit(1)
    click.echo(result.message)


@cloud.command("note")
@click.argument("instance")
@click.argument("note_text")
@pass_client
@handle_api_errors
def cloud_note(client: ZhaomuClient, instance, note_text):
    """Set user note for a cloud server."""
    sid = resolve_by_ip(client, client.cloud.list, instance)
    req = NoteRequest(note=note_text)
    result = client.cloud.note(sid, req)
    if json_output({"success": result.success, "message": result.message}):
        return
    if not result.success:
        click.echo(f"Error: {result.message}", err=True)
        raise SystemExit(1)
    click.echo(result.message)


@cloud.command("refresh-traffic")
@click.argument("instance")
@pass_client
@handle_api_errors
def cloud_refresh_traffic(client: ZhaomuClient, instance):
    """Refresh traffic usage for a cloud server."""
    sid = resolve_by_ip(client, client.cloud.list, instance)
    result = client.cloud.refresh_traffic(sid)
    if json_output({"success": result.success, "message": result.message}):
        return
    if not result.success:
        click.echo(f"Error: {result.message}", err=True)
        raise SystemExit(1)
    click.echo(result.message)
