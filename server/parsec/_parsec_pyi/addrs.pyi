# Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

from __future__ import annotations

from typing import Union

from parsec._parsec_pyi.crypto import VerifyKey
from parsec._parsec_pyi.enumerate import InvitationType
from parsec._parsec_pyi.ids import BootstrapToken, InvitationToken, OrganizationID, VlobID

class ParsecAddr:
    def __init__(self, hostname: str, port: int | None, use_ssl: bool) -> None: ...
    def __lt__(self, other: ParsecAddr) -> bool: ...
    def __gt__(self, other: ParsecAddr) -> bool: ...
    def __le__(self, other: ParsecAddr) -> bool: ...
    def __ge__(self, other: ParsecAddr) -> bool: ...
    def __hash__(self) -> int: ...
    @property
    def hostname(self) -> str: ...
    @property
    def port(self) -> int: ...
    @property
    def use_ssl(self) -> bool: ...
    @property
    def netloc(self) -> str: ...
    def to_url(self) -> str: ...
    def to_http_domain_url(self, path: str = "") -> str: ...
    def to_http_redirection_url(self) -> str: ...
    @classmethod
    def from_url(cls, url: str, allow_http_redirection: bool = False) -> ParsecAddr: ...

class ParsecOrganizationAddr(ParsecAddr):
    def __init__(
        self,
        organization_id: OrganizationID,
        root_verify_key: VerifyKey,
        hostname: str,
        port: int | None,
        use_ssl: bool = True,
    ) -> None: ...
    def __hash__(self) -> int: ...
    @property
    def organization_id(self) -> OrganizationID: ...
    @property
    def root_verify_key(self) -> VerifyKey: ...
    @property
    def hostname(self) -> str: ...
    @property
    def port(self) -> int: ...
    @property
    def use_ssl(self) -> bool: ...
    @property
    def netloc(self) -> str: ...
    def get_server_addr(self) -> ParsecAddr: ...
    def to_url(self) -> str: ...
    def to_http_redirection_url(self) -> str: ...
    @classmethod
    def from_url(cls, url: str, allow_http_redirection: bool = False) -> ParsecOrganizationAddr: ...
    @classmethod
    def build(
        cls,
        server_addr: ParsecAddr,
        organization_id: OrganizationID,
        root_verify_key: VerifyKey,
    ) -> ParsecOrganizationAddr: ...

class ParsecActionAddr:
    @classmethod
    def from_url(
        cls, url: str, allow_http_redirection: bool = False
    ) -> Union[
        ParsecOrganizationBootstrapAddr,
        ParsecOrganizationFileLinkAddr,
        ParsecInvitationAddr,
        ParsecPkiEnrollmentAddr,
    ]: ...

class ParsecOrganizationBootstrapAddr(ParsecAddr):
    def __init__(
        self,
        organization_id: OrganizationID,
        token: BootstrapToken | None,
        hostname: str,
        port: int | None,
        use_ssl: bool = True,
    ) -> None: ...
    def __hash__(self) -> int: ...
    @property
    def organization_id(self) -> OrganizationID: ...
    @property
    def token(self) -> BootstrapToken | None: ...
    @property
    def hostname(self) -> str: ...
    @property
    def port(self) -> int: ...
    @property
    def use_ssl(self) -> bool: ...
    @property
    def netloc(self) -> str: ...
    def generate_organization_addr(self, root_verify_key: VerifyKey) -> ParsecOrganizationAddr: ...
    def get_server_addr(self) -> ParsecAddr: ...
    def to_url(self) -> str: ...
    def to_http_domain_url(self, path: str = "") -> str: ...
    def to_http_redirection_url(self) -> str: ...
    @classmethod
    def from_url(
        cls, url: str, allow_http_redirection: bool = False
    ) -> ParsecOrganizationBootstrapAddr: ...
    @classmethod
    def build(
        cls,
        server_addr: ParsecAddr,
        organization_id: OrganizationID,
        token: BootstrapToken | None = None,
    ) -> ParsecOrganizationBootstrapAddr: ...

