// Parsec Cloud (https://parsec.cloud) Copyright (c) BSLv1.1 (eventually AGPLv3) 2016-2021 Scille SAS

use async_std::sync::Mutex;
use std::cmp::{max, min};
use std::collections::HashMap;

use libparsec_client_types::{
    Chunk, LocalDevice, LocalFileManifest, LocalFolderManifest, LocalManifest,
    LocalWorkspaceManifest,
};
use libparsec_types::{
    BlockAccess, DeviceID, EntryID, FileDescriptor, FileManifest, FolderManifest,
};

use crate::file_operations::{prepare_read, prepare_reshape, prepare_resize, prepare_write};
use crate::storage::WorkspaceStorage;
use crate::{ChunkOrBlockID, FSError, FSResult, Language};

/// A stateless class to centralize all file transactions.
///
/// The actual state is stored in the local storage and file transactions
/// have access to the remote loader to download missing resources.
///
/// The exposed transactions all take a file descriptor as first argument.
/// The file descriptors correspond to an entry id which points to a file
/// on the file system (i.e. a file manifest).
///
/// The corresponding file is locked while performing the change (i.e. between
/// the reading and writing of the corresponding manifest) in order to avoid
/// race conditions and data corruption.
///
/// The table below lists the effects of the 6 file transactions:
/// - close    -> remove file descriptor from local storage
/// - write    -> affects file content and possibly file size
/// - truncate -> affects file size and possibly file content
/// - read     -> no side effect
/// - flush    -> no-op
pub struct FileTransactions {
    workspace_id: EntryID,
    device: LocalDevice,
    local_storage: WorkspaceStorage,
    write_count: Mutex<HashMap<FileDescriptor, u64>>,
    prefered_language: Language,
}

impl FileTransactions {
    pub fn new(
        workspace_id: EntryID,
        device: LocalDevice,
        local_storage: WorkspaceStorage,
        prefered_language: Language,
    ) -> Self {
        Self {
            workspace_id,
            device,
            local_storage,
            write_count: Mutex::new(HashMap::new()),
            prefered_language,
        }
    }

    pub fn local_author(&self) -> &DeviceID {
        &self.device.device_id
    }

    fn normalize_argument(arg: i64, manifest: &LocalFileManifest) -> u64 {
        if arg < 0 {
            manifest.size
        } else {
            arg as u64
        }
    }

    /// Return the data between the start and stop index.
    /// The data is treated as padded with an infinite amount of null bytes before index 0.
    fn padded_data(data: &[u8], start: i64, stop: i64) -> Vec<u8> {
        if start <= stop && stop <= 0 {
            return vec![0; (stop - start) as usize];
        }
        if 0 <= start && start <= stop {
            return data[start as usize..stop as usize].to_vec();
        }

        let mut res = vec![0; (stop - start) as usize];
        (&mut res[start.unsigned_abs() as usize..]).copy_from_slice(&data[..stop as usize]);

        res
    }

    fn read_chunk<'a>(chunk: &Chunk, data: &'a [u8]) -> FSResult<&'a [u8]> {
        let begin = (chunk.start - chunk.raw_offset) as usize;
        let end = (chunk.stop.get() - chunk.raw_offset) as usize;
        let len = data.len();
        if begin < end && end <= len {
            Ok(&data[begin..end])
        } else {
            Err(FSError::InvalidIndexes { begin, end, len })
        }
    }

    async fn write_chunk(&self, chunk: &Chunk, content: &[u8], offset: i64) -> FSResult<u64> {
        let data = Self::padded_data(
            content,
            offset,
            offset + chunk.stop.get() as i64 - chunk.start as i64,
        );
        self.local_storage.set_chunk(chunk.id, &data)?;
        Ok(data.len() as u64)
    }

    async fn build_data(&self, chunks: &[Chunk]) -> FSResult<(Vec<u8>, Vec<BlockAccess>)> {
        if chunks.is_empty() {
            return Ok((vec![], vec![]));
        }

        let mut missing = vec![];
        let (start, stop) = (chunks[0].start, chunks[chunks.len() - 1].stop);
        let mut result = vec![0; (stop.get() - start) as usize];

        for chunk in chunks {
            let data = self.local_storage.get_chunk(chunk.id)?;
            match Self::read_chunk(chunk, &data) {
                Ok(data) => (&mut result
                    [(chunk.start - start) as usize..(chunk.stop.get() - start) as usize])
                    .copy_from_slice(data),
                _ => {
                    if let Some(access) = &chunk.access {
                        missing.push(access.clone())
                    }
                }
            }
        }

        Ok((result, missing))
    }

    async fn get_confinement_point(&self, entry_id: EntryID) -> Option<EntryID> {
        // Load the corresponding manifest
        let mut current_manifest = match self.local_storage.get_manifest(entry_id) {
            Ok(manifest) => manifest,
            // A missing entry is never confined
            _ => return None,
        };

        // Walk the parent chain until the workspace manifest is reached
        while let LocalManifest::File(LocalFileManifest {
            base: FileManifest { parent, .. },
            ..
        })
        | LocalManifest::Folder(LocalFolderManifest {
            base: FolderManifest { parent, .. },
            ..
        }) = current_manifest
        {
            current_manifest = match self.local_storage.get_manifest(parent) {
                Ok(manifest) => {
                    // A parent manifest is necessarely a local folder/workspace manifest
                    match &manifest {
                        LocalManifest::Folder(LocalFolderManifest {
                            local_confinement_points,
                            ..
                        })
                        | LocalManifest::Workspace(LocalWorkspaceManifest {
                            local_confinement_points,
                            ..
                        }) => {
                            // The entry is not confined
                            if local_confinement_points.contains(&current_manifest.id()) {
                                return Some(manifest.id());
                            }
                        }
                        _ => unreachable!(),
                    }

                    // Walk down
                    manifest
                }
                // In the very unlikely case where the parent manifest is not present,
                // simply consider the entry to be not confined as having false negative
                // on confinement detection is not a big deal
                _ => return None,
            };
        }

        None
    }

    // Atomic transactions

    pub async fn fd_size(&self, fd: FileDescriptor) -> FSResult<u64> {
        Ok(self.local_storage.load_file_descriptor(fd)?.size)
    }

    pub async fn fd_close(&self, fd: FileDescriptor) -> FSResult<()> {
        let manifest = self.local_storage.load_file_descriptor(fd)?;

        let entry_id = manifest.base.id;
        let mutex = self.local_storage.lock_entry_id(entry_id).await;
        let guard = mutex.lock().await;

        // Force writing to disk
        self.local_storage
            .ensure_manifest_persistent(entry_id, true)
            .await?;
        // Atomic change
        self.local_storage.remove_file_descriptor(fd);

        // Clear write count
        self.write_count.lock().await.remove(&fd);

        self.local_storage.release_entry_id(entry_id, guard).await;

        Ok(())
    }

    pub async fn fd_write(
        &self,
        fd: FileDescriptor,
        mut content: &[u8],
        offset: i64,
        constrained: bool,
    ) -> FSResult<usize> {
        let mut manifest = self.local_storage.load_file_descriptor(fd)?;

        let entry_id = manifest.base.id;
        let mutex = self.local_storage.lock_entry_id(entry_id).await;
        let guard = mutex.lock().await;

        // Constrained - truncate content to the right length
        if constrained {
            let end_offset = min(manifest.size as i64, offset + content.len() as i64);
            let len = max(end_offset - offset, 0);
            content = &content[..len as usize];
        }

        // No-op
        if content.is_empty() {
            return Ok(0);
        }

        // Prepare
        let updated = self.device.timestamp();
        let offset = Self::normalize_argument(offset, &manifest);
        let (write_operations, removed_ids) =
            prepare_write(&mut manifest, content.len() as u64, offset, updated);

        // Writing
        let mut write_count = self.write_count.lock().await;
        let write_count_fd = write_count.entry(fd).or_default();
        for (chunk, offset) in write_operations {
            *write_count_fd += self.write_chunk(&chunk, content, offset).await?;
        }

        // Atomic change
        let removed_ids = removed_ids
            .into_iter()
            .map(ChunkOrBlockID::ChunkID)
            .collect();
        self.local_storage
            .set_manifest(
                manifest.base.id,
                LocalManifest::File(manifest.clone()),
                true,
                true,
                Some(removed_ids),
            )
            .await?;

        // Reshaping
        if *write_count_fd >= u64::from(manifest.blocksize) {
            self.manifest_reshape(&manifest, true).await?;
            write_count.remove(&fd);
        }

        self.local_storage.release_entry_id(entry_id, guard).await;

        Ok(0)
    }

    pub async fn fd_resize(
        &self,
        fd: FileDescriptor,
        length: u64,
        truncate_only: bool,
    ) -> FSResult<()> {
        let manifest = self.local_storage.load_file_descriptor(fd)?;

        if truncate_only && manifest.size <= length {
            return Ok(());
        }

        let entry_id = manifest.base.id;
        let mutex = self.local_storage.lock_entry_id(entry_id).await;
        let guard = mutex.lock().await;

        self.manifest_resize(manifest, length, true).await?;

        self.local_storage.release_entry_id(entry_id, guard).await;
        Ok(())
    }

    pub async fn fd_read(
        &self,
        fd: FileDescriptor,
        size: i64,
        offset: i64,
        raise_eof: bool,
    ) -> FSResult<Vec<u8>> {
        // Loop over attempts
        loop {
            // Load missing blocks
            // TODO
            // self.remote_loader.load_blocks(missing);

            // Fetch and lock
            let manifest = self.local_storage.load_file_descriptor(fd)?;

            let entry_id = manifest.base.id;
            let mutex = self.local_storage.lock_entry_id(entry_id).await;
            let guard = mutex.lock().await;

            // End of fle
            if raise_eof && offset >= manifest.size as i64 {
                return Err(FSError::EndOfFile);
            }

            // Normalize
            let offset = Self::normalize_argument(offset, &manifest);
            let size = Self::normalize_argument(size, &manifest);

            // No-op
            if offset > manifest.size {
                return Ok(vec![]);
            }

            // Prepare
            let chunks = prepare_read(&manifest, size, offset);
            let (data, missing) = self.build_data(&chunks).await?;

            // Return the data
            if missing.is_empty() {
                return Ok(data);
            }

            self.local_storage.release_entry_id(entry_id, guard).await;
        }
    }

    pub async fn fd_flush(&self, fd: FileDescriptor) -> FSResult<()> {
        let manifest = self.local_storage.load_file_descriptor(fd)?;

        let entry_id = manifest.base.id;
        let mutex = self.local_storage.lock_entry_id(entry_id).await;
        let guard = mutex.lock().await;

        self.manifest_reshape(&manifest, false).await?;
        self.local_storage
            .ensure_manifest_persistent(entry_id, true)
            .await?;

        self.local_storage.release_entry_id(entry_id, guard).await;

        Ok(())
    }

    /// This internal helper does not perform any locking
    async fn manifest_resize(
        &self,
        mut manifest: LocalFileManifest,
        length: u64,
        cache_only: bool,
    ) -> FSResult<()> {
        // No-op
        if manifest.size == length {
            return Ok(());
        }

        // Prepare
        let updated = self.device.timestamp();
        let (write_operations, removed_ids) = prepare_resize(&mut manifest, length, updated);

        // Writting
        for (chunk, offset) in write_operations {
            self.write_chunk(&chunk, &[], offset).await?;
        }

        // Atomic change
        let removed_ids = removed_ids
            .into_iter()
            .map(ChunkOrBlockID::ChunkID)
            .collect();

        self.local_storage
            .set_manifest(
                manifest.base.id,
                LocalManifest::File(manifest),
                cache_only,
                true,
                Some(removed_ids),
            )
            .await?;

        Ok(())
    }

    /// This internal helper does not perform any locking
    async fn manifest_reshape(
        &self,
        manifest: &LocalFileManifest,
        cache_only: bool,
    ) -> FSResult<Vec<BlockAccess>> {
        // Prepare data structures
        let mut missing = vec![];

        for (block, source, destination, write_back, removed_ids) in prepare_reshape(manifest) {
            // Build data block
            let (data, mut extra_missing) = self.build_data(&source).await?;

            // Missing data
            if !extra_missing.is_empty() {
                missing.append(&mut extra_missing);
                continue;
            }

            // Write data if necessary
            let new_chunk = destination
                .evolve_as_block(&data)
                .expect("data should be valid");
            if write_back {
                self.write_chunk(&new_chunk, &data, 0).await?;
            }

            // Craft the new manifest
            let mut manifest = manifest.clone();
            manifest
                .set_single_block(block, new_chunk)
                .expect("block index should be set");

            // Set the new manifest, acting as a checkpoint
            let removed_ids = removed_ids
                .into_iter()
                .map(ChunkOrBlockID::ChunkID)
                .collect();
            self.local_storage
                .set_manifest(
                    manifest.base.id,
                    LocalManifest::File(manifest),
                    true,
                    true,
                    Some(removed_ids),
                )
                .await?;
        }

        // Flush if necessary
        if !cache_only {
            self.local_storage
                .ensure_manifest_persistent(manifest.base.id, true)
                .await?;
        }

        // Return missing block ids
        Ok(missing)
    }
}

