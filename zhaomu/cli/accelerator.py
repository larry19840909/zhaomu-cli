import datetime
import json

import click

from zhaomu.cli import handle_api_errors, json_output, pass_client
from zhaomu.cli.resolvers import resolve_by_ip
from zhaomu.client import ZhaomuClient
from zhaomu.errors import AuthError
from zhaomu.models.accelerator import (
    AcceleratorOrderRequest,
    AcceleratorModifyRequest,
    AcceleratorPortRequest,
    TrafficUsage,
)

REGION_NAMES = {"cn-bj2": "Beijing", "cn-sh2": "Shanghai", "cn-gd": "Guangzhou"}


@click.group()
def accelerator():
    """Manage overseas server accelerators."""


@accelerator.command("list")
@pass_client
@handle_api_errors
def accelerator_list(client: ZhaomuClient):
    """List all accelerators."""
    result = client.accelerator.list()
    if json_output([{"id": a.id, "ip": a.ip, "port": a.port, "type": a.type,
                     "area": a.area, "region": a.region, "startTime": a.startTime,
                     "endTime": a.endTime} for a in result]):
        return
    click.echo(f"{'ID':<6} {'IP':<18} {'Port':<8} {'Type':<10} {'Area':<12} {'Region'}")
    for a in result:
        region_name = REGION_NAMES.get(a.region, a.region)
        click.echo(f"{a.id:<6} {a.ip:<18} {a.port:<8} {a.type:<10} {a.area:<12} {region_name}")


@accelerator.command("info")
@click.argument("accelerator_id")
@pass_client
@handle_api_errors
def accelerator_info(client: ZhaomuClient, accelerator_id):
    """Show accelerator details."""
    aid = resolve_by_ip(client, client.accelerator.list, accelerator_id)
    result = client.accelerator.info(aid)
    if json_output({"id": result.id, "ip": result.ip, "port": result.port,
                    "type": result.type, "area": result.area, "region": result.region,
                    "domain": result.domain, "startTime": result.startTime,
                    "endTime": result.endTime, "renewPrice": result.renewPrice}):
        return
    region_name = REGION_NAMES.get(result.region, result.region)
    click.echo(f"ID:         {result.id}")
    click.echo(f"IP:         {result.ip}")
    click.echo(f"Port:       {result.port}")
    click.echo(f"Type:       {result.type}")
    click.echo(f"Area:       {result.area}")
    click.echo(f"Region:     {region_name}")
    click.echo(f"Domain:     {result.domain}")
    click.echo(f"Start:      {result.startTime}")
    click.echo(f"End:        {result.endTime}")
    click.echo(f"Renew Price: {result.renewPrice}")


@accelerator.command("order")
@click.option("-p", "--product", type=int, default=1, help="Product ID (1=Basic, 2=Pro)")
@click.option("--region", required=True, help="Entry region (cn-bj2/cn-sh2/cn-gd)")
@click.option("--ip", required=True, help="Server IP")
@click.option("--port", type=int, required=True, help="Application port (not 80/443)")
@click.option("--area", required=True, help="Server area (Chinese: 台湾、香港、东京、新加坡… documented as 香港/新加坡/东京/洛杉矶/华盛顿/法兰克福/拉各斯)")
@click.option("--period", type=int, default=1, help="Payment cycle (1=Monthly,2=Quarterly,3=Half-year,4=Yearly)")
@pass_client
@handle_api_errors
def accelerator_order(client: ZhaomuClient, product, region, ip, port, area, period):
    """Order an accelerator."""
    req = AcceleratorOrderRequest(productId=product, region=region, ip=ip,
                                  port=port, area=area, paymentCycle=period)
    result = client.accelerator.order(req)
    if json_output({"success": result.success, "message": result.message}):
        return
    if not result.success:
        click.echo(f"Error: {result.message}", err=True)
        raise SystemExit(1)
    click.echo(result.message)


@accelerator.command("renew")
@click.argument("accelerator_id")
@click.option("--period", type=int, default=1, help="Payment cycle (1=Monthly,2=Quarterly,3=Half-year,4=Yearly)")
@pass_client
@handle_api_errors
def accelerator_renew(client: ZhaomuClient, accelerator_id, period):
    """Renew an accelerator."""
    aid = resolve_by_ip(client, client.accelerator.list, accelerator_id)
    result = client.accelerator.renew(aid, period)
    if json_output({"success": result.success, "message": result.message}):
        return
    if not result.success:
        click.echo(f"Error: {result.message}", err=True)
        raise SystemExit(1)
    click.echo(result.message)


@accelerator.command("upgrade")
@click.argument("accelerator_id")
@click.option("--period", type=int, default=1, help="Payment cycle (1=Monthly,2=Quarterly,3=Half-year,4=Yearly)")
@pass_client
@handle_api_errors
def accelerator_upgrade(client: ZhaomuClient, accelerator_id, period):
    """Upgrade an accelerator."""
    aid = resolve_by_ip(client, client.accelerator.list, accelerator_id)
    result = client.accelerator.upgrade(aid, period)
    if json_output({"success": result.success, "message": result.message}):
        return
    if not result.success:
        click.echo(f"Error: {result.message}", err=True)
        raise SystemExit(1)
    click.echo(result.message)


