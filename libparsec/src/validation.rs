// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

use std::str::FromStr;

/// Validate a label without doing a unicode normalization.
pub fn validate_entry_name(raw: &str) -> bool {
    libparsec_types::EntryName::from_str(raw).is_ok()
}

pub fn validate_path(raw: &str) -> bool {
    libparsec_types::FsPath::from_str(raw).is_ok()
}

/// Validate a label without doing a unicode normalization.
pub fn validate_human_handle_label(raw: &str) -> bool {
    libparsec_types::HumanHandle::label_is_valid(raw)
}

/// Validate an email without doing a unicode normalization.
pub fn validate_email(raw: &str) -> bool {
    use std::str::FromStr;
    libparsec_types::EmailAddress::from_str(raw).is_ok()
}

/// Validate a label without doing a unicode normalization.
pub fn validate_device_label(raw: &str) -> bool {
    libparsec_types::DeviceLabel::from_str(raw).is_ok()
}

pub fn validate_invitation_token(raw: &str) -> bool {
    libparsec_types::InvitationToken::from_hex(raw).is_ok()
}

pub fn validate_organization_id(raw: &str) -> bool {
    libparsec_types::OrganizationID::from_str(raw).is_ok()
}
