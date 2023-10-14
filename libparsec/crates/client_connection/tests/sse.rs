#![cfg(not(target_arch = "wasm32"))]
// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

mod proxy;

use futures_util::StreamExt;
use libparsec_client_connection::{AuthenticatedCmds, ConnectionError, SSEResponseOrMissedEvents};
use libparsec_platform_http_proxy::ProxyConfig;
use libparsec_protocol::authenticated_cmds::latest as authenticated_cmds;
use libparsec_testbed::TestbedEnv;
use libparsec_tests_lite::{p_assert_eq, p_assert_matches, parsec_test};

#[parsec_test(testbed = "coolorg", with_server)]
#[timeout(std::time::Duration::from_secs(5))]
async fn last_event_id(env: &TestbedEnv) {
    let alice = env.local_device("alice@dev1");
    let bob = env.local_device("bob@dev1");
    let mallory = env.local_device("mallory@dev1");

    let alice_proxy = proxy::spawn(env.server_addr.clone()).await.unwrap();

    let alice_proxy_cfg = alice_proxy.get_proxy().unwrap();
    let cmds_alice =
        AuthenticatedCmds::new(&env.discriminant_dir, alice.clone(), alice_proxy_cfg).unwrap();
    let cmds_bob =
        AuthenticatedCmds::new(&env.discriminant_dir, bob.clone(), ProxyConfig::default()).unwrap();
    let cmds_mallory = AuthenticatedCmds::new(
        &env.discriminant_dir,
        mallory.clone(),
        ProxyConfig::default(),
    )
    .unwrap();

    let bob_send_ping = |msg: &'static str| async {
        let rep = cmds_bob
            .send(authenticated_cmds::ping::Req {
                ping: msg.to_string(),
            })
            .await
            .expect("Failed to send ping");
        p_assert_matches!(rep, authenticated_cmds::ping::Rep::Ok { .. });
    };

    let mut sse_alice = cmds_alice
        .start_sse::<authenticated_cmds::events_listen::Req>(None)
        .await
        .unwrap();
    let mut sse_mallory = cmds_mallory
        .start_sse::<authenticated_cmds::events_listen::Req>(None)
        .await
        .unwrap();

    bob_send_ping("Hello world").await;

    let expected_response =
        SSEResponseOrMissedEvents::Response(authenticated_cmds::events_listen::Rep::Ok(
            authenticated_cmds::events_listen::APIEvent::Pinged {
                ping: "Hello world".into(),
            },
        ));

    let alice_event = sse_alice.next().await.unwrap().unwrap();
    p_assert_eq!(alice_event.message, expected_response);
    let last_alice_event_id = dbg!(alice_event.id);

    p_assert_eq!(
        sse_mallory.next().await.unwrap().unwrap().message,
        expected_response
    );

    alice_proxy.disconnect().await;
    bob_send_ping("Alice should be disconnected").await;

    let expected_response =
        SSEResponseOrMissedEvents::Response(authenticated_cmds::events_listen::Rep::Ok(
            authenticated_cmds::events_listen::APIEvent::Pinged {
                ping: "Alice should be disconnected".into(),
            },
        ));

    p_assert_eq!(
        sse_mallory.next().await.unwrap().unwrap().message,
        expected_response
    );

    let sse_alice_err = sse_alice.next().await.unwrap().unwrap_err();
    p_assert_matches!(
        sse_alice_err,
        ConnectionError::NoResponse(Some(e)) if e.to_string() == "request or response body error: error reading a body from connection: unexpected EOF during chunk size line",
        "{}", {
            if let ConnectionError::NoResponse(Some(e)) = &sse_alice_err {
                format!("ConnectionError::NoResponse({})", e)
            } else {
                format!("{:?}", sse_alice_err)
            }
        }
    );

    assert!(sse_alice.next().await.is_none());

    log::info!("Reconnect alice");

    let mut sse_alice = cmds_alice
        .start_sse::<authenticated_cmds::events_listen::Req>(Some(&last_alice_event_id))
        .await
        .unwrap();

    assert_eq!(
        sse_alice.next().await.unwrap().unwrap().message,
        expected_response
    );

    alice_proxy.close().await.unwrap();
}
