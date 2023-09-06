// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

// mod build;
mod build;
mod crc_hash;
mod events;
mod utils;

pub use build::*;
pub use events::*;

use libparsec_types::prelude::*;

use crc_hash::CrcHash;

pub struct TestbedTemplate {
    pub id: &'static str,
    pub events: Vec<TestbedEvent>,
    build_counters: TestbedTemplateBuilderCounters,
}

impl std::fmt::Debug for TestbedTemplate {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("TestbedTemplate")
            .field("id", &self.id)
            .field("events", &self.events)
            .finish()
    }
}

impl TestbedTemplate {
    pub fn from_builder(id: &'static str) -> TestbedTemplateBuilder {
        TestbedTemplateBuilder::new(id)
    }

    pub fn compute_crc(&self) -> u32 {
        let mut hasher = crc32fast::Hasher::new();
        for event in self.events.iter() {
            event.crc_hash(&mut hasher);
        }
        // Note `build_counters` is only used to add new events, hence there
        // is no need to hash it
        hasher.finalize()
    }

    pub fn root_signing_key(&self) -> &SigningKey {
        match self
            .events
            .first()
            .expect("Organization is not bootstrapped")
        {
            TestbedEvent::BootstrapOrganization(x) => &x.root_signing_key,
            _ => unreachable!(),
        }
    }

    pub fn sequester_authority_signing_key(&self) -> &SequesterSigningKeyDer {
        match self
            .events
            .first()
            .expect("Organization is not bootstrapped")
        {
            TestbedEvent::BootstrapOrganization(x) => x
                .sequester_authority
                .as_ref()
                .map(|sequester_authority| &sequester_authority.signing_key)
                .expect("Not a sequestered organization"),
            _ => unreachable!(),
        }
    }

    pub fn device_signing_key<'a>(&'a self, device_id: &DeviceID) -> &'a SigningKey {
        self.events
            .iter()
            .find_map(|e| match e {
                TestbedEvent::BootstrapOrganization(TestbedEventBootstrapOrganization {
                    first_user_device_id: candidate,
                    first_user_first_device_signing_key: signing_key,
                    ..
                })
                | TestbedEvent::NewUser(TestbedEventNewUser {
                    device_id: candidate,
                    first_device_signing_key: signing_key,
                    ..
                })
                | TestbedEvent::NewDevice(TestbedEventNewDevice {
                    device_id: candidate,
                    signing_key,
                    ..
                }) if candidate == device_id => Some(signing_key),
                _ => None,
            })
            .expect("Device doesn't exist")
    }

    pub fn device_local_symkey<'a>(&'a self, device_id: &DeviceID) -> &'a SecretKey {
        self.events
            .iter()
            .find_map(|e| match e {
                TestbedEvent::BootstrapOrganization(TestbedEventBootstrapOrganization {
                    first_user_device_id: candidate,
                    first_user_local_symkey: local_symkey,
                    ..
                })
                | TestbedEvent::NewUser(TestbedEventNewUser {
                    device_id: candidate,
                    local_symkey,
                    ..
                })
                | TestbedEvent::NewDevice(TestbedEventNewDevice {
                    device_id: candidate,
                    local_symkey,
                    ..
                }) if candidate == device_id => Some(local_symkey),
                _ => None,
            })
            .expect("Device doesn't exist")
    }

    pub fn user_private_key<'a>(&'a self, user_id: &UserID) -> &'a PrivateKey {
        self.events
            .iter()
            .find_map(|e| match e {
                TestbedEvent::BootstrapOrganization(TestbedEventBootstrapOrganization {
                    first_user_device_id: candidate,
                    first_user_private_key: private_key,
                    ..
                })
                | TestbedEvent::NewUser(TestbedEventNewUser {
                    device_id: candidate,
                    private_key,
                    ..
                }) if candidate.user_id() == user_id => Some(private_key),
                _ => None,
            })
            .expect("User doesn't exist")
    }

    pub fn user_profile_at(
        &self,
        user_id: &UserID,
        up_to_certificate_index: IndexInt,
    ) -> UserProfile {
        let mut current_profile = None;
        self.events.iter().find_map(|e| {
            let maybe_profile_update = match e {
                TestbedEvent::BootstrapOrganization(TestbedEventBootstrapOrganization {
                    first_user_device_id,
                    first_user_certificate_index,
                    ..
                }) if first_user_device_id.user_id() == user_id => {
                    Some((UserProfile::Admin, *first_user_certificate_index))
                }
                TestbedEvent::NewUser(TestbedEventNewUser {
                    device_id,
                    initial_profile,
                    user_certificate_index,
                    ..
                }) if device_id.user_id() == user_id => {
                    Some((*initial_profile, *user_certificate_index))
                }
                TestbedEvent::UpdateUserProfile(TestbedEventUpdateUserProfile {
                    user,
                    profile,
                    certificate_index,
                    ..
                }) if user == user_id => Some((*profile, *certificate_index)),
                _ => None,
            };
            maybe_profile_update.map(|(profile, certificate_index)| {
                if certificate_index > up_to_certificate_index {
                    // Stop iteration
                    Some(())
                } else {
                    current_profile = Some(profile);
                    None
                }
            })
        });
        current_profile.expect("User doesn't exist")
    }

    pub fn certificates(&self) -> impl Iterator<Item = TestbedTemplateEventCertificate> + '_ {
        self.events
            .iter()
            .flat_map(|event| event.certificates(self))
    }
}