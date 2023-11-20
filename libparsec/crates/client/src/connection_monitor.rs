// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

use std::{ops::ControlFlow, sync::Arc, collections::HashMap};

use libparsec_client_connection::{
    AuthenticatedCmds, ConnectionError, RateLimiter, SSEEventID, SSEResponseOrMissedEvents,
};
use libparsec_platform_async::{spawn, stream::StreamExt, JoinHandle};
use libparsec_platform_storage::certificates::PerTopicLastTimestamps;
use libparsec_protocol::authenticated_cmds::v4::events_listen::{APIEvent, Rep, Req};

use crate::event_bus::*;

pub struct ConnectionMonitor {
    worker: JoinHandle<()>,
}

fn dispatch_api_event(event: APIEvent, event_bus: &EventBus) {
    match event {
        APIEvent::Pinged { .. } => (),
        APIEvent::ServerConfig { active_users_limit, user_profile_outsider_allowed } => {
            let event = EventServerConfigChanged {active_users_limit, user_profile_outsider_allowed};
            event_bus.send(&event);
        }
        APIEvent::Invitation { status, token } => {
            let event = EventInviteStatusChanged {
                invitation_status: status,
                token,
            };
            event_bus.send(&event);
        }
        APIEvent::PkiEnrollment {  } => {
            let event = EventPkiEnrollmentUpdated {};
            event_bus.send(&event);
        }
        APIEvent::CommonCertificate { timestamp } => {
            let event = EventCertificatesUpdated { last_timestamps: PerTopicLastTimestamps{
                common: Some(timestamp), realm: HashMap::default(), sequester: None, shamir: None
            } };
            event_bus.send(&event);
        }
        APIEvent::SequesterCertificate { timestamp } => {
            let event = EventCertificatesUpdated { last_timestamps: PerTopicLastTimestamps{
                common: None, realm: HashMap::default(), sequester: Some(timestamp), shamir: None
            } };
            event_bus.send(&event);
        }
        APIEvent::ShamirCertificate { timestamp } => {
            let event = EventCertificatesUpdated { last_timestamps: PerTopicLastTimestamps{
                common: None, realm: HashMap::default(), sequester: None, shamir: Some(timestamp)
            } };
            event_bus.send(&event);
        }
        APIEvent::RealmCertificate { realm_id, timestamp } => {
            let event = EventCertificatesUpdated { last_timestamps: PerTopicLastTimestamps{
                common: None, realm: HashMap::from([(realm_id, timestamp)]), sequester: None, shamir: None
            } };
            event_bus.send(&event);
        }
        APIEvent::Vlob { author, blob, last_common_certificate_timestamp, last_realm_certificate_timestamp, realm_id, timestamp, version, vlob_id } => {
            let event = EventRealmVlobUpdated {
                author,
                blob,
                last_common_certificate_timestamp,
                last_realm_certificate_timestamp,
                realm_id,
                timestamp,
                version,
                vlob_id,
            };
            event_bus.send(&event);
        }
    }
}

#[derive(PartialEq, Eq)]
enum ConnectionState {
    Offline,
    Online,
}

impl ConnectionMonitor {
    /// Connection monitor must be the last monitor to start !
    pub async fn start(cmds: Arc<AuthenticatedCmds>, event_bus: EventBus) -> Self {
        let worker = spawn(async move {
            let mut state = ConnectionState::Offline;
            let mut last_event_id: Option<SSEEventID> = None;
            let mut backoff = RateLimiter::new();

            // As last monitor to start, we send this event to wake up all the other monitors
            event_bus.send(&EventMissedServerEvents);

            loop {
                backoff.wait().await;

                let mut stream = match cmds.start_sse::<Req>(last_event_id.as_ref()).await {
                    Ok(stream) => stream,
                    Err(err) => {
                        if handle_sse_error(&mut state, &event_bus, err.into()).is_break() {
                            return;
                        }
                        continue;
                    }
                };

                backoff.reset();

                while let Some(res) = stream.next().await {
                    match res {
                        Ok(event) => {
                            if let Some(retry) = event.retry {
                                backoff.set_desired_duration(retry)
                            }
                            if Some(&event.id) != last_event_id.as_ref() {
                                last_event_id.replace(event.id);
                            }
                            match event.message {
                                SSEResponseOrMissedEvents::MissedEvents => {
                                    event_bus.send(&EventMissedServerEvents);
                                }

                                SSEResponseOrMissedEvents::Response(rep) => {
                                    if ConnectionState::Offline == state {
                                        event_bus.send(&EventOnline);
                                        state = ConnectionState::Online;
                                    }

                                    match rep {
                                        Rep::Ok(event) => dispatch_api_event(event, &event_bus),
                                        // Unexpected error status
                                        rep => {
                                            log::warn!(
                                                "`events_listen` unexpected error response: {:?}",
                                                rep
                                            );
                                        }
                                    };
                                }
                            }
                        }
                        Err(err) => {
                            if handle_sse_error(&mut state, &event_bus, err).is_break() {
                                return;
                            }
                        }
                    }
                }
            }
        });

        Self { worker }
    }
}

fn handle_sse_error(
    state: &mut ConnectionState,
    event_bus: &EventBus,
    err: ConnectionError,
) -> ControlFlow<()> {
    if &ConnectionState::Online == state {
        event_bus.send(&EventOffline);
        *state = ConnectionState::Offline;
    }

    match err {
        // The only legit error is if we couldn't reach the server...
        ConnectionError::NoResponse(_) => ControlFlow::Continue(()),

        // ...otherwise the server rejected us, hence there is no use
        // retrying to connect and we just stop this coroutine
        ConnectionError::ExpiredOrganization => {
            event_bus.send(&EventExpiredOrganization);
            ControlFlow::Break(())
        }
        ConnectionError::RevokedUser => {
            event_bus.send(&EventRevokedUser);
            ControlFlow::Break(())
        }
        ConnectionError::UnsupportedApiVersion {
            api_version,
            supported_api_versions,
        } => {
            let event = EventIncompatibleServer(IncompatibleServerReason::UnsupportedApiVersion {
                api_version,
                supported_api_versions,
            });
            event_bus.send(&event);
            ControlFlow::Break(())
        }
        err => {
            let event =
                EventIncompatibleServer(IncompatibleServerReason::Unexpected(Arc::new(err.into())));
            event_bus.send(&event);
            ControlFlow::Break(())
        }
    }
}

impl Drop for ConnectionMonitor {
    fn drop(&mut self) {
        self.worker.abort()
    }
}
