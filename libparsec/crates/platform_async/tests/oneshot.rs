// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 (eventually AGPL-3.0) 2016-present Scille SAS

#[tokio::test]
pub async fn oneshot() {
    use libparsec_platform_async::oneshot;
    let (sx, rx) = oneshot::channel::<u8>();

    #[allow(clippy::let_unit_value)]
    let ret = sx.send(42).unwrap();
    assert!(matches!(ret, ()));

    let ret = rx.await.unwrap();
    assert!(matches!(ret, 42));
}

#[tokio::test]
pub async fn oneshot_try_recv() {
    use libparsec_platform_async::oneshot;
    let (sx, mut rx) = oneshot::channel::<u8>();

    let err = rx.try_recv().unwrap_err();
    assert!(matches!(err, oneshot::TryRecvError::Empty));

    #[allow(clippy::let_unit_value)]
    let ret = sx.send(42).unwrap();
    assert!(matches!(ret, ()));

    let ret = rx.try_recv().unwrap();
    assert!(matches!(ret, 42));

    let err = rx.try_recv().unwrap_err();
    assert!(matches!(err, oneshot::TryRecvError::Closed));
}

#[tokio::test]
pub async fn oneshot_receiver_dropped_before_send() {
    use libparsec_platform_async::oneshot;
    let (sx, rx) = oneshot::channel::<u8>();
    drop(rx);

    let err = sx.send(42).unwrap_err();
    assert!(matches!(err, 42));
}

#[tokio::test]
pub async fn oneshot_sender_dropped_before_send() {
    use libparsec_platform_async::oneshot;
    let (sx, rx) = oneshot::channel::<u8>();
    drop(sx);

    let err = rx.await.unwrap_err();
    assert!(matches!(err, oneshot::RecvError { .. }));
}

#[tokio::test]
pub async fn oneshot_sender_dropped_before_send_try_recv() {
    use libparsec_platform_async::oneshot;
    let (sx, mut rx) = oneshot::channel::<u8>();
    drop(sx);

    let err = rx.try_recv().unwrap_err();
    assert!(matches!(err, oneshot::TryRecvError::Closed));
}