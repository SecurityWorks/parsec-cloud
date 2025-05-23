// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

use proptest::prelude::*;
use proptest::test_runner::Config;
use proptest_state_machine::{prop_state_machine, ReferenceStateMachine, StateMachineTest};
use std::collections::HashSet;
use std::io::Seek;
use std::io::{Cursor, Read, SeekFrom, Write};

use libparsec_tests_fixtures::prelude::*;
use libparsec_types::prelude::*;

use super::file_operations::Storage;

const MAX_SIZE: u64 = 64;

pub struct FileOperationOracleStateMachine;

/// The possible transitions of the state machine.
#[derive(Clone, Debug)]
pub enum Transition {
    Read { size: u64, offset: u64 },
    Write { content: Vec<u8>, offset: u64 },
    Resize { length: u64 },
    Reshape,
}

#[derive(Default, Clone, Debug, PartialEq, Eq)]
pub struct ReferenceState {
    cursor: std::io::Cursor<Vec<u8>>,
    data: Vec<u8>,
}

// Implementation of the reference state machine that drives the test. That is,
// it's used to generate a sequence of transitions the `StateMachineTest`.
impl ReferenceStateMachine for FileOperationOracleStateMachine {
    type State = ReferenceState;
    type Transition = Transition;

    fn init_state() -> BoxedStrategy<Self::State> {
        Just(ReferenceState::default()).boxed()
    }

    fn transitions(_state: &Self::State) -> BoxedStrategy<Self::Transition> {
        prop_oneof![
            (0..MAX_SIZE).prop_flat_map(|size| {
                (0..MAX_SIZE).prop_map(move |offset| Transition::Read { size, offset })
            }),
            (0..MAX_SIZE).prop_flat_map(|offset| {
                any_with::<Vec<u8>>(prop::collection::size_range(0..MAX_SIZE as usize).lift())
                    .prop_map(move |content| Transition::Write { content, offset })
            }),
            (0..MAX_SIZE).prop_map(|length| Transition::Resize { length }),
            Just(Transition::Reshape),
        ]
        .boxed()
    }

    fn apply(mut state: Self::State, transition: &Self::Transition) -> Self::State {
        match transition {
            Transition::Read { size, offset } => {
                state.data.resize(*size as usize, 0);
                state.cursor.seek(SeekFrom::Start(*offset)).unwrap();
                let n = state.cursor.read(&mut state.data).unwrap();
                state.data.truncate(n);
            }
            Transition::Write { content, offset } => {
                if !content.is_empty() {
                    state.cursor.seek(SeekFrom::Start(*offset)).unwrap();
                    state.cursor.write_all(content).unwrap();
                }
            }
            Transition::Resize { length } => {
                let mut buf = state.cursor.into_inner();
                buf.resize(*length as usize, 0);
                state.cursor = Cursor::new(buf);
            }
            Transition::Reshape => (),
        }
        state.cursor.seek(SeekFrom::End(0)).unwrap();
        state
    }
}

pub struct FileOperationStateMachine {
    storage: Storage,
    manifest: LocalFileManifest,
    device_id: DeviceID,
    time_provider: TimeProvider,
}

impl FileOperationStateMachine {
    fn read(&self, size: u64, offset: u64, expected: &[u8]) {
        let data = self.storage.read(&self.manifest, size, offset);
        assert_eq!(data, expected);
    }

    fn resize(&mut self, length: u64) {
        let timestamp = self.time_provider.now();
        self.storage.resize(&mut self.manifest, length, timestamp);
    }

    fn write(&mut self, content: &[u8], offset: u64) {
        let timestamp = self.time_provider.now();
        self.storage
            .write(&mut self.manifest, content, offset, timestamp);
    }

    fn reshape(&mut self) {
        self.storage.reshape(&mut self.manifest);
        assert!(self.manifest.is_reshaped());
    }
}

impl StateMachineTest for FileOperationStateMachine {
    type SystemUnderTest = Self;
    type Reference = FileOperationOracleStateMachine;

    fn init_test(
        _ref_state: &<Self::Reference as ReferenceStateMachine>::State,
    ) -> Self::SystemUnderTest {
        let time_provider = TimeProvider::default();
        let device_id = DeviceID::default();
        let mut manifest =
            LocalFileManifest::new(device_id, VlobID::default(), time_provider.now());
        manifest.blocksize = Blocksize::try_from(8).unwrap();
        manifest.base.blocksize = manifest.blocksize;
        FileOperationStateMachine {
            storage: Storage::default(),
            manifest,
            device_id,
            time_provider,
        }
    }

    fn apply(
        mut state: Self::SystemUnderTest,
        ref_state: &<Self::Reference as ReferenceStateMachine>::State,
        transition: Transition,
    ) -> Self::SystemUnderTest {
        match transition {
            Transition::Reshape => {
                state.reshape();
            }
            Transition::Resize { length } => {
                state.resize(length);
            }
            Transition::Read { size, offset } => {
                state.read(size, offset, &ref_state.data);
            }
            Transition::Write { content, offset } => {
                state.write(&content, offset);
            }
        }
        state
    }

    fn check_invariants(
        state: &Self::SystemUnderTest,
        ref_state: &<Self::Reference as ReferenceStateMachine>::State,
    ) {
        // 1. Manifest integrity
        state.manifest.check_data_integrity().unwrap();
        // 2. Same size for the manifest and the cursor
        assert_eq!(ref_state.cursor.position(), state.manifest.size);
        // 3. Remote conversion is OK
        if state.manifest.is_reshaped() {
            let remote = state
                .manifest
                .to_remote(state.device_id, state.time_provider.now())
                .unwrap();
            // Data size matches the block access size
            for block_access in remote.blocks.iter() {
                let chunk_id = ChunkID::from_hex(&block_access.id.hex()).unwrap();
                let data_length = state.storage.0.get(&chunk_id).unwrap().len();
                assert_eq!(block_access.size.get() as usize, data_length);
            }
            LocalFileManifest::from_remote(remote)
                .check_data_integrity()
                .unwrap();
        }
        // 3. No corruption or leaks in the storage
        let manifest_ids: HashSet<_> = state
            .manifest
            .blocks
            .iter()
            .flat_map(|b| b.iter().map(|c| c.id))
            .collect();
        let storage_ids: HashSet<_> = state.storage.0.keys().cloned().collect();
        assert_eq!(manifest_ids, storage_ids);
        // 4. Data size matches metadata
        for chunk_view in state.manifest.blocks.iter().flatten() {
            let data_length = state.storage.0.get(&chunk_view.id).unwrap().len();
            assert_eq!(chunk_view.raw_size.get() as usize, data_length);
        }
    }
}

prop_state_machine! {
    #![proptest_config(Config {
        cases: 10000, // About 2 seconds
        .. Config::default()
    })]
    #[parsec_test]
    fn file_operations_stateful_test(
        // This is a macro's keyword - only `sequential` is currently supported.
        sequential
        // The number of transitions to be generated for each case. This can
        // be a single numerical value or a range as in here.
        1..20
        // Macro's boilerplate to separate the following identifier.
        =>
        // The name of the type that implements `StateMachineTest`.
        FileOperationStateMachine
    );
}
