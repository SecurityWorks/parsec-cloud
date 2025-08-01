# Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

from typing import Any, ClassVar, Generic, TypeVar

#
# Meta-types
#
# These types are not part of the API but are meant to be used to describe it.
#

OK = TypeVar("OK")
ERR = TypeVar("ERR")
REFERENCED = TypeVar("REFERENCED")


class Result(Generic[OK, ERR]):
    pass


class Enum:
    pass


class EnumItemUnit:
    pass


# e.g.
#
#       enum Foo {
#           A{a: u32},
#           B(u32, u32),
#           C
#       }
#
# represented as:
#
#     class Foo(Variant):
#         class A:
#             a: int
#         B = VariantItemTuple(int, int)
#         C = VariantItemUnit()
class Variant:
    pass


class VariantItemUnit:
    pass


class VariantItemTuple:
    def __init__(self, *items: Any):
        self.items = items


# Similar to a variant, but:
# - also provide an `error` field that contains the `to_string()` of the value.
# - Doesn't allow js-to-rust conversion (given this is only a type returned by the Rust API)
class ErrorVariant(Variant):
    pass


class Structure:
    pass


# Represent passing parameter in function by reference
class Ref(Generic[REFERENCED]):
    pass


# A type that should be converted from/into string
class StrBasedType:
    pass


# A type that should be converted from/into bytes
class BytesBasedType:
    pass


# A type that should be converted from/into f64
class F64BasedType:
    pass


# Types that should be converted into f64 on js side, but from u8 on rs side
class U8BasedType(int):
    pass


# Types that should be converted into f64 on js side, but from i32 on rs side
class I32BasedType:
    pass


# Types that should be converted into f64 on js side, but from u32 on rs side
class U32BasedType:
    pass


# Types that should be converted into f64 on js side, but from i64 on rs side
class I64BasedType:
    pass


# Types that should be converted into f64 on js side, but from u64 on rs side
class U64BasedType:
    pass


class CustomConversionType:
    pass


#
# Common types
#


class U8(U8BasedType):
    pass


class NonZeroU8(U8BasedType):
    custom_from_rs_u8 = "|x: u8| -> Result<std::num::NonZeroU8, _> { std::num::NonZeroU8::try_from(x).map_err(|e| e.to_string()) }"
    custom_to_rs_u8 = "|x: std::num::NonZeroU8| -> Result<u8, &'static str> { Ok(x.get()) }"


class I32(I32BasedType):
    pass


class U32(U32BasedType):
    pass


class I64(I64BasedType):
    pass


class U64(U64BasedType):
    pass


class VersionInt(U32BasedType):
    pass


class SizeInt(U64BasedType):
    pass


class IndexInt(U64BasedType):
    pass


class Handle(U32BasedType):
    pass


class ApiVersion(StrBasedType):
    custom_from_rs_string = "|s: String| -> Result<_, String> { libparsec::ApiVersion::try_from(s.as_str()).map_err(|e| e.to_string()) }"
    custom_to_rs_string = (
        "|x: libparsec::ApiVersion| -> Result<String, &'static str> { Ok(x.to_string()) }"
    )


class OrganizationID(StrBasedType):
    custom_from_rs_string = "|s: String| -> Result<_, String> { libparsec::OrganizationID::try_from(s.as_str()).map_err(|e| e.to_string()) }"


class UserID(StrBasedType):
    custom_from_rs_string = "|s: String| -> Result<libparsec::UserID, _> { libparsec::UserID::from_hex(s.as_str()).map_err(|e| e.to_string()) }"
    custom_to_rs_string = "|x: libparsec::UserID| -> Result<String, &'static str> { Ok(x.hex()) }"


class DeviceID(StrBasedType):
    custom_from_rs_string = "|s: String| -> Result<libparsec::DeviceID, _> { libparsec::DeviceID::from_hex(s.as_str()).map_err(|e| e.to_string()) }"
    custom_to_rs_string = "|x: libparsec::DeviceID| -> Result<String, &'static str> { Ok(x.hex()) }"


class DeviceLabel(StrBasedType):
    custom_from_rs_string = "|s: String| -> Result<_, String> { libparsec::DeviceLabel::try_from(s.as_str()).map_err(|e| e.to_string()) }"


class EmailAddress(StrBasedType):
    custom_from_rs_string = "|s: String| -> Result<_, String> { libparsec::EmailAddress::from_str(s.as_str()).map_err(|e| e.to_string()) }"
    custom_to_rs_string = (
        "|x: libparsec::EmailAddress| -> Result<_, &'static str> { Ok(x.to_string()) }"
    )


class HumanHandle(Structure):
    email: EmailAddress
    label: str
    custom_getters: ClassVar = {
        "email": "|obj: &libparsec::HumanHandle| -> libparsec::EmailAddress { obj.email().clone() }",
        "label": "|obj| -> &str { fn a(o: &libparsec::HumanHandle) -> &str { o.label() } a(obj) }",
    }
    custom_init: str = """
        |email: libparsec::EmailAddress, label: String| -> Result<_, String> {
            libparsec::HumanHandle::new(email, &label).map_err(|e| e.to_string())
        }
    """


