"""CODE-0012 offline blueprint/ghost product-path staging planner.

This module deliberately does not import or call EML, touch the game process,
write a resource, or deploy a mod.  It converts the historical Architect Lua
implementation into a deterministic, reviewable canary plan.  The symbolic
GUIDs and candidate item IDs are never sent to an asset API.
"""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from tools.ArchitectVoxel.architect_voxel import compress_occupancy, iter_coordinates

ROOT = Path(__file__).resolve().parents[2]
SOURCE_LUA = ROOT / "src" / "mod.lua"
MANIFEST_NAME = "blueprint_ghost_identity_perturbation_manifest.json"
SAFE_DIMENSIONS = (4, 4, 4)
SAFE_PAYLOAD_BYTES = 8
PRIVATE_NAMESPACE = "architect-toolkit-code0012-canary-v1"
KNOWN_IDS = {81726253, 3828821633, 1458989991, 3094089500, 2719914608}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fnv1a32(text: str) -> int:
    value = 0x811C9DC5
    for byte in text.encode("utf-8"):
        value = ((value ^ byte) * 0x01000193) & 0xFFFFFFFF
    return value


def private_item_id(variant: str) -> int:
    """Mirror the proven source expression ``fnv1a32("architect_toolkit:" .. key)``.

    This is a candidate only: no ItemInfo is created offline.  A collision with
    a known or duplicate identity is a hard failure in the planner.
    """
    return fnv1a32(f"architect_toolkit:{variant.lower()}")