#[cfg(test)]
mod tests {
    use std::num::NonZeroU64;

    use libparsec_types::{DateTime, DEFAULT_BLOCK_SIZE};
    use rstest::rstest;

    use super::*;
    use crate::conftest::alice_file_transactions;

    impl FileTransactions {
        fn get_manifest(&self, file: &File) -> LocalFileManifest {
            if let LocalManifest::File(file) =
                self.local_storage.get_manifest(file.entry_id).unwrap()
            {
                file
            } else {
                panic!()
            }
        }

        async fn set_manifest(&self, file: &File, manifest: LocalManifest) {
            let mutex = self.local_storage.lock_entry_id(file.entry_id).await;
            let guard = mutex.lock().await;
            self.local_storage
                .set_manifest(file.entry_id, manifest, false, true, None)
                .await
                .unwrap();
            self.local_storage
                .release_entry_id(file.entry_id, guard)
                .await;
        }

        fn open(&self, file: &File) -> FileDescriptor {
            self.local_storage
                .create_file_descriptor(file.fresh_manifest.clone())
        }
    }

    struct File {
        fresh_manifest: LocalFileManifest,
        entry_id: EntryID,
    }

    async fn foo_txt_factory(aft: &FileTransactions) -> File {
        let device_id = &aft.local_storage.device.device_id;
        let now = DateTime::from_ymd(2000, 1, 2);
        let placeholder = LocalFileManifest::new(
            device_id.clone(),
            EntryID::default(),
            now,
            DEFAULT_BLOCK_SIZE,
        );
        let remote_v1 = placeholder.to_remote(device_id.clone(), now).unwrap();
        let manifest = LocalFileManifest::from_remote(remote_v1).unwrap();
        let file = File {
            fresh_manifest: manifest.clone(),
            entry_id: manifest.base.id,
        };

        aft.set_manifest(&file, LocalManifest::File(manifest)).await;

        file
    }