class DateTime(F64BasedType):
    custom_from_rs_f64 = """|n: f64| -> Result<_, &'static str> { libparsec::DateTime::from_timestamp_micros((n * 1_000_000f64) as i64).map_err(|_| "Out-of-bound datetime") }"""
    custom_to_rs_f64 = "|dt: libparsec::DateTime| -> Result<f64, &'static str> { Ok((dt.as_timestamp_micros() as f64) / 1_000_000f64) }"
    # We use Luxon's Datetime type on client side
    custom_ts_type_declaration = (
        "export type { DateTime } from 'luxon'; import type { DateTime } from 'luxon';"
    )


class Password(StrBasedType):
    custom_from_rs_string = "|s: String| -> Result<_, String> { Ok(s.into()) }"


class Path(StrBasedType):
    custom_from_rs_string = (
        "|s: String| -> Result<_, &'static str> { Ok(std::path::PathBuf::from(s)) }"
    )
    custom_to_rs_string = '|path: std::path::PathBuf| -> Result<_, _> { path.into_os_string().into_string().map_err(|_| "Path contains non-utf8 characters") }'


class FsPath(StrBasedType):
    custom_from_rs_string = "|s: String| -> Result<_, String> { s.parse::<libparsec::FsPath>().map_err(|e| e.to_string()) }"
    custom_to_rs_string = (
        "|path: libparsec::FsPath| -> Result<_, &'static str> { Ok(path.to_string()) }"
    )


class SequesterServiceID(StrBasedType):
    custom_from_rs_string = "|s: String| -> Result<libparsec::SequesterServiceID, _> { libparsec::SequesterServiceID::from_hex(s.as_str()).map_err(|e| e.to_string()) }"
    custom_to_rs_string = (
        "|x: libparsec::SequesterServiceID| -> Result<String, &'static str> { Ok(x.hex()) }"
    )


class SequesterVerifyKeyDer(BytesBasedType):
    pass


class KeyDerivation(BytesBasedType):
    pass


class SecretKey(BytesBasedType):
    pass


class SASCode(StrBasedType):
    custom_from_rs_string = "|s: String| -> Result<_, String> { s.parse::<libparsec::SASCode>().map_err(|e| e.to_string()) }"


class EntryName(StrBasedType):
    custom_from_rs_string = "|s: String| -> Result<_, _> { s.parse::<libparsec::EntryName>().map_err(|e| e.to_string()) }"


# VlobID and InvitationToken, are defined as strings (instead of
# Uint8Array) so that the Typescript code only manipulates strings without
# conversion or parsing.


class VlobID(StrBasedType):
    custom_from_rs_string = "|s: String| -> Result<libparsec::VlobID, _> { libparsec::VlobID::from_hex(s.as_str()).map_err(|e| e.to_string()) }"
    custom_to_rs_string = "|x: libparsec::VlobID| -> Result<String, &'static str> { Ok(x.hex()) }"


class InvitationToken(StrBasedType):
    custom_from_rs_string = "|s: String| -> Result<libparsec::InvitationToken, _> { libparsec::InvitationToken::from_hex(s.as_str()).map_err(|e| e.to_string()) }"
    custom_to_rs_string = (
        "|x: libparsec::InvitationToken| -> Result<String, &'static str> { Ok(x.hex()) }"
    )


class ValidationCode(StrBasedType):
    custom_from_rs_string = "|s: String| -> Result<libparsec::ValidationCode, _> { libparsec::ValidationCode::from_str(&s).map_err(|e| e.to_string()) }"
    custom_to_rs_string = (
        "|x: libparsec::ValidationCode| -> Result<String, &'static str> { Ok(x.into()) }"
    )


class GreetingAttemptID(StrBasedType):
    custom_from_rs_string = "|s: String| -> Result<libparsec::GreetingAttemptID, _> { libparsec::GreetingAttemptID::from_hex(s.as_str()).map_err(|e| e.to_string()) }"
    custom_to_rs_string = (
        "|x: libparsec::GreetingAttemptID| -> Result<String, &'static str> { Ok(x.hex()) }"
    )


class UserProfile(Enum):
    Admin = EnumItemUnit
    Standard = EnumItemUnit
    Outsider = EnumItemUnit


class RealmRole(Enum):
    Owner = EnumItemUnit
    Manager = EnumItemUnit
    Contributor = EnumItemUnit
    Reader = EnumItemUnit


class InvitationStatus(Enum):
    Pending = EnumItemUnit
    Finished = EnumItemUnit
    Cancelled = EnumItemUnit


class InvitationType(Enum):
    User = EnumItemUnit
    Device = EnumItemUnit
    ShamirRecovery = EnumItemUnit


class AccountAuthMethodID(StrBasedType):
    custom_from_rs_string = "|s: String| -> Result<libparsec::AccountAuthMethodID, _> { libparsec::AccountAuthMethodID::from_hex(s.as_str()).map_err(|e| e.to_string()) }"
    custom_to_rs_string = (
        "|x: libparsec::AccountAuthMethodID| -> Result<String, &'static str> { Ok(x.hex()) }"
    )


class AccountVaultItemOpaqueKeyID(StrBasedType):
    custom_from_rs_string = "|s: String| -> Result<libparsec::AccountVaultItemOpaqueKeyID, _> { libparsec::AccountVaultItemOpaqueKeyID::from_hex(s.as_str()).map_err(|e| e.to_string()) }"
    custom_to_rs_string = "|x: libparsec::AccountVaultItemOpaqueKeyID| -> Result<String, &'static str> { Ok(x.hex()) }"