def private_identity(variant: str, resource: str) -> str:
    """Create a stable symbolic UUID for diagnostics only."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{PRIVATE_NAMESPACE}:{variant}:{resource}"))


def _pattern_a() -> frozenset[tuple[int, int, int]]:
    # Eight corners: unmistakable sparse shell/corner control.
    return frozenset((x, y, z) for x in (0, 3) for y in (0, 3) for z in (0, 3))


def _pattern_b() -> frozenset[tuple[int, int, int]]:
    # Eight central voxels: a visually distinct compact block.
    return frozenset((x, y, z) for x in (1, 2) for y in (1, 2) for z in (1, 2))


def _payload(dimensions: tuple[int, int, int], occupied: frozenset[tuple[int, int, int]]) -> bytes:
    return compress_occupancy(dimensions, occupied)


def _preview(dimensions: tuple[int, int, int], occupied: frozenset[tuple[int, int, int]]) -> bytes:
    return bytes(18 if point in occupied else 0 for point in iter_coordinates(dimensions))


def historical_source_evidence(source_path: Path = SOURCE_LUA) -> dict[str, Any]:
    """Check only exact Architect-owned source anchors; never fabricate APIs."""
    if not source_path.is_file():
        return {"status": "BLOCKED_MISSING_PROVEN_SOURCE", "sourcePath": str(source_path), "anchors": {}}
    text = source_path.read_text(encoding="utf-8")
    anchors = {
        "itemInfoCreate": 'game.assets.create_resource(\n            itemTemplate.data,\n            "keen::ItemInfo"',
        "voxelModelCreate": '"keen::VoxelModelResource"',
        "renderModelCreate": '"keen::RenderModel"',
        "blueprintRegistryAppend": "table.insert(\n        blueprintRegistry.blueprintItems",
        "itemRegistryLink": "itemRegistry.itemRefs",
        "safePayloadCap": "MAX_SAFE_EML_PLACEMENT_BYTES = 8",
    }
    found = {name: token in text for name, token in anchors.items()}
    line_numbers: dict[str, int | None] = {}
    lines = text.splitlines()
    for name, token in anchors.items():
        line_numbers[name] = next((i for i, line in enumerate(lines, 1) if token.splitlines()[0] in line), None)
    status = "PROVEN_SOURCE_ANCHORED" if all(found.values()) else "BLOCKED_MISSING_PROVEN_SOURCE"
    return {
        "status": status,
        "sourcePath": str(source_path),
        "anchors": found,
        "lineNumbers": line_numbers,
        "operations": {
            "createPrivateItemInfo": "PROVEN_SOURCE" if found["itemInfoCreate"] else "UNKNOWN",
            "createPrivateVoxelModel": "PROVEN_SOURCE" if found["voxelModelCreate"] else "UNKNOWN",
            "createPrivateRenderModelCompanion": "PROVEN_SOURCE" if found["renderModelCreate"] else "UNKNOWN",
            "appendBlueprintRegistryEntry": "PROVEN_SOURCE" if found["blueprintRegistryAppend"] else "UNKNOWN",
            "linkItemRegistryEntry": "PROVEN_SOURCE" if found["itemRegistryLink"] else "UNKNOWN",
            "payloadLimit": "PROVEN_SOURCE" if found["safePayloadCap"] else "UNKNOWN",
        },
        "execution": "NOT_EXECUTED_OFFLINE",
    }


@dataclass(frozen=True)
class Canary:
    name: str
    final_pattern: str
    ghost_pattern: str
    preview_only_sufficient: bool
    disposable_world_required: bool


CANARIES = (
    Canary("CONTROL", "A", "A", True, False),
    Canary("GHOST_VARIANT", "A", "B", True, False),
    Canary("FINAL_VARIANT", "B", "A", False, True),
    Canary("CROSS_WIRED", "A", "B", False, True),
)


def _variant_report(canary: Canary, source: Mapping[str, Any], patterns: Mapping[str, bytes], previews: Mapping[str, bytes]) -> dict[str, Any]:
    final_payload = patterns[canary.final_pattern]
    ghost_preview = previews[canary.ghost_pattern]
    item_id = private_item_id(f"code0012_{canary.name}")
    ids = {key: private_identity(canary.name, key) for key in ("itemInfo", "blueprint", "voxelModel", "renderModel")}
    source_refs = {
        "itemInfoTemplate": {"resourceType": "keen::ItemInfo", "itemId": 81726253, "evidence": "src/mod.lua SOURCE_CEILING_ID"},
        "blueprintTemplate": {"resourceType": "keen::VoxelBlueprintItem", "itemId": 3828821633, "dimensions": list(SAFE_DIMENSIONS), "evidence": "src/mod.lua SOURCE_4X4X4_ID"},
        "voxelModelTemplate": {"resourceType": "keen::VoxelModelResource", "itemId": 3828821633, "evidence": "src/mod.lua preview clone path"},
        "renderModelTemplate": {"resourceType": "keen::RenderModel", "relationship": "same-GUID companion", "evidence": "src/mod.lua private render clone path"},
    }
    valid = source["status"] == "PROVEN_SOURCE_ANCHORED" and len(final_payload) == SAFE_PAYLOAD_BYTES and len(ghost_preview) == 64
    return {
        "variant": canary.name,
        "createdPrivateItemId": None,
        "privateItemIdCandidate": item_id,
        "itemIdAvailable": False,
        "identityMaterialization": {
            "itemId": {"status": "PROVEN_SOURCE_METHOD", "expression": f"fnv1a32(architect_toolkit:code0012_{canary.name.lower()})"},
            "guid": {"status": "PROVEN_SOURCE_RUNTIME_GENERATED", "method": "game.assets.create_resource", "deterministicOffline": False},
        },
        "resourceIdentities": {"identityKind": "OFFLINE_PLAN_SYMBOLIC_NOT_ASSET_GUID", **ids},
        "sourceTemplateResources": source_refs,
        "placement": {
            "dimensions": list(SAFE_DIMENSIONS),
            "compressed": True,
            "compressedLength": len(final_payload),
            "payloadSha256": _sha256(final_payload),
            "payloadHex": final_payload.hex(),
            "pattern": f"{canary.final_pattern} (private final occupancy)",
        },
        "ghost": {
            "dimensions": list(SAFE_DIMENSIONS),
            "voxelValueVisible": 18,
            "emptyValue": 0,
            "previewLength": len(ghost_preview),
            "previewSha256": _sha256(ghost_preview),
            "previewValues": list(ghost_preview),
            "pattern": f"{canary.ghost_pattern} (private ghost occupancy)",
            "renderModelCompanion": True,
        },
        "intendedPreviewAppearance": "corner shell" if canary.ghost_pattern == "A" else "central block",
        "intendedFinalPlacementAppearance": "corner shell" if canary.final_pattern == "A" else "central block",
        "previewOnlyTestingSufficient": canary.preview_only_sufficient,
        "disposableWorldPlacementRequired": canary.disposable_world_required,
        "cleanupReloadNotes": "Discard staging identities; reload session. No shared vanilla resource is modified.",
        "resourceWrites": "NOT_EXECUTED_OFFLINE",
        "validationPassed": valid,
        "evidenceStatus": "STAGING_PLAN_READY" if valid else "BLOCKED_MISSING_PROVEN_SOURCE",
        "crossWiredPrivateOnly": canary.name == "CROSS_WIRED",
    }


def build_manifest(source_path: Path = SOURCE_LUA) -> dict[str, Any]:
    source = historical_source_evidence(source_path)
    pattern_a = _payload(SAFE_DIMENSIONS, _pattern_a())
    pattern_b = _payload(SAFE_DIMENSIONS, _pattern_b())
    previews = {"A": _preview(SAFE_DIMENSIONS, _pattern_a()), "B": _preview(SAFE_DIMENSIONS, _pattern_b())}
    patterns = {"A": pattern_a, "B": pattern_b}
    canaries = [_variant_report(canary, source, patterns, previews) for canary in CANARIES]
    duplicate_candidates = len({row["privateItemIdCandidate"] for row in canaries}) != len(canaries)
    return {
        "schemaVersion": 1,
        "codeId": "CODE-0012",
        "status": "PRODUCT_PATH_STAGING_READY" if source["status"] == "PROVEN_SOURCE_ANCHORED" else "BLOCKED_MISSING_PROVEN_SOURCE",
        "executionMode": "OFFLINE_STAGING_ONLY",
        "gameMutation": False,
        "deployedRuntimeChanged": False,
        "sourceEvidence": source,
        "adapter": {
            "name": "ArchitectVanillaBlueprintGhostAdapter",
            "status": "STAGING_PLAN_ONLY",
            "provenPath": [
                "private ItemInfo clone from an existing ItemInfo template",
                "private VoxelBlueprintItem entry with bounded compressed payload",
                "private VoxelModelResource clone for ghost values 18/0",
                "same-GUID private RenderModel companion",
                "ItemRegistry.itemRefs and blueprint registry linkage after validation",
            ],
            "notImplemented": ["offline GUID allocation", "automatic loader integration", "runtime cleanup/reload"],
            "idempotentSessionStartup": "NOT_APPLICABLE_OFFLINE_UNTIL_EML_RUNTIME_EXISTS",
            "identityMaterialization": "ITEM_ID_FNV1A32_PROVEN; GUID_CREATED_BY_EML_AT_RUNTIME; NOT_MATERIALIZED_OFFLINE",
            "runtimePackage": {"module": "runtime/staging/ArchitectProductPathPreview.lua", "defaultEnabled": False, "placementAutomation": False, "loaderIntegration": "EXPLICIT_ENTRY_POINT_NOT_LOADED"},
            "collisionPolicy": "fail closed on candidate ID collision or missing source anchor",
            "sharedVanillaMutation": False,
        },
        "safeCanaryPolicy": {"dimensions": list(SAFE_DIMENSIONS), "maxCompressedPayloadBytes": SAFE_PAYLOAD_BYTES, "dynamicArrayResize": False, "allocation": False},
        "patterns": {name: {"payloadHex": data.hex(), "payloadSha256": _sha256(data), "compressedLength": len(data)} for name, data in patterns.items()},
        "ghostPatterns": {name: {"previewSha256": _sha256(data), "previewLength": len(data), "previewValues": list(data), "visibleValue": 18, "emptyValue": 0} for name, data in previews.items()},
        "variants": canaries,
        "identityChecks": {"candidateIdsUnique": not duplicate_candidates, "candidateIdsAvoidKnownIds": all(row["privateItemIdCandidate"] not in KNOWN_IDS for row in canaries), "symbolicGuidsOnly": True},
        "manualTestStatus": "NOT_RUN_USER_PREVIEW_REQUIRED",
        "observerDecision": {"install": False, "deploy": False, "failClosed": True, "reason": "Offline staging manifest only; no runtime EML adapter is invoked."},
    }


def write_manifest(output: Path, source_path: Path = SOURCE_LUA) -> dict[str, Any]:
    report = build_manifest(source_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(output)
    return report


def write_preview_module(manifest: Mapping[str, Any], output: Path) -> None:
    """Emit a disabled-by-default Lua package from the authoritative manifest.

    The emitted module mirrors only calls already present in ``src/mod.lua``.
    It is not loaded by the current mod and exposes no placement operation.
    """
    def lua_string(value: str) -> str:
        return json.dumps(value, ensure_ascii=False)

    rows = []
    for row in manifest["variants"]:
        placement = row["placement"]
        ghost = row["ghost"]
        rows.append(
            "    {variant=%s, itemId=%d, finalPayloadHex=%s, ghostPattern=%s, "
            "ghostPreview={%s}, itemInfoGuid=%s, blueprintGuid=%s, voxelModelGuid=%s, renderModelGuid=%s}," % (
                lua_string(row["variant"]), row["privateItemIdCandidate"], lua_string(placement["payloadHex"]),
                lua_string(ghost["pattern"].split(" ")[0]), ",".join(str(v) for v in ghost["previewValues"]), lua_string(row["resourceIdentities"]["itemInfo"]),
                lua_string(row["resourceIdentities"]["blueprint"]), lua_string(row["resourceIdentities"]["voxelModel"]),
                lua_string(row["resourceIdentities"]["renderModel"])))
    text = """-- CODE-0013 preview-only product-path package (generated from the CODE-0012 manifest).
