# Parsec Cloud (https://parsec.cloud) Copyright (c) AGPL-3.0 2016-present Scille SAS
from __future__ import annotations

from typing import Optional
import click
import urllib.parse

from parsec.utils import DateTime, trio_run
from parsec.api.protocol import OrganizationID
from parsec.api.rest import organization_stats_rep_serializer
from parsec.cli_utils import cli_exception_handler, ParsecDateTimeClickType
from parsec.core.types import BackendAddr
from parsec.core.backend_connection.transport import http_request
from parsec.core.cli.utils import cli_command_base_options


async def _stats_organization(
    organization_id: OrganizationID, backend_addr: BackendAddr, administration_token: str
) -> None:
    url = backend_addr.to_http_domain_url(
        f"/administration/organizations/{organization_id.str}/stats"
    )

    rep_data = await http_request(
        url=url, method="GET", headers={"authorization": f"Bearer {administration_token}"}
    )

    cooked_rep_data = organization_stats_rep_serializer.loads(rep_data)
    for key, value in cooked_rep_data.items():
        click.echo(f"{key}: {value}")


async def _stats_server(
    backend_addr: BackendAddr,
    administration_token: str,
    from_date: Optional[DateTime],
    to_date: Optional[DateTime],
    format: str,
) -> None:
    query_args = {"format": format}
    if from_date is not None:
        query_args["from"] = from_date.to_rfc3339()
    if to_date is not None:
        query_args["to"] = to_date.to_rfc3339()

    url = backend_addr.to_http_domain_url("/administration/stats")
    url += f"?{urllib.parse.urlencode(query_args)}"
    rep = await http_request(
        url=url, method="GET", headers={"authorization": f"Bearer {administration_token}"}
    )
    return rep.decode()


@click.command(short_help="get data&user statistics on organization")
@click.argument("organization_id", required=True, type=OrganizationID)
@click.option("--addr", "-B", required=True, type=BackendAddr.from_url, envvar="PARSEC_ADDR")
@click.option("--administration-token", "-T", required=True, envvar="PARSEC_ADMINISTRATION_TOKEN")
@cli_command_base_options
def stats_organization(
    organization_id: OrganizationID,
    addr: BackendAddr,
    administration_token: str,
    debug: bool,
    **kwargs,
) -> None:
    with cli_exception_handler(debug):
        trio_run(_stats_organization, organization_id, addr, administration_token)


@click.command(short_help="Get a per-organization report of server usage")
@click.option("--addr", "-B", required=True, type=BackendAddr.from_url, envvar="PARSEC_ADDR")
@click.option(
    "--administration-token",
    "-T",
    required=True,
    envvar="PARSEC_ADMINISTRATION_TOKEN",
)
@click.option(
    "--from",
    type=ParsecDateTimeClickType(),
)
@click.option(
    "--to",
    type=ParsecDateTimeClickType(),
)
@click.option("--output", type=click.File("w"))
@click.option(
    "--format",
    default="json",
    type=click.Choice(["json", "csv"]),
    show_default=True,
)
@cli_command_base_options
def stats_server(
    addr: BackendAddr,
    administration_token: str,
    output: click.File,
    format: str,
    debug: bool,
    **kwargs,
) -> None:
    # from/to cannot be passed as regular function param given they are Python keywords
    from_: Optional[DateTime] = kwargs["from"]
    to_: Optional[DateTime] = kwargs["to"]
    with cli_exception_handler(debug):
        data = trio_run(_stats_server, addr, administration_token, from_, to_, format)
        output.write(data)
