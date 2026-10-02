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


-- ============================================================
-- Blueprint Registry
-- ============================================================

local blueprintRegistries =
    game.assets.get_resources_by_type(
        "keen::VoxelBlueprintItemRegistryResource"
    )

local blueprintRegistry =
    blueprintRegistries[1].data


-- ============================================================
-- Blueprint Generator
-- ============================================================

local function registerBlueprint(def)

    print(
        "Architect Toolkit: generating "
        .. def.key
    )

    local newItemId =
        hasher.fnv1a32(
            "architect_toolkit:"
            .. def.key
        )

    if itemIdExists(newItemId) then
        print(
            "Architect Toolkit: item ID already exists: "
            .. tostring(newItemId)
        )
        return nil
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

    local itemTemplateId =
        def.itemTemplateId
        or def.sourceItemId

    local blueprintTemplateId =
        def.blueprintTemplateId
        or def.sourceItemId

    local previewTemplateId =
        def.previewTemplateId
        or blueprintTemplateId

    local itemTemplate =
        findItemById(itemTemplateId)

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

    if sourceBlueprint.size.x ~= def.sizeX
        or sourceBlueprint.size.y ~= def.sizeY
        or sourceBlueprint.size.z ~= def.sizeZ then

        print(
            "Architect Toolkit: SKIP "
            .. def.key
            .. " - blueprint template size mismatch."
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

    if previewVoxel.data.size.x ~= def.sizeX
        or previewVoxel.data.size.y ~= def.sizeY
        or previewVoxel.data.size.z ~= def.sizeZ then

        print(
            "Architect Toolkit: SKIP "
            .. def.key
            .. " - preview voxel size mismatch."
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
        def.debugName

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

    table.insert(
        itemRegistry.itemRefs,
        newItem
    )

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

    -- Mutate the cloned native payload in-place.
    for i, value in ipairs(placementData) do
        newBlueprint.data[i] = value
    end

    newBlueprint.isDataCompressed = true

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
    }

}


-- ============================================================
-- Generate everything
-- ============================================================

local generated = {}

for _, definition in ipairs(definitions) do

    local result =
        registerBlueprint(definition)

    if result then
        table.insert(
            generated,
            result
        )
    end
end


-- ============================================================
-- Diagnostics
-- ============================================================

local output = {}

table.insert(
    output,
    "ARCHITECT TOOLKIT - BLUEPRINT GENERATOR V2 - SAFE LUA BACKEND"
)

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
-- in a later runtime layer. The six generated shapes above remain
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

