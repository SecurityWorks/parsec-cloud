// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 (eventually AGPL-3.0) 2016-present Scille SAS

use libparsec_types::prelude::*;

#[derive(Debug, Clone, serde::Serialize)]
#[non_exhaustive] // Force use of `new()` constructor to compute crc
pub struct TestbedTemplate {
    pub id: &'static str,
    pub root_signing_key: SigningKey,
    pub devices: Vec<TestbedDeviceData>,
    pub users: Vec<TestbedUserData>,
    pub device_files: Vec<TestbedDeviceFileData>,
    // TODO: finish me !
    // pub manifests: Vec<std::sync::Arc<Manifest>>,
    // pub vlobs: Vec<(VlobID, Bytes)>,
    // pub blocks: Vec<(BlockID, Bytes)>,
    // pub messages: Vec<(DeviceID, DateTime, Bytes, MessageContent)>,
    // pub sequester_services: Vec<(SequesterServiceID, SequesterServiceCertificate)>,
    pub crc: u32,
}

impl TestbedTemplate {
    pub fn device(&self, device_id: &DeviceID) -> &TestbedDeviceData {
        match self.devices.iter().find(|x| x.device_id == *device_id) {
            Some(device) => device,
            None => {
                let devices: Vec<_> = self.devices.iter().map(|d| d.device_id.as_ref()).collect();
                panic!(
                    "Unknown device `{}` in environment `{}`, valid devices: {:?}",
                    device_id, self.id, devices
                )
            }
        }
    }

    pub fn user(&self, user_id: &UserID) -> &TestbedUserData {
        match self.users.iter().find(|x| x.user_id == *user_id) {
            Some(user) => user,
            None => {
                let users: Vec<_> = self.users.iter().map(|d| d.user_id.as_ref()).collect();
                panic!(
                    "Unknown user `{}` in environment `{}`, valid users: {:?}",
                    user_id, self.id, users
                )
            }
        }
    }

    pub fn new(
        id: &'static str,
        root_signing_key: SigningKey,
        devices: Vec<TestbedDeviceData>,
        users: Vec<TestbedUserData>,
        device_files: Vec<TestbedDeviceFileData>,
    ) -> Self {
        let mut hasher = crc32fast::Hasher::new();

        // Remember that changing the order (or adding items) to the hasher change the result !
        hasher.update(id.as_bytes());
        hasher.update(root_signing_key.as_ref());
        for device in &devices {
            hasher.update(&device.crc.to_le_bytes());
        }
        for user in &users {
            hasher.update(&user.crc.to_le_bytes());
        }
        for device_file in &device_files {
            hasher.update(&device_file.crc.to_le_bytes());
        }

        Self {
            id,
            root_signing_key,
            devices,
            users,
            device_files,
            crc: hasher.finalize(),
        }
    }
}

#[derive(Debug, Clone, serde::Serialize)]
#[non_exhaustive] // Force use of `new()` constructor to compute crc
pub struct TestbedDeviceData {
    pub device_id: DeviceID,
    pub device_label: Option<DeviceLabel>,
    pub signing_key: SigningKey,
    pub local_symkey: SecretKey,
    pub certif: DeviceCertificate,
    pub raw_certif: Bytes,
    pub raw_redacted_certif: Bytes,
    pub crc: u32,
}

impl TestbedDeviceData {
    pub(crate) fn new(
        device_id: &DeviceID,
        device_label: Option<DeviceLabel>,
        signing_key: SigningKey,
        local_symkey: SecretKey,
        author: CertificateSignerOwned,
        author_signkey: &SigningKey,
        timestamp: DateTime,
    ) -> Self {
        let mut certif = DeviceCertificate {
            author,
            timestamp,
            device_id: device_id.to_owned(),
            device_label: None,
            verify_key: signing_key.verify_key(),
        };
        let raw_redacted_certif = certif.dump_and_sign(author_signkey);
        certif.device_label = device_label.clone();
        let raw_certif = certif.dump_and_sign(author_signkey);

        // Remember that changing the order (or adding items) to the hasher change the result !
        let mut hasher = crc32fast::Hasher::new();
        // Most data are contained in the certif (indirectly for the signing key)
        hasher.update(&raw_certif);
        hasher.update(local_symkey.as_ref());

        Self {
            device_id: device_id.to_owned(),
            device_label,
            signing_key,
            local_symkey,
            certif,
            raw_certif: raw_certif.into(),
            raw_redacted_certif: raw_redacted_certif.into(),
            crc: hasher.finalize(),
        }
    }
}

#[derive(Debug, Clone, serde::Serialize)]
#[non_exhaustive] // Force use of `new()` constructor to compute crc
pub struct TestbedUserData {
    pub user_id: UserID,
    pub human_handle: Option<HumanHandle>,
    pub private_key: PrivateKey,
    pub profile: UserProfile,
    pub user_manifest_id: EntryID,
    pub user_manifest_key: SecretKey,
    pub certif: UserCertificate,
    pub raw_certif: Bytes,
    pub raw_redacted_certif: Bytes,
    pub crc: u32,
}

impl TestbedUserData {
    #[allow(clippy::too_many_arguments)]
    pub(crate) fn new(
        user_id: &UserID,
        human_handle: Option<HumanHandle>,
        private_key: PrivateKey,
        profile: UserProfile,
        user_manifest_id: EntryID,
        user_manifest_key: SecretKey,
        author: CertificateSignerOwned,
        author_signkey: &SigningKey,
        timestamp: DateTime,
    ) -> Self {
        let mut certif = UserCertificate {
            author,
            timestamp,
            user_id: user_id.to_owned(),
            human_handle: None,
            public_key: private_key.public_key(),
            profile,
        };
        let raw_redacted_certif = certif.dump_and_sign(author_signkey);
        certif.human_handle = human_handle.clone();
        let raw_certif = certif.dump_and_sign(author_signkey);

        // Remember that changing the order (or adding items) to the hasher change the result !
        let mut hasher = crc32fast::Hasher::new();
        // Most data are contained in the certif (indirectly for the private key)
        hasher.update(&raw_certif);
        hasher.update(user_manifest_id.as_bytes());
        hasher.update(user_manifest_key.as_ref());

        Self {
            user_id: user_id.to_owned(),
            human_handle,
            private_key,
            profile,
            user_manifest_id,
            user_manifest_key,
            certif,
            raw_certif: raw_certif.into(),
            raw_redacted_certif: raw_redacted_certif.into(),
            crc: hasher.finalize(),
        }
    }
}

#[derive(Debug, Clone, serde::Serialize)]
#[non_exhaustive] // Force use of `new()` constructor to compute crc
pub struct TestbedDeviceFileData {
    // TODO: should also support non-password authentication ?
    pub device_id: DeviceID,
    pub password: String,
    pub local_symkey: SecretKey,
    pub crc: u32,
}

impl TestbedDeviceFileData {
    pub(crate) fn new(device_id: DeviceID, password: String, local_symkey: SecretKey) -> Self {
        // Remember that changing the order (or adding items) to the hasher change the result !
        let mut hasher = crc32fast::Hasher::new();
        hasher.update(device_id.as_ref().as_bytes());
        hasher.update(password.as_bytes());
        hasher.update(local_symkey.as_ref());

        TestbedDeviceFileData {
            device_id,
            password,
            local_symkey,
            crc: hasher.finalize(),
        }
    }
}
