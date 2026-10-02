print("Architect Toolkit loaded!")

-- ============================================================
-- Architect Toolkit - Blueprint Generator v1
-- ============================================================

local SOURCE_CEILING_ID = 81726253

-- Native 3D blueprint templates discovered in the current game's
-- VoxelBlueprintItemRegistryResource.
--
-- We deliberately use existing blueprints with the SAME dimensions as
-- the generated 3D shapes instead of stretching the 8x1x8 ceiling item.
-- This keeps ItemInfo / voxel preview / render-model dimensions aligned.
local SOURCE_8X8X8_ID = 1982827643
local SOURCE_8X4X8_ID = 950598916

-- Small 4x4x4 compressed native blueprint.
-- Its placement payload is only 8 bytes, matching the size of the
-- already-proven 8x1x8 ceiling payload. This lets us test whether
-- the native crash is tied to larger nested dynamic arrays.
local SOURCE_4X4X4_ID = 3828821633

-- ============================================================
-- Backend policy
-- ============================================================
--
-- EML/Lua backend:
--   Proven safe up to 8 compressed placement bytes.
--
-- Larger generated blueprint payloads currently hit Enshrouded's
-- native BaseDynamicArray allocator assertion after injection.
--
-- We fail closed instead of risking another game crash.
local MAX_SAFE_EML_PLACEMENT_BYTES = 8

-- ============================================================
-- Single Architect Blueprint carrier
-- ============================================================
-- One stable ItemInfo + one stable VoxelBlueprint entry are registered.
-- Architect owns the shape catalog; only the selected shape is materialized
-- into the carrier for this game session. This avoids growing the Hammer
-- registries with one permanent item per shape.
--
-- All currently supported carrier shapes contain exactly 64 voxels, so the
-- proven 8-byte compressed placement backing and 64-value preview backing can
-- be reused without resizing their dynamic arrays.
local ARCHITECT_CARRIER_ITEM_ID = 1033899955
local ARCHITECT_CARRIER_DEBUG_NAME = "ArchitectToolkit_Blueprint_Carrier"
local ARCHITECT_CARRIER_VOXEL_COUNT = 64
local ARCHITECT_DEFAULT_SHAPE_KEY = "ring_4m"

-- EML module loading is externally evidenced by Ember. This config is read
-- once at startup. Live in-session shape swapping remains deliberately
-- disabled until a safe refresh/selection boundary is independently proven.
local architectCarrierConfigLoaded = false
local architectCarrierConfigError = ""
local okCarrierConfig, carrierConfigResult = pcall(function()
    return require("Config.Architect_Blueprint_Config")
end)
if okCarrierConfig then
    architectCarrierConfigLoaded = true
else
    architectCarrierConfigError = tostring(carrierConfigResult or "")
end

local ACTIVE_ARCHITECT_SHAPE_KEY = ARCHITECT_DEFAULT_SHAPE_KEY
if type(ArchitectToolkit_ActiveShapeKey) == "string"
    and ArchitectToolkit_ActiveShapeKey ~= "" then
    ACTIVE_ARCHITECT_SHAPE_KEY = ArchitectToolkit_ActiveShapeKey
end

-- ============================================================
-- Utility
-- ============================================================

local function findItemById(itemId)

    local items =
        game.assets.get_resources_by_type(
            "keen::ItemInfo"
        )

    for _, resource in ipairs(items) do
        if resource.data.itemId.value == itemId then
            return resource
        end
    end

    return nil
end


local function findBlueprintByItemId(registry, itemId)

    for _, blueprint in ipairs(
        registry.blueprintItems
    ) do
        if blueprint.itemId.value == itemId then
            return blueprint
        end
    end

    return nil
end


local function itemIdExists(itemId)

    return findItemById(itemId) ~= nil
end


-- ============================================================
-- Shape generation
--
-- Coordinates are zero-based:
--
-- x = left/right
-- y = vertical
-- z = forward/back
-- ============================================================

local Shapes = {}


function Shapes.hollowRectangle(sizeX, sizeY, sizeZ)

    return function(x, y, z)

        return
            x == 0
            or x == sizeX - 1
            or z == 0
            or z == sizeZ - 1

    end
end


function Shapes.hollowBox(sizeX, sizeY, sizeZ)

    return function(x, y, z)

        return
            x == 0
            or x == sizeX - 1
            or y == 0
            or y == sizeY - 1
            or z == 0
            or z == sizeZ - 1

    end
end


function Shapes.filled()

    return function(x, y, z)
        return true
    end
end


function Shapes.checkerboard()

    return function(x, y, z)
        return ((x + y + z) % 2) == 0
    end
end


function Shapes.cross(sizeX, sizeY, sizeZ)

    local centerX =
        math.floor((sizeX - 1) / 2)

    local centerZ =
        math.floor((sizeZ - 1) / 2)

    return function(x, y, z)

        return
            x == centerX
            or z == centerZ

    end
end


function Shapes.diagonalCross(sizeX, sizeY, sizeZ)

    return function(x, y, z)
        return
            x == z
            or (x + z) == (sizeX - 1)
    end
end


function Shapes.diamond(sizeX, sizeY, sizeZ)

    local centerX = (sizeX - 1) / 2
    local centerZ = (sizeZ - 1) / 2
    local radius = (math.min(sizeX, sizeZ) / 2) - 0.5

    return function(x, y, z)
        return
            math.abs(x - centerX)
            + math.abs(z - centerZ)
            <= radius
    end
end


function Shapes.stairs(sizeX, sizeY, sizeZ)

    return function(x, y, z)
        local height = math.floor(((x + 1) * sizeY) / sizeX)
        return y < height
    end
end


function Shapes.pyramid(sizeX, sizeY, sizeZ)

    local maxInset =
        math.floor((math.min(sizeX, sizeZ) - 1) / 2)

    return function(x, y, z)
        local inset =
            math.floor((y * (maxInset + 1)) / sizeY)

        return
            x >= inset
            and x < (sizeX - inset)
            and z >= inset
            and z < (sizeZ - inset)
    end
end


function Shapes.archway(sizeX, sizeY, sizeZ)

    return function(x, y, z)
        return
            x == 0
            or x == sizeX - 1
            or y == sizeY - 1
    end
end


function Shapes.filledCircle(sizeX, sizeY, sizeZ)

    local centerX =
        (sizeX - 1) / 2

    local centerZ =
        (sizeZ - 1) / 2

    local radius =
        math.min(sizeX, sizeZ) / 2

    local radiusSquared =
        radius * radius

    return function(x, y, z)

        local dx =
            x - centerX

        local dz =
            z - centerZ

        local distanceSquared =
            (dx * dx) + (dz * dz)

        return
            distanceSquared <= radiusSquared
    end
end


function Shapes.ring(sizeX, sizeY, sizeZ)

    local centerX =
        (sizeX - 1) / 2

    local centerZ =
        (sizeZ - 1) / 2

    local outerRadius =
        math.min(sizeX, sizeZ) / 2

    local innerRadius =
        outerRadius - 1.5

    local outerSquared =
        outerRadius * outerRadius

    local innerSquared =
        innerRadius * innerRadius

    return function(x, y, z)

        local dx =
            x - centerX

        local dz =
            z - centerZ

        local distanceSquared =
            (dx * dx) + (dz * dz)

        return
            distanceSquared <= outerSquared
            and distanceSquared >= innerSquared
    end
end


function Shapes.filledCylinder(sizeX, sizeY, sizeZ)

    local centerX = (sizeX - 1) / 2
    local centerZ = (sizeZ - 1) / 2
    local radius = math.min(sizeX, sizeZ) / 2
    local radiusSquared = radius * radius

    return function(x, y, z)

        local dx = x - centerX
        local dz = z - centerZ

        return
            (dx * dx) + (dz * dz)
            <= radiusSquared
    end
end


function Shapes.hollowCylinder(sizeX, sizeY, sizeZ)

    local centerX = (sizeX - 1) / 2
    local centerZ = (sizeZ - 1) / 2

    local outerRadius =
        math.min(sizeX, sizeZ) / 2

    local innerRadius =
        outerRadius - 1.5

    local outerSquared =
        outerRadius * outerRadius

    local innerSquared =
        innerRadius * innerRadius

    return function(x, y, z)

        local dx = x - centerX
        local dz = z - centerZ

        local distanceSquared =
            (dx * dx) + (dz * dz)

        return
            distanceSquared <= outerSquared
            and distanceSquared >= innerSquared
    end
end


function Shapes.sphere(sizeX, sizeY, sizeZ)

    local centerX = (sizeX - 1) / 2
    local centerY = (sizeY - 1) / 2
    local centerZ = (sizeZ - 1) / 2

    local radius =
        math.min(sizeX, sizeY, sizeZ) / 2

    local radiusSquared =
        radius * radius

    return function(x, y, z)

        local dx = x - centerX
        local dy = y - centerY
        local dz = z - centerZ

        return
            (dx * dx)
            + (dy * dy)
            + (dz * dz)
            <= radiusSquared
    end
end


function Shapes.dome(sizeX, sizeY, sizeZ)

    local centerX = (sizeX - 1) / 2
    local centerZ = (sizeZ - 1) / 2

    -- Dome is the upper half of a sphere whose
    -- center sits on the bottom plane.
    local radius =
        math.min(sizeX, sizeZ) / 2

    local radiusSquared =
        radius * radius

    return function(x, y, z)

        local dx = x - centerX
        local dy = y
        local dz = z - centerZ

        return
            (dx * dx)
            + (dy * dy)
            + (dz * dz)
            <= radiusSquared
    end
end


-- ============================================================
-- Generate VoxelModelResource preview data
--
-- Our proven building preview values:
--
-- 18 = visible building voxel
--  0 = empty
-- ============================================================

local function generatePreviewData(
    sizeX,
    sizeY,
    sizeZ,
    predicate
)

    local data = {}

    for y = 0, sizeY - 1 do

        for z = 0, sizeZ - 1 do

            for x = 0, sizeX - 1 do

                if predicate(x, y, z) then
                    table.insert(data, 18)
                else
                    table.insert(data, 0)
                end

            end
        end
    end

    return data
end


-- ============================================================
-- Generate compressed blueprint placement data
--
-- EML/game blueprint compression:
-- one occupancy bit per voxel.
--
-- Current v1 uses dimensions where X = 8, which matches
-- our proven byte-row layout.
-- ============================================================

local function generateCompressedData(
    sizeX,
    sizeY,
    sizeZ,
    predicate
)

    local result = {}

    local currentByte = 0
    local bitIndex = 0

    for y = 0, sizeY - 1 do

        for z = 0, sizeZ - 1 do

            for x = 0, sizeX - 1 do

                if predicate(x, y, z) then

                    currentByte =
                        currentByte
                        + (2 ^ bitIndex)

                end

                bitIndex =
                    bitIndex + 1

                if bitIndex == 8 then

                    table.insert(
                        result,
                        currentByte
                    )

                    currentByte = 0
                    bitIndex = 0

                end

            end
        end
    end

    if bitIndex ~= 0 then
        table.insert(
            result,
            currentByte
        )
    end

    return result
end


-- ============================================================
-- Item Registry
-- ============================================================

local itemRegistries =
    game.assets.get_resources_by_type(
        "keen::ItemRegistryResource"
    )

local itemRegistry =
    itemRegistries[1].data

-- Backend shape ItemInfos are resolution resources, not player-facing build
-- menu entries. Set true only for compatibility testing of the old behavior.
local exposeBackendItems = false
-- The Ring path is proven. Apply the same guarded registration procedure to
-- every procedural shape, independently; a failed shape never blocks another.
local experimentalRegisterRingInItemRegistry = true
local experimentalRegisterProceduralShapesInItemRegistry = true
local EXPERIMENTAL_RING_ITEM_ID = ARCHITECT_CARRIER_ITEM_ID
local proceduralShapeExpectedItemIds = {
    hollow_ceiling_4m = ARCHITECT_CARRIER_ITEM_ID,
    filled_circle_4m = ARCHITECT_CARRIER_ITEM_ID,
    ring_4m = ARCHITECT_CARRIER_ITEM_ID,
    cross_4m = ARCHITECT_CARRIER_ITEM_ID,
    diamond_4m = ARCHITECT_CARRIER_ITEM_ID,
    diagonal_cross_4m = ARCHITECT_CARRIER_ITEM_ID,
    sphere_2m = ARCHITECT_CARRIER_ITEM_ID,
    filled_cylinder_2m = ARCHITECT_CARRIER_ITEM_ID,
    hollow_cube_2m = ARCHITECT_CARRIER_ITEM_ID,
    stairs_2m = ARCHITECT_CARRIER_ITEM_ID,
    pyramid_2m = ARCHITECT_CARRIER_ITEM_ID,
    archway_2m = ARCHITECT_CARRIER_ITEM_ID
}
local proceduralShapeRegistration = {}
for key, itemId in pairs(proceduralShapeExpectedItemIds) do
    proceduralShapeRegistration[key] = {
        key = key,
        itemId = itemId,
        itemGuid = "",
        category = "",
        equipmentSlot = "",
        previewValid = false,
        blueprintMappingFound = false,
        blueprintDimensions = "",
        registryLinkBefore = false,
        registryLinkAdded = false,
        registryLinkAfter = false,
        validationPassed = false,
        failureReason = "notEvaluated",
        donorItemId = 0,
        donorDebugName = ""
    }
end
-- Category prototype gate. No category mutation is performed until a
-- supported Hammer menu/category resource is evidenced by the audit below.
-- Keeping this true exercises the fail-closed path and makes the intended
-- future experiment explicit without risking ItemInfo/UI corruption.
local architectHammerCategoryEnabled = true
local backendRegistryLinksSuppressed = 0
local backendRegistryLinksAlreadyPresent = 0
local cleanupNotes = {}
local ringItemRegistryExperiment = {
    ringItemId = EXPERIMENTAL_RING_ITEM_ID,
    ringItemGuid = "",
    ringItemRegistryLinkPresentBefore = false,
    ringItemRegistryLinkAdded = false,
    ringItemRegistryLinkPresentAfter = false,
    failureReason = ""
}

local ringFinalIdentity = {
    itemId = EXPERIMENTAL_RING_ITEM_ID,
    guid = "",
    category = "",
    equipmentSlot = "",
    previewVoxelModel = "",
    blueprintRegistryIndex = -1,
    blueprintSize = "",
    exactRegistryLinkPresent = false,
    validationPassed = false,
    validationFailureReason = "notEvaluated"
}

local function inspectExactItemRegistryLink(itemResource, expectedItemId)
    local exactGuid = tostring(itemResource and itemResource.guid or "")
    local exactPresent = false
    local sameIdDifferentGuid = false

    for _, itemRef in ipairs(itemRegistry.itemRefs) do
        local ok, linked = pcall(function()
            return game.assets.get_resource(itemRef, "keen::ItemInfo", 0)
        end)

        if ok and linked and linked.data.itemId
            and linked.data.itemId.value == expectedItemId then
            if tostring(linked.guid or "") == exactGuid then
                exactPresent = true
            else
                sameIdDifferentGuid = true
            end
        end
    end

    return exactPresent, sameIdDifferentGuid
end

