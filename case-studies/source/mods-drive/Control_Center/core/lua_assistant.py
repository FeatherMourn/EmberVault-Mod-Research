"""Generate conservative Lua/EML starter code from structured definitions."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


class LuaAssistantError(ValueError):
    pass


class LuaAssistant:
    """Generate source text only; it never executes generated Lua."""

    def generate(self, definition: dict[str, Any], destination: Path | None = None) -> str:
        project_id = self._slug(definition.get("id") or definition.get("name"))
        resource_type = str(definition.get("resource_type", "keen::ItemInfo"))
        required_api = str(definition.get("required_loader_api", "assets.register_resource"))
        donor_id = definition.get("donor_id")
        donor_guid = definition.get("donor_guid")
        initial_guid_match = json.dumps(str(donor_guid)) if donor_guid else "nil"
        new_item_id = definition.get("new_item_id")
        donor_recipe_id = definition.get("donor_recipe_id")
        new_recipe_id = definition.get("new_recipe_id")
        donor_line = f"local DONOR_ID = {int(donor_id)}" if isinstance(donor_id, int) and donor_id > 0 else "local DONOR_ID = nil -- set after donor validation"
        customization = definition.get("customization") or {}
        # Icon replacement is only packaged/planned today; it has not passed a
        # same-build in-game rendering check. Keep it research-only here too,
        # matching ContentCompiler's capability contract.
        verified_fields = {"identity", "localization", "recipe", "layout"}
        operations: list[str] = []
        for key, value in customization.items() if isinstance(customization, dict) else ():
            if key in verified_fields and isinstance(value, dict):
                for field, field_value in value.items():
                    operations.append(f"    clone.data[{json.dumps(str(field))}] = {self._lua_value(field_value)}")
            else:
                operations.append(f"    -- RESEARCH-ONLY: {key} customization is recorded but not applied until runtime evidence exists.")
        operation_block = "\n".join(operations) or "    -- No verified customization operations requested."
        if resource_type == "keen::ItemInfo" and isinstance(donor_id, int) and isinstance(new_item_id, int):
            donor_match = (f"tostring(candidate.guid) == {json.dumps(str(donor_guid))}" if donor_guid
                           else "candidate.data.itemId and candidate.data.itemId.value == DONOR_ID")
            recipe_block = ""
            if isinstance(donor_recipe_id, int) and isinstance(new_recipe_id, int):
                recipe_block = f'''\n    local recipe_registry = kfc.resources('keen::RecipeRegistryResource')[1]\n    local donor_recipe\n    local function recipe_matches(recipe)\n        if recipe and recipe.recipeId and recipe.recipeId.value == {donor_recipe_id} then return true end\n        for _, output in pairs(recipe and recipe.output or {{}}) do\n            if output and output.item and output.item.value == {int(donor_id)} then return true end\n            if output and output.itemRef and output.itemRef.value == {int(donor_id)} then return true end\n        end\n        return false\n    end\n    for _, candidate_type in ipairs({{'keen::RecipeRegistryResource', 'keen::ds::RecipeRegistryResource'}}) do\n        for _, candidate_registry in pairs(kfc.resources(candidate_type)) do\n            for _, candidate_recipe in pairs(candidate_registry.data and candidate_registry.data.recipes or {{}}) do\n                if recipe_matches(candidate_recipe) then\n                    donor_recipe = candidate_recipe\n                    recipe_registry = candidate_registry\n                    break\n                end\n            end\n            if donor_recipe then break end\n        end\n        if donor_recipe then break end\n    end\n    if recipe_registry and donor_recipe then\n        local recipe = kfc.deep_copy(donor_recipe)\n        recipe.recipeId.value = {new_recipe_id}\n        for _, output in pairs(recipe.output or {{}}) do\n            if output.item then output.item.value = {new_item_id} end\n            if output.itemRef then output.itemRef = clone.guid end\n        end\n        kfc.append_registry(recipe_registry, 'recipes', recipe)\n        local ui = kfc.resources('keen::FbUiBundle')[1]\n        if ui then kfc.clone_recipe_set(ui, {donor_recipe_id}, {new_recipe_id}) end\n        log("REGISTERED_RECIPE", {new_recipe_id})\n    else\n        log("BLOCKED", "donor_recipe_not_found")\n    end'''
            runtime_block = f'''    if not donor then log("BLOCKED", "donor_not_found"); return {{}} end
    local ok_clone, clone_or_error = pcall(function()
        return game.assets.register_resource(donor.data, 'keen::ItemInfo')
    end)
    if not ok_clone or not clone_or_error then log("ERROR", "clone_failed|" .. tostring(clone_or_error)); return {{}} end
    local clone = clone_or_error
    clone.data.itemId.value = {new_item_id}
    local item_registry
    for _, candidate in pairs(game.assets.get_resources_by_type('keen::ItemRegistryResource') or {{}}) do
        if candidate and candidate.data and candidate.data.itemRefs then
            item_registry = candidate
            break
        end
    end
    if item_registry then
        clone.data.objectId = clone.guid
        table.insert(item_registry.data.itemRefs, clone)
        if item_registry.data.dbgNames then
            table.insert(item_registry.data.dbgNames, clone.data.debugName)
        end
    end
{operation_block}
    log("CLONED_ITEM", {new_item_id})
{recipe_block}
'''
        else:
            runtime_block = '''    -- Generic resources require a donor-specific runtime adapter.
    local clone = nil -- populate only after donor lookup and clone validation.
    if clone then
''' + operation_block + '''
    end'''
        source = f'''-- Generated by Enshrouded Control Center.
-- This module is research-only until its donor schema and runtime evidence are verified.
local REQUIRED_API = {json.dumps(required_api)}
local RESOURCE_TYPE = {json.dumps(resource_type)}
{donor_line}
local kfc = require('kfc_content_registry')

local function log(kind, value)
    print("[CC-GENERATED:{project_id}] " .. kind .. "|" .. tostring(value or ""))
end

local function resources(type_name)
    local ok, result = pcall(function() return game.assets.get_resources_by_type(type_name) or {{}} end)
    if not ok then log("ERROR", type_name .. "|" .. tostring(result)); return {{}} end
    return result
end

-- EML executes mod.lua as a top-level patch script. Keep the generated
-- operations at module load time, matching the verified furniture probes.
do
    log("CAPABILITY_REQUIRED", REQUIRED_API)
    log("RESOURCE_TYPE", RESOURCE_TYPE)
    -- Donor lookup and registration must be implemented only after validation.
    local initial_items = resources(RESOURCE_TYPE)
    local donor
    for _, resource in pairs(initial_items) do
        if resource and resource.data then
            if {initial_guid_match} ~= nil and tostring(resource.guid) == {initial_guid_match} then
                log("DONOR_MATCH", tostring(resource.guid))
                donor = resource
            end
        end
    end
    log("DONOR_SCAN_DONE", tostring(donor ~= nil))
    if not DONOR_ID then log("BLOCKED", "donor_id_required"); return {{}} end
{runtime_block}
end

return {{}}
'''
        if destination is not None:
            destination = Path(destination); destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_suffix(destination.suffix + ".tmp")
            temporary.write_text(source, encoding="utf-8")
            temporary.replace(destination)
        return source

    def generate_minimal_clone_probe(self, donor_guid: str, new_item_id: int,
                                     project_id: str = "minimal_clone_probe",
                                     destination: Path | None = None) -> str:
        """Generate the smallest runtime registration experiment."""
        if not donor_guid or not isinstance(new_item_id, int) or new_item_id <= 0:
            raise LuaAssistantError("A donor GUID and positive new item ID are required.")
        source = f'''-- Minimal generated clone probe; research-only.
local DONOR_GUID = {json.dumps(str(donor_guid))}
local NEW_ITEM_ID = {new_item_id}
local function log(kind, value)
    print("[CC-MINIMAL-CLONE:{self._slug(project_id)}] " .. kind .. "|" .. tostring(value or ""))
end
local items = game.assets.get_resources_by_type('keen::ItemInfo') or {{}}
local donor
for _, resource in pairs(items) do
    if resource and tostring(resource.guid) == DONOR_GUID then donor = resource; break end
end
log("DONOR", tostring(donor ~= nil))
if not donor then return {{}} end
local ok, result = pcall(function()
    return game.assets.register_resource(donor.data, 'keen::ItemInfo')
end)
log("REGISTER", tostring(ok) .. "|" .. tostring(result))
if not ok or not result then return {{}} end
result.data.itemId.value = NEW_ITEM_ID
log("CLONED_ITEM", NEW_ITEM_ID)
return {{}}
'''
        if destination is not None:
            destination = Path(destination); destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(source, encoding="utf-8")
        return source

    def generate_registry_clone_probe(self, donor_guid: str, new_item_id: int,
                                      project_id: str = "registry_clone_probe",
                                      destination: Path | None = None) -> str:
        """Generate a research probe for registration plus item-registry indexing."""
        if not donor_guid or not isinstance(new_item_id, int) or new_item_id <= 0:
            raise LuaAssistantError("A donor GUID and positive new item ID are required.")
        source = f'''-- Generated registry clone probe; research-only.
local DONOR_GUID = {json.dumps(str(donor_guid))}
local NEW_ITEM_ID = {new_item_id}
local function log(kind, value)
    print("[CC-REGISTRY-CLONE:{self._slug(project_id)}] " .. kind .. "|" .. tostring(value or ""))
end
local items = game.assets.get_resources_by_type('keen::ItemInfo') or {{}}
local donor
for _, resource in pairs(items) do
    if resource and tostring(resource.guid) == DONOR_GUID then donor = resource; break end
end
log("DONOR", tostring(donor ~= nil))
if not donor then return {{}} end
local ok, result = pcall(function()
    return game.assets.register_resource(donor.data, 'keen::ItemInfo')
end)
log("REGISTER", tostring(ok) .. "|" .. tostring(result))
if not ok or not result then return {{}} end
result.data.itemId.value = NEW_ITEM_ID
result.data.objectId = result.guid
if result.data.debugName then
    result.data.debugName = "CC_Generated_Clone_" .. tostring(NEW_ITEM_ID)
end
local registry
for _, candidate in pairs(game.assets.get_resources_by_type('keen::ItemRegistryResource') or {{}}) do
    if candidate and candidate.data and candidate.data.itemRefs then
        registry = candidate
        break
    end
end
if not registry or not registry.data or not registry.data.itemRefs then
    log("REGISTRY", "missing")
    return {{}}
end
local before = #registry.data.itemRefs
local first_entry = registry.data.itemRefs[1]
log("FIRST_SHAPE", "rawItem=" .. tostring(first_entry and first_entry.itemId and first_entry.itemId.value)
    .. "|dataItem=" .. tostring(first_entry and first_entry.data and first_entry.data.itemId and first_entry.data.itemId.value)
    .. "|guid=" .. tostring(first_entry and first_entry.guid))
table.insert(registry.data.itemRefs, result)
if registry.data.dbgNames then
    table.insert(registry.data.dbgNames, result.data.debugName)
    log("DBG_NAMES", "updated")
else
    log("DBG_NAMES", "missing")
end
local after = #registry.data.itemRefs
log("REGISTRY", tostring(before) .. "->" .. tostring(after))
local last_entry = registry.data.itemRefs[after]
log("ENTRY_SHAPE", "rawItem=" .. tostring(last_entry and last_entry.itemId and last_entry.itemId.value)
    .. "|dataItem=" .. tostring(last_entry and last_entry.data and last_entry.data.itemId and last_entry.data.itemId.value)
    .. "|guid=" .. tostring(last_entry and last_entry.guid))
local found = false
for index = 1, #registry.data.itemRefs do
    local entry = registry.data.itemRefs[index]
    local entry_data = entry and entry.data or entry
    if entry_data and entry_data.itemId and entry_data.itemId.value == NEW_ITEM_ID then
        found = true
        break
    end
end
log("INDEX_LOOKUP", tostring(found))
if found then log("INDEXED_ITEM", NEW_ITEM_ID) end
return {{}}
'''
        if destination is not None:
            destination = Path(destination); destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(source, encoding="utf-8")
        return source

    def generate_visual_substitution_probe(self, resource_type: str,
                                            dependency_guids: list[str],
                                            project_id: str = "visual_substitution_probe",
                                            destination: Path | None = None) -> str:
        """Generate a read-only resource-graph probe for visual dependencies."""
        if not str(resource_type).strip():
            raise LuaAssistantError("A resource type is required.")
        guids = [str(guid).strip() for guid in dependency_guids if str(guid).strip()]
        if not guids:
            raise LuaAssistantError("At least one dependency GUID is required.")
        encoded = ", ".join(json.dumps(guid) for guid in guids)
        source = f'''-- Generated visual substitution probe; research-only and read-only.
local RESOURCE_TYPE = {json.dumps(str(resource_type).strip())}
local DEPENDENCIES = {{{encoded}}}
local function log(kind, value)
    print("[CC-VISUAL-PROBE:{self._slug(project_id)}] " .. kind .. "|" .. tostring(value or ""))
end
local resources = game.assets.get_resources_by_type(RESOURCE_TYPE) or {{}}
local found = {{}}
for _, resource in pairs(resources) do
    local guid = tostring(resource and resource.guid or "")
    if guid ~= "" then found[guid] = true end
end
for _, dependency in ipairs(DEPENDENCIES) do
    log("DEPENDENCY", dependency .. "|" .. tostring(found[dependency] == true))
end
log("GRAPH_SCAN", RESOURCE_TYPE .. "|count=" .. tostring(#resources))
log("ACTION", "read_only_no_visual_mutation")
return {{}}
'''
        if destination is not None:
            destination = Path(destination); destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(source, encoding="utf-8")
        return source

    def generate_visual_field_probe(self, donor_guid: str,
                                    project_id: str = "visual_field_probe",
                                    destination: Path | None = None) -> str:
        """Generate a read-only donor-field inventory probe."""
        if not str(donor_guid).strip():
            raise LuaAssistantError("A donor GUID is required.")
        source = f'''-- Generated donor visual-field probe; research-only and read-only.
local DONOR_GUID = {json.dumps(str(donor_guid).strip())}
local function log(kind, value)
    print("[CC-VISUAL-FIELDS:{self._slug(project_id)}] " .. kind .. "|" .. tostring(value or ""))
end
local donor
for _, resource in pairs(game.assets.get_resources_by_type('keen::ItemInfo') or {{}}) do
    if resource and tostring(resource.guid) == DONOR_GUID then donor = resource; break end
end
if not donor or not donor.data then log("DONOR", "missing"); return {{}} end
log("DONOR", tostring(donor.guid))
local visual_fields = {{"iconImage", "iconModel", "iconScene", "visualModel", "visualEntity", "placedEntity", "material", "texture", "objectId"}}
for _, field in ipairs(visual_fields) do
    local value = donor.data[field]
    log("FIELD", field .. "|" .. tostring(value ~= nil) .. "|" .. tostring(value and value.guid or value and value.value or value or "nil"))
end
log("ACTION", "read_only_field_inventory")
return {{}}
'''
        if destination is not None:
            destination = Path(destination); destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(source, encoding="utf-8")
        return source

    def generate_resource_graph_probe(self, resource_guids: list[str],
                                      resource_types: list[str],
                                      project_id: str = "resource_graph_probe",
                                      destination: Path | None = None) -> str:
        """Generate a read-only GUID-to-resource-family graph probe."""
        guids = [str(value).strip() for value in resource_guids if str(value).strip()]
        types = [str(value).strip() for value in resource_types if str(value).strip()]
        if not guids or not types:
            raise LuaAssistantError("Resource GUIDs and resource types are required.")
        encoded_guids = ", ".join(json.dumps(value) for value in guids)
        encoded_types = ", ".join(json.dumps(value) for value in types)
        source = f'''-- Generated resource graph probe; research-only and read-only.
local GUIDS = {{{encoded_guids}}}
local TYPES = {{{encoded_types}}}
local function log(kind, value)
    print("[CC-RESOURCE-GRAPH:{self._slug(project_id)}] " .. kind .. "|" .. tostring(value or ""))
end
for _, type_name in ipairs(TYPES) do
    local ok, result = pcall(function() return game.assets.get_resources_by_type(type_name) end)
      if not ok then
          log("TYPE_ERROR", type_name .. "|" .. tostring(result))
      else
          local resources = result or {{}}
          for _, resource in pairs(resources) do
              local guid = tostring(resource and resource.guid or "")
              for _, wanted in ipairs(GUIDS) do
                  if guid == wanted then
                      log("MATCH", wanted .. "|" .. type_name)
                  end
            end
        end
          log("TYPE_SCAN", type_name .. "|count=" .. tostring(#resources))
    end
end
log("ACTION", "read_only_resource_graph")
return {{}}
'''
        if destination is not None:
            destination = Path(destination); destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(source, encoding="utf-8")
        return source

    def generate_interaction_donor_probe(self, resource_type: str, resource_guid: str,
                                         interaction_key: str = "",
                                         project_id: str = "interaction_donor_probe",
                                         destination: Path | None = None) -> str:
        """Generate a bounded read-only inspection of an asset-backed interaction donor."""
        if not str(resource_type).strip() or not str(resource_guid).strip():
            raise LuaAssistantError("An interaction resource type and donor GUID are required.")
        source = f'''-- Generated interaction-donor probe; research-only, read-only, single-player scope.
local TYPE_NAME = {json.dumps(str(resource_type).strip())}
local WANTED_GUID = {json.dumps(str(resource_guid).strip())}
local INTERACTION_KEY = {json.dumps(str(interaction_key).strip())}
local function log(kind, value)
    print("[CC-INTERACTION-DONOR:{self._slug(project_id)}] " .. kind .. "|" .. tostring(value or ""))
end
local ok, resources = pcall(function() return game.assets.get_resources_by_type(TYPE_NAME) or {{}} end)
if not ok then log("TYPE_ERROR", tostring(resources)); return {{}} end
local found = nil
for _, resource in pairs(resources or {{}}) do
    if resource and tostring(resource.guid) == WANTED_GUID then found = resource; break end
end
if not found then
    log("RESULT", "donor_not_found"); log("COUNT", #(resources or {{}})); return {{}}
end
local read_ok, payload = pcall(function() return found.data end)
log("RESULT", "donor_found|read=" .. tostring(read_ok))
if read_ok and payload then
    local key_ok, value = pcall(function() return payload[INTERACTION_KEY] end)
    log("FIELD", INTERACTION_KEY .. "|read=" .. tostring(key_ok) .. "|value=" .. tostring(value))
end
log("AUTHORITY", "unknown")
log("PERSISTENCE", "unknown")
log("ACTION", "read_only_asset_backed_interaction_inspection")
return {{}}
'''
        if destination is not None:
            destination = Path(destination); destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(source, encoding="utf-8")
        return source

    def generate_single_resource_probe(self, resource_type: str, resource_guid: str,
                                       project_id: str = "single_resource_probe",
                                       destination: Path | None = None) -> str:
        """Generate the smallest possible GUID lookup probe."""
        if not str(resource_type).strip() or not str(resource_guid).strip():
            raise LuaAssistantError("A resource type and GUID are required.")
        source = f'''-- Generated single-resource probe; research-only and read-only.
local TYPE_NAME = {json.dumps(str(resource_type).strip())}
local WANTED_GUID = {json.dumps(str(resource_guid).strip())}
local function log(kind, value)
    print("[CC-SINGLE-RESOURCE:{self._slug(project_id)}] " .. kind .. "|" .. tostring(value or ""))
end
local ok, result = pcall(function()
    return game.assets.get_resources_by_type(TYPE_NAME) or {{}}
end)
if not ok then
    log("TYPE_ERROR", tostring(result))
    return {{}}
end
local resources = result or {{}}
local found = false
for _, resource in pairs(resources) do
    if resource and tostring(resource.guid) == WANTED_GUID then found = true; break end
end
log("RESULT", TYPE_NAME .. "|" .. WANTED_GUID .. "|" .. tostring(found))
log("COUNT", #resources)
log("ACTION", "read_only_single_lookup")
return {{}}
'''
        if destination is not None:
            destination = Path(destination); destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(source, encoding="utf-8")
        return source

    def generate_resource_metadata_probe(self, resource_type: str,
                                         wanted_guid: str,
                                         project_id: str = "resource_metadata_probe",
                                         destination: Path | None = None) -> str:
        """Generate a read-only identity probe for undecodable resource families."""
        if not str(resource_type).strip() or not str(wanted_guid).strip():
            raise LuaAssistantError("A resource type and GUID are required.")
        source = f'''-- Generated resource metadata probe; research-only and read-only.
local TYPE_NAME = {json.dumps(str(resource_type).strip())}
local WANTED_GUID = {json.dumps(str(wanted_guid).strip())}
local function log(kind, value)
    print("[CC-RESOURCE-METADATA:{self._slug(project_id)}] " .. tostring(kind) .. "|" .. tostring(value or ""))
end
-- Record the live API surface before attempting the call. This makes a
-- loader/API mismatch immediately distinguishable from a bad resource type.
log("API", "assets=" .. type(game.assets) .. "|metadata=" .. type(game.assets and game.assets.get_resource_metadata_by_type) .. "|resources=" .. type(game.assets and game.assets.get_resources_by_type))
local ok, result = pcall(function()
    return game.assets.get_resource_metadata_by_type(TYPE_NAME) or {{}}
end)
if not ok then log("TYPE_ERROR", tostring(result)); return {{}} end
local found = false
local count = 0
for _, row in pairs(result or {{}}) do
    count = count + 1
    if row and tostring(row.guid) == WANTED_GUID then
        found = true
        log("MATCH", tostring(row.guid) .. "|part=" .. tostring(row.part))
    end
end
log("COUNT", count)
log("RESULT", tostring(found))
log("ACTION", "read_only_metadata_identity")
return {{}}
'''
        if destination is not None:
            destination = Path(destination); destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(source, encoding="utf-8")
        return source

    def generate_resource_metadata_single_probe(self, resource_type: str,
                                                 wanted_guid: str,
                                                 project_id: str = "resource_metadata_single_probe",
                                                 destination: Path | None = None) -> str:
        """Generate a bounded metadata lookup probe for one resource identity."""
        if not str(resource_type).strip() or not str(wanted_guid).strip():
            raise LuaAssistantError("A resource type and GUID are required.")
        source = f'''-- Generated bounded resource metadata probe; read-only.
local TYPE_NAME = {json.dumps(str(resource_type).strip())}
local WANTED_GUID = {json.dumps(str(wanted_guid).strip())}
local function log(kind, value)
    print("[CC-RESOURCE-METADATA:{self._slug(project_id)}] " .. tostring(kind) .. "|" .. tostring(value or ""))
end
log("API", "metadata=" .. type(game.assets and game.assets.get_resource_metadata))
log("BEFORE_CALL", TYPE_NAME .. "|" .. WANTED_GUID)
local ok, result = pcall(function()
    return game.assets.get_resource_metadata(WANTED_GUID, TYPE_NAME, 0)
end)
log("AFTER_CALL", "ok=" .. tostring(ok) .. "|result=" .. tostring(result))
if ok and result then
    log("IDENTITY", "guid=" .. tostring(result.guid) .. "|type=" .. tostring(result.type) .. "|part=" .. tostring(result.part))
end
return {{}}
'''
        if destination is not None:
            destination = Path(destination); destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(source, encoding="utf-8")
        return source

    def generate_blueprint_registry_payload_probe(
        self, resource_guid: str,
        project_id: str = "voxel_blueprint_registry_payload_probe",
        destination: Path | None = None,
    ) -> str:
        """Generate a bounded, read-only blueprint registry payload probe."""
        if not str(resource_guid).strip():
            raise LuaAssistantError("A blueprint registry GUID is required.")
        source = f'''-- Generated blueprint registry payload probe; research-only and read-only.
local RESOURCE_GUID = {json.dumps(str(resource_guid).strip())}
local function log(kind, value)
    print("[CC-BLUEPRINT-PAYLOAD:{self._slug(project_id)}] " .. tostring(kind) .. "|" .. tostring(value or ""))
end
log("BEGIN", "read_only=true|bounded=true")
local ok, resource = pcall(function()
    return game.assets.get_resource(RESOURCE_GUID, "keen::VoxelBlueprintItemRegistryResource", 0)
end)
log("LOOKUP", "ok=" .. tostring(ok) .. "|found=" .. tostring(resource ~= nil))
if not ok or not resource or not resource.data then log("RESULT", "lookup_failed"); return {{}} end
local payload = resource.data
local items = payload.blueprintItems
log("PAYLOAD", "type=" .. type(payload))
log("FIELD", "blueprintItems|ok=" .. tostring(items ~= nil) .. "|type=" .. type(items))
local count = 0
if items then count = #items end
log("FIELD", "blueprintItems_length|ok=true|value=" .. tostring(count))
local function summarize(label, item)
    if not item then log(label, "ok=false"); return end
    local size = item.size or {{}}
    log(label, "ok=true|itemId=" .. tostring(item.itemId) .. "|size=" .. tostring(size.x) .. "x" .. tostring(size.y) .. "x" .. tostring(size.z) .. "|compressed=" .. tostring(item.isDataCompressed))
end
if count > 0 then summarize("FIRST", items[1]) end
if count > 1 then summarize("LAST", items[count]) end
log("BOUNDARY", "created=false|registered=false|mutated=false|attached=false|world=false|save=false")
log("RESULT", "blueprint_registry_payload_read_complete")
return {{}}
'''
        if destination is not None:
            destination = Path(destination); destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(source, encoding="utf-8")
        return source

    def generate_item_visual_reference_probe(self, donor_guid: str, new_item_id: int,
                                             replacement_model_guid: str,
                                             project_id: str = "item_visual_reference_probe",
                                             destination: Path | None = None) -> str:
        """Probe assignment of an ItemInfo iconModel reference on a clone only."""
        if not str(donor_guid).strip() or not isinstance(new_item_id, int) or new_item_id <= 0:
            raise LuaAssistantError("A donor GUID and positive new item ID are required.")
        if not str(replacement_model_guid).strip():
            raise LuaAssistantError("A replacement model GUID is required.")
        source = f'''-- Generated ItemInfo visual-reference probe; research-only.
local DONOR_GUID = {json.dumps(str(donor_guid).strip())}
local NEW_ITEM_ID = {new_item_id}
local REPLACEMENT_MODEL = {json.dumps(str(replacement_model_guid).strip())}
local function log(kind, value)
    print("[CC-ITEM-VISUAL:{self._slug(project_id)}] " .. kind .. "|" .. tostring(value or ""))
end
local donor
for _, resource in pairs(game.assets.get_resources_by_type('keen::ItemInfo') or {{}}) do
    if resource and tostring(resource.guid) == DONOR_GUID then donor = resource; break end
end
if not donor then log("DONOR", "missing"); return {{}} end
local ok_clone, clone = pcall(function()
    return game.assets.register_resource(donor.data, 'keen::ItemInfo')
end)
if not ok_clone or not clone then log("CLONE_ERROR", tostring(clone)); return {{}} end
clone.data.itemId.value = NEW_ITEM_ID
local before = clone.data.iconModel
local ok_assign, assign_error = pcall(function()
    clone.data.iconModel = REPLACEMENT_MODEL
end)
log("ASSIGN", tostring(ok_assign) .. "|" .. tostring(assign_error or ""))
log("BEFORE", tostring(before and before.guid or before and before.value or before or "nil"))
log("AFTER", tostring(clone.data.iconModel and clone.data.iconModel.guid or clone.data.iconModel and clone.data.iconModel.value or clone.data.iconModel or "nil"))
log("ACTION", "clone_only_no_registry_mutation")
return {{}}
'''
        if destination is not None:
            destination = Path(destination); destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(source, encoding="utf-8")
        return source

    def generate_localization_probe(self, locale_guid: str,
                                    project_id: str = "localization_probe",
                                    destination: Path | None = None) -> str:
        """Generate an explicit research-only localization registration probe."""
        if not str(locale_guid).strip():
            raise LuaAssistantError("A replacement localization GUID is required.")
        source = f'''-- Generated localization registration probe; research-only.
-- This intentionally uses the compiled payload and does not claim that the
-- target build consumes newly-created localization tags.
local LOCALE_GUID = {json.dumps(str(locale_guid).strip())}
local function log(kind, value)
    print("[CC-LOCALIZATION:{self._slug(project_id)}] " .. kind .. "|" .. tostring(value or ""))
end
local ok, helper = pcall(require, 'kfc_localization_registry')
if not ok or not helper then
    log("BLOCKED", "localization_helper_unavailable|" .. tostring(helper))
    return {{}}
end
local ok_payload, entries = pcall(require, 'localization_payload')
if not ok_payload or not entries then
    log("BLOCKED", "localization_payload_unavailable|" .. tostring(entries))
    return {{}}
end
local ok_register, result = pcall(function()
    return helper.register(entries, LOCALE_GUID, 'en')
end)
log(ok_register and "REGISTERED" or "ERROR", tostring(result))
log("ACTION", "research_only_localization_registration")
return {{}}
'''
        if destination is not None:
            destination = Path(destination); destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(source, encoding="utf-8")
        return source

    @staticmethod
    def manifest_snippet(definition: dict[str, Any]) -> dict[str, Any]:
        return {
            "entrypoint": "src/mod.lua",
            "feature_state": "research-only",
            "capabilities": ["patch"],
            "required_loader_api": definition.get("required_loader_api", "assets.register_resource"),
        }

    @staticmethod
    def _slug(value: Any) -> str:
        result = re.sub(r"[^a-zA-Z0-9_-]+", "_", str(value or "").strip()).strip("_").lower()
        if not result:
            raise LuaAssistantError("Definition requires an id or name.")
        return result[:64]

    @staticmethod
    def _lua_value(value: Any) -> str:
        """Serialize only scalar JSON values for conservative generated Lua."""
        if isinstance(value, bool):
            return "true" if value else "false"
        if value is None:
            return "nil"
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return repr(value)
        if isinstance(value, str):
            return json.dumps(value)
        raise LuaAssistantError("Generated runtime fields must use scalar values; keep structured edits research-only.")
