-- CODE-0013 preview-only product-path package (generated from the CODE-0012 manifest).
-- Disabled by default. This file is staged only; it is not loaded by src/mod.lua.
-- It performs no placement automation. Enabling it is an explicit user action.
local M = {}
M.config = { enabled = false, codeId = "CODE-0013", mode = "PREVIEW_ONLY", maxPayloadBytes = 8 }
M.canaries = {
    {variant="CONTROL", itemId=3552148149, finalPayloadHex="0990000000000990", ghostPattern="A", ghostPreview={18,0,0,18,0,0,0,0,0,0,0,0,18,0,0,18,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,18,0,0,18,0,0,0,0,0,0,0,0,18,0,0,18}, itemInfoGuid="35ca0e60-6189-5766-b9bd-233a1c49cdb6", blueprintGuid="383753ef-6bf8-5099-a460-3bbf0fa2a41e", voxelModelGuid="1b9aff1c-fcda-58a8-9b73-d9bc58967f94", renderModelGuid="44ecdda1-3d29-546c-9537-817ee4761333"},
    {variant="GHOST_VARIANT", itemId=2561652817, finalPayloadHex="0990000000000990", ghostPattern="B", ghostPreview={0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,18,18,0,0,18,18,0,0,0,0,0,0,0,0,0,0,18,18,0,0,18,18,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0}, itemInfoGuid="d5c62fe3-3db6-5bce-8871-10f81016741f", blueprintGuid="03997cbd-fb48-5590-83b7-9bf9157ed15c", voxelModelGuid="550e028a-ff2e-5aaa-876b-5230c1abef55", renderModelGuid="5a4119d1-6565-5be3-a637-2bdd847564f9"},
    {variant="FINAL_VARIANT", itemId=1892633990, finalPayloadHex="0000600660060000", ghostPattern="A", ghostPreview={18,0,0,18,0,0,0,0,0,0,0,0,18,0,0,18,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,18,0,0,18,0,0,0,0,0,0,0,0,18,0,0,18}, itemInfoGuid="af2dd38e-2de6-5c1a-ad0b-79111a18a371", blueprintGuid="0e7b3944-ef00-537a-a692-2ccfd851285e", voxelModelGuid="b6b11db8-8725-5ba7-a124-2cb04cebe1f2", renderModelGuid="83b5a2d2-db5b-5f2e-aa09-6e2b3a3ad9a7"},
    {variant="CROSS_WIRED", itemId=2330891540, finalPayloadHex="0990000000000990", ghostPattern="B", ghostPreview={0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,18,18,0,0,18,18,0,0,0,0,0,0,0,0,0,0,18,18,0,0,18,18,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0}, itemInfoGuid="d6d68208-ae4f-50f2-841c-f55d94fff696", blueprintGuid="f15ad580-0052-5f19-9577-4df46a3bfa6b", voxelModelGuid="fcf6101c-cddc-519d-8bef-b27da52d2f15", renderModelGuid="16a77f87-adcf-5910-a97f-9e5ba2e5baae"},
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
    for pair in string.gmatch(hex, "%x%x") do table.insert(bytes, tonumber(pair, 16)) end
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