    #[rstest]
    async fn test_close_unknown_fd(#[future] alice_file_transactions: FileTransactions) {
        let fd = FileDescriptor(42);
        assert_eq!(
            alice_file_transactions
                .await
                .fd_close(fd)
                .await
                .unwrap_err(),
            FSError::InvalidFileDescriptor(fd)
        );
    }

    #[rstest]
    async fn test_operations_on_file(#[future] alice_file_transactions: FileTransactions) {
        let aft = alice_file_transactions.await;
        let foo_txt = foo_txt_factory(&aft).await;
        let fd = aft.open(&foo_txt);

        DateTime::freeze_time(Some(DateTime::from_ymd(2000, 1, 3)));
        {
            aft.fd_write(fd, b"hello ", 0, false).await.unwrap();
            aft.fd_write(fd, b"world !", -1, false).await.unwrap();
            aft.fd_write(fd, b"H", 0, false).await.unwrap();
            aft.fd_write(fd, b"", 0, false).await.unwrap();

            let fd2 = aft.open(&foo_txt);

            aft.fd_write(fd2, b"!!!", -1, false).await.unwrap();
            let data = aft.fd_read(fd2, 1, 0, false).await.unwrap();
            assert_eq!(data, b"H");

            aft.fd_close(fd2).await.unwrap();
        }
        DateTime::freeze_time(None);

        let data = aft.fd_read(fd, 5, 6, false).await.unwrap();
        assert_eq!(data, b"world");

        aft.fd_close(fd).await.unwrap();

        let fd2 = aft.open(&foo_txt);

        let data = aft.fd_read(fd2, -1, 0, false).await.unwrap();
        assert_eq!(data, b"Hello world !!!!");

        aft.fd_close(fd2).await.unwrap();
    }

    #[rstest]
    async fn test_flush_file(#[future] alice_file_transactions: FileTransactions) {
        let aft = alice_file_transactions.await;
        let foo_txt = foo_txt_factory(&aft).await;

        let fd = aft.open(&foo_txt);

        DateTime::freeze_time(Some(DateTime::from_ymd(2000, 1, 3)));
        {
            aft.fd_write(fd, b"hello ", 0, false).await.unwrap();
            aft.fd_write(fd, b"world !", -1, false).await.unwrap();
        }
        DateTime::freeze_time(None);

        aft.fd_flush(fd).await.unwrap();

        aft.fd_close(fd).await.unwrap();
    }

    #[rstest]
    async fn test_block_not_loaded_entry(#[future] alice_file_transactions: FileTransactions) {
        let aft = alice_file_transactions.await;
        let foo_txt = foo_txt_factory(&aft).await;

        let mut foo_manifest = aft.get_manifest(&foo_txt);
        let chunk1_data = [b'a'; 10];
        let chunk2_data = [b'b'; 5];
        let chunk1 = Chunk::new(0, NonZeroU64::try_from(10).unwrap())
            .evolve_as_block(&chunk1_data)
            .unwrap();
        let chunk2 = Chunk::new(10, NonZeroU64::try_from(15).unwrap())
            .evolve_as_block(&chunk2_data)
            .unwrap();
        let chunk1_id = chunk1.id;
        let chunk2_id = chunk2.id;
        foo_manifest.blocks = vec![vec![chunk1, chunk2]];
        foo_manifest.size = 15;

        aft.set_manifest(&foo_txt, LocalManifest::File(foo_manifest))
            .await;

        let fd = aft.open(&foo_txt);

        // TODO: Handle FSRemoveBlockNotFound error

        aft.local_storage
            .set_chunk(chunk1_id, &chunk1_data)
            .unwrap();
        aft.local_storage
            .set_chunk(chunk2_id, &chunk2_data)
            .unwrap();

        let data = aft.fd_read(fd, 14, 0, false).await.unwrap();
        assert_eq!(data, [&chunk1_data[..], &chunk2_data[..4]].concat())
    }

    #[ignore]
    #[rstest]
    async fn test_load_block_from_remote(#[future] alice_file_transactions: FileTransactions) {
        let aft = alice_file_transactions.await;
        let foo_txt = foo_txt_factory(&aft).await;

        // Prepare the backend
        // TODO

        let mut foo_manifest = aft.get_manifest(&foo_txt);
        let chunk1_data = [b'a'; 10];
        let chunk2_data = [b'b'; 5];
        let chunk1 = Chunk::new(0, NonZeroU64::try_from(10).unwrap())
            .evolve_as_block(&chunk1_data)
            .unwrap();
        let chunk2 = Chunk::new(10, NonZeroU64::try_from(15).unwrap())
            .evolve_as_block(&chunk2_data)
            .unwrap();
        foo_manifest.blocks = vec![vec![chunk1.clone(), chunk2.clone()]];
        foo_manifest.size = 15;

        aft.set_manifest(&foo_txt, LocalManifest::File(foo_manifest))
            .await;

        let fd = aft.open(&foo_txt);
        let chunk1_id = chunk1.access.unwrap().id;
        let chunk2_id = chunk2.access.unwrap().id;
        // TODO: remote
        aft.local_storage.clear_clean_block(chunk1_id);
        aft.local_storage.clear_clean_block(chunk2_id);

        let data = aft.fd_read(fd, 14, 0, false).await.unwrap();
        assert_eq!(data, [&chunk1_data[..], &chunk2_data[..4]].concat())
    }
}
