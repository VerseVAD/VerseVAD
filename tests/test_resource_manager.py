from __future__ import annotations

import hashlib

from versevad.core.resources import (
    LocalResourceManager,
    ResourceProvenance,
    ResourceSpec,
    ResourceState,
)


def test_available_resource_records_checksum_without_changing_file(tmp_path) -> None:
    payload = b"term,score\nstone,4.8\n"
    resource_path = tmp_path / "concreteness" / "ratings.csv"
    resource_path.parent.mkdir()
    resource_path.write_bytes(payload)
    expected_hash = hashlib.sha256(payload).hexdigest()
    before = resource_path.read_bytes()
    manager = LocalResourceManager(tmp_path)

    status = manager.validate(
        ResourceSpec(
            resource_id="brysbaert-concreteness",
            display_name="Synthetic concreteness fixture",
            relative_path="concreteness/ratings.csv",
            version="fixture-1",
            accepted_sha256=(expected_hash,),
        )
    )

    assert status.state is ResourceState.AVAILABLE
    assert status.source_sha256 == expected_hash
    assert status.size_bytes == len(payload)
    assert resource_path.read_bytes() == before

    provenance = ResourceProvenance.from_available_status(
        status,
        citation="Synthetic fixture.",
        adapter_version="test-adapter-1",
    )
    assert provenance.version == "fixture-1"
    assert provenance.source_sha256 == expected_hash


def test_missing_resource_has_plain_language_status(tmp_path) -> None:
    manager = LocalResourceManager(tmp_path)

    status = manager.validate(
        ResourceSpec(
            resource_id="subtlex-us",
            display_name="SUBTLEX-US",
            relative_path="frequency/subtlex-us.xlsx",
        )
    )

    assert status.state is ResourceState.MISSING
    assert status.source_sha256 == ""
    assert "was not found" in status.message


def test_unrecognized_checksum_is_an_unsupported_version(tmp_path) -> None:
    resource_path = tmp_path / "frequency.csv"
    resource_path.write_text("word,zipf\nstone,4.0\n", encoding="utf-8")
    manager = LocalResourceManager(tmp_path)

    status = manager.validate(
        ResourceSpec(
            resource_id="subtlex-us",
            display_name="SUBTLEX-US",
            relative_path="frequency.csv",
            accepted_sha256=("0" * 64,),
        )
    )

    assert status.state is ResourceState.UNSUPPORTED_VERSION
    assert status.source_sha256
    assert "not a supported version" in status.message


def test_empty_resource_is_malformed(tmp_path) -> None:
    (tmp_path / "empty.csv").touch()
    manager = LocalResourceManager(tmp_path)

    status = manager.validate(
        ResourceSpec(
            resource_id="empty",
            display_name="Empty fixture",
            relative_path="empty.csv",
        )
    )

    assert status.state is ResourceState.MALFORMED
    assert "empty" in status.message


def test_resource_path_cannot_escape_configured_root(tmp_path) -> None:
    manager = LocalResourceManager(tmp_path / "resources")

    status = manager.validate(
        ResourceSpec(
            resource_id="escape",
            display_name="Escaping fixture",
            relative_path="../outside.csv",
        )
    )

    assert status.state is ResourceState.MALFORMED
    assert "outside the configured resource directory" in status.message


def test_validate_many_preserves_declared_order(tmp_path) -> None:
    manager = LocalResourceManager(tmp_path)
    specs = (
        ResourceSpec("first", "First", "first.csv"),
        ResourceSpec("second", "Second", "second.csv"),
    )

    statuses = manager.validate_many(specs)

    assert tuple(status.resource_id for status in statuses) == ("first", "second")


def test_missing_resource_cannot_be_recorded_as_completed_provenance(tmp_path) -> None:
    manager = LocalResourceManager(tmp_path)
    status = manager.validate(ResourceSpec("missing", "Missing", "missing.csv"))

    try:
        ResourceProvenance.from_available_status(status)
    except ValueError as error:
        assert "available resource" in str(error)
    else:
        raise AssertionError("Missing resources must not become result provenance.")
