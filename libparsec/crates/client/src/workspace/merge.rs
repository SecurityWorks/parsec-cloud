// Parsec Cloud (https://parsec.cloud) Copyright (c) BUSL-1.1 2016-present Scille SAS

use std::{
    collections::{HashMap, HashSet},
    sync::Arc,
};

use libparsec_types::prelude::*;

const FILENAME_CONFLICT_SUFFIX: &str = "Parsec - name conflict";
const _FILE_CONTENT_CONFLICT_SUFFIX: &str = "Parsec - content conflict";

#[derive(Debug, PartialEq, Eq)]
pub(super) enum MergeLocalFileManifestOutcome {
    NoChange,
    Merged(LocalFileManifest),
    Conflict(FileManifest),
}

#[derive(Debug, PartialEq, Eq)]
pub(super) enum MergeLocalFolderManifestOutcome {
    NoChange,
    Merged(Arc<LocalFolderManifest>),
}

pub(super) fn merge_local_file_manifest(
    local_author: DeviceID,
    timestamp: DateTime,
    local_manifest: &LocalFileManifest,
    remote_manifest: FileManifest,
) -> MergeLocalFileManifestOutcome {
    // 0) Sanity checks, caller is responsible to handle them properly !
    debug_assert_eq!(local_manifest.base.id, remote_manifest.id);

    // 1) Shortcut in case the remote is outdated
    if remote_manifest.version <= local_manifest.base.version {
        return MergeLocalFileManifestOutcome::NoChange;
    }

    // 2) Shortcut in case only the remote has changed
    if !local_manifest.need_sync {
        return MergeLocalFileManifestOutcome::Merged(LocalFileManifest::from_remote(
            remote_manifest,
        ));
    }

    // Both the remote and the local have changed

    // 3) The remote changes are ours (our current local changes occurs while
    // we were uploading previous local changes that became the remote changes),
    // simply acknowledge the remote changes and keep our local changes
    if remote_manifest.author == local_author {
        let mut new_local = local_manifest.to_owned();
        new_local.base = remote_manifest;
        return MergeLocalFileManifestOutcome::Merged(new_local);
    }

    // 4) Merge data and ensure the sync is still needed

    // Destruct local and remote manifests to ensure this code with fail to compile
    // whenever a new field is introduced.
    let LocalFileManifest {
        // `need_sync` has already been checked
        need_sync: _,
        // Ignore `updated`: we don't merge data that change on each sync
        updated: _,
        base: local_base,
        parent: local_parent,
        size: local_size,
        blocksize: local_blocksize,
        blocks: local_blocks,
    } = local_manifest;
    let FileManifest {
        // `id` has already been checked
        id: _,
        // Ignore `author`&`timestamp`: we don't merge data that change on each sync
        author: _,
        // Ignore `author`: we don't merge data that change on each sync
        timestamp: _,
        // Ignore `version`: we don't merge data that change on each sync
        version: _,
        // Ignore `updated`: we don't merge data that change on each sync
        updated: _,
        // `created` should never change, so in theory we should have
        // `local.base.created == remote.base.created`, but there is no strict
        // guarantee (e.g. remote manifest may have been uploaded by a buggy client)
        // so we have no choice but to accept whatever value remote provides.
        created: _,
        parent: remote_parent,
        size: remote_size,
        blocksize: remote_blocksize,
        blocks: remote_blocks,
    } = &remote_manifest;

    // Compare data that cause a hard merge conflict

    if *remote_size != *local_size || *remote_blocksize != *local_blocksize {
        return MergeLocalFileManifestOutcome::Conflict(remote_manifest);
    }

    let mut remote_blocks_iter = remote_blocks.iter();
    for local_block_access in local_blocks
        .iter()
        // In local manifest each blocksize area is represented by a list of chunks,
        // on the other hand the remote manifest only store the non-empty list of chunks
        .filter(|chunks| !chunks.is_empty())
        // Remote manifest is only composed of reshaped blocks
        .map(|chunks| chunks[0].get_block_access())
    {
        let remote_block_access = remote_blocks_iter.next();
        match (local_block_access, remote_block_access) {
            (_, None) | (Err(_), _) => {
                return MergeLocalFileManifestOutcome::Conflict(remote_manifest);
            }
            (Ok(local_block_access), Some(remote_block_access)) => {
                if local_block_access != remote_block_access {
                    return MergeLocalFileManifestOutcome::Conflict(remote_manifest);
                }
            }
        }
    }
    if remote_blocks_iter.next().is_some() {
        return MergeLocalFileManifestOutcome::Conflict(remote_manifest);
    }

    // The data can be merged ! But will the sync still be needed once merged ?
    //
    // Like they say in Megaforce "Deeds not words !", so we manually compare
    // the remaining fields to determine if a sync is still needed.
    //
    // /!\ Extra attention should be paid here if we want to add new fields
    // /!\ with their own sync logic, as this optimization may shadow them!

    let new_parent = merge_parent(local_base.parent, *local_parent, *remote_parent);

    if new_parent == *remote_parent {
        MergeLocalFileManifestOutcome::Merged(LocalFileManifest::from_remote(remote_manifest))
    } else {
        let mut local_from_remote = LocalFileManifest::from_remote(remote_manifest);
        local_from_remote.parent = new_parent;
        local_from_remote.updated = timestamp;
        local_from_remote.need_sync = true;
        MergeLocalFileManifestOutcome::Merged(local_from_remote)
    }
}