-- Disabled by default. This file is staged only; it is not loaded by src/mod.lua.
-- It performs no placement automation. Enabling it is an explicit user action.
local M = {}
M.config = { enabled = false, codeId = "CODE-0013", mode = "PREVIEW_ONLY", maxPayloadBytes = 8 }
M.canaries = {
%s
}

local SOURCE_ITEM_TEMPLATE_ID = 81726253
local SOURCE_4X4X4_ID = 3828821633

local function result(def, status, reason)
    return {variant = def.variant, itemId = def.itemId, status = status, failureReason = reason or "", writeAttempted = false}
end

local function findItem(items, id)
    for _, resource in ipairs(items or {}) do
        if resource.data and resource.data.itemId and resource.data.itemId.value == id then return resource end
    end
    return nil
end

local function findBlueprint(registry, id)
    for _, blueprint in ipairs((registry and registry.blueprintItems) or {}) do
        if blueprint.itemId and blueprint.itemId.value == id then return blueprint end
    end
    return nil
end

local function hexBytes(hex)
    local bytes = {}
    for pair in string.gmatch(hex, "%%x%%x") do table.insert(bytes, tonumber(pair, 16)) end
    return bytes
end

local function exactLinked(itemRegistry, item)
    for _, reference in ipairs((itemRegistry and itemRegistry.itemRefs) or {}) do
        local ok, linked = pcall(function() return game.assets.get_resource(reference, "keen::ItemInfo", 0) end)
        if ok and linked and tostring(linked.guid or "") == tostring(item.guid or "") then return true end
    end
    return false