local function findExactRegisteredRingItem()
    local expectedGuid = tostring(ringItemRegistryExperiment.ringItemGuid or "")
    for _, itemRef in ipairs(itemRegistry.itemRefs or {}) do
        local ok, linked = pcall(function()
            return game.assets.get_resource(itemRef, "keen::ItemInfo", 0)
        end)
        if ok and linked and linked.data.itemId
            and linked.data.itemId.value == EXPERIMENTAL_RING_ITEM_ID
            and tostring(linked.guid or "") == expectedGuid then
            return linked
        end
    end
    return nil
end


-- ============================================================
-- Blueprint Registry
-- ============================================================

local blueprintRegistries =
    game.assets.get_resources_by_type(
        "keen::VoxelBlueprintItemRegistryResource"
    )

local blueprintRegistry =
    blueprintRegistries[1].data

-- Ring-only Construction Hammer donor experiment. This chooses an existing
-- vanilla blueprint ItemInfo only when its category differs from the Ceiling
-- donor and it has a real blueprint-registry mapping. No enum/category value
-- is invented and no UI collection is edited.
local experimentalRingHammerDonorEnabled = true
local ringHammerDonor = nil
local ringHammerDonorCandidates = {}
local ringHammerDonorAudit = {
    sourceCeilingCategory = "",
    selectedItemId = 0,
    selectedItemGuid = "",
    selectedDebugName = "",
    selectedCategory = "",
    selectedEquipmentSlot = "",
    selectionReason = "notEvaluated",
    metadataApplied = false,
    metadataApplicationReason = "notAttempted"
}

local function ringDonorText(value)
    local ok, result = pcall(function() return tostring(value or "") end)
    return ok and result or ""
end

local function ringDonorHasBlueprint(itemId)
    return findBlueprintByItemId(blueprintRegistry, itemId) ~= nil
end

local function ringDonorEquipmentSlot(item)
    return ringDonorText(item and item.data and item.data.equipment
        and item.data.equipment.slot)
end

local function ringDonorHasValidPreview(item)
    local voxelRef = item and item.data and item.data.equipment
        and item.data.equipment.voxelObject
    if not voxelRef or tostring(voxelRef) == "" then return false end
    local ok, voxel = pcall(function()
        return game.assets.get_resource(voxelRef, "keen::VoxelModelResource", 0)
    end)
    return ok and voxel ~= nil and voxel.data ~= nil and voxel.data.size ~= nil
end

local function discoverRingHammerDonor()
    local ceiling = findItemById(SOURCE_CEILING_ID)
    local ceilingCategory = ringDonorText(ceiling and ceiling.data.category)
    ringHammerDonorAudit.sourceCeilingCategory = ceilingCategory

    if not experimentalRingHammerDonorEnabled then
        ringHammerDonorAudit.selectionReason = "experimentDisabled"
        return nil
    end

    local ok, items = pcall(function()
        return game.assets.get_resources_by_type("keen::ItemInfo")
    end)
    if not ok or not items then
        ringHammerDonorAudit.selectionReason = "itemInfoEnumerationFailed"
        return nil
    end

    for _, item in ipairs(items) do
        local id = item.data.itemId and item.data.itemId.value or 0
        local name = ringDonorText(item.data.debugName)
        local category = ringDonorText(item.data.category)
        local equipmentSlot = ringDonorEquipmentSlot(item)
        local lowerName = string.lower(name)
        local wallScore = nil
        if string.find(lowerName, "wide wall", 1, true) then
            wallScore = 0
        elseif string.find(lowerName, "widewall", 1, true) then
            wallScore = 1
        elseif string.find(lowerName, "wall", 1, true) then
            wallScore = 2
        end

        -- Shape blueprints are structurally distinct from building materials:
        -- materials use BlueprintMaterial_* / BuildTools and are never Ring
        -- donors, regardless of their debug name. A wall name is only a
        -- secondary preference among proven BuildTool/Blueprint entries.
        if id ~= SOURCE_CEILING_ID and category == "Blueprints"
            and equipmentSlot == "BuildTool" and ringDonorHasBlueprint(id)
            and ringDonorHasValidPreview(item) then
            table.insert(ringHammerDonorCandidates, {
                item = item,
                itemId = id,
                debugName = name,
                category = category,
                equipmentSlot = equipmentSlot,
                -- Name is a secondary tie-breaker only. Any structurally
                -- proven geometric blueprint is safer than a material item.
                score = wallScore or 10
            })
        end
    end

    table.sort(ringHammerDonorCandidates, function(a, b)
        if a.score ~= b.score then return a.score < b.score end
        return a.itemId < b.itemId
    end)

    if #ringHammerDonorCandidates == 0 then
        ringHammerDonorAudit.selectionReason = "noMappedBuildToolBlueprintDonorFound"
        return nil
    end

    local chosen = ringHammerDonorCandidates[1]
    ringHammerDonorAudit.selectedItemId = chosen.itemId
    ringHammerDonorAudit.selectedItemGuid = ringDonorText(chosen.item.guid)
    ringHammerDonorAudit.selectedDebugName = chosen.debugName
    ringHammerDonorAudit.selectedCategory = chosen.category
    ringHammerDonorAudit.selectedEquipmentSlot = chosen.equipmentSlot
    ringHammerDonorAudit.selectionReason = "existingMappedBuildToolBlueprintDonor"
    return chosen.item
end

ringHammerDonor = discoverRingHammerDonor()

-- Registration is deliberately performed only after the shape ItemInfo and
-- its VoxelBlueprintItem entry both exist. This is the proven Ring ordering.
local function proceduralPreviewIsValid(itemResource)
    local voxelRef = itemResource and itemResource.data
        and itemResource.data.equipment
        and itemResource.data.equipment.voxelObject
    if not voxelRef or tostring(voxelRef) == "" then return false end
    local ok, voxel = pcall(function()
        return game.assets.get_resource(voxelRef, "keen::VoxelModelResource", 0)
    end)
    return ok and voxel ~= nil and voxel.data ~= nil and voxel.data.size ~= nil
end

local function proceduralBlueprintDimensions(blueprint)
    if not blueprint or not blueprint.size then return "" end
    local x, y, z = blueprint.size.x, blueprint.size.y, blueprint.size.z
    if type(x) ~= "number" or type(y) ~= "number" or type(z) ~= "number"
        or x <= 0 or y <= 0 or z <= 0 then
        return ""
    end
    return tostring(x) .. "x" .. tostring(y) .. "x" .. tostring(z)
end

local function proceduralItemInfoIdentityIsUnique(itemResource, expectedItemId)
    local expectedGuid = tostring(itemResource and itemResource.guid or "")
    local ok, allItemInfos = pcall(function()
        return game.assets.get_resources_by_type("keen::ItemInfo")
    end)
    if not ok or not allItemInfos then
        return false, "itemInfoIdentityEnumerationFailed"
    end
    for _, candidate in ipairs(allItemInfos) do
        local candidateId = candidate.data and candidate.data.itemId
            and candidate.data.itemId.value
        if candidateId == expectedItemId
            and tostring(candidate.guid or "") ~= expectedGuid then
            return false, "conflictingItemInfoWithSameItemIdDifferentGuid"
        end
    end
    return true, ""
end

local function registerValidatedProceduralShape(def, itemResource, blueprint)
    local result = proceduralShapeRegistration[def.key]
    local expectedItemId = proceduralShapeExpectedItemIds[def.key]
    if not result or not expectedItemId then return false end

    result.itemGuid = tostring(itemResource and itemResource.guid or "")
    result.category = ringDonorText(itemResource and itemResource.data
        and itemResource.data.category)
    result.equipmentSlot = ringDonorEquipmentSlot(itemResource)
    result.previewValid = proceduralPreviewIsValid(itemResource)
    result.blueprintDimensions = proceduralBlueprintDimensions(blueprint)
    result.donorItemId = ringHammerDonorAudit.selectedItemId
    result.donorDebugName = ringHammerDonorAudit.selectedDebugName
    result.blueprintMappingFound = blueprint ~= nil and blueprint.itemId ~= nil
        and blueprint.itemId.value == expectedItemId

    if def.key == "ring_4m" and not experimentalRegisterRingInItemRegistry then
        result.failureReason = "ringRegistrationExperimentDisabled"
        return false
    end
    if not experimentalRegisterProceduralShapesInItemRegistry then
        result.failureReason = "proceduralRegistrationExperimentDisabled"
        return false
    end
    if not itemResource or not itemResource.data or not itemResource.data.itemId
        or itemResource.data.itemId.value ~= expectedItemId then
        result.failureReason = "itemInfoIdDoesNotMatchDeterministicExpectedId"
        return false
    end
    if expectedItemId ~= ARCHITECT_CARRIER_ITEM_ID then
        result.failureReason = "carrierItemIdMismatch"
        return false
    end
    if result.itemGuid == "" then
        result.failureReason = "itemInfoGuidMissing"
        return false
    end
    local identityUnique, identityFailureReason =
        proceduralItemInfoIdentityIsUnique(itemResource, expectedItemId)
    if not identityUnique then
        result.failureReason = identityFailureReason
        return false
    end
    if result.category ~= "Blueprints" then
        result.failureReason = "itemInfoCategoryIsNotBlueprints"
        return false
    end
    if result.equipmentSlot ~= "BuildTool" then
        result.failureReason = "itemInfoEquipmentSlotIsNotBuildTool"
        return false
    end
    if not result.previewValid then
        result.failureReason = "previewVoxelModelInvalid"
        return false
    end
    if not result.blueprintMappingFound then
        result.failureReason = "blueprintItemIdMappingMissingOrMismatched"
        return false
    end
    if result.blueprintDimensions == "" then
        result.failureReason = "blueprintDimensionsInvalid"
        return false
    end

    local presentBefore, idCollision =
        inspectExactItemRegistryLink(itemResource, expectedItemId)
    result.registryLinkBefore = presentBefore
    if idCollision then
        result.failureReason = "differentItemInfoWithSameItemIdAlreadyLinked"
        return false
    end
    if not presentBefore then
        local ok, err = pcall(function()
            table.insert(itemRegistry.itemRefs, itemResource)
        end)
        if not ok then
            result.failureReason = "itemRegistryAppendFailed: " .. tostring(err)
            return false
        end
        result.registryLinkAdded = true
    end
    result.registryLinkAfter =
        select(1, inspectExactItemRegistryLink(itemResource, expectedItemId))
    result.validationPassed = result.registryLinkAfter
    result.failureReason = result.validationPassed and ""
        or "exactItemRegistryLinkNotResolvableAfterAppend"

    if def.key == "ring_4m" then
        ringItemRegistryExperiment.ringItemGuid = result.itemGuid
        ringItemRegistryExperiment.ringItemRegistryLinkPresentBefore =
            result.registryLinkBefore
        ringItemRegistryExperiment.ringItemRegistryLinkAdded =
            result.registryLinkAdded
        ringItemRegistryExperiment.ringItemRegistryLinkPresentAfter =
            result.registryLinkAfter
        ringItemRegistryExperiment.failureReason = result.failureReason
    end
    return result.validationPassed
end


-- ============================================================
-- Blueprint Generator
-- ============================================================

