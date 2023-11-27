// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

use std::path::PathBuf;

pub use libparsec_client_connection::ProxyConfig;

pub const DEFAULT_WORKSPACE_STORAGE_CACHE_SIZE: u64 = 512 * 1024 * 1024;

#[derive(Debug, Clone, Copy)]
pub enum WorkspaceStorageCacheSize {
    Default,
    // TODO: support arbitrary int size in bindings
    Custom { size: u32 },
}

impl WorkspaceStorageCacheSize {
    pub fn cache_size(&self) -> u64 {
        match &self {
            Self::Default => DEFAULT_WORKSPACE_STORAGE_CACHE_SIZE,
            Self::Custom { size } => *size as u64,
        }
    }
}

#[derive(Debug, Clone)]
pub struct ClientConfig {
    // On web, `config_dir`&`data_base_dir` are converted into String and
    // used as database name when using IndexedDB API
    pub config_dir: PathBuf,
    pub data_base_dir: PathBuf,
    #[cfg(not(target_arch = "wasm32"))]
    pub mountpoint_base_dir: PathBuf, // Ignored on web
    pub workspace_storage_cache_size: WorkspaceStorageCacheSize,
    // pub prevent_sync_pattern: Option<PathBuf>,
    pub proxy: ProxyConfig,
}