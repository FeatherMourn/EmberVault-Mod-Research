-- Minimal example based on the verified furniture compatibility fixture.
-- Use only after validating donor schemas for the target game build.
local kfc = require('kfc_content_registry')

local DONOR_ITEM_ID = 2940001508
local DONOR_RECIPE_ID = 3531872774
local NEW_ITEM_ID = 3987654321
local NEW_RECIPE_ID = 3987654322

local donor = kfc.find_by_value('keen::ItemInfo', 'itemId', DONOR_ITEM_ID)
if not donor then return {} end

local clone = kfc.clone_resource(donor, 'keen::ItemInfo')
clone.data.itemId.value = NEW_ITEM_ID
kfc.append_registry(kfc.resources('keen::ItemRegistryResource')[1], 'itemRefs', clone)

local bundle = kfc.resources('keen::FbUiBundle')[1]
if bundle then kfc.clone_recipe_set(bundle, DONOR_RECIPE_ID, NEW_RECIPE_ID) end
return {}
