// Parsec Cloud (https://parsec.cloud) Copyright (c) BSLv1.1 (eventually AGPLv3) 2016-2021 Scille SAS

use std::collections::HashSet;

use pyo3::prelude::*;
use pyo3::types::{PyList, PySet, PyTuple};

use libparsec_core_fs::file_operations;

use crate::binding_utils::py_to_rs_datetime;
use crate::ids::ChunkID;
use crate::local_manifest::{Chunk, LocalFileManifest};

// Conversion helpers

fn to_py_chunks(py: Python, chunks: Vec<parsec_client_types::Chunk>) -> &PyTuple {
    PyTuple::new(py, chunks.into_iter().map(|x| Chunk(x).into_py(py)))
}

fn to_py_removed_ids(
    py: Python,
    to_remove: HashSet<libparsec::api_types::ChunkID>,
) -> PyResult<&PySet> {
    PySet::new(
        py,
        &to_remove
            .iter()
            .map(|x| ChunkID(*x).into_py(py))
            .collect::<Vec<_>>(),
    )
}

fn to_py_write_operations(
    py: Python,
    write_operations: Vec<(parsec_client_types::Chunk, i64)>,
) -> &PyList {
    PyList::new(
        py,
        write_operations
            .into_iter()
            .map(|(x, y)| (Chunk(x).into_py(py), y)),
    )
}

// Exposed functions

#[pyfunction]
pub(crate) fn prepare_read(
    py: Python,
    manifest: LocalFileManifest,
    size: u64,
    offset: u64,
) -> PyResult<&PyTuple> {
    let result = file_operations::prepare_read(&manifest.0, size, offset);
    Ok(to_py_chunks(py, result))
}

#[pyfunction]
pub(crate) fn prepare_write<'a>(
    py: Python<'a>,
    mut manifest: LocalFileManifest,
    size: u64,
    offset: u64,
    timestamp: &PyAny,
) -> PyResult<&'a PyTuple> {
    let (write_operations, to_remove) = file_operations::prepare_write(
        &mut manifest.0,
        size,
        offset,
        py_to_rs_datetime(timestamp)?,
    );
    Ok(PyTuple::new(
        py,
        vec![
            LocalFileManifest(manifest.0).into_py(py),
            to_py_write_operations(py, write_operations).into_py(py),
            to_py_removed_ids(py, to_remove)?.into_py(py),
        ],
    ))
}

#[pyfunction]
pub(crate) fn prepare_resize<'a>(
    py: Python<'a>,
    mut manifest: LocalFileManifest,
    size: u64,
    timestamp: &PyAny,
) -> PyResult<&'a PyTuple> {
    let (write_operations, to_remove) =
        file_operations::prepare_resize(&mut manifest.0, size, py_to_rs_datetime(timestamp)?);
    Ok(PyTuple::new(
        py,
        vec![
            LocalFileManifest(manifest.0).into_py(py),
            to_py_write_operations(py, write_operations).into_py(py),
            to_py_removed_ids(py, to_remove)?.into_py(py),
        ],
    ))
}

#[pyfunction]
pub(crate) fn prepare_reshape(py: Python, manifest: LocalFileManifest) -> PyResult<&PyList> {
    let iterator = file_operations::prepare_reshape(&manifest.0);
    let collected: Vec<_> = iterator
        .map(|(block, old_chunks, new_chunk, write_back, to_remove)| {
            Ok(PyTuple::new(
                py,
                vec![
                    block.into_py(py),
                    to_py_chunks(py, old_chunks).into_py(py),
                    Chunk(new_chunk).into_py(py),
                    write_back.into_py(py),
                    to_py_removed_ids(py, to_remove)?.into_py(py),
                ],
            ))
        })
        .collect::<PyResult<_>>()?;
    Ok(PyList::new(py, collected))
}