pub(super) fn merge_local_folder_manifest(
    local_author: DeviceID,
    timestamp: DateTime,
    prevent_sync_pattern: Option<&Regex>,
    local: &LocalFolderManifest,
    remote: FolderManifest,
) -> MergeLocalFolderManifestOutcome {
    // Destruct local and remote manifests to ensure this code with fail to compile whenever a new field is introduced.
    let LocalFolderManifest {
        base:
            FolderManifest {
                id: local_base_id,
                version: local_base_version,
                children: local_base_children,
                parent: local_base_parent,
                // Ignored, we don't merge data that change on each sync
                author: _,
                // `created` should never change, so in theory we should have
                // `local.base.created == remote.base.created`, but there is no strict
                // guarantee (e.g. remote manifest may have been uploaded by a buggy client)
                // so we have no choice but to accept whatever value remote provides.
                created: _,
                // Ignored, we don't merge data that change on each sync
                timestamp: _,
                // Ignored, we don't merge data that change on each sync
                updated: _,
            },
        children: local_children,
        parent: local_parent,
        need_sync: local_need_sync,
        speculative: local_speculative,
        // Ignored, that field is merged in `from_remote_with_local_context`
        remote_confinement_points: _,
        // Ignored, that field is merged in `from_remote_with_local_context`
        local_confinement_points: _,
        // Ignored, we don't merge data that change on each sync
        updated: _,
    } = local;

    // 0) Sanity checks, caller is responsible to handle them properly !
    debug_assert_eq!(local_base_id, &remote.id);

    // TODO: Allow to force re-applying the prevent sync pattern (idempotent)
    // if force_apply_pattern {
    //     local_manifest = local_manifest.apply_prevent_sync_pattern(prevent_sync_pattern, timestamp)
    // }

    // 1) Shortcut in case the remote is outdated
    if remote.version <= *local_base_version {
        return MergeLocalFolderManifestOutcome::NoChange;
    }

    let local_from_remote = LocalFolderManifest::from_remote_with_local_context(
        remote,
        prevent_sync_pattern,
        local,
        timestamp,
    );

    // 2) Shortcut in case only the remote has changed
    if !local_need_sync {
        return MergeLocalFolderManifestOutcome::Merged(Arc::new(local_from_remote));
    }

    // Both the remote and the local have changed

    // 3) The remote changes are ours (our current local changes occurs while
    // we were uploading previous local changes that became the remote changes),
    // simply acknowledge the remote changes and keep our local changes
    //
    // However speculative manifest can lead to a funny behavior:
    // 1) alice has access to the workspace
    // 2) alice upload a new remote workspace manifest
    // 3) alice gets it local storage removed
    // So next time alice tries to access this workspace she will
    // creates a speculative workspace manifest.
    // This speculative manifest will eventually be synced against
    // the previous remote manifest which appears to be remote
    // changes we know about (given we are the author of it !).
    // If the speculative flag is not taken into account, we would
    // consider we have willingly removed all entries from the remote,
    // hence uploading a new expunged remote manifest.
    //
    // Of course removing local storage is an unlikely situation, but:
    // - it cannot be ruled out and would produce rare&exotic behavior
    //   that would be considered as bug :/
    // - the fixtures and server data binder system used in the tests
    //   makes it much more likely
    if local_from_remote.base.author == local_author && !local_speculative {
        let mut new_local = local.to_owned();
        new_local.base = local_from_remote.base;
        return MergeLocalFolderManifestOutcome::Merged(Arc::new(new_local));
    }

    // 4) Merge data and ensure the sync is still needed

    // Solve the folder conflict
    let merged_children = merge_children(
        local_base_children,
        local_children,
        &local_from_remote.children,
    );
    let merged_parent = merge_parent(*local_base_parent, *local_parent, local_from_remote.parent);

    // Children merge can end up with nothing to sync.
    //
    // This is typically the case when we sync for the first time a workspace
    // shared with us that we didn't modify:
    // - the workspace manifest is a speculative placeholder (with arbitrary update&create dates)
    // - on sync the update date is different than in the remote, so a merge occurs
    // - given we didn't modify the workspace, the children merge is trivial
    // So without this check each each user we share the workspace with would
    // sync a new workspace manifest version with only it updated date changing :/
    //
    // Another case where this happen:
    // - we have local change on our workspace manifest for removing an entry
    // - we rely on a base workspace manifest in version N
    // - remote workspace manifest is in version N+1 and already integrate the removal
    //
    // /!\ Extra attention should be paid here if we want to add new fields
    // /!\ with their own sync logic, as this optimization may shadow them!

    let merge_need_sync =
        merged_children != local_from_remote.children || merged_parent != local_from_remote.parent;
    let merge_update = if merge_need_sync {
        timestamp
    } else {
        local_from_remote.base.updated
    };

    let manifest = LocalFolderManifest {
        children: merged_children,
        parent: merged_parent,
        need_sync: merge_need_sync,
        updated: merge_update,
        speculative: false,
        base: local_from_remote.base,
        local_confinement_points: local_from_remote.local_confinement_points,
        remote_confinement_points: local_from_remote.remote_confinement_points,
    };

    MergeLocalFolderManifestOutcome::Merged(Arc::new(manifest))
}