local function registerBlueprint(def)

    print(
        "Architect Toolkit: generating "
        .. def.key
    )

    local newItemId = ARCHITECT_CARRIER_ITEM_ID

    if itemIdExists(newItemId) then
        local existingItem = findItemById(newItemId)
        local existingBlueprint =
            findBlueprintByItemId(
                blueprintRegistry,
                newItemId
            )
        print(
            "Architect Toolkit: deterministic backend item already exists: "
            .. tostring(newItemId)
        )
        table.insert(
            cleanupNotes,
            "cached backend resource retained: " .. def.key
        )
        for _, itemRef in ipairs(itemRegistry.itemRefs) do
            local ok, linked = pcall(function()
                return game.assets.get_resource(itemRef, "keen::ItemInfo", 0)
            end)
            if ok and linked and linked.data.itemId
                and linked.data.itemId.value == newItemId then
                backendRegistryLinksAlreadyPresent =
                    backendRegistryLinksAlreadyPresent + 1
            end
        end
        local cachedRegistrationPassed =
            registerValidatedProceduralShape(def, existingItem, existingBlueprint)
        if def.key == "ring_4m" and existingItem then
            local cachedSlot = ringDonorEquipmentSlot(existingItem)
            local cachedCategory = ringDonorText(existingItem.data.category)
            local cachedBlueprint = findBlueprintByItemId(blueprintRegistry, newItemId)
            ringFinalIdentity.guid = tostring(existingItem.guid or "")
            ringFinalIdentity.category = cachedCategory
            ringFinalIdentity.equipmentSlot = cachedSlot
            ringFinalIdentity.previewVoxelModel = ringDonorText(
                existingItem.data.equipment and existingItem.data.equipment.voxelObject)
            if cachedRegistrationPassed and cachedCategory == "Blueprints"
                and cachedSlot == "BuildTool" and cachedBlueprint then
                ringFinalIdentity.exactRegistryLinkPresent =
                    findExactRegisteredRingItem() ~= nil
                ringFinalIdentity.validationPassed =
                    ringFinalIdentity.exactRegistryLinkPresent
                ringFinalIdentity.validationFailureReason =
                    ringFinalIdentity.validationPassed and ""
                    or "ringExactItemRegistryLinkMissingAfterCachedValidation"
            else
                ringFinalIdentity.validationFailureReason =
                    proceduralShapeRegistration[def.key].failureReason
            end
        end
        return {
            key = def.key,
            itemId = newItemId,
            itemGuid = existingItem and tostring(existingItem.guid) or "",
            voxelGuid = "",
            previewBytes = 0,
            placementBytes = 0,
            renderStatus = existingBlueprint and "CACHED BACKEND RESOURCE" or "CACHED ITEM WITHOUT BLUEPRINT"
        }
    end

    -- --------------------------------------------------------
    -- Separate templates:
    --
    -- itemTemplateId:
    --   ItemInfo we clone. For 3D tests we deliberately keep
    --   using the already-proven ceiling ItemInfo.
    --
    -- blueprintTemplateId:
    --   Native blueprint entry with the SAME voxel dimensions.
    --
    -- previewTemplateId:
    --   Native item whose voxelObject has matching dimensions.
    -- --------------------------------------------------------

    local itemTemplateId = SOURCE_CEILING_ID
    local blueprintTemplateId = SOURCE_CEILING_ID
    local previewTemplateId = SOURCE_CEILING_ID

    -- Use the structurally qualified geometric BuildTool donor for every
    -- player-facing procedural shape. If discovery failed, retain the legacy
    -- template but validation below will refuse ItemRegistry registration.
    local itemTemplate = ringHammerDonor or findItemById(itemTemplateId)

    local previewTemplate =
        findItemById(previewTemplateId)

    if not itemTemplate then
        print("Architect Toolkit: item template not found.")
        return nil
    end

    if not previewTemplate then
        print("Architect Toolkit: preview template not found.")
        return nil
    end

    local sourceBlueprint =
        findBlueprintByItemId(
            blueprintRegistry,
            blueprintTemplateId
        )

    if not sourceBlueprint then
        print("Architect Toolkit: blueprint template not found.")
        return nil
    end

    local requestedVoxelCount = def.sizeX * def.sizeY * def.sizeZ
    if requestedVoxelCount ~= ARCHITECT_CARRIER_VOXEL_COUNT then
        print(
            "Architect Toolkit: SKIP "
            .. def.key
            .. " - carrier requires exactly "
            .. tostring(ARCHITECT_CARRIER_VOXEL_COUNT)
            .. " voxels."
        )
        return nil
    end

    local predicate =
        def.shape(
            def.sizeX,
            def.sizeY,
            def.sizeZ
        )

    local previewData =
        generatePreviewData(
            def.sizeX,
            def.sizeY,
            def.sizeZ,
            predicate
        )

    local placementData =
        generateCompressedData(
            def.sizeX,
            def.sizeY,
            def.sizeZ,
            predicate
        )

    -- --------------------------------------------------------
    -- Safe Lua backend gate
    -- --------------------------------------------------------

    if #placementData > MAX_SAFE_EML_PLACEMENT_BYTES then

        print(
            "Architect Toolkit: "
            .. def.key
            .. " requires large-shape backend ("
            .. tostring(#placementData)
            .. " placement bytes > safe Lua limit "
            .. tostring(MAX_SAFE_EML_PLACEMENT_BYTES)
            .. "). Skipping safely."
        )

        return nil
    end

    -- --------------------------------------------------------
    -- Preview handling
    --
    -- Critical allocator safety rule:
    -- NEVER replace a native dynamic array with a fresh Lua
    -- table for the 3D path. Reuse native backing storage and
    -- mutate elements in-place.
    --
    -- For 3D, we currently share a native same-size preview.
    -- For the already-proven 2D path, we may clone and mutate
    -- the VoxelModelResource in-place.
    -- --------------------------------------------------------

    local previewVoxelRef =
        previewTemplate.data.equipment.voxelObject

    local previewVoxel =
        game.assets.get_resource(
            previewVoxelRef,
            "keen::VoxelModelResource",
            0
        )

    if not previewVoxel then
        print("Architect Toolkit: preview voxel model not found.")
        return nil
    end

    local sourcePreviewCount = 0
    for _ in ipairs(previewVoxel.data.data or {}) do
        sourcePreviewCount = sourcePreviewCount + 1
    end
    if sourcePreviewCount ~= ARCHITECT_CARRIER_VOXEL_COUNT then
        print(
            "Architect Toolkit: SKIP "
            .. def.key
            .. " - carrier preview backing length mismatch: "
            .. tostring(sourcePreviewCount)
        )
        return nil
    end

    local customVoxel = nil
    local renderStatus = "SHARED NATIVE PREVIEW"

    if def.clonePreview ~= false then

        customVoxel =
            game.assets.create_resource(
                previewVoxel.data,
                "keen::VoxelModelResource"
            )

        local previewCount = 0
        for _ in ipairs(customVoxel.data.data) do
            previewCount = previewCount + 1
        end

        if previewCount ~= #previewData then
            print(
                "Architect Toolkit: SKIP "
                .. def.key
                .. " - preview data length mismatch."
            )
            return nil
        end

        customVoxel.data.size.x = def.sizeX
        customVoxel.data.size.y = def.sizeY
        customVoxel.data.size.z = def.sizeZ

        for i, value in ipairs(previewData) do
            customVoxel.data.data[i] = value
        end

        customVoxel.data.isTerrain = false

        local sourceRender =
            game.assets.get_resource(
                previewVoxelRef,
                "keen::RenderModel",
                0
            )

        if sourceRender then

            local ok, result =
                pcall(function()

                    return game.assets.create_resource(
                        sourceRender.data,
                        "keen::RenderModel",
                        customVoxel.guid,
                        0
                    )

                end)

            if ok then
                renderStatus = "CREATED"
            else
                renderStatus =
                    "FAILED: "
                    .. tostring(result)
            end
        else
            renderStatus = "SOURCE RENDER NOT FOUND"
        end
    end

    -- --------------------------------------------------------
    -- Create ItemInfo from the proven-safe item template.
    -- --------------------------------------------------------

    local newItem =
        game.assets.create_resource(
            itemTemplate.data,
            "keen::ItemInfo"
        )

    newItem.data.itemId.value =
        newItemId

    newItem.data.debugName =
        ARCHITECT_CARRIER_DEBUG_NAME

    if ringHammerDonor then
        -- The clone carries only an existing donor's already-known Hammer UI
        -- metadata (category, icon, object/visual relations). The Ring then
        -- restores its own deterministic identity and voxel preview below.
        ringHammerDonorAudit.metadataApplied = true
        ringHammerDonorAudit.metadataApplicationReason =
            "clonedExistingMappedVanillaWallItemInfo"
    elseif def.key == "ring_4m" then
        ringHammerDonorAudit.metadataApplicationReason =
            "noSafeMappedNonCeilingWallDonor"
    end

    if customVoxel then
        newItem.data.equipment.voxelObject =
            customVoxel
    else
        -- Share the native same-size voxel preview for now.
        newItem.data.equipment.voxelObject =
            previewTemplate.data.equipment.voxelObject
    end

    -- Resize placement/snapping bounds.
    local metersPerVoxel = 0.5

    local worldX = def.sizeX * metersPerVoxel
    local worldY = def.sizeY * metersPerVoxel
    local worldZ = def.sizeZ * metersPerVoxel

    newItem.data.equipment.placementAABBmin.x = 0
    newItem.data.equipment.placementAABBmin.y = 0
    newItem.data.equipment.placementAABBmin.z = 0

    newItem.data.equipment.placementAABBmax.x = worldX
    newItem.data.equipment.placementAABBmax.y = worldY
    newItem.data.equipment.placementAABBmax.z = worldZ

    newItem.data.equipment.snappingAABBmin.x = 0
    newItem.data.equipment.snappingAABBmin.y = 0
    newItem.data.equipment.snappingAABBmin.z = 0

    newItem.data.equipment.snappingAABBmax.x = worldX
    newItem.data.equipment.snappingAABBmax.y = worldY
    newItem.data.equipment.snappingAABBmax.z = worldZ

    -- --------------------------------------------------------
    -- Validate the native blueprint payload BEFORE registering
    -- anything. If this fails, we leave no partially inserted item.
    -- --------------------------------------------------------

    local nativePlacementCount = 0

    for _ in ipairs(sourceBlueprint.data) do
        nativePlacementCount =
            nativePlacementCount + 1
    end

    if nativePlacementCount ~= #placementData then
        print(
            "Architect Toolkit: SKIP "
            .. def.key
            .. " - placement data length mismatch: native="
            .. tostring(nativePlacementCount)
            .. " generated="
            .. tostring(#placementData)
        )
        return nil
    end

    -- Registration occurs only after the matching blueprint entry is present
    -- and all ItemInfo identity checks pass. No direct/unchecked append path.
    local deferProceduralRegistration =
        proceduralShapeExpectedItemIds[def.key] ~= nil
    if not deferProceduralRegistration then
        backendRegistryLinksSuppressed = backendRegistryLinksSuppressed + 1
    end

    -- --------------------------------------------------------
    -- Clone native same-size blueprint entry.
    -- --------------------------------------------------------

    local count = 0
    for _ in ipairs(
        blueprintRegistry.blueprintItems
    ) do
        count = count + 1
    end

    table.insert(
        blueprintRegistry.blueprintItems,
        sourceBlueprint
    )

    local newBlueprint =
        blueprintRegistry.blueprintItems[
            count + 1
        ]

    newBlueprint.itemId.value =
        newItemId

    newBlueprint.size.x = def.sizeX
    newBlueprint.size.y = def.sizeY
    newBlueprint.size.z = def.sizeZ

    -- Mutate the cloned native payload in-place. The carrier catalog is
    -- deliberately restricted to 64-voxel shapes, so this remains exactly
    -- the donor's proven 8-byte backing length and does not resize it.
    for i, value in ipairs(placementData) do
        newBlueprint.data[i] = value
    end

    newBlueprint.isDataCompressed = true

    if deferProceduralRegistration then
        local registrationPassed =
            registerValidatedProceduralShape(def, newItem, newBlueprint)
    end

    if def.key == "ring_4m" then
        local blueprintIndex = -1
        local finalSlot = ringDonorEquipmentSlot(newItem)
        local finalCategory = ringDonorText(newItem.data.category)
        local finalVoxel = ringDonorText(newItem.data.equipment
            and newItem.data.equipment.voxelObject)
        for index, blueprint in ipairs(blueprintRegistry.blueprintItems or {}) do
            if blueprint.itemId and blueprint.itemId.value == EXPERIMENTAL_RING_ITEM_ID then
                blueprintIndex = index
                break
            end
        end

        ringFinalIdentity.guid = tostring(newItem.guid or "")
        ringFinalIdentity.category = finalCategory
        ringFinalIdentity.equipmentSlot = finalSlot
        ringFinalIdentity.previewVoxelModel = finalVoxel
        ringFinalIdentity.blueprintRegistryIndex = blueprintIndex
        ringFinalIdentity.blueprintSize = tostring(newBlueprint.size.x) .. "x"
            .. tostring(newBlueprint.size.y) .. "x" .. tostring(newBlueprint.size.z)

        if newItem.data.itemId.value ~= EXPERIMENTAL_RING_ITEM_ID then
            ringFinalIdentity.validationFailureReason = "ringItemIdMismatch"
        elseif finalCategory ~= "Blueprints" then
            ringFinalIdentity.validationFailureReason = "ringCategoryIsNotBlueprints"
        elseif finalSlot ~= "BuildTool" then
            ringFinalIdentity.validationFailureReason = "ringEquipmentSlotIsNotBuildTool"
        elseif finalVoxel == "" then
            ringFinalIdentity.validationFailureReason = "ringPreviewVoxelMissing"
        elseif blueprintIndex < 0 then
            ringFinalIdentity.validationFailureReason = "ringBlueprintRegistryMappingMissing"
        else
            ringFinalIdentity.exactRegistryLinkPresent =
                findExactRegisteredRingItem() ~= nil
            if ringFinalIdentity.exactRegistryLinkPresent then
                ringFinalIdentity.validationPassed = true
                ringFinalIdentity.validationFailureReason = ""
            else
                ringFinalIdentity.validationFailureReason =
                    "ringExactItemRegistryLinkMissingAfterAppend"
            end
        end
    end

    return {

        key =
            def.key,

        itemId =
            newItemId,

        itemGuid =
            tostring(newItem.guid),

        voxelGuid =
            customVoxel
            and tostring(customVoxel.guid)
            or tostring(previewVoxel.guid),

        previewBytes =
            #previewData,

        placementBytes =
            #placementData,

        renderStatus =
            renderStatus

    }
end


-- ============================================================
-- Blueprint Definitions
-- ============================================================

local definitions = {

    -- --------------------------------------------------------
    -- Proven 2D shapes
    -- --------------------------------------------------------

    {
        key =
            "hollow_ceiling_4m",

        debugName =
            "ArchitectToolkit_Blueprint_HollowCeiling_4m",

        sourceItemId =
            SOURCE_CEILING_ID,

        sizeX = 8,
        sizeY = 1,
        sizeZ = 8,

        shape =
            Shapes.hollowRectangle
    },

    {
        key =
            "filled_circle_4m",

        debugName =
            "ArchitectToolkit_Blueprint_FilledCircle_4m",

        sourceItemId =
            SOURCE_CEILING_ID,

        sizeX = 8,
        sizeY = 1,
        sizeZ = 8,

        shape =
            Shapes.filledCircle
    },

    {
        key =
            "ring_4m",

        debugName =
            "ArchitectToolkit_Blueprint_Ring_4m",

        sourceItemId =
            SOURCE_CEILING_ID,

        sizeX = 8,
        sizeY = 1,
        sizeZ = 8,

        shape =
            Shapes.ring
    },

    {
        key =
            "cross_4m",

        debugName =
            "ArchitectToolkit_Blueprint_Cross_4m",

        sourceItemId =
            SOURCE_CEILING_ID,

        sizeX = 8,
        sizeY = 1,
        sizeZ = 8,

        shape =
            Shapes.cross
    },

    {
        key =
            "diamond_4m",

        debugName =
            "ArchitectToolkit_Blueprint_Diamond_4m",

        sourceItemId =
            SOURCE_CEILING_ID,

        sizeX = 8,
        sizeY = 1,
        sizeZ = 8,

        shape =
            Shapes.diamond
    },

    {
        key =
            "diagonal_cross_4m",

        debugName =
            "ArchitectToolkit_Blueprint_DiagonalCross_4m",

        sourceItemId =
            SOURCE_CEILING_ID,

        sizeX = 8,
        sizeY = 1,
        sizeZ = 8,

        shape =
            Shapes.diagonalCross
    },

    -- --------------------------------------------------------
    -- Safe Lua 3D backend
    --
    -- 4x4x4 = 64 voxels = 8 compressed placement bytes.
    -- These use a native 4x4x4 blueprint + preview template.
    --
    -- clonePreview = true:
    -- we clone the same-size native VoxelModelResource and
    -- mutate its 64 preview values in place. The existing 2D
    -- preview path has already proven a 64-value preview array
    -- can be cloned safely.
    -- --------------------------------------------------------

    {
        key =
            "sphere_2m",

        debugName =
            "ArchitectToolkit_Blueprint_Sphere_2m",

        sourceItemId =
            SOURCE_CEILING_ID,

        itemTemplateId =
            SOURCE_CEILING_ID,

        blueprintTemplateId =
            SOURCE_4X4X4_ID,

        previewTemplateId =
            SOURCE_4X4X4_ID,

        clonePreview = true,

        sizeX = 4,
        sizeY = 4,
        sizeZ = 4,

        shape =
            Shapes.sphere
    },

    {
        key =
            "filled_cylinder_2m",

        debugName =
            "ArchitectToolkit_Blueprint_FilledCylinder_2m",

        sourceItemId =
            SOURCE_CEILING_ID,

        itemTemplateId =
            SOURCE_CEILING_ID,

        blueprintTemplateId =
            SOURCE_4X4X4_ID,

        previewTemplateId =
            SOURCE_4X4X4_ID,

        clonePreview = true,

        sizeX = 4,
        sizeY = 4,
        sizeZ = 4,

        shape =
            Shapes.filledCylinder
    },

    {
        key =
            "hollow_cube_2m",

        debugName =
            "ArchitectToolkit_Blueprint_HollowCube_2m",

        sourceItemId =
            SOURCE_CEILING_ID,

        itemTemplateId =
            SOURCE_CEILING_ID,

        blueprintTemplateId =
            SOURCE_4X4X4_ID,

        previewTemplateId =
            SOURCE_4X4X4_ID,

        clonePreview = true,

        sizeX = 4,
        sizeY = 4,
        sizeZ = 4,

        shape =
            Shapes.hollowBox
    },

    {
        key =
            "stairs_2m",

        debugName =
            "ArchitectToolkit_Blueprint_Stairs_2m",

        sourceItemId =
            SOURCE_CEILING_ID,

        itemTemplateId =
            SOURCE_CEILING_ID,

        blueprintTemplateId =
            SOURCE_4X4X4_ID,

        previewTemplateId =
            SOURCE_4X4X4_ID,

        clonePreview = true,

        sizeX = 4,
        sizeY = 4,
        sizeZ = 4,

        shape =
            Shapes.stairs
    },

    {
        key =
            "pyramid_2m",

        debugName =
            "ArchitectToolkit_Blueprint_Pyramid_2m",

        sourceItemId =
            SOURCE_CEILING_ID,

        itemTemplateId =
            SOURCE_CEILING_ID,

        blueprintTemplateId =
            SOURCE_4X4X4_ID,

        previewTemplateId =
            SOURCE_4X4X4_ID,

        clonePreview = true,

        sizeX = 4,
        sizeY = 4,
        sizeZ = 4,

        shape =
            Shapes.pyramid
    },

    {
        key =
            "archway_2m",

        debugName =
            "ArchitectToolkit_Blueprint_Archway_2m",

        sourceItemId =
            SOURCE_CEILING_ID,

        itemTemplateId =
            SOURCE_CEILING_ID,

        blueprintTemplateId =
            SOURCE_4X4X4_ID,

        previewTemplateId =
            SOURCE_4X4X4_ID,

        clonePreview = true,

        sizeX = 4,
        sizeY = 4,
        sizeZ = 4,

        shape =
            Shapes.archway
    }

}


local definitionByKey = {}
for _, definition in ipairs(definitions) do
    definitionByKey[definition.key] = definition
end

local activeDefinition = definitionByKey[ACTIVE_ARCHITECT_SHAPE_KEY]
if not activeDefinition then
    print(
        "Architect Toolkit: unknown carrier shape '"
        .. tostring(ACTIVE_ARCHITECT_SHAPE_KEY)
        .. "'; falling back to "
        .. ARCHITECT_DEFAULT_SHAPE_KEY
    )
    ACTIVE_ARCHITECT_SHAPE_KEY = ARCHITECT_DEFAULT_SHAPE_KEY
    activeDefinition = definitionByKey[ACTIVE_ARCHITECT_SHAPE_KEY]
end

-- ============================================================
-- Generate everything
-- ============================================================

local generated = {}

if activeDefinition then
    local result = registerBlueprint(activeDefinition)
    if result then
        table.insert(generated, result)
    end
end


-- ============================================================
-- Diagnostics
-- ============================================================

local output = {}

table.insert(
    output,
    "ARCHITECT TOOLKIT - SINGLE BLUEPRINT CARRIER - EXPERIMENTAL"
)
table.insert(output, "Carrier Item ID: " .. tostring(ARCHITECT_CARRIER_ITEM_ID))
table.insert(output, "Active Shape: " .. tostring(ACTIVE_ARCHITECT_SHAPE_KEY))
table.insert(output, "Config Loaded: " .. tostring(architectCarrierConfigLoaded))
if architectCarrierConfigError ~= "" then
    table.insert(output, "Config Error: " .. architectCarrierConfigError)
end

table.insert(
    output,
    "Generated: "
    .. tostring(#generated)
)

for _, result in ipairs(generated) do

    table.insert(
        output,
        ""
    )

    table.insert(
        output,
        "KEY: "
        .. result.key
    )

    table.insert(
        output,
        "ITEM ID: "
        .. tostring(result.itemId)
    )

    table.insert(
        output,
        "ITEM GUID: "
        .. result.itemGuid
    )

    table.insert(
        output,
        "VOXEL GUID: "
        .. result.voxelGuid
    )

    table.insert(
        output,
        "PREVIEW VALUES: "
        .. tostring(result.previewBytes)
    )

    table.insert(
        output,
        "PLACEMENT BYTES: "
        .. tostring(result.placementBytes)
    )

    table.insert(
        output,
        "RENDER COMPANION: "
        .. result.renderStatus
    )

end


io.export(
    "architect_toolkit/blueprint_generator_v1.txt",
    table.concat(
        output,
        "\n"
    )
)


print(
    "Architect Toolkit: Blueprint Generator v1 complete!"
)

local carrierState = {}
table.insert(carrierState, "{")
table.insert(carrierState, "  \"version\": \"single_blueprint_carrier_v1\",")
table.insert(carrierState, "  \"carrierItemId\": " .. tostring(ARCHITECT_CARRIER_ITEM_ID) .. ",")
table.insert(carrierState, "  \"carrierDebugName\": \"" .. ARCHITECT_CARRIER_DEBUG_NAME .. "\",")
table.insert(carrierState, "  \"activeShapeKey\": \"" .. tostring(ACTIVE_ARCHITECT_SHAPE_KEY) .. "\",")
table.insert(carrierState, "  \"configLoaded\": " .. tostring(architectCarrierConfigLoaded) .. ",")
table.insert(carrierState, "  \"catalogCount\": " .. tostring(#definitions) .. ",")
table.insert(carrierState, "  \"registeredCarrierCount\": " .. tostring(#generated) .. ",")
table.insert(carrierState, "  \"liveShapeSwapSupported\": false,")
table.insert(carrierState, "  \"selectionRequiresRestart\": true,")
table.insert(carrierState, "  \"nativeRuntimeModified\": false")
table.insert(carrierState, "}")
io.export("architect_toolkit/single_blueprint_carrier_state.json", table.concat(carrierState, "\n"))


-- ============================================================
-- Architect's Wand v0.9
-- ============================================================
--
-- First standalone Architect Toolkit control item.
--
-- Behavior source:
--   Tool_Quickbuilder_Hammer / item 693164685
--
-- Development obtain path:
--   Clone the native zero-cost Workbench Quickbuilder recipe.
--
-- v0.1 goals:
--   * independent ItemInfo / deterministic item id
--   * independent name + description LocaTags
--   * retain proven native Quickbuilder BuildTool behavior
--   * retain native hammer icon / visual for now
--   * craftable from the Workbench for development testing
--   * tertiary action continues to open UiBuildingMenu for now
--
-- The custom Architect menu will replace/intercept that UI action
-- in a later runtime layer. The single Architect carrier above remains
-- registered as the safe procedural backend while we build that UI.
-- ============================================================

-- v0.9 uses a normal vanilla weapon wand as the ACTUAL item base.
-- No Quickbuilder Hammer identity.
-- No NpcSummoner_Intro identity.
--
-- Weapon_T1_1H_Wand_01_Fire
local ARCHITECT_WAND_SOURCE_ITEM_ID = 1693828837

-- Temporary development obtain path only: reuse the known
-- Workbench Quickbuilder recipe shell, retargeted to our item.
local ARCHITECT_WAND_SOURCE_RECIPE_ID = 2390259004

-- Source and visual donor are intentionally the same now.
local ARCHITECT_WAND_VISUAL_DONOR_ITEM_ID = 1693828837

local ARCHITECT_WAND_ITEM_ID =
    hasher.fnv1a32(
        "architect_toolkit:architect_wand"
    )

local ARCHITECT_WAND_RECIPE_ID =
    hasher.fnv1a32(
        "architect_toolkit:recipe_architect_wand_workbench"
    )

local function architectFindItemById(itemId)
    local items =
        game.assets.get_resources_by_type(
            "keen::ItemInfo"
        )

    for _, item in ipairs(items) do
        if item.data.itemId
            and item.data.itemId.value == itemId then
            return item
        end
    end

    return nil
end

local function architectFindMainItemRegistry()
    local registries =
        game.assets.get_resources_by_type(
            "keen::ItemRegistryResource"
        )

    local best = nil
    local bestCount = -1

    for _, registry in ipairs(registries) do
        local count = 0
        for _ in ipairs(registry.data.itemRefs) do
            count = count + 1
        end

        if count > bestCount then
            best = registry
            bestCount = count
        end
    end

    return best
end

local function architectFindMainRecipeRegistry()
    local registries =
        game.assets.get_resources_by_type(
            "keen::RecipeRegistryResource"
        )

    local best = nil
    local bestCount = -1

    for _, registry in ipairs(registries) do
        local count = 0
        for _ in ipairs(registry.data.recipes) do
            count = count + 1
        end

        if count > bestCount then
            best = registry
            bestCount = count
        end
    end

    return best
end

local function architectFindRegisteredItemById(registry, itemId)

    for _, itemRef in ipairs(registry.data.itemRefs) do

        local ok, item = pcall(function()

            return game.assets.get_resource(
                itemRef,
                "keen::ItemInfo",
                0
            )

        end)

        if ok and item
            and item.data.itemId
            and item.data.itemId.value == itemId then

            return item
        end
    end

    return nil
end


local function architectItemIdExists(registry, itemId)
    for _, itemRef in ipairs(registry.data.itemRefs) do
        local ok, item = pcall(function()
            return game.assets.get_resource(
                itemRef,
                "keen::ItemInfo",
                0
            )
        end)

        if ok and item
            and item.data.itemId
            and item.data.itemId.value == itemId then
            return true
        end
    end

    return false
end

local function architectRecipeIdExists(registry, recipeId)
    for _, recipe in ipairs(registry.data.recipes) do
        if recipe.recipeId
            and recipe.recipeId.value == recipeId then
            return true
        end
    end

    return false
end

local function architectFindRecipeById(registry, recipeId)
    for _, recipe in ipairs(registry.data.recipes) do
        if recipe.recipeId
            and recipe.recipeId.value == recipeId then
            return recipe
        end
    end

    return nil
end

local function architectCloneLocaTag(sourceRef, newText, newDescription)
    if not sourceRef then
        return nil
    end

    local okGet, source = pcall(function()
        return game.assets.get_resource(
            sourceRef,
            "keen::LocaTag",
            0
        )
    end)

    if not okGet or not source then
        return nil
    end

    local okCreate, clone = pcall(function()
        return game.assets.create_resource(
            source.data,
            "keen::LocaTag"
        )
    end)

    if not okCreate or not clone then
        return nil
    end

    clone.data.keenglish = newText

    if newDescription ~= nil then
        clone.data.description = newDescription
    end

    return clone
end

local function architectRegisterWand()

    print("Architect Toolkit: registering Architect's Wand v0.9...")

    local sourceItem =
        architectFindItemById(
            ARCHITECT_WAND_SOURCE_ITEM_ID
        )

    if not sourceItem then
        print("Architect Toolkit: native simple weapon wand source not found.")
        return nil
    end

    local visualDonor =
        architectFindItemById(
            ARCHITECT_WAND_VISUAL_DONOR_ITEM_ID
        )

    if not visualDonor then
        print("Architect Toolkit: Wand visual donor NpcSummoner_Intro not found.")
        return nil
    end

    local itemRegistry =
        architectFindMainItemRegistry()

    local recipeRegistry =
        architectFindMainRecipeRegistry()

    if not itemRegistry then
        print("Architect Toolkit: ItemRegistryResource not found for Wand.")
        return nil
    end

    if not recipeRegistry then
        print("Architect Toolkit: RecipeRegistryResource not found for Wand.")
        return nil
    end

    -- --------------------------------------------------------
    -- IMPORTANT:
    --
    -- EML can load our previously-generated deterministic item
    -- from its patched cache. Older builds returned immediately
    -- when that happened, which meant newer visual changes never
    -- touched the already-existing custom item.
    --
    -- v0.4 updates the existing Wand in place when present.
    -- --------------------------------------------------------

    local existingWand =
        architectFindRegisteredItemById(
            itemRegistry,
            ARCHITECT_WAND_ITEM_ID
        )

    local existingRecipe =
        architectFindRecipeById(
            recipeRegistry,
            ARCHITECT_WAND_RECIPE_ID
        )

    local sourceRecipe =
        architectFindRecipeById(
            recipeRegistry,
            ARCHITECT_WAND_SOURCE_RECIPE_ID
        )

    if not sourceRecipe then
        print("Architect Toolkit: source Workbench Quickbuilder recipe not found.")
        return nil
    end

    -- --------------------------------------------------------
    -- Independent display localization.
    -- --------------------------------------------------------

    local wandName =
        architectCloneLocaTag(
            sourceItem.data.name,
            "Architect's Wand",
            "Architect Toolkit item name"
        )

    local wandDescription =
        architectCloneLocaTag(
            sourceItem.data.description,
            "A precision building focus used by the Architect Toolkit.",
            "Architect Toolkit item description"
        )

    -- --------------------------------------------------------
    -- Clone the native Quickbuilder Hammer ItemInfo.
    -- Keep its objectId/icon/visual behavior for this first pass.
    -- --------------------------------------------------------

    local wand = existingWand
    local wandWasExisting = wand ~= nil

    if not wand then

        wand =
            game.assets.create_resource(
                sourceItem.data,
                "keen::ItemInfo"
            )

        wand.data.itemId.value =
            ARCHITECT_WAND_ITEM_ID

    end

    wand.data.debugName =
        "ArchitectToolkit_ArchitectsWand"

    -- Custom LocaTag creation is currently failing in EML.
    -- For v0.5, use the donor's already-valid localization refs as
    -- a temporary proof that this is no longer the Quickbuilder item.
    if wandName then
        wand.data.name = wandName
    else
        wand.data.name = visualDonor.data.name
    end

    if wandDescription then
        wand.data.description = wandDescription
    else
        wand.data.description = visualDonor.data.description
    end

    -- --------------------------------------------------------
    -- Hybridize appearance:
    --
    -- KEEP from Quickbuilder:
    --   category / BuildTool slot
    --   cursor + placement behavior
    --   UiBuildingMenu tertiary action
    --   all other building-tool mechanics
    --
    -- BORROW from NpcSummoner_Intro:
    --   wand-like icon
    --   equipped visual entity
    --   Wand animation set
    --
    -- We deliberately do NOT replace objectId yet. Earlier tests
    -- showed objectId changes can break item icon/render behavior.
    -- --------------------------------------------------------

    -- Critical v0.5 change:
    --
    -- Enshrouded's crafting/inventory presentation is evidently
    -- resolving the displayed object through ItemInfo.objectId.
    -- Direct icon/visual field changes applied correctly in the
    -- exported ItemInfo but the UI still rendered the hammer.
    --
    -- Point objectId at a complete, known-good vanilla wand-like
    -- object graph rather than at a newly generated GUID.
    -- v0.9 deliberately remains a normal weapon wand.
    -- This is the cleanest stable identity we have tested:
    -- source, object graph, category, slot, icon, visual and
    -- animation all come from the SAME vanilla item family.
    wand.data.objectId =
        sourceItem.data.objectId

    wand.data.category =
        sourceItem.data.category

    -- Weapon wand has a proper inventory icon model/scene.
    -- Its iconImage is zero, so keep the BuildTool base image only
    -- when the donor does not provide one.
    if tostring(visualDonor.data.iconImage)
        ~= "00000000-0000-0000-0000-000000000000" then

        wand.data.iconImage =
            visualDonor.data.iconImage
    end

    wand.data.iconModel =
        visualDonor.data.iconModel

    wand.data.iconScene =
        visualDonor.data.iconScene

    wand.data.equipment.visualEntity =
        visualDonor.data.equipment.visualEntity

    wand.data.equipment.visualModel =
        visualDonor.data.equipment.visualModel

    wand.data.equipment.primaryAnimationSet =
        visualDonor.data.equipment.primaryAnimationSet

    wand.data.equipment.secondaryAnimationSet =
        visualDonor.data.equipment.secondaryAnimationSet

    -- --------------------------------------------------------
    -- Keep the weapon wand's own native action hints untouched.
    --
    -- Architect Toolkit will open its custom build UI from our
    -- runtime hotkey/menu layer instead of trying to turn this
    -- ItemInfo into a BuildTool. That avoids Enshrouded replacing
    -- the item with a hammer or summoning tool.
    -- --------------------------------------------------------

    if not wandWasExisting then

        table.insert(
            itemRegistry.data.itemRefs,
            wand
        )

    end

    -- --------------------------------------------------------
    -- Clone the native zero-cost Workbench Quickbuilder recipe.
    -- Source recipe already has one placeholder zero-count input
    -- and one output. We preserve that structure and only retarget
    -- the output to the new Wand.
    -- --------------------------------------------------------

    local newRecipe = existingRecipe
    local recipeWasExisting = newRecipe ~= nil

    if not newRecipe then

        local recipeCount = 0

        for _ in ipairs(recipeRegistry.data.recipes) do
            recipeCount = recipeCount + 1
        end

        table.insert(
            recipeRegistry.data.recipes,
            sourceRecipe
        )

        newRecipe =
            recipeRegistry.data.recipes[
                recipeCount + 1
            ]

    end

    newRecipe.recipeId.value =
        ARCHITECT_WAND_RECIPE_ID

    newRecipe.debugName =
        "Recipe_ArchitectToolkit_ArchitectsWand_Workbench"

    if wandName then
        newRecipe.recipeName = wandName
    else
        newRecipe.recipeName = visualDonor.data.name
    end

    local outputCount = 0
    local wandOutput = nil

    for _, output in ipairs(newRecipe.output) do
        outputCount = outputCount + 1
        if outputCount == 1 then
            wandOutput = output
        end
    end

    if not wandOutput then
        print("Architect Toolkit: cloned Wand recipe has no output entry.")
        return nil
    end

    wandOutput.item.value =
        ARCHITECT_WAND_ITEM_ID

    wandOutput.itemRef =
        wand

    wandOutput.count = 1


    -- --------------------------------------------------------
    -- Workbench UI recipe-tree linkage
    --
    -- RecipeRegistryResource alone is not enough for the recipe
    -- browser. FbUiBundle contains a parallel crafting recipe tree
    -- whose sets explicitly list recipe IDs. Clone the native
    -- Quickbuilder recipe entry inside that tree and retarget the
    -- cloned HashKey32 to the Architect Wand recipe ID.
    -- --------------------------------------------------------

    local uiLinkCount = 0
    local uiBundleCount = 0

    local okBundles, uiBundles = pcall(function()
        return game.assets.get_resources_by_type(
            "keen::FbUiBundle"
        )
    end)

    if okBundles and uiBundles then

        for _, bundle in ipairs(uiBundles) do

            uiBundleCount = uiBundleCount + 1

            local crafting =
                bundle.data
                and bundle.data.menu
                and bundle.data.menu.crafting

            local recipes =
                crafting
                and crafting.recipes

            if recipes and recipes.trees then

                for _, tree in ipairs(recipes.trees) do
                    if tree.groups then
                        for _, group in ipairs(tree.groups) do
                            if group.sets then
                                for _, set in ipairs(group.sets) do
                                    if set.entries then

                                        local sourceEntry = nil
                                        local entryCount = 0

                                        for _, entry in ipairs(set.entries) do
                                            entryCount = entryCount + 1

                                            local value =
                                                entry.value
                                                or entry

                                            if value == ARCHITECT_WAND_SOURCE_RECIPE_ID then
                                                sourceEntry = entry
                                                break
                                            end
                                        end

                                        if sourceEntry then

                                            -- Avoid duplicate insertion if cache/reload
                                            -- already contains our recipe id.
                                            local alreadyLinked = false

                                            for _, entry in ipairs(set.entries) do
                                                local value =
                                                    entry.value
                                                    or entry

                                                if value == ARCHITECT_WAND_RECIPE_ID then
                                                    alreadyLinked = true
                                                    break
                                                end
                                            end

                                            if not alreadyLinked then

                                                table.insert(
                                                    set.entries,
                                                    sourceEntry
                                                )

                                                local newEntry =
                                                    set.entries[
                                                        entryCount + 1
                                                    ]

                                                if newEntry.value ~= nil then
                                                    newEntry.value =
                                                        ARCHITECT_WAND_RECIPE_ID
                                                else
                                                    -- Fallback for a scalar-mapped hash.
                                                    set.entries[
                                                        entryCount + 1
                                                    ] = ARCHITECT_WAND_RECIPE_ID
                                                end

                                                uiLinkCount =
                                                    uiLinkCount + 1

                                            end
                                        end
                                    end
                                end
                            end
                        end
                    end
                end
            end
        end
    end

    print(
        "Architect Toolkit: Wand UI recipe links="
        .. tostring(uiLinkCount)
        .. " across FbUiBundle resources="
        .. tostring(uiBundleCount)
    )

    local diagnostics = {
        "ARCHITECT TOOLKIT - ARCHITECT'S WAND v0.9",
        "",
        "SOURCE ITEM ID: " .. tostring(ARCHITECT_WAND_SOURCE_ITEM_ID),
        "SOURCE DEBUG NAME: " .. tostring(sourceItem.data.debugName),
        "SOURCE CATEGORY: " .. tostring(sourceItem.data.category),
        "SOURCE RECIPE ID: " .. tostring(ARCHITECT_WAND_SOURCE_RECIPE_ID),
        "VISUAL DONOR ITEM ID: " .. tostring(ARCHITECT_WAND_VISUAL_DONOR_ITEM_ID),
        "VISUAL DONOR DEBUG NAME: " .. tostring(visualDonor.data.debugName),
        "VISUAL DONOR OBJECT ID: " .. tostring(visualDonor.data.objectId),
        "VISUAL DONOR NAME REF: " .. tostring(visualDonor.data.name),
        "WAND ITEM ID: " .. tostring(ARCHITECT_WAND_ITEM_ID),
        "WAND ITEM GUID: " .. tostring(wand.guid),
        "WAND UPDATED EXISTING: " .. tostring(wandWasExisting),
        "RECIPE UPDATED EXISTING: " .. tostring(recipeWasExisting),
        "WAND RECIPE ID: " .. tostring(ARCHITECT_WAND_RECIPE_ID),
        "ITEM REGISTRY GUID: " .. tostring(itemRegistry.guid),
        "RECIPE REGISTRY GUID: " .. tostring(recipeRegistry.guid),
        "NAME LOCATAG: " .. (wandName and tostring(wandName.guid) or "FAILED"),
        "DESCRIPTION LOCATAG: " .. (wandDescription and tostring(wandDescription.guid) or "FAILED"),
        "CATEGORY: " .. tostring(wand.data.category),
        "EQUIPMENT SLOT: " .. tostring(wand.data.equipment.slot),
        "TERTIARY GAMEPLAY ACTION: " .. tostring(wand.data.uiActionHints.tertiaryGameplayAction),
        "ARCHITECT MENU ROUTING: runtime layer / not ItemInfo",
        "OBJECT ID: " .. tostring(wand.data.objectId),
        "ICON IMAGE: " .. tostring(wand.data.iconImage),
        "ICON MODEL: " .. tostring(wand.data.iconModel),
        "ICON SCENE: " .. tostring(wand.data.iconScene),
        "VISUAL ENTITY: " .. tostring(wand.data.equipment.visualEntity),
        "PRIMARY ANIMATION: " .. tostring(wand.data.equipment.primaryAnimationSet),
        "SECONDARY ANIMATION: " .. tostring(wand.data.equipment.secondaryAnimationSet),
        "RECIPE WORKSHOP ID: " .. tostring(newRecipe.workshopId and newRecipe.workshopId.value),
        "RECIPE OUTPUT ITEM ID: " .. tostring(wandOutput.item.value),
        "RECIPE OUTPUT COUNT: " .. tostring(wandOutput.count),
        "FBUI BUNDLES: " .. tostring(uiBundleCount),
        "UI RECIPE LINKS ADDED: " .. tostring(uiLinkCount)
    }

    io.export(
        "architect_toolkit/architect_wand_v09.txt",
        table.concat(diagnostics, "\n")
    )

    print(
        "Architect Toolkit: Architect's Wand registered. itemId="
        .. tostring(ARCHITECT_WAND_ITEM_ID)
        .. " recipeId="
        .. tostring(ARCHITECT_WAND_RECIPE_ID)
    )

    return wand
end

architectRegisterWand()

-- ============================================================
-- Architect Toolkit - Runtime Bridge Manifest v1
-- ============================================================
--
-- The external Architect Runtime cannot directly inspect Lua state.
-- Export the generated backend registrations in a machine-readable
-- form so the UI can bind to the exact Item IDs created by EML.
--
-- This is a startup-time capability handshake only. Live placement
-- still requires the future game-side runtime bridge.
-- ============================================================

local function architectJsonEscape(value)

    local s = tostring(value or "")

    s = string.gsub(s, "\\", "\\\\")
    s = string.gsub(s, "\"", "\\\"")
    s = string.gsub(s, "\r", "\\r")
    s = string.gsub(s, "\n", "\\n")
    s = string.gsub(s, "\t", "\\t")

    return s
end


local function architectShapeDisplayName(key)

    local names = {
        hollow_ceiling_4m = "Hollow Square",
        filled_circle_4m = "Filled Circle",
        ring_4m = "Ring",
        cross_4m = "Cross",
        diamond_4m = "Diamond",
        diagonal_cross_4m = "Diagonal Cross",
        sphere_2m = "Sphere",
        filled_cylinder_2m = "Filled Cylinder",
        hollow_cube_2m = "Hollow Cube",
        stairs_2m = "Stairs",
        pyramid_2m = "Stepped Pyramid",
        archway_2m = "Archway"
    }

    return names[key] or key
end


local function architectShapeSizeLabel(key)

    if string.find(key, "_4m", 1, true) then
        return "4m"
    end

    if string.find(key, "_2m", 1, true) then
        return "2m"
    end

    return "Custom"
end


local manifest = {}

table.insert(manifest, "{")
table.insert(manifest, "  \"protocolVersion\": 1,")
table.insert(manifest, "  \"backend\": \"EML Single Blueprint Carrier\",")
table.insert(
    manifest,
    "  \"wandItemId\": "
    .. tostring(ARCHITECT_WAND_ITEM_ID)
    .. ","
)
table.insert(
    manifest,
    "  \"maxSafePlacementBytes\": "
    .. tostring(MAX_SAFE_EML_PLACEMENT_BYTES)
    .. ","
)
table.insert(manifest, "  \"carrierItemId\": " .. tostring(ARCHITECT_CARRIER_ITEM_ID) .. ",")
table.insert(manifest, "  \"activeShapeKey\": \"" .. architectJsonEscape(ACTIVE_ARCHITECT_SHAPE_KEY) .. "\",")
table.insert(manifest, "  \"shapeSelectionMode\": \"startup_config_restart_required\",")
table.insert(manifest, "  \"liveShapeSwapSupported\": false,")
table.insert(manifest, "  \"catalogKeys\": [")
for index, definition in ipairs(definitions) do
    table.insert(manifest, "    \"" .. architectJsonEscape(definition.key) .. "\"" .. (index < #definitions and "," or ""))
end
table.insert(manifest, "  ],")
table.insert(manifest, "  \"shapes\": [")

for index, result in ipairs(generated) do

    local comma =
        index < #generated
        and ","
        or ""

    table.insert(manifest, "    {")
    table.insert(
        manifest,
        "      \"key\": \""
        .. architectJsonEscape(result.key)
        .. "\","
    )
    table.insert(
        manifest,
        "      \"displayName\": \""
        .. architectJsonEscape(
            architectShapeDisplayName(result.key)
        )
        .. "\","
    )
    table.insert(
        manifest,
        "      \"sizeLabel\": \""
        .. architectJsonEscape(
            architectShapeSizeLabel(result.key)
        )
        .. "\","
    )
    table.insert(
        manifest,
        "      \"itemId\": "
        .. tostring(result.itemId)
        .. ","
    )
    table.insert(
        manifest,
        "      \"itemGuid\": \""
        .. architectJsonEscape(result.itemGuid)
        .. "\","
    )
    table.insert(
        manifest,
        "      \"voxelGuid\": \""
        .. architectJsonEscape(result.voxelGuid)
        .. "\","
    )
    table.insert(
        manifest,
        "      \"placementBytes\": "
        .. tostring(result.placementBytes)
    )
    table.insert(
        manifest,
        "    }"
        .. comma
    )
end

table.insert(manifest, "  ]")
table.insert(manifest, "}")

io.export(
    "architect_toolkit/backend_manifest.json",
    table.concat(manifest, "\n")
)

local ringRegistryDiagnostic = {}
local otherProceduralShapesLinkedByExperiment = 0
for key, result in pairs(proceduralShapeRegistration) do
    if key ~= "ring_4m" and result.registryLinkAfter then
        otherProceduralShapesLinkedByExperiment =
            otherProceduralShapesLinkedByExperiment + 1
    end
end
table.insert(ringRegistryDiagnostic, "{")
table.insert(ringRegistryDiagnostic, "  \"experiment\": \"ring_item_registry_registration\",")
table.insert(ringRegistryDiagnostic, "  \"experimentalRegisterRingInItemRegistry\": " .. tostring(experimentalRegisterRingInItemRegistry) .. ",")
table.insert(ringRegistryDiagnostic, "  \"ringItemId\": " .. tostring(ringItemRegistryExperiment.ringItemId) .. ",")
table.insert(ringRegistryDiagnostic, "  \"ringItemGuid\": \"" .. architectJsonEscape(ringItemRegistryExperiment.ringItemGuid) .. "\",")
table.insert(ringRegistryDiagnostic, "  \"ringItemRegistryLinkPresentBefore\": " .. tostring(ringItemRegistryExperiment.ringItemRegistryLinkPresentBefore) .. ",")
table.insert(ringRegistryDiagnostic, "  \"ringItemRegistryLinkAdded\": " .. tostring(ringItemRegistryExperiment.ringItemRegistryLinkAdded) .. ",")
table.insert(ringRegistryDiagnostic, "  \"ringItemRegistryLinkPresentAfter\": " .. tostring(ringItemRegistryExperiment.ringItemRegistryLinkPresentAfter) .. ",")
table.insert(ringRegistryDiagnostic, "  \"failureReason\": \"" .. architectJsonEscape(ringItemRegistryExperiment.failureReason) .. "\",")
table.insert(ringRegistryDiagnostic, "  \"ringHammerDonorItemId\": " .. tostring(ringHammerDonorAudit.selectedItemId) .. ",")
table.insert(ringRegistryDiagnostic, "  \"ringHammerDonorCategory\": \"" .. architectJsonEscape(ringHammerDonorAudit.selectedCategory) .. "\",")
table.insert(ringRegistryDiagnostic, "  \"ringHammerDonorMetadataApplied\": " .. tostring(ringHammerDonorAudit.metadataApplied) .. ",")
table.insert(ringRegistryDiagnostic, "  \"otherBackendShapesLinkedByExperiment\": " .. tostring(otherProceduralShapesLinkedByExperiment) .. ",")
table.insert(ringRegistryDiagnostic, "  \"architectWandModifiedByExperiment\": false")
table.insert(ringRegistryDiagnostic, "}")
io.export(
    "architect_toolkit/ring_item_registry_registration.json",
    table.concat(ringRegistryDiagnostic, "\n")
)

-- Consolidated outcome of the guarded, native-resolver registration path.
-- Each row is independent: one invalid resource is never appended and never
-- prevents a separate valid shape from being registered.
local function proceduralJsonBoolean(value)
    return value == true and "true" or "false"
end

local proceduralRegistrationOrder = {
    "hollow_ceiling_4m",
    "filled_circle_4m",
    "ring_4m",
    "cross_4m",
    "diamond_4m",
    "diagonal_cross_4m",
    "sphere_2m",
    "filled_cylinder_2m",
    "hollow_cube_2m",
    "stairs_2m",
    "pyramid_2m",
    "archway_2m"
}
local proceduralRegistrationExport = {}
table.insert(proceduralRegistrationExport, "{")
table.insert(proceduralRegistrationExport,
    "  \"version\": \"procedural_blueprint_registration_v1\",")
table.insert(proceduralRegistrationExport,
    "  \"experimentalRegisterProceduralShapesInItemRegistry\": "
    .. proceduralJsonBoolean(experimentalRegisterProceduralShapesInItemRegistry)
    .. ",")
table.insert(proceduralRegistrationExport, "  \"shapes\": [")
for index, key in ipairs(proceduralRegistrationOrder) do
    local result = proceduralShapeRegistration[key]
    local comma = index < #proceduralRegistrationOrder and "," or ""
    table.insert(proceduralRegistrationExport,
        "    {\"key\":\"" .. architectJsonEscape(result.key)
        .. "\",\"itemId\":" .. tostring(result.itemId)
        .. ",\"itemGuid\":\"" .. architectJsonEscape(result.itemGuid)
        .. "\",\"category\":\"" .. architectJsonEscape(result.category)
        .. "\",\"equipmentSlot\":\"" .. architectJsonEscape(result.equipmentSlot)
        .. "\",\"previewValid\":" .. proceduralJsonBoolean(result.previewValid)
        .. ",\"blueprintMappingFound\":" .. proceduralJsonBoolean(result.blueprintMappingFound)
        .. ",\"blueprintDimensions\":\"" .. architectJsonEscape(result.blueprintDimensions)
        .. "\",\"registryLinkBefore\":" .. proceduralJsonBoolean(result.registryLinkBefore)
        .. ",\"registryLinkAdded\":" .. proceduralJsonBoolean(result.registryLinkAdded)
        .. ",\"registryLinkAfter\":" .. proceduralJsonBoolean(result.registryLinkAfter)
        .. ",\"validationPassed\":" .. proceduralJsonBoolean(result.validationPassed)
        .. ",\"failureReason\":\"" .. architectJsonEscape(result.failureReason)
        .. "\",\"donorItemId\":" .. tostring(result.donorItemId)
        .. ",\"donorDebugName\":\"" .. architectJsonEscape(result.donorDebugName)
        .. "\"}" .. comma)
end
table.insert(proceduralRegistrationExport, "  ]")
table.insert(proceduralRegistrationExport, "}")
io.export(
    "architect_toolkit/procedural_blueprint_registration.json",
    table.concat(proceduralRegistrationExport, "\n")
)

print(
    "Architect Toolkit: backend bridge manifest exported - "
    .. tostring(#generated)
    .. " shape(s)."
)

-- Conservative cleanup report. Existing cached links are reported rather than
-- rebuilding EML-owned dynamic arrays, which has caused allocator failures.
local cleanup = {}
table.insert(cleanup, "{")
table.insert(cleanup, "  \"version\": \"registry_cleanup_v1\",")
table.insert(cleanup, "  \"exposeBackendItems\": " .. tostring(exposeBackendItems) .. ",")
table.insert(cleanup, "  \"experimentalRegisterRingInItemRegistry\": " .. tostring(experimentalRegisterRingInItemRegistry) .. ",")
table.insert(cleanup, "  \"ringItemId\": " .. tostring(ringItemRegistryExperiment.ringItemId) .. ",")
table.insert(cleanup, "  \"ringItemGuid\": \"" .. architectJsonEscape(ringItemRegistryExperiment.ringItemGuid) .. "\",")
table.insert(cleanup, "  \"ringItemRegistryLinkPresentBefore\": " .. tostring(ringItemRegistryExperiment.ringItemRegistryLinkPresentBefore) .. ",")
table.insert(cleanup, "  \"ringItemRegistryLinkAdded\": " .. tostring(ringItemRegistryExperiment.ringItemRegistryLinkAdded) .. ",")
table.insert(cleanup, "  \"ringItemRegistryLinkPresentAfter\": " .. tostring(ringItemRegistryExperiment.ringItemRegistryLinkPresentAfter) .. ",")
table.insert(cleanup, "  \"backendShapeCount\": " .. tostring(#generated) .. ",")
table.insert(cleanup, "  \"backendItemRegistryLinksSuppressed\": " .. tostring(backendRegistryLinksSuppressed) .. ",")
table.insert(cleanup, "  \"backendItemRegistryLinksAlreadyPresent\": " .. tostring(backendRegistryLinksAlreadyPresent) .. ",")
table.insert(cleanup, "  \"wandItemId\": " .. tostring(ARCHITECT_WAND_ITEM_ID) .. ",")
table.insert(cleanup, "  \"wandRecipeId\": " .. tostring(ARCHITECT_WAND_RECIPE_ID) .. ",")
table.insert(cleanup, "  \"backendItems\": [")
for index, result in ipairs(generated) do
    table.insert(cleanup, "    {\"key\":\"" .. architectJsonEscape(result.key) .. "\",\"itemId\":" .. tostring(result.itemId) .. "}" .. (index < #generated and "," or ""))
end
table.insert(cleanup, "  ],")
table.insert(cleanup, "  \"legacyArchitectEntriesDetected\": [],")
table.insert(cleanup, "  \"visibleLinksRemoved\": [],")
table.insert(cleanup, "  \"entriesIntentionallyRetained\": [\"backend ItemInfo cache resources and blueprint registry entries\"],")
table.insert(cleanup, "  \"cleanupNotPerformed\": [\"existing ItemRegistry/FbUi dynamic-array links are not rebuilt or deleted without a confirmed EML-safe removal API\"]")
table.insert(cleanup, "}")
io.export("architect_toolkit/registry_cleanup_report.json", table.concat(cleanup, "\n"))

-- ============================================================
-- Observe-only UI reference audit
-- ============================================================
-- This intentionally performs no deletion or array reconstruction. It traces
-- all safe, known registry and UI-tree paths before any future cleanup.
local auditIds = {
    [ARCHITECT_CARRIER_ITEM_ID] = "architect_blueprint_carrier",
    [2077670299] = "architect_wand",
    [1932263044] = "architect_wand_recipe"
}

local auditMatches = {}
local function auditAdd(resourceType, resourceGuid, field, targetId, index, audience)
    table.insert(auditMatches, {
        resourceType = resourceType,
        resourceGuid = tostring(resourceGuid or ""),
        field = field,
        targetId = targetId,
        index = index or -1,
        audience = audience
    })
end

-- ItemInfo is the safest category/build-tool metadata view available.
local okItems, auditItems = pcall(function()
    return game.assets.get_resources_by_type("keen::ItemInfo")
end)
if okItems and auditItems then
    for _, item in ipairs(auditItems) do
        local id = item.data.itemId and item.data.itemId.value
        if id and auditIds[id] then
            auditAdd("keen::ItemInfo", item.guid, "itemId/category/equipment", id, -1, "potentially_user_facing")
        end
    end
end

for _, registry in ipairs(itemRegistries) do
    for index, itemRef in ipairs(registry.data.itemRefs) do
        local ok, item = pcall(function()
            return game.assets.get_resource(itemRef, "keen::ItemInfo", 0)
        end)
        if ok and item and item.data.itemId and auditIds[item.data.itemId.value] then
            auditAdd("keen::ItemRegistryResource", registry.guid, "itemRefs", item.data.itemId.value, index, "potentially_user_facing")
        end
    end
end

for _, registry in ipairs(blueprintRegistries) do
    for index, blueprint in ipairs(registry.data.blueprintItems) do
        if blueprint.itemId and auditIds[blueprint.itemId.value] then
            auditAdd("keen::VoxelBlueprintItemRegistryResource", registry.guid, "blueprintItems", blueprint.itemId.value, index, "backend_or_building_ui")
        end
    end
end

local okRecipeRegistries, auditRecipeRegistries = pcall(function()
    return game.assets.get_resources_by_type("keen::RecipeRegistryResource")
end)
if okRecipeRegistries and auditRecipeRegistries then
    for _, registry in ipairs(auditRecipeRegistries) do
        for index, recipe in ipairs(registry.data.recipes) do
            local recipeId = recipe.recipeId and recipe.recipeId.value
            if recipeId and auditIds[recipeId] then
                auditAdd("keen::RecipeRegistryResource", registry.guid, "recipes.recipeId", recipeId, index, "potentially_user_facing")
            end
            for _, output in ipairs(recipe.output or {}) do
                local outputId = output.item and output.item.value
                if outputId == ARCHITECT_WAND_ITEM_ID then
                    auditAdd("keen::RecipeRegistryResource", registry.guid, "recipes.output.item", outputId, index, "potentially_user_facing_recipe_output")
                end
            end
        end
    end
end

local okAuditBundles, auditBundles = pcall(function()
    return game.assets.get_resources_by_type("keen::FbUiBundle")
end)
if okAuditBundles and auditBundles then
    for _, bundle in ipairs(auditBundles) do
        local trees = bundle.data and bundle.data.menu and bundle.data.menu.crafting
            and bundle.data.menu.crafting.recipes and bundle.data.menu.crafting.recipes.trees
        if trees then
            for _, tree in ipairs(trees) do
                for _, group in ipairs(tree.groups or {}) do
                    for _, set in ipairs(group.sets or {}) do
                        for index, entry in ipairs(set.entries or {}) do
                            local value = entry.value or entry
                            if auditIds[value] then
                                auditAdd("keen::FbUiBundle", bundle.guid, "menu.crafting.recipes.trees.groups.sets.entries", value, index, "user_facing_recipe_tree")
                            end
                        end
                    end
                end
            end
        end
    end
end

local audit = {}
table.insert(audit, "{")
table.insert(audit, "  \"version\": \"ui_reference_audit_v1\",")
table.insert(audit, "  \"mutationPerformed\": false,")
table.insert(audit, "  \"limitations\": [\"Only EML-accessible typed registries and FbUi crafting trees were enumerated; unknown native menu collections are not guessed at.\"],")
table.insert(audit, "  \"references\": [")
for index, entry in ipairs(auditMatches) do
    table.insert(audit, "    {\"resourceType\":\"" .. architectJsonEscape(entry.resourceType) .. "\",\"resourceGuid\":\"" .. architectJsonEscape(entry.resourceGuid) .. "\",\"field\":\"" .. architectJsonEscape(entry.field) .. "\",\"targetId\":" .. tostring(entry.targetId) .. ",\"index\":" .. tostring(entry.index) .. ",\"audience\":\"" .. architectJsonEscape(entry.audience) .. "\"}" .. (index < #auditMatches and "," or ""))
end
table.insert(audit, "  ]")
table.insert(audit, "}")
io.export("architect_toolkit/ui_reference_audit.json", table.concat(audit, "\n"))

-- Workbench provenance audit: emit every entry in the exact FbUi set that
-- contains the Architect recipe, plus all recipes at its workshop. Read-only.
local workbenchAudit = {}
local function wbAdd(line) table.insert(workbenchAudit, line) end
wbAdd("{")
wbAdd("  \"version\": \"workbench_reference_audit_v1\",")
wbAdd("  \"mutationPerformed\": false,")
wbAdd("  \"entries\": [")
local wbEntries = {}
local function wbRecipeRecord(recipe, recipeGuid, path)
    local outputs = {}
    for _, output in ipairs(recipe.output or {}) do
        local id = output.item and output.item.value or 0
        local item = architectFindItemById(id)
        table.insert(outputs, "{\"itemId\":" .. tostring(id) .. ",\"count\":" .. tostring(output.count or 0) .. ",\"itemGuid\":\"" .. architectJsonEscape(item and item.guid or "") .. "\",\"debugName\":\"" .. architectJsonEscape(item and item.data.debugName or "") .. "\",\"category\":\"" .. architectJsonEscape(item and item.data.category or "") .. "\",\"slot\":\"" .. architectJsonEscape(item and item.data.equipment and item.data.equipment.slot or "") .. "\",\"objectId\":\"" .. architectJsonEscape(item and item.data.objectId or "") .. "\",\"iconModel\":\"" .. architectJsonEscape(item and item.data.iconModel or "") .. "\"}")
    end
    table.insert(wbEntries, "{\"recipeId\":" .. tostring(recipe.recipeId and recipe.recipeId.value or 0) .. ",\"recipeGuid\":\"" .. architectJsonEscape(recipeGuid) .. "\",\"workshopId\":" .. tostring(recipe.workshopId and recipe.workshopId.value or 0) .. ",\"path\":\"" .. architectJsonEscape(path) .. "\",\"outputs\":[" .. table.concat(outputs, ",") .. "]}")
end

local seenRecipe = {}
for _, bundle in ipairs(auditBundles or {}) do
    local trees = bundle.data and bundle.data.menu and bundle.data.menu.crafting and bundle.data.menu.crafting.recipes and bundle.data.menu.crafting.recipes.trees
    for ti, tree in ipairs(trees or {}) do for gi, group in ipairs(tree.groups or {}) do for si, set in ipairs(group.sets or {}) do
        local containsArchitect = false
        for _, entry in ipairs(set.entries or {}) do if (entry.value or entry) == ARCHITECT_WAND_RECIPE_ID then containsArchitect = true end end
        if containsArchitect then
            for ei, entry in ipairs(set.entries or {}) do
                local id = entry.value or entry
                for _, registry in ipairs(auditRecipeRegistries or {}) do for _, recipe in ipairs(registry.data.recipes) do
                    if recipe.recipeId and recipe.recipeId.value == id and not seenRecipe[id] then
                        seenRecipe[id] = true
                        wbRecipeRecord(recipe, registry.guid, "FbUiBundle:" .. tostring(bundle.guid) .. "/tree:" .. ti .. "/group:" .. gi .. "/set:" .. si .. "/entry:" .. ei)
                    end
                end end
            end
        end
    end end end
end
for _, registry in ipairs(auditRecipeRegistries or {}) do for _, recipe in ipairs(registry.data.recipes) do
    if recipe.workshopId and recipe.workshopId.value == 1302892403 and not seenRecipe[recipe.recipeId.value] then
        seenRecipe[recipe.recipeId.value] = true
        wbRecipeRecord(recipe, registry.guid, "workshop:1302892403")
    end
end end
for index, value in ipairs(wbEntries) do wbAdd("    " .. value .. (index < #wbEntries and "," or "")) end
wbAdd("  ]")
wbAdd("}")
io.export("architect_toolkit/workbench_reference_audit.json", table.concat(workbenchAudit, "\n"))

-- Item identity audit: scan every live ItemInfo, not only registry links.
local identity = {"{", "  \"version\": \"architect_item_identity_audit_v1\",", "  \"items\": ["}
local identityRows = {}
for _, item in ipairs(auditItems or {}) do
    local id = item.data.itemId and item.data.itemId.value
    if id == ARCHITECT_WAND_ITEM_ID or id == 693164685 then
        local linked = false
        for _, ref in ipairs(itemRegistry.itemRefs) do
            if tostring(ref) == tostring(item.guid) then linked = true end
        end
        local legacy = string.find(tostring(item.data.debugName or ""), "ArchitectToolkit", 1, true) ~= nil
            or string.find(tostring(item.data.category or ""), "BuildTool", 1, true) ~= nil
        table.insert(identityRows, "{\"guid\":\"" .. architectJsonEscape(item.guid) .. "\",\"itemId\":" .. tostring(id) .. ",\"debugName\":\"" .. architectJsonEscape(item.data.debugName or "") .. "\",\"category\":\"" .. architectJsonEscape(item.data.category or "") .. "\",\"slot\":\"" .. architectJsonEscape(item.data.equipment and item.data.equipment.slot or "") .. "\",\"objectId\":\"" .. architectJsonEscape(item.data.objectId or "") .. "\",\"iconModel\":\"" .. architectJsonEscape(item.data.iconModel or "") .. "\",\"iconScene\":\"" .. architectJsonEscape(item.data.iconScene or "") .. "\",\"visualEntity\":\"" .. architectJsonEscape(item.data.equipment and item.data.equipment.visualEntity or "") .. "\",\"matchesWandDonor\":" .. tostring(id == ARCHITECT_WAND_ITEM_ID and tostring(item.data.objectId) == tostring(sourceItem and sourceItem.data.objectId)) .. ",\"legacyBuildToolLike\":" .. tostring(legacy) .. ",\"itemRegistryReferencesExactGuid\":" .. tostring(linked) .. "}")
    end
end
for index, row in ipairs(identityRows) do table.insert(identity, "    " .. row .. (index < #identityRows and "," or "")) end
table.insert(identity, "  ]")
table.insert(identity, "}")
io.export("architect_toolkit/architect_item_identity_audit.json", table.concat(identity, "\n"))

-- ============================================================
-- Construction Hammer category audit (fail-closed)
-- ============================================================
-- EML exposes ItemInfo.category and the ItemRegistry/blueprint resources, but
-- this mod has not identified an EML-writable Hammer menu/category registry.
-- Do not invent an enum value or append unknown UI structures. The flag is
-- intentionally non-operative until this audit finds an evidenced route.
local architectShapeIds = {
    [ARCHITECT_CARRIER_ITEM_ID] = ACTIVE_ARCHITECT_SHAPE_KEY
}

local function hammerField(value)
    local ok, result = pcall(function() return tostring(value or "") end)
    return ok and result or ""
end

-- JSON booleans must never be produced by tostring(nil), which would emit the
-- invalid JSON token `nil`. Use this only for the Hammer audit serialization.
local function hammerJsonBoolean(value)
    if value == true then return "true" end
    if value == false then return "false" end
    return "null"
end

local function hammerJsonNumber(value)
    if type(value) == "number" then return tostring(value) end
    return "null"
end

local function hammerItemMetadata(item)
    local data = item and item.data or {}
    local equipment = data.equipment or {}
    return {
        guid = hammerField(item and item.guid),
        itemId = data.itemId and data.itemId.value or 0,
        debugName = hammerField(data.debugName),
        category = hammerField(data.category),
        equipmentSlot = hammerField(equipment.slot),
        objectId = hammerField(data.objectId),
        iconModel = hammerField(data.iconModel),
        iconScene = hammerField(data.iconScene),
        voxelObject = hammerField(equipment.voxelObject),
        visualEntity = hammerField(equipment.visualEntity)
    }
end

-- Build a bounded view of vanilla blueprint-backed ItemInfos by category. It
-- compares only fields EML can read safely; it does not infer enum meanings.
local blueprintItemIds = {}
for _, registry in ipairs(blueprintRegistries or {}) do
    for _, blueprint in ipairs(registry.data.blueprintItems or {}) do
        if blueprint.itemId and blueprint.itemId.value then
            blueprintItemIds[blueprint.itemId.value] = true
        end
    end
end

local categorySamples = {}
for _, item in ipairs(auditItems or {}) do
    local metadata = hammerItemMetadata(item)
    if blueprintItemIds[metadata.itemId] and metadata.category ~= ""
        and not architectShapeIds[metadata.itemId] then
        local bucket = categorySamples[metadata.category]
        if not bucket then
            bucket = {}
            categorySamples[metadata.category] = bucket
        end
        if #bucket < 3 then table.insert(bucket, metadata) end
    end
end

local categoryRows = {}
for category, samples in pairs(categorySamples) do
    local sampleRows = {}
    for _, sample in ipairs(samples) do
        table.insert(sampleRows,
            "{\"itemId\":" .. hammerJsonNumber(sample.itemId)
            .. ",\"guid\":\"" .. architectJsonEscape(sample.guid)
            .. "\",\"debugName\":\"" .. architectJsonEscape(sample.debugName)
            .. "\",\"equipmentSlot\":\"" .. architectJsonEscape(sample.equipmentSlot)
            .. "\",\"objectId\":\"" .. architectJsonEscape(sample.objectId)
            .. "\",\"iconModel\":\"" .. architectJsonEscape(sample.iconModel)
            .. "\",\"iconScene\":\"" .. architectJsonEscape(sample.iconScene)
            .. "\"}")
    end
    table.insert(categoryRows,
        "{\"categoryMetadata\":\"" .. architectJsonEscape(category)
        .. "\",\"samples\":[" .. table.concat(sampleRows, ",") .. "]}")
end
table.sort(categoryRows)

local mappedVanillaItemRows = {}
for _, item in ipairs(auditItems or {}) do
    local metadata = hammerItemMetadata(item)
    if blueprintItemIds[metadata.itemId] and not architectShapeIds[metadata.itemId] then
        local classification = "mapped_other"
        if metadata.equipmentSlot == "BuildTool"
            and metadata.category == "Blueprints" then
            classification = "geometric_build_blueprint"
        elseif string.sub(metadata.equipmentSlot, 1, 18) == "BlueprintMaterial_"
            and metadata.category == "BuildTools" then
            classification = "building_material"
        end
        table.insert(mappedVanillaItemRows,
            "{\"itemId\":" .. hammerJsonNumber(metadata.itemId)
            .. ",\"guid\":\"" .. architectJsonEscape(metadata.guid)
            .. "\",\"debugName\":\"" .. architectJsonEscape(metadata.debugName)
            .. "\",\"category\":\"" .. architectJsonEscape(metadata.category)
            .. "\",\"equipmentSlot\":\"" .. architectJsonEscape(metadata.equipmentSlot)
            .. "\",\"objectId\":\"" .. architectJsonEscape(metadata.objectId)
            .. "\",\"previewVoxelModel\":\"" .. architectJsonEscape(metadata.voxelObject)
            .. "\",\"previewVoxelModelValid\":" .. hammerJsonBoolean(ringDonorHasValidPreview(item))
            .. ",\"classification\":\"" .. classification .. "\"}")
    end
end
table.sort(mappedVanillaItemRows)

local architectRows = {}
for itemId, shapeName in pairs(architectShapeIds) do
    local item = findItemById(itemId)
    local old = hammerItemMetadata(item)
    local exactRegistryLink = false
    for _, itemRef in ipairs(itemRegistry.itemRefs or {}) do
        local ok, linked = pcall(function()
            return game.assets.get_resource(itemRef, "keen::ItemInfo", 0)
        end)
        if ok and linked and tostring(linked.guid or "") == old.guid then
            exactRegistryLink = true
        end
    end
    -- No category write: new metadata intentionally equals old metadata.
    table.insert(architectRows,
        "{\"shape\":\"" .. architectJsonEscape(shapeName)
        .. "\",\"itemId\":" .. hammerJsonNumber(itemId)
        .. ",\"guid\":\"" .. architectJsonEscape(old.guid)
        .. "\",\"oldCategoryMetadata\":\"" .. architectJsonEscape(old.category)
        .. "\",\"newCategoryMetadata\":\"" .. architectJsonEscape(old.category)
        .. "\",\"equipmentSlot\":\"" .. architectJsonEscape(old.equipmentSlot)
        .. "\",\"objectId\":\"" .. architectJsonEscape(old.objectId)
        .. "\",\"iconModel\":\"" .. architectJsonEscape(old.iconModel)
        .. "\",\"iconScene\":\"" .. architectJsonEscape(old.iconScene)
        .. "\",\"itemRegistryExactLinkPresent\":" .. hammerJsonBoolean(exactRegistryLink)
        .. ",\"categoryMutationApplied\":false}")
end
table.sort(architectRows)

local donorRows = {}
for index, candidate in ipairs(ringHammerDonorCandidates) do
    if index > 8 then break end
    local donor = hammerItemMetadata(candidate.item)
    table.insert(donorRows,
        "{\"itemId\":" .. hammerJsonNumber(candidate.itemId)
        .. ",\"guid\":\"" .. architectJsonEscape(donor.guid)
        .. "\",\"debugName\":\"" .. architectJsonEscape(candidate.debugName)
        .. "\",\"categoryMetadata\":\"" .. architectJsonEscape(candidate.category)
        .. "\",\"selectionScore\":" .. hammerJsonNumber(candidate.score)
        .. ",\"blueprintRegistryMappingPresent\":true"
        .. ",\"objectId\":\"" .. architectJsonEscape(donor.objectId)
        .. "\",\"iconModel\":\"" .. architectJsonEscape(donor.iconModel)
        .. "\",\"iconScene\":\"" .. architectJsonEscape(donor.iconScene)
        .. "\",\"previewVoxelModel\":\"" .. architectJsonEscape(donor.voxelObject)
        .. "\"}")
end

local function hammerRegistryItemById(itemId)
    for _, itemRef in ipairs(itemRegistry.itemRefs or {}) do
        local ok, linked = pcall(function()
            return game.assets.get_resource(itemRef, "keen::ItemInfo", 0)
        end)
        if ok and linked and linked.data.itemId
            and linked.data.itemId.value == itemId then
            return linked
        end
    end
    return nil
end

local function hammerBlueprintDetails(itemId)
    for index, blueprint in ipairs(blueprintRegistry.blueprintItems or {}) do
        if blueprint.itemId and blueprint.itemId.value == itemId then
            return index, tostring(blueprint.size.x) .. "x"
                .. tostring(blueprint.size.y) .. "x" .. tostring(blueprint.size.z)
        end
    end
    return -1, ""
end

local failedManualItem = hammerRegistryItemById(SOURCE_CEILING_ID)
local failedManualMetadata = hammerItemMetadata(failedManualItem)
local failedManualBlueprintIndex, failedManualBlueprintSize =
    hammerBlueprintDetails(SOURCE_CEILING_ID)
local finalRingItem = hammerRegistryItemById(EXPERIMENTAL_RING_ITEM_ID)
local finalRingMetadata = hammerItemMetadata(finalRingItem)
local finalRingBlueprintIndex, finalRingBlueprintSize =
    hammerBlueprintDetails(EXPERIMENTAL_RING_ITEM_ID)
if finalRingItem then
    ringFinalIdentity.guid = finalRingMetadata.guid
    ringFinalIdentity.category = finalRingMetadata.category
    ringFinalIdentity.equipmentSlot = finalRingMetadata.equipmentSlot
    ringFinalIdentity.previewVoxelModel = finalRingMetadata.voxelObject
    ringFinalIdentity.blueprintRegistryIndex = finalRingBlueprintIndex
    ringFinalIdentity.blueprintSize = finalRingBlueprintSize
    ringFinalIdentity.exactRegistryLinkPresent =
        tostring(finalRingMetadata.guid) == tostring(ringItemRegistryExperiment.ringItemGuid)
end

local hammerAudit = {}
table.insert(hammerAudit, "{")
table.insert(hammerAudit, "  \"version\": \"hammer_category_audit_v1\",")
table.insert(hammerAudit, "  \"architectHammerCategoryEnabled\": " .. hammerJsonBoolean(architectHammerCategoryEnabled) .. ",")
table.insert(hammerAudit, "  \"experimentalRingHammerDonorEnabled\": " .. hammerJsonBoolean(experimentalRingHammerDonorEnabled) .. ",")
table.insert(hammerAudit, "  \"prototypeApplied\": " .. hammerJsonBoolean(ringHammerDonorAudit.metadataApplied) .. ",")
table.insert(hammerAudit, "  \"categoryCreationPossible\": \"not_evidenced_fail_closed\",")
table.insert(hammerAudit, "  \"categoryLabelCreationPossible\": \"not_evidenced_localization_unresolved\",")
table.insert(hammerAudit, "  \"categoryMembershipModificationPossible\": \"ItemInfo.category_is_readable_but_no_Hammer_menu_effect_is_proven\",")
table.insert(hammerAudit, "  \"discoveredCategoryMechanism\": {\"itemInfoField\":\"keen::ItemInfo.category\",\"itemRegistryRole\":\"registration/native resolver population\",\"blueprintRegistryRole\":\"blueprint linkage\",\"fbUiBundleResult\":\"accessible trees are crafting recipe trees; no Construction Hammer category/group collection was evidenced\",\"orderingOrGroupingResource\":\"not found through supported EML-accessible resources\"},")
table.insert(hammerAudit, "  \"vanillaBlueprintCategorySamples\": [")
for index, row in ipairs(categoryRows) do
    table.insert(hammerAudit, "    " .. row .. (index < #categoryRows and "," or ""))
end
table.insert(hammerAudit, "  ],")
table.insert(hammerAudit, "  \"mappedVanillaBlueprintItemInfos\": [")
for index, row in ipairs(mappedVanillaItemRows) do
    table.insert(hammerAudit, "    " .. row .. (index < #mappedVanillaItemRows and "," or ""))
end
table.insert(hammerAudit, "  ],")
table.insert(hammerAudit, "  \"ringDonorSelection\": {\"sourceCeilingCategory\":\"" .. architectJsonEscape(ringHammerDonorAudit.sourceCeilingCategory) .. "\",\"selectedItemId\":" .. hammerJsonNumber(ringHammerDonorAudit.selectedItemId) .. ",\"selectedItemGuid\":\"" .. architectJsonEscape(ringHammerDonorAudit.selectedItemGuid) .. "\",\"selectedDebugName\":\"" .. architectJsonEscape(ringHammerDonorAudit.selectedDebugName) .. "\",\"selectedCategory\":\"" .. architectJsonEscape(ringHammerDonorAudit.selectedCategory) .. "\",\"selectionReason\":\"" .. architectJsonEscape(ringHammerDonorAudit.selectionReason) .. "\",\"metadataApplied\":" .. hammerJsonBoolean(ringHammerDonorAudit.metadataApplied) .. ",\"metadataApplicationReason\":\"" .. architectJsonEscape(ringHammerDonorAudit.metadataApplicationReason) .. "\"},")
table.insert(hammerAudit, "  \"mappedVanillaShapeDonorCandidates\": [")
for index, row in ipairs(donorRows) do
    table.insert(hammerAudit, "    " .. row .. (index < #donorRows and "," or ""))
end
table.insert(hammerAudit, "  ],")
table.insert(hammerAudit, "  \"failedManualSelectionItem81726253\": {\"itemId\":81726253,\"guid\":\"" .. architectJsonEscape(failedManualMetadata.guid) .. "\",\"debugName\":\"" .. architectJsonEscape(failedManualMetadata.debugName) .. "\",\"category\":\"" .. architectJsonEscape(failedManualMetadata.category) .. "\",\"equipmentSlot\":\"" .. architectJsonEscape(failedManualMetadata.equipmentSlot) .. "\",\"objectId\":\"" .. architectJsonEscape(failedManualMetadata.objectId) .. "\",\"previewVoxelModel\":\"" .. architectJsonEscape(failedManualMetadata.voxelObject) .. "\",\"blueprintRegistryIndex\":" .. hammerJsonNumber(failedManualBlueprintIndex) .. ",\"blueprintSize\":\"" .. architectJsonEscape(failedManualBlueprintSize) .. "\"},")
table.insert(hammerAudit, "  \"finalRingIdentity\": {\"finalRingItemId\":1458989991,\"finalRingGuid\":\"" .. architectJsonEscape(ringFinalIdentity.guid) .. "\",\"finalRingCategory\":\"" .. architectJsonEscape(ringFinalIdentity.category) .. "\",\"finalRingEquipmentSlot\":\"" .. architectJsonEscape(ringFinalIdentity.equipmentSlot) .. "\",\"finalRingPreviewVoxelModel\":\"" .. architectJsonEscape(ringFinalIdentity.previewVoxelModel) .. "\",\"finalRingBlueprintRegistryIndex\":" .. hammerJsonNumber(ringFinalIdentity.blueprintRegistryIndex) .. ",\"finalRingBlueprintSize\":\"" .. architectJsonEscape(ringFinalIdentity.blueprintSize) .. "\",\"finalRingRegistryLinkPresent\":" .. hammerJsonBoolean(ringFinalIdentity.exactRegistryLinkPresent) .. ",\"identityValidationPassed\":" .. hammerJsonBoolean(ringFinalIdentity.validationPassed) .. ",\"identityValidationFailureReason\":\"" .. architectJsonEscape(ringFinalIdentity.validationFailureReason) .. "\",\"selectedDonorItemId\":" .. hammerJsonNumber(ringHammerDonorAudit.selectedItemId) .. ",\"selectedDonorDebugName\":\"" .. architectJsonEscape(ringHammerDonorAudit.selectedDebugName) .. "\",\"selectedDonorCategory\":\"" .. architectJsonEscape(ringHammerDonorAudit.selectedCategory) .. "\",\"selectedDonorEquipmentSlot\":\"" .. architectJsonEscape(ringHammerDonorAudit.selectedEquipmentSlot) .. "\"},")
table.insert(hammerAudit, "  \"architectShapes\": [")
for index, row in ipairs(architectRows) do
    table.insert(hammerAudit, "    " .. row .. (index < #architectRows and "," or ""))
end
table.insert(hammerAudit, "  ],")
table.insert(hammerAudit, "  \"uiLinksCreatedOrChanged\": [],")
table.insert(hammerAudit, "  \"localizationStatus\": \"unresolved_no_custom_label_created\",")
table.insert(hammerAudit, "  \"notSafelyModified\": [\"keen::ItemInfo.category\",\"unknown Construction Hammer menu collections\",\"FbUiBundle crafting trees\",\"vanilla ItemInfo resources\",\"ItemRegistry itemRefs\"],")
table.insert(hammerAudit, "  \"nativePlacementCodeModified\": false")
table.insert(hammerAudit, "}")
io.export("architect_toolkit/hammer_category_audit.json", table.concat(hammerAudit, "\n"))

-- ============================================================
-- ItemInfo / VoxelBlueprint identity integrity audit (read-only)
-- ============================================================
-- GUID text is used only to calculate diagnostic FNV candidates. It is never
-- passed back into an asset API and no ItemInfo ID/GUID is changed here.
local function identityUnsigned32(value)
    if value and value < 0 then return value + 4294967296 end
    return value or 0
end

local function identityFNV(text)
    if not text or text == "" then return 0, false end
    local ok, value = pcall(function() return hasher.fnv1a32(text) end)
    return ok and identityUnsigned32(value) or 0, ok
end

local function identityRegistryMembership(item)
    local result = {
        exact = false,
        objectReference = "",
        targetGuid = ""
    }
    local wantedGuid = tostring(item and item.guid or "")
    for _, itemRef in ipairs(itemRegistry.itemRefs or {}) do
        local ok, linked = pcall(function()
            return game.assets.get_resource(itemRef, "keen::ItemInfo", 0)
        end)
        if ok and linked and tostring(linked.guid or "") == wantedGuid then
            result.exact = true
            result.objectReference = tostring(itemRef)
            result.targetGuid = tostring(linked.guid or "")
            break
        end
    end
    return result
end

local function identityBlueprintMatches(itemId)
    local matches = {}
    for index, blueprint in ipairs(blueprintRegistry.blueprintItems or {}) do
        if blueprint.itemId and blueprint.itemId.value == itemId then
            table.insert(matches, {
                index = index,
                itemIdObject = tostring(blueprint.itemId),
                itemIdValue = blueprint.itemId.value,
                size = tostring(blueprint.size.x) .. "x" .. tostring(blueprint.size.y)
                    .. "x" .. tostring(blueprint.size.z)
            })
        end
    end
    return matches
end

local function identityPreview(item)
    local ref = item and item.data and item.data.equipment
        and item.data.equipment.voxelObject
    local result = { objectReference = tostring(ref or ""), guid = "", valid = false }
    if not ref or tostring(ref) == "" then return result end
    local ok, voxel = pcall(function()
        return game.assets.get_resource(ref, "keen::VoxelModelResource", 0)
    end)
    if ok and voxel then
        result.guid = tostring(voxel.guid or "")
        result.valid = voxel.data ~= nil and voxel.data.size ~= nil
    end
    return result
end

local function identityAuditRecord(item, expectedItemId, label)
    local data = item and item.data or {}
    local guid = tostring(item and item.guid or "")
    local idObject = tostring(data.itemId or "")
    local itemId = data.itemId and data.itemId.value or 0
    local lowerGuid = string.lower(guid)
    local unbracedGuid = string.gsub(lowerGuid, "[{}]", "")
    local hashGuid, hashGuidValid = identityFNV(guid)
    local hashLower, hashLowerValid = identityFNV(lowerGuid)
    local hashUnbraced, hashUnbracedValid = identityFNV(unbracedGuid)
    local registry = identityRegistryMembership(item)
    local preview = identityPreview(item)
    local blueprints = identityBlueprintMatches(itemId)
    local blueprintRows = {}
    local allBlueprintIdsMatch = #blueprints > 0

    for _, match in ipairs(blueprints) do
        if match.itemIdValue ~= itemId then allBlueprintIdsMatch = false end
        table.insert(blueprintRows,
            "{\"index\":" .. tostring(match.index)
            .. ",\"itemIdObject\":\"" .. architectJsonEscape(match.itemIdObject)
            .. "\",\"itemIdValue\":" .. tostring(match.itemIdValue)
            .. ",\"dimensions\":\"" .. architectJsonEscape(match.size) .. "\"}")
    end

    local mismatchFlags = {}
    if expectedItemId ~= nil and itemId ~= expectedItemId then
        table.insert(mismatchFlags, "expectedItemIdMismatch")
    end
    if not registry.exact then table.insert(mismatchFlags, "missingExactItemRegistryLink") end
    if #blueprints == 0 then table.insert(mismatchFlags, "missingVoxelBlueprintMapping") end
    if not allBlueprintIdsMatch then table.insert(mismatchFlags, "blueprintItemIdMismatch") end
    if not preview.valid then table.insert(mismatchFlags, "missingOrInvalidPreviewVoxelModel") end
    if hashGuidValid and itemId ~= hashGuid
        and hashLowerValid and itemId ~= hashLower
        and hashUnbracedValid and itemId ~= hashUnbraced then
        table.insert(mismatchFlags, "itemIdDoesNotMatchTestedGuidTextFNVForms")
    end

    return {
        label = label,
        guid = guid,
        debugName = tostring(data.debugName or ""),
        category = tostring(data.category or ""),
        equipmentSlot = tostring(data.equipment and data.equipment.slot or ""),
        itemIdObject = idObject,
        itemId = itemId,
        expectedItemId = expectedItemId or 0,
        expectedItemIdMatches = expectedItemId == nil or itemId == expectedItemId,
        registry = registry,
        preview = preview,
        blueprintRows = blueprintRows,
        blueprintMappingPresent = #blueprints > 0,
        allBlueprintIdsMatch = allBlueprintIdsMatch,
        hashGuid = hashGuid,
        hashGuidValid = hashGuidValid,
        hashLower = hashLower,
        hashLowerValid = hashLowerValid,
        hashUnbraced = hashUnbraced,
        hashUnbracedValid = hashUnbracedValid,
        itemIdMatchesGuidHash = hashGuidValid and itemId == hashGuid,
        itemIdMatchesLowerGuidHash = hashLowerValid and itemId == hashLower,
        itemIdMatchesUnbracedGuidHash = hashUnbracedValid and itemId == hashUnbraced,
        mismatchFlags = mismatchFlags
    }
end

local function identityAuditJson(record)
    local mismatchRows = {}
    for _, flag in ipairs(record.mismatchFlags or {}) do
        table.insert(mismatchRows, "\"" .. architectJsonEscape(flag) .. "\"")
    end
    return "{\"label\":\"" .. architectJsonEscape(record.label)
        .. "\",\"itemInfoGuid\":\"" .. architectJsonEscape(record.guid)
        .. "\",\"debugName\":\"" .. architectJsonEscape(record.debugName)
        .. "\",\"category\":\"" .. architectJsonEscape(record.category)
        .. "\",\"equipmentSlot\":\"" .. architectJsonEscape(record.equipmentSlot)
        .. "\",\"itemIdObject\":\"" .. architectJsonEscape(record.itemIdObject)
        .. "\",\"itemIdValue\":" .. tostring(record.itemId)
        .. ",\"expectedItemId\":" .. tostring(record.expectedItemId)
        .. ",\"expectedItemIdMatches\":" .. tostring(record.expectedItemIdMatches)
        .. ",\"exactItemRegistryMembership\":" .. tostring(record.registry.exact)
        .. ",\"itemRegistryObjectReference\":\"" .. architectJsonEscape(record.registry.objectReference)
        .. "\",\"itemRegistryTargetGuid\":\"" .. architectJsonEscape(record.registry.targetGuid)
        .. "\",\"previewVoxelObjectReference\":\"" .. architectJsonEscape(record.preview.objectReference)
        .. "\",\"previewVoxelGuid\":\"" .. architectJsonEscape(record.preview.guid)
        .. "\",\"previewVoxelValid\":" .. tostring(record.preview.valid)
        .. ",\"matchingVoxelBlueprintItems\":[" .. table.concat(record.blueprintRows, ",") .. "]"
        .. ",\"blueprintMappingPresent\":" .. tostring(record.blueprintMappingPresent)
        .. ",\"allMatchingBlueprintItemIdsMatch\":" .. tostring(record.allBlueprintIdsMatch)
        .. ",\"fnv1a32Candidates\":{\"guidText\":" .. tostring(record.hashGuid)
        .. ",\"guidTextValid\":" .. tostring(record.hashGuidValid)
        .. ",\"lowerGuidText\":" .. tostring(record.hashLower)
        .. ",\"lowerGuidTextValid\":" .. tostring(record.hashLowerValid)
        .. ",\"unbracedLowerGuidText\":" .. tostring(record.hashUnbraced)
        .. ",\"unbracedLowerGuidTextValid\":" .. tostring(record.hashUnbracedValid)
        .. "},\"itemIdMatchesGuidTextFNV\":" .. tostring(record.itemIdMatchesGuidHash)
        .. ",\"itemIdMatchesLowerGuidTextFNV\":" .. tostring(record.itemIdMatchesLowerGuidHash)
        .. ",\"itemIdMatchesUnbracedLowerGuidTextFNV\":" .. tostring(record.itemIdMatchesUnbracedGuidHash)
        .. ",\"mismatchFlags\":[" .. table.concat(mismatchRows, ",") .. "]"
        .. "}"
end

local vanillaIdentityRecords = {}
for _, item in ipairs(auditItems or {}) do
    local data = item.data or {}
    local slot = tostring(data.equipment and data.equipment.slot or "")
    if data.category == "Blueprints" and slot == "BuildTool"
        and data.itemId and not architectShapeIds[data.itemId.value] then
        table.insert(vanillaIdentityRecords, identityAuditRecord(item, nil, "vanilla"))
    end
end
table.sort(vanillaIdentityRecords, function(a, b) return a.itemId < b.itemId end)

local vanillaExportRows, vanillaGuidHashMatches, vanillaWithBlueprint = {}, 0, 0
for index, record in ipairs(vanillaIdentityRecords) do
    if index > 20 then break end
    if record.itemIdMatchesGuidHash or record.itemIdMatchesLowerGuidHash
        or record.itemIdMatchesUnbracedGuidHash then
        vanillaGuidHashMatches = vanillaGuidHashMatches + 1
    end
    if record.blueprintMappingPresent then vanillaWithBlueprint = vanillaWithBlueprint + 1 end
    table.insert(vanillaExportRows, identityAuditJson(record))
end

local ringIdentityRecord = identityAuditRecord(
    hammerRegistryItemById(EXPERIMENTAL_RING_ITEM_ID)
        or findItemById(EXPERIMENTAL_RING_ITEM_ID),
    EXPERIMENTAL_RING_ITEM_ID,
    "architect_ring")
local selected817Record = identityAuditRecord(
    hammerRegistryItemById(SOURCE_CEILING_ID) or findItemById(SOURCE_CEILING_ID),
    SOURCE_CEILING_ID,
    "captured_vanilla_selection_81726253")

local identityAudit = {}
table.insert(identityAudit, "{")
table.insert(identityAudit, "  \"version\": \"blueprint_identity_audit_v1\",")
table.insert(identityAudit, "  \"mutationPerformed\": false,")
table.insert(identityAudit, "  \"guidHashHypothesis\": \"FNV1a32 candidates are diagnostic-only over canonical textual GUID forms; no GUID text was passed into EML asset APIs.\",")
table.insert(identityAudit, "  \"vanillaRequestedMinimum\": 20,")
table.insert(identityAudit, "  \"vanillaExportedCount\": " .. tostring(#vanillaExportRows) .. ",")
table.insert(identityAudit, "  \"vanillaGuidTextHashMatchCount\": " .. tostring(vanillaGuidHashMatches) .. ",")
table.insert(identityAudit, "  \"vanillaWithBlueprintMappingCount\": " .. tostring(vanillaWithBlueprint) .. ",")
table.insert(identityAudit, "  \"vanillaBuildToolBlueprints\": [")
for index, row in ipairs(vanillaExportRows) do
    table.insert(identityAudit, "    " .. row .. (index < #vanillaExportRows and "," or ""))
end
table.insert(identityAudit, "  ],")
table.insert(identityAudit, "  \"architectRing\": " .. identityAuditJson(ringIdentityRecord) .. ",")
table.insert(identityAudit, "  \"capturedVanillaSelection81726253\": " .. identityAuditJson(selected817Record))
table.insert(identityAudit, "}")
io.export("architect_toolkit/blueprint_identity_audit.json", table.concat(identityAudit, "\n"))