class ParsecOrganizationFileLinkAddr(ParsecAddr):
    def __init__(
        self,
        organization_id: OrganizationID,
        workspace_id: VlobID,
        key_index: int,
        encrypted_path: bytes,
        hostname: str,
        port: int | None,
        use_ssl: bool = True,
    ) -> None: ...
    def __hash__(self) -> int: ...
    @property
    def hostname(self) -> str: ...
    @property
    def port(self) -> int: ...
    @property
    def use_ssl(self) -> bool: ...
    @property
    def netloc(self) -> str: ...
    @property
    def organization_id(self) -> OrganizationID: ...
    @property
    def workspace_id(self) -> VlobID: ...
    @property
    def key_index(self) -> int: ...
    @property
    def encrypted_path(self) -> bytes: ...
    def get_server_addr(self) -> ParsecAddr: ...
    def to_url(self) -> str: ...
    def to_http_redirection_url(self) -> str: ...
    @classmethod
    def from_url(
        cls, url: str, allow_http_redirection: bool = False
    ) -> ParsecOrganizationFileLinkAddr: ...
    @classmethod
    def build(
        cls,
        organization_addr: ParsecOrganizationAddr,
        workspace_id: VlobID,
        key_index: int,
        encrypted_path: bytes,
    ) -> ParsecOrganizationFileLinkAddr: ...

class ParsecInvitationAddr(ParsecAddr):
    def __init__(
        self,
        organization_id: OrganizationID,
        invitation_type: InvitationType,
        token: InvitationToken,
        hostname: str,
        port: int | None,
        use_ssl: bool = True,
    ) -> None: ...
    def __hash__(self) -> int: ...
    @property
    def hostname(self) -> str: ...
    @property
    def port(self) -> int: ...
    @property
    def use_ssl(self) -> bool: ...
    @property
    def netloc(self) -> str: ...
    @property
    def organization_id(self) -> OrganizationID: ...
    @property
    def invitation_type(self) -> InvitationType: ...
    @property
    def token(self) -> InvitationToken: ...
    def get_server_addr(self) -> ParsecAddr: ...
    def to_url(self) -> str: ...
    def to_http_redirection_url(self) -> str: ...
    def generate_organization_addr(self, root_verify_key: VerifyKey) -> ParsecOrganizationAddr: ...
    @classmethod
    def from_url(cls, url: str, allow_http_redirection: bool = False) -> ParsecInvitationAddr: ...
    @classmethod
    def build(
        cls,
        server_addr: ParsecAddr,
        organization_id: OrganizationID,
        invitation_type: InvitationType,
        token: InvitationToken,
    ) -> ParsecInvitationAddr: ...

class ParsecPkiEnrollmentAddr(ParsecAddr):
    def __init__(
        self,
        organization_id: OrganizationID,
        hostname: str,
        port: int | None,
        use_ssl: bool = True,
    ) -> None: ...
    def __hash__(self) -> int: ...
    @property
    def hostname(self) -> str: ...
    @property
    def port(self) -> int: ...
    @property
    def use_ssl(self) -> bool: ...
    @property
    def netloc(self) -> str: ...
    @property
    def organization_id(self) -> OrganizationID: ...
    def get_server_addr(self) -> ParsecAddr: ...
    def to_url(self) -> str: ...
    def to_http_redirection_url(self) -> str: ...
    def to_http_domain_url(self, path: str = "") -> str: ...
    def generate_organization_addr(self, root_verify_key: VerifyKey) -> ParsecOrganizationAddr: ...
    @classmethod
    def from_url(
        cls, url: str, allow_http_redirection: bool = False
    ) -> ParsecPkiEnrollmentAddr: ...
    @classmethod
    def build(
        cls, server_addr: ParsecAddr, organization_id: OrganizationID
    ) -> ParsecPkiEnrollmentAddr: ...