fn merge_parent(base: VlobID, local: VlobID, remote: VlobID) -> VlobID {
    let remote_change = remote != base;
    let local_change = local != base;
    match (local_change, remote_change) {
        // No change
        (false, false) => base,
        // Local change
        (true, false) => local,
        // Remote change
        (false, true) => remote,
        // Both remote and local change, conflict !
        //
        // In this case, we simply decide that the remote is right since it means
        // another user managed to upload their change first. Tough luck for the
        // local device!
        //
        // Note the changing the parent is most likely part of a reparenting operation,
        // hence dropping the local change means the destination parent folder will
        // contain an invalid entry (i.e. an entry pointing to our manifest, which
        // itself points to another parent). This is considered okay given parent
        // merge conflict is considered as a rare event and the entry will simply
        // be ignored for all practical purpose.
        (true, true) => remote,
    }
}

fn merge_children(
    base: &HashMap<EntryName, VlobID>,
    local: &HashMap<EntryName, VlobID>,
    remote: &HashMap<EntryName, VlobID>,
) -> HashMap<EntryName, VlobID> {
    // Prepare lookups
    let base_reversed: HashMap<_, _> = base.iter().map(|(k, v)| (*v, k)).collect();
    let local_reversed: HashMap<_, _> = local.iter().map(|(k, v)| (*v, k)).collect();
    let remote_reversed: HashMap<_, _> = remote.iter().map(|(k, v)| (*v, k)).collect();

    // All ids that might remain
    let ids = {
        let mut ids: HashSet<VlobID> = HashSet::new();
        ids.extend(local_reversed.keys());
        ids.extend(remote_reversed.keys());
        ids
    };

    // First map all ids to their rightful name
    let mut solved_local_children: HashMap<EntryName, VlobID> = HashMap::new();
    let mut solved_remote_children: HashMap<EntryName, VlobID> = HashMap::new();
    for id in ids {
        let base_name = base_reversed.get(&id).cloned();
        let local_name = local_reversed.get(&id).cloned();
        let remote_name = remote_reversed.get(&id).cloned();
        match (base_name, local_name, remote_name) {
            // a) Local and remote agree on this entry

            // Removed locally and remotely
            (_, None, None) => {}
            // Preserved remotely and locally with the same naming
            (_, Some(local_name), Some(remote_name)) if local_name == remote_name => {
                solved_remote_children.insert(remote_name.to_owned(), id);
            }

            // b) Conflict between local and remote on this entry

            // Added locally
            (None, Some(local_name), None) => {
                solved_local_children.insert(local_name.to_owned(), id);
            }
            // Added remotely
            (None, None, Some(remote_name)) => {
                solved_remote_children.insert(remote_name.to_owned(), id);
            }

            // Removed locally but renamed remotely
            (Some(base_name), None, Some(remote_name)) if base_name != remote_name => {
                solved_remote_children.insert(remote_name.to_owned(), id);
            }
            // Removed remotely but renamed locally
            (Some(base_name), Some(local_name), None) if base_name != local_name => {
                solved_remote_children.insert(local_name.to_owned(), id);
            }
            // Removed locally
            (Some(_), None, _) => {
                // Note that locally removed children might not be synchronized at this point
            }
            // Removed remotely
            (Some(_), _, None) => {
                // Note that we're blindly removing children just because the remote said so
                // This is OK as long as users have a way to recover their local changes
            }

            // Renamed locally
            (Some(base_name), Some(local_name), Some(remote_name)) if base_name == remote_name => {
                solved_local_children.insert(local_name.to_owned(), id);
            }
            // Renamed remotely
            (Some(base_name), Some(local_name), Some(remote_name)) if base_name == local_name => {
                solved_remote_children.insert(remote_name.to_owned(), id);
            }
            // Renamed both locally and remotely
            (_, Some(_), Some(remote_name)) => {
                // In this case, we simply decide that the remote is right since it means
                // another user managed to upload their change first. Tough luck for the
                // local device!
                solved_remote_children.insert(remote_name.to_owned(), id);
            }
        }
    }

    // Merge mappings and fix conflicting names
    let mut children = solved_remote_children;
    for (entry_name, entry_id) in solved_local_children {
        let entry_name = if children.contains_key(&entry_name) {
            get_conflict_filename(&entry_name, FILENAME_CONFLICT_SUFFIX, |new_entry_name| {
                children.contains_key(new_entry_name)
            })
        } else {
            entry_name
        };
        children.insert(entry_name, entry_id);
    }

    children
}