end

local function registerOne(def)
    if not M.config.enabled then return result(def, "DISABLED_BY_DEFAULT", "previewPackageDisabled") end
    if #hexBytes(def.finalPayloadHex) ~= M.config.maxPayloadBytes then return result(def, "FAIL_CLOSED", "payloadExceedsSafeEnvelope") end
    local ok, items = pcall(function() return game.assets.get_resources_by_type("keen::ItemInfo") end)
    if not ok or not items then return result(def, "FAIL_CLOSED", "itemInfoEnumerationFailed") end
    if findItem(items, def.itemId) then return result(def, "FAIL_CLOSED", "itemIdCollisionRequiresRuntimeIdentityCheck") end
    local itemTemplate = findItem(items, SOURCE_ITEM_TEMPLATE_ID)
    local previewTemplate = findItem(items, SOURCE_4X4X4_ID)
    if not itemTemplate or not previewTemplate then return result(def, "FAIL_CLOSED", "missingSourceItemTemplate") end
    if itemTemplate.data.category ~= "Blueprints" or not itemTemplate.data.equipment or itemTemplate.data.equipment.slot ~= "BuildTool" then return result(def, "FAIL_CLOSED", "sourceItemTemplateNotGeometricBuildTool") end
    local registries = game.assets.get_resources_by_type("keen::ItemRegistryResource")
    local blueprintRegistries = game.assets.get_resources_by_type("keen::VoxelBlueprintItemRegistryResource")
    if not registries or not registries[1] or not blueprintRegistries or not blueprintRegistries[1] then return result(def, "FAIL_CLOSED", "missingRegistryResource") end
    local itemRegistry = registries[1].data
    local blueprintRegistry = blueprintRegistries[1].data
    local sourceBlueprint = findBlueprint(blueprintRegistry, SOURCE_4X4X4_ID)
    if not sourceBlueprint or not sourceBlueprint.data or #sourceBlueprint.data ~= M.config.maxPayloadBytes then return result(def, "FAIL_CLOSED", "missingOrUnsafeBlueprintTemplate") end
    local voxelRef = previewTemplate.data.equipment and previewTemplate.data.equipment.voxelObject
    local voxel = voxelRef and game.assets.get_resource(voxelRef, "keen::VoxelModelResource", 0)
    if not voxel or not voxel.data or not voxel.data.data or #voxel.data.data ~= #def.ghostPreview then return result(def, "FAIL_CLOSED", "missingOrMismatchedVoxelModel") end
    local customVoxel = game.assets.create_resource(voxel.data, "keen::VoxelModelResource")
    for index, value in ipairs(def.ghostPreview) do customVoxel.data.data[index] = value end
    customVoxel.data.isTerrain = false
    local sourceRender = game.assets.get_resource(voxelRef, "keen::RenderModel", 0)
    if not sourceRender then return result(def, "FAIL_CLOSED", "missingRenderModelCompanion") end
    local renderCreated = false
    game.assets.create_resource(sourceRender.data, "keen::RenderModel", customVoxel.guid, 0); renderCreated = true
    local newItem = game.assets.create_resource(itemTemplate.data, "keen::ItemInfo")
    newItem.data.itemId.value = def.itemId
    newItem.data.debugName = "ArchitectToolkit_CODE0013_" .. def.variant
    newItem.data.equipment.voxelObject = customVoxel
    table.insert(blueprintRegistry.blueprintItems, sourceBlueprint)
    local newBlueprint = blueprintRegistry.blueprintItems[#blueprintRegistry.blueprintItems]
    newBlueprint.itemId.value = def.itemId
    local payload = hexBytes(def.finalPayloadHex)
    for index, value in ipairs(payload) do newBlueprint.data[index] = value end
    newBlueprint.isDataCompressed = true
    table.insert(itemRegistry.itemRefs, newItem)
    return {variant = def.variant, itemId = def.itemId, status = "REGISTERED_PRIVATE_RESOURCES", failureReason = "", writeAttempted = true, itemInfoGuid = tostring(newItem.guid or ""), blueprintGuid = tostring(newBlueprint.guid or ""), voxelModelGuid = tostring(customVoxel.guid or ""), renderModelCreated = renderCreated, finalPayloadHex = def.finalPayloadHex, ghostPattern = def.ghostPattern, itemRegistryLinked = exactLinked(itemRegistry, newItem)}
end

function M.activate()
    if not M.config.enabled then
        return {status = "DISABLED_BY_DEFAULT", codeId = M.config.codeId, mode = M.config.mode, writeAttempted = false}
    end
    local results = {status = "PREVIEW_REGISTRATION_ATTEMPTED", codeId = M.config.codeId, mode = M.config.mode, placementEnabled = false, variants = {}}
    for _, def in ipairs(M.canaries) do table.insert(results.variants, registerOne(def)) end
    M.lastResults = results
    return results
end

function M.previewOnly()
    if not M.config.enabled then return {status = "DISABLED_BY_DEFAULT", reason = "previewPackageDisabled", writeAttempted = false} end
    return {status = "PREVIEW_ONLY", previewEnabled = true, placementCommitEnabled = false, placementAutomation = false, writeAttempted = false}
end

if M.config.enabled then M.activate() end
return M
""" % "\n".join(rows)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="\n")


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE_LUA)
    parser.add_argument("--output", type=Path, default=ROOT / "bridge" / MANIFEST_NAME)
    parser.add_argument("--lua-output", type=Path, default=None)
    args = parser.parse_args()
    report = write_manifest(args.output, args.source)
    if args.lua_output:
        write_preview_module(report, args.lua_output)
    print(json.dumps({"status": report["status"], "variants": len(report["variants"]), "output": str(args.output)}, sort_keys=True))
    return 0 if report["status"] == "PRODUCT_PATH_STAGING_READY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
