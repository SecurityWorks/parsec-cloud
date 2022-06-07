// Parsec Cloud (https://parsec.cloud) Copyright (c) BSLv1.1 (eventually AGPLv3) 2016-2021 Scille SAS

use diesel::{Connection, ExpressionMethods, RunQueryDsl, SqliteConnection};
use rstest::rstest;
use std::num::NonZeroU64;
use std::path::PathBuf;

use parsec_api_crypto::HashDigest;
use parsec_api_types::{
    BlockAccess, BlockID, Blocksize, CertificateSignerOwned, DateTime, EntryID, FileManifest,
    FolderManifest, WorkspaceManifest,
};

use crate::model::Workspace;
use crate::schema::{block, device, info, realm_role, user_ as user, vlob_atom};

use tests_fixtures::{alice, Device};

impl Workspace {
    pub fn init_db(conn: &mut SqliteConnection, device: &Device) {
        use std::collections::HashMap;

        use parsec_api_types::DeviceCertificate;

        let t0 = "2000-1-1T00:00:00Z".parse::<DateTime>().unwrap();
        let _t0 = t0.get_f64_with_us_precision();

        diesel::insert_or_ignore_into(realm_role::table)
            .values((
                realm_role::_id.eq(0),
                realm_role::role_certificate.eq(&b"role"[..]),
            ))
            .execute(conn)
            .unwrap();

        diesel::insert_or_ignore_into(user::table)
            .values((user::_id.eq(0), user::user_certificate.eq(&b"user"[..])))
            .execute(conn)
            .unwrap();

        let device_certif = DeviceCertificate {
            author: CertificateSignerOwned::Root,
            timestamp: t0,
            device_id: device.device_id.clone(),
            device_label: None,
            verify_key: device.signing_key.verify_key().clone(),
        }
        .dump_and_sign(&device.signing_key);

        diesel::insert_or_ignore_into(device::table)
            .values((
                device::_id.eq(0),
                device::device_certificate.eq(&device_certif),
            ))
            .execute(conn)
            .unwrap();

        diesel::insert_or_ignore_into(block::table)
            .values((
                block::_id.eq(0),
                block::block_id.eq(&b"block_id"[..]),
                block::data.eq(&b"data"[..]),
                block::author.eq(0),
                block::size.eq(4),
                block::created_on.eq(0.),
            ))
            .execute(conn)
            .unwrap();

        // WorkspaceManifest
        // |_ FileManifest (file0)
        // |_ FolderManifest (folder0)
        //    |_ FileManifest (file00)
        //    |_ FolderManifest (folder00)
        //    |_ FolderManifest (folder01)
        //       |_ FileManifest (file010)
        //       |_ FileManifest (file011)

        let workspace_id = EntryID::default();
        let file0_id = EntryID::default();
        let folder0_id = EntryID::default();
        let file00_id = EntryID::default();
        let folder00_id = EntryID::default();
        let folder01_id = EntryID::default();
        let file010_id = EntryID::default();
        let file011_id = EntryID::default();

        let file0_block0_id = BlockID::default();
        let file0_block1_id = BlockID::default();
        let file0_block2_id = BlockID::default();
        let file00_block_id = BlockID::default();
        let file010_block_id = BlockID::default();
        let file011_block_id = BlockID::default();

        let file0_data0 = b"Hello ";
        let file0_data1 = b"World ";
        let file0_data2 = [0; 1];
        let file00_data = b"file00's content";
        let file010_data = b"file010's content";
        let file011_data = b"file011's content";

        let insert_manifest = |conn: &mut SqliteConnection, id: &[u8], manifest: &[u8]| {
            diesel::insert_or_ignore_into(vlob_atom::table)
                .values((
                    vlob_atom::vlob_id.eq(id),
                    vlob_atom::version.eq(1),
                    vlob_atom::blob.eq(manifest),
                    vlob_atom::size.eq(manifest.len() as i32),
                    vlob_atom::author.eq(0),
                    vlob_atom::timestamp.eq(_t0),
                ))
                .execute(conn)
                .unwrap()
        };

        let insert_data = |conn: &mut SqliteConnection, id: &[u8], data: &[u8]| {
            diesel::insert_or_ignore_into(block::table)
                .values((
                    block::block_id.eq(id),
                    block::data.eq(data),
                    block::author.eq(0),
                    block::size.eq(data.len() as i32),
                    block::created_on.eq(_t0),
                ))
                .execute(conn)
                .unwrap()
        };

        diesel::insert_or_ignore_into(info::table)
            .values((
                info::magic.eq(87947),
                info::version.eq(1),
                info::realm_id.eq((*workspace_id).as_ref()),
            ))
            .execute(conn)
            .unwrap();

        let workspace_manifest = WorkspaceManifest {
            author: device.device_id.clone(),
            timestamp: t0,
            id: workspace_id,
            version: 1,
            created: t0,
            updated: t0,
            children: HashMap::from([
                ("file0".parse().unwrap(), file0_id),
                ("folder0".parse().unwrap(), folder0_id),
            ]),
        }
        .dump_sign_and_encrypt(&device.signing_key, &device.local_symkey);

        let file0 = FileManifest {
            author: device.device_id.clone(),
            timestamp: t0,
            id: file0_id,
            parent: workspace_id,
            version: 1,
            created: t0,
            updated: t0,
            size: (file0_data0.len() + file0_data1.len() + file0_data2.len()) as u64,
            blocksize: Blocksize::try_from(512).expect("Invalid blocksize"),
            blocks: vec![
                BlockAccess {
                    id: file0_block0_id,
                    key: device.local_symkey.clone(),
                    offset: 0,
                    size: NonZeroU64::try_from(file0_data0.len() as u64).unwrap(),
                    digest: HashDigest::from_data(&file0_data0[..]),
                },
                BlockAccess {
                    id: file0_block1_id,
                    key: device.local_symkey.clone(),
                    offset: file0_data0.len() as u64,
                    size: NonZeroU64::try_from(file0_data1.len() as u64).unwrap(),
                    digest: HashDigest::from_data(&file0_data1[..]),
                },
                BlockAccess {
                    id: file0_block2_id,
                    key: device.local_symkey.clone(),
                    offset: (file0_data0.len() + file0_data1.len()) as u64,
                    size: NonZeroU64::try_from(file0_data2.len() as u64).unwrap(),
                    digest: HashDigest::from_data(&file0_data2[..]),
                },
            ],
        }
        .dump_sign_and_encrypt(&device.signing_key, &device.local_symkey);

        let folder0 = FolderManifest {
            author: device.device_id.clone(),
            timestamp: t0,
            id: folder0_id,
            parent: workspace_id,
            version: 1,
            created: t0,
            updated: t0,
            children: HashMap::from([
                ("file00".parse().unwrap(), file00_id),
                ("folder00".parse().unwrap(), folder00_id),
                ("folder01".parse().unwrap(), folder01_id),
            ]),
        }
        .dump_sign_and_encrypt(&device.signing_key, &device.local_symkey);

        let file00 = FileManifest {
            author: device.device_id.clone(),
            timestamp: t0,
            id: file00_id,
            parent: EntryID::from(folder0_id),
            version: 1,
            created: t0,
            updated: t0,
            size: file00_data.len() as u64,
            blocksize: Blocksize::try_from(512).expect("Invalid blocksize"),
            blocks: vec![BlockAccess {
                id: file00_block_id,
                key: device.local_symkey.clone(),
                offset: 0,
                size: NonZeroU64::try_from(file00_data.len() as u64).unwrap(),
                digest: HashDigest::from_data(&file00_data[..]),
            }],
        }
        .dump_sign_and_encrypt(&device.signing_key, &device.local_symkey);

        let folder00 = FolderManifest {
            author: device.device_id.clone(),
            timestamp: t0,
            id: folder00_id,
            parent: EntryID::from(folder0_id),
            version: 1,
            created: t0,
            updated: t0,
            children: HashMap::new(),
        }
        .dump_sign_and_encrypt(&device.signing_key, &device.local_symkey);

        let folder01 = FolderManifest {
            author: device.device_id.clone(),
            timestamp: t0,
            id: folder01_id,
            parent: EntryID::from(folder0_id),
            version: 1,
            created: t0,
            updated: t0,
            children: HashMap::from([
                ("file010".parse().unwrap(), file010_id),
                ("file011".parse().unwrap(), file011_id),
            ]),
        }
        .dump_sign_and_encrypt(&device.signing_key, &device.local_symkey);

        let file010 = FileManifest {
            author: device.device_id.clone(),
            timestamp: t0,
            id: file010_id,
            parent: EntryID::from(folder01_id),
            version: 1,
            created: t0,
            updated: t0,
            size: file010_data.len() as u64,
            blocksize: Blocksize::try_from(512).expect("Invalid blocksize"),
            blocks: vec![BlockAccess {
                id: file010_block_id,
                key: device.local_symkey.clone(),
                offset: 0,
                size: NonZeroU64::try_from(file010_data.len() as u64).unwrap(),
                digest: HashDigest::from_data(&file010_data[..]),
            }],
        }
        .dump_sign_and_encrypt(&device.signing_key, &device.local_symkey);

        let file011 = FileManifest {
            author: device.device_id.clone(),
            timestamp: t0,
            id: file011_id,
            parent: EntryID::from(folder01_id),
            version: 1,
            created: t0,
            updated: t0,
            size: file011_data.len() as u64,
            blocksize: Blocksize::try_from(512).expect("Invalid blocksize"),
            blocks: vec![BlockAccess {
                id: file011_block_id,
                key: device.local_symkey.clone(),
                offset: 0,
                size: NonZeroU64::try_from(file011_data.len() as u64).unwrap(),
                digest: HashDigest::from_data(&file011_data[..]),
            }],
        }
        .dump_sign_and_encrypt(&device.signing_key, &device.local_symkey);

        insert_manifest(conn, (*workspace_id).as_ref(), &workspace_manifest);
        insert_manifest(conn, (*file0_id).as_ref(), &file0);
        insert_data(conn, (*file0_block0_id).as_ref(), &file0_data0[..]);
        insert_data(conn, (*file0_block1_id).as_ref(), &file0_data1[..]);
        insert_data(conn, (*file0_block2_id).as_ref(), &file0_data2[..]);
        insert_manifest(conn, (*folder0_id).as_ref(), &folder0);
        insert_manifest(conn, (*file00_id).as_ref(), &file00);
        insert_data(conn, (*file00_block_id).as_ref(), &file00_data[..]);
        insert_manifest(conn, (*folder00_id).as_ref(), &folder00);
        insert_manifest(conn, (*folder01_id).as_ref(), &folder01);
        insert_manifest(conn, (*file010_id).as_ref(), &file010);
        insert_data(conn, (*file010_block_id).as_ref(), &file010_data[..]);
        insert_manifest(conn, (*file011_id).as_ref(), &file011);
        insert_data(conn, (*file011_block_id).as_ref(), &file011_data[..]);
    }
}

