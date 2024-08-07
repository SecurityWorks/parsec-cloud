// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

use libparsec::{
    authenticated_cmds::latest::invite_new_device::{self, InviteNewDeviceRep},
    InvitationType, ParsecInvitationAddr,
};

use crate::utils::*;

#[derive(clap::Parser)]
pub struct InviteDevice {
    #[clap(flatten)]
    config: ConfigWithDeviceSharedOpts,
}

pub async fn invite_device(invite_device: InviteDevice) -> anyhow::Result<()> {
    let InviteDevice {
        config: ConfigWithDeviceSharedOpts { config_dir, device },
    } = invite_device;
    log::trace!(
        "Inviting a device (confdir={}, device={})",
        config_dir.display(),
        device.as_deref().unwrap_or("N/A")
    );

    load_cmds_and_run(config_dir, device, |cmds, device| async move {
        let mut handle = start_spinner("Creating device invitation".into());

        let rep = cmds
            .send(invite_new_device::Req { send_email: false })
            .await?;

        let url = match rep {
            InviteNewDeviceRep::Ok { token, .. } => ParsecInvitationAddr::new(
                device.organization_addr.clone(),
                device.organization_id().clone(),
                InvitationType::Device,
                token,
            )
            .to_url(),
            rep => {
                return Err(anyhow::anyhow!(
                    "Server refused to create device invitation: {rep:?}"
                ));
            }
        };

        handle.stop_with_message(format!("Invitation URL: {YELLOW}{url}{RESET}"));

        Ok(())
    })
    .await
}