@accelerator.command("modify-ip")
@click.argument("accelerator_id")
@click.option("--ip", required=True, help="New server IP")
@click.option("--area", required=True, help="Server area (Chinese values, e.g. 香港/新加坡/东京)")
@pass_client
@handle_api_errors
def accelerator_modify_ip(client: ZhaomuClient, accelerator_id, ip, area):
    """Modify accelerator server IP."""
    aid = resolve_by_ip(client, client.accelerator.list, accelerator_id)
    req = AcceleratorModifyRequest(ip=ip, area=area)
    result = client.accelerator.modify_ip(aid, req)
    if json_output({"success": result.success, "message": result.message}):
        return
    if not result.success:
        click.echo(f"Error: {result.message}", err=True)
        raise SystemExit(1)
    click.echo(result.message)


@accelerator.command("modify-port")
@click.argument("accelerator_id")
@click.option("--port", type=int, required=True, help="New application port")
@pass_client
@handle_api_errors
def accelerator_modify_port(client: ZhaomuClient, accelerator_id, port):
    """Modify accelerator application port."""
    aid = resolve_by_ip(client, client.accelerator.list, accelerator_id)
    req = AcceleratorPortRequest(port=port)
    result = client.accelerator.modify_port(aid, req)
    if json_output({"success": result.success, "message": result.message}):
        return
    if not result.success:
        click.echo(f"Error: {result.message}", err=True)
        raise SystemExit(1)
    click.echo(result.message)


@accelerator.command("traffic-usage")
@click.argument("accelerator_id", required=False)
@click.pass_context
@handle_api_errors
def accelerator_traffic_usage(ctx, accelerator_id):
    """查看加速器每日流量用量。

    指定 ACCELERATOR_ID 时：查看单个加速器的每日详情（支持数字 ID 或 IP）。
    不指定时：列出所有加速器的流量透视表（行=ID，列=日期），并汇总。

    首次使用会提示输入朝暮数据 Web 管理后台的登录凭据，
    登录后凭据会被安全存储，后续使用无需重复输入。
    """
    from zhaomu.config import Config
    from zhaomu.web_client import ZhaomuWebClient

    config_path = ctx.meta.get("zhaomu_config", "config.json")

    # 读取 web_session_file 配置（如有）
    web_session_file = ""
    try:
        cfg = Config.load(config_path)
        web_session_file = cfg.web_session_file
    except Exception:
        pass

    # ---- 单加速器模式 ----
    if accelerator_id:
        api_client = ZhaomuClient.from_config(config_path)
        aid = resolve_by_ip(api_client, api_client.accelerator.list, accelerator_id)
        _show_single_traffic(aid, web_session_file)
        api_client.close()
        return

    # ---- 全量透视表模式 ----
    api_client = ZhaomuClient.from_config(config_path)
    accelerators = api_client.accelerator.list()
    if not accelerators:
        click.echo("暂无加速器。")
        api_client.close()
        return

    accelerators.sort(key=lambda a: a.id)

    # 构建 id → ip 映射
    ip_map = {a.id: a.ip for a in accelerators}

    # 确保 Web 登录
    web = ZhaomuWebClient(session_file=web_session_file or None)
    try:
        _ensure_web_login(web)

        # JSON 模式：收集全部数据后统一输出
        if ctx.meta.get("zhaomu_json"):
            all_data: dict[int, list[dict]] = {}
            for acc in accelerators:
                try:
                    raw = web.traffic_usage(acc.id)
                    all_data[acc.id] = raw if raw else []
                except Exception:
                    all_data[acc.id] = []
            click.echo(json.dumps({
                str(k): [{"Date": r.Date, "Traffic": r.Traffic, "BillingState": r.BillingState}
                         for r in TrafficUsage._from_list(v)]
                for k, v in all_data.items()
            }, ensure_ascii=False, indent=2, default=str))
            api_client.close()
            return

        # 交互模式：串行查询，每完成一个立刻输出一行
        _show_pivot_table_streaming_serial(web, accelerators, ip_map)

    except AuthError as e:
        click.echo(f"认证失败: {e}", err=True)
        click.echo("提示: 可删除 ~/.zhaomu/session.json 后重新运行以重新登录。", err=True)
        raise SystemExit(1)
    finally:
        web.close()
        api_client.close()


def _ensure_web_login(web):
    """确保 Web 客户端已认证。"""
    from zhaomu.web_client import ZhaomuWebClient

    if not web.has_session() and not web.has_credentials():
        click.echo("首次使用需要登录朝暮数据 Web 管理后台。")
        username = click.prompt("用户名/邮箱/手机号")
        password = click.prompt("登录密码", hide_input=True)
        click.echo("正在登录...")
        web.login(username, password)
        click.echo("登录成功，凭据已保存。")


def _show_single_traffic(aid: int, session_file: str = ""):
    """展示单加速器流量详情。"""
    from zhaomu.web_client import ZhaomuWebClient

    web = ZhaomuWebClient(session_file=session_file or None)
    try:
        _ensure_web_login(web)

        raw = web.traffic_usage(aid)
        records = TrafficUsage._from_list(raw) if raw else []

        if json_output([
            {"Date": r.Date, "Traffic": r.Traffic, "BillingState": r.BillingState}
            for r in records
        ]):
            return

        if not records:
            click.echo("暂无流量数据。")
            return

        click.echo(f"加速器 #{aid} 每日流量用量：")
        click.echo(f"{'日期':<12} {'流量(GB)':>10}   {'计费'}")
        click.echo("-" * 35)
        for r in records:
            try:
                date_str = datetime.datetime.fromtimestamp(r.Date).strftime("%Y-%m-%d")
            except (OSError, ValueError):
                date_str = str(r.Date)
            traffic_str = f"{r.Traffic:.1f}" if r.Traffic else "0.0"
            billing_str = "是" if r.BillingState == "Yes" else "否"
            click.echo(f"{date_str:<12} {traffic_str:>10}   {billing_str}")

    except AuthError as e:
        click.echo(f"认证失败: {e}", err=True)
        click.echo("提示: 可删除 ~/.zhaomu/session.json 后重新运行以重新登录。", err=True)
        raise SystemExit(1)
    finally:
        web.close()


def _show_pivot_table_streaming_serial(web, accelerators, ip_map: dict[int, str]):
    """串行查询每个加速器，完成一个立刻输出一行（非 JSON 模式）。"""
    if ip_map is None:
        ip_map = {}

    # 先查询第一个加速器确定日期布局
    if not accelerators:
        return

    first = accelerators[0]
    try:
        raw = web.traffic_usage(first.id)
        first_records = raw if raw else []
    except Exception:
        click.echo(f"#{first.id}: 查询失败", err=True)
        return

    # 从第一个加速器的数据构建日期集
    date_set: set[int] = set()
    for r in first_records:
        ts = r.get("Date", 0)
        if ts:
            date_set.add(ts)
    sorted_dates = sorted(date_set)

    if not sorted_dates:
        click.echo("暂无流量数据。")
        return

    date_labels = []
    for ts in sorted_dates:
        try:
            date_labels.append(datetime.datetime.fromtimestamp(ts).strftime("%m-%d"))
        except (OSError, ValueError):
            date_labels.append(str(ts))

    # 列宽（用全部加速器的 IP/ID 来计算）
    id_width = max(10, max((len(str(a.id)) for a in accelerators), default=6) + 2)
    ip_width = max(8, max((len(ip_map.get(a.id, "—")) for a in accelerators), default=4) + 2)
    cell_width = max(8, max((len(lbl) for lbl in date_labels), default=6) + 3)
    summary_width = 8
    total_width = id_width + ip_width + len(date_labels) * cell_width + summary_width

    # 打印表头
    click.echo(f"{'加速器 #'.ljust(id_width)}{'IP'.ljust(ip_width)}{''.join(lbl.center(cell_width) for lbl in date_labels)}{'汇总'.center(summary_width)}")
    click.echo("-" * total_width)

    column_totals = [0.0] * len(sorted_dates)
    grand_total = 0.0

    def _print_row(aid, ip_str, records):
        nonlocal grand_total
        tmap: dict[int, float] = {}
        for r in records:
            ts = r.get("Date", 0)
            val = r.get("Traffic", 0)
            tmap[ts] = float(val) if val else 0.0
        row_sum = 0.0
        cells = []
        for i, ts in enumerate(sorted_dates):
            val = tmap.get(ts, 0.0)
            cells.append(f"{val:.1f}".center(cell_width))
            column_totals[i] += val
            row_sum += val
        grand_total += row_sum
        click.echo(f"{str(aid).ljust(id_width)}{ip_str}{''.join(cells)}{f'{row_sum:.1f}'.center(summary_width)}")

    # 打印第一个加速器的行
    ip_str = ip_map.get(first.id, "—").ljust(ip_width)
    _print_row(first.id, ip_str, first_records)

    # 串行查询剩余加速器，完成一个立刻打印一行
    for acc in accelerators[1:]:
        aid = acc.id
        ip_str = ip_map.get(aid, "—").ljust(ip_width)
        try:
            raw = web.traffic_usage(aid)
            records = raw if raw else []
            _print_row(aid, ip_str, records)
        except Exception:
            err_cells = "".join("ERR".center(cell_width) for _ in sorted_dates)
            click.echo(f"{str(aid).ljust(id_width)}{ip_str}{err_cells}{'ERR'.center(summary_width)}")

    # 合计行
    click.echo("-" * total_width)
    total_ip = "".ljust(ip_width)
    total_cells = "".join(f"{col_sum:.1f}".center(cell_width) for col_sum in column_totals)
    click.echo(f"{'合计'.ljust(id_width)}{total_ip}{total_cells}{f'{grand_total:.1f}'.center(summary_width)}")