#[rstest]
fn test_parsec_sequestre_dump(alice: &Device) {
    use diesel::connection::SimpleConnection;

    let input = "/tmp/parsec_sequestre_dump.sqlite";
    let output = PathBuf::from("/tmp/out");
    let dir = std::env::var("CARGO_MANIFEST_DIR").expect("CARGO_MANIFEST_DIR should be set");

    macro_rules! read_sql {
        ($file: literal) => {
            std::fs::read_to_string(format!("{dir}/migrations/{}", $file)).unwrap()
        };
    }

    let mut conn = SqliteConnection::establish(input).unwrap();

    let sql = read_sql!("0000_init/down.sql") + &read_sql!("0000_init/up.sql");

    conn.batch_execute(&sql).unwrap();

    Workspace::init_db(&mut conn, alice);

    Workspace::dump(&mut conn, &alice.local_symkey, &output).unwrap();

    assert_eq!(std::fs::read("/tmp/out/file0").unwrap(), b"Hello World \0");
    assert_eq!(
        std::fs::read("/tmp/out/folder0/file00").unwrap(),
        b"file00's content"
    );
    assert_eq!(
        std::fs::read("/tmp/out/folder0/folder01/file010").unwrap(),
        b"file010's content"
    );
    assert_eq!(
        std::fs::read("/tmp/out/folder0/folder01/file011").unwrap(),
        b"file011's content"
    );
}
