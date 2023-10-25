// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

// `allow-unwrap-in-test` don't behave as expected, see:
// https://github.com/rust-lang/rust-clippy/issues/11119
#![allow(clippy::unwrap_used)]

use std::io;

use libparsec_platform_http_proxy::ProxyConfig;
use libparsec_types::BackendAddr;
use rand::Rng;
use tokio::{
    net::{TcpListener, TcpStream},
    sync::{mpsc, oneshot},
};

pub struct ProxyHandle {
    join_handle: tokio::task::JoinHandle<io::Result<()>>,
    port: u16,
    notify_disconnect: mpsc::Sender<Event>,
}

impl ProxyHandle {
    pub fn get_proxy(&self) -> anyhow::Result<ProxyConfig> {
        ProxyConfig::default()
            .with_http_proxy(format!("http://localhost:{}", self.port))?
            .with_https_proxy(format!("http://localhost:{}", self.port))
    }

    pub async fn disconnect(&self) {
        log::trace!("Notify proxy server to close the connections ...");
        self.notify_disconnect
            .send(Event::Disconnect)
            .await
            .unwrap()
    }

    pub async fn close(self) -> io::Result<()> {
        self.notify_disconnect.send(Event::Close).await.unwrap();
        self.join_handle.await.unwrap()
    }
}

enum Event {
    Close,
    Disconnect,
}

pub async fn spawn(backend_addr: BackendAddr) -> io::Result<ProxyHandle> {
    let port = rand::thread_rng().gen_range(10_000..u16::MAX);
    let (tx_server_ready, rx_server_ready) = oneshot::channel();
    let (tx_disconnect, rx_disconnect) = mpsc::channel(1);
    let server = ProxyServer {
        port,
        backend_addr,
        notify_disconnect: rx_disconnect,
    };
    let handle = tokio::task::spawn(server.run(tx_server_ready));

    match rx_server_ready.await {
        Ok(_) => {
            log::trace!("Proxy server is ready");
            Ok(ProxyHandle {
                join_handle: handle,
                port,
                notify_disconnect: tx_disconnect,
            })
        }
        Err(_) => {
            log::error!("Failed to start proxy server, joining the thread ...");
            let expect_err = handle
                .await
                .expect("Failed to join the proxy server thread")
                .expect_err("The server should have failed");
            log::error!("The server failed to start because: {expect_err}");
            Err(expect_err)
        }
    }
}

struct ProxyServer {
    port: u16,
    backend_addr: BackendAddr,
    notify_disconnect: mpsc::Receiver<Event>,
}

impl ProxyServer {
    async fn run(mut self, ready: oneshot::Sender<()>) -> io::Result<()> {
        let url = self.backend_addr.to_http_url(None);
        let server_addr = extract_url_domain_and_port(&url).ok_or_else(|| {
            io::Error::new(
                io::ErrorKind::InvalidData,
                format!("Cannot extract domain and port on url `{url}`"),
            )
        })?;
        log::trace!("backend url: {url}, {server_addr:?}");
        let listener = TcpListener::bind(("localhost", self.port)).await?;
        ready
            .send(())
            .expect("The other side is waiting for this message");

        loop {
            // We wait for incoming connection from the client or until we are notified.
            let (mut client_socket, client_addr) = tokio::select! {
                res = listener.accept() => {
                    res
                }
                res = self.notify_disconnect.recv() => {
                    match res {
                        Some(Event::Disconnect) => {
                            continue
                        },
                        Some(Event::Close) | None => {
                            break
                        },
                    }
                }
            }?;
            log::trace!("New client {}", client_addr);

            // We connect to the actual backend.
            let mut server_socket = match TcpStream::connect(server_addr).await {
                Ok(v) => {
                    log::trace!("Connected to backend");
                    v
                }
                Err(e) => {
                    log::error!("Failed to connect to the backend: {e}");
                    drop(client_socket);
                    continue;
                }
            };

            // Now we stream the data from the client/server to server/client or until we receive a
            // message from `notify_disconnect`.
            tokio::select! {
                copy_res = tokio::io::copy_bidirectional(&mut client_socket, &mut server_socket) => {
                    log::warn!("Client / Server finished communicating ({copy_res:?})");
                }
                res = self.notify_disconnect.recv() => {
                    log::debug!("Disconnect client from proxy ...");
                    drop(client_socket);
                    drop(server_socket);
                    match res {
                        Some(Event::Disconnect) => {
                            continue;
                        },
                        Some(Event::Close) | None => {
                            break
                        },
                    }
                }
            }
        }

        log::info!("Proxy stopped");
        Ok(())
    }
}

fn extract_url_domain_and_port(u: &url::Url) -> Option<(&str, u16)> {
    let domain = u.host_str()?;

    let port = u
        .port_or_known_default()
        .unwrap_or_else(|| panic!("Unsupported scheme: {}", u.scheme()));

    Some((domain, port))
}