fn get_conflict_filename(
    filename: &EntryName,
    suffix: &str,
    is_reserved: impl Fn(&EntryName) -> bool,
) -> EntryName {
    let mut count = 1;
    let mut new_filename = rename_with_suffix(filename, suffix);
    while is_reserved(&new_filename) {
        count += 1;
        let suffix_with_count = format!("{} ({})", suffix, count);
        new_filename = rename_with_suffix(filename, &suffix_with_count);
    }
    new_filename
}

fn rename_with_suffix(name: &EntryName, suffix: &str) -> EntryName {
    // Separate file name from the extensions (if any)
    let raw = name.as_ref();
    let (original_base_name, original_extension) = match raw.split_once('.') {
        None => (raw, None),
        Some((base, ext)) => (base, Some(ext)),
    };
    // Loop over attempts, in case the produced entry name is too long
    let mut base_name = original_base_name;
    let mut extension = original_extension;
    loop {
        // Convert to EntryName
        let raw = if let Some(extension) = extension {
            format!("{} ({}).{}", base_name, suffix, extension)
        } else {
            format!("{} ({})", base_name, suffix)
        };
        match raw.parse::<EntryName>() {
            Ok(name) => return name,
            Err(EntryNameError::NameTooLong) => {
                if base_name.len() > 10 {
                    // Simply strip 10 characters from the first name then try again
                    base_name = base_name
                        .get(..(base_name.len() - 10))
                        .expect("already checked");
                } else {
                    // Very rare case where the extension part is very long
                    // Pop the left most extension and restore the original base name
                    base_name = original_base_name;
                    extension = match extension.expect("must contain extension").split_once('.') {
                        Some((_, kept)) => Some(kept),
                        None => {
                            // Really ??? What is your use case to have an extension part
                            // composed of a single extension longer than 200bytes o_O'
                            None
                        }
                    };
                }
            }
            Err(_) => unreachable!(),
        }
    }
}
