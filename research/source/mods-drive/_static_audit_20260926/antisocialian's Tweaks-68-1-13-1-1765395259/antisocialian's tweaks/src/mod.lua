debugLog = true -- set false to disable the debug info printed to the console logs for eml


-- This section changes some things from the BalancingTable, level caps, skill points per level, gem salvage %
bplayerTweaks = true -- set false to disable this group
PlevelMax = 300 -- 100
PlevelCap = 100 -- 45
IlevelCap = 300 -- 50
biLevelCap = true -- match items maxLevel to the above ILevelCap
skillPL = 8 -- 2
gemSalv = 1.0 -- 0.5
gemProbMax = true -- Sets all to 1.0 defaults ="common": 0.0,"uncommon": 0.05000000074505806,"rare": 0.25,"epic": 0.5,"legendary": 1.0


-- This section is for changing the items: stack sizes, axe damage, pickaxe 'damage'
bitemTweaks = true -- set false to disable this group
maxStack = 65535 -- varies, script changes everything that stacks higher than 1 to this value
axeMulti = 10 -- 1 should disable and be default numbers **NOTE** not working
pickaxeMulti = 10 -- 1 should disable and be default numbers


-- This section is to change terrain that drops items to drop 1:1
bterrainTweaks = true -- set false to disable this group
terrainTweakValue = 1 -- This one is weird, for every x blocks of the terrain you break you get 1 item. this also varies for each terrain type


-- This part should unlock all recipes so you don't have to pickup an item first
brecipeUnlockTweaks = true -- set false to disable this group


-- should change the factory buildings that have an inventory to act like magic chests and have their inventory available to craft with
bfactoryTweaks = true -- set false to disable this group


-- should change resources to drop more
bresourceTweaks = true -- set false to disable this group
resDropMulti = 10 -- set to 1 for default
itemDropMulti = 10 -- set to 1 for default


-- should set buffs to replace always instead of only when the buff ends(is near ending?)
bbuffTweaks = true
buffMulti = 10

-- chest slot buff will enable doubling the chest slots(WIP)
bchestSizeTweaks = true
chestMaxSize = 96 -- technically you can get 104 which would be 13 rows, but it looks nicer with 96 at 12 rows. larger than this and some slots at the top are cut off and you can't see what's in them

-- should make furniture storage act like magic chests
-- does this even do anything? not sure furniture has storage slots...
bfurnitureMagic = true

-- should be base tweaks, like build area and number of altars
bbaseTweaks = true
baseSizeMulti = 2
bnoNoBuildZones = true
bnoBuildZoneNeeded = true
bbuildInFog = true

-- creative mode crafting, makes everything free to craft.
-- **NOTE** all factories also have their recipes made creative and they will run constantly, filling their inventories even tho the items they create are not needed with this mode turned on.
bcreativeTweaks = false

-- Fog of war Tweaks
bfogOfWarTweaks = true
fogOfWarRange = 5000 -- default 300, this uncovers the terrain part of the map and not the map icons that might be there

-- fast travel to 'all' map icons
bfasttravelEveryIcon = true

-- increase base inventory?
binventoryTweaks = true
backpackSize = 40

-- remove skill points given from everything(?)
bskillPointsBlock = false
skillMulti = 0 

-- spell Tweaks
bspellstweaks = true
spellCastTimeMulti = 0.1 -- default 1, below 1 makes the spells(with a staff) cast faster than default, and above 1 will make the spells cast slower than default
spellManaMulti = 0.1 -- default 1, below 1 makes the spell(with a staff) cheaper mana-wise, and above 1 makes the spells more expensive


-- *****************************************************************************************
-- Please don't change things below and then complain when you broke it.
-- *****************************************************************************************

function log(m)  print("[antisocialian's Tweaks] " .. tostring(m)) end
function warn(m) print("[antisocialian's Tweaks][WARN] " .. tostring(m)) end

-- This section changes some things from the BalancingTable, level caps, skill points per level, gem salvage %
function balancingTableTweaks()
	local bTable = game.assets.get_resources_by_type("keen::BalancingTable")[1].data
	
	bTable["playerLevelMax"] = PlevelMax
	if debugLog then log("playerLevelMax = " .. tostring(PlevelMax)) end
	
	bTable["playerLevelCap"] = PlevelCap
	if debugLog then log("playerLevelCap = " .. tostring(PlevelCap)) end
	
	bTable["itemLevelCap"] = IlevelCap
	if debugLog then log("itemLevelCap = " .. tostring(IlevelCap)) end
	
	-- change the max level range for all items to match the item level cap
	-- i assume this should let lower level model gear drop with higher level & higher level stats. ¯\_(ツ)_/¯
	if biLevelCap then 
		local itable = game.assets.get_resources_by_type("keen::ItemInfo")
		local iCount = 0
		for _, i in pairs(itable) do
			if not (string.find(i.data["debugName"] , "Material")) then
				i.data["itemLevelRange"]["maxLevel"] = IlevelCap
				iCount = iCount + 1
			end
		end
		if debugLog then log("modified "..tostring(iCount).." items to have the maxLevel be "..tostring(IlevelCap)) end
	end

	
	bTable["skillPointsPerLevel"] = skillPL
	if debugLog then log("skillPointsPerLevel = " .. tostring(skillPL)) end
	
	bTable["gemCrafting"]["salvageGainPercentage"] = gemSalv
	if debugLog then log("gemCrafting-salvageGainPercentage = " .. tostring(gemSalv)) end
	if gemProbMax then
		bTable["gemSlotProbability"]["common"] = 1.0
		bTable["gemSlotProbability"]["uncommon"] = 1.0
		bTable["gemSlotProbability"]["rare"] = 1.0
		bTable["gemSlotProbability"]["epic"] = 1.0
		bTable["gemSlotProbability"]["legendary"] = 1.0
		if debugLog then log("gem slot probability for all rarities set to 1.0") end
	end
end


-- This section is for changing the items: stack sizes, axe damage, pickaxe 'damage'
function itemInfoTweaks()
	local itemInfos = game.assets.get_resources_by_type("keen::ItemInfo")
	local itemCounts = 0
	local axeCounts = 0
	local pickCounts = 0
	for _, i in ipairs(itemInfos) do
		if i.data["maxStackSize"] > 1 then
			i.data["maxStackSize"] = maxStack
			itemCounts = itemCounts + 1
		end
		if i.data["equipment"]["slot"] == "Tool" or i.data["equipment"]["slot"] == "BuildTool" then
			if string.find(i.data["debugName"] , "Axe")  and string.find(i.data["debugName"] , "Axe") then
				i.data["damageSetup"]["distribution"]["woodDamage"] = i.data["damageSetup"]["distribution"]["woodDamage"] * axeMulti
				axeCounts = axeCounts + 1		
			end
			if string.find(i.data["debugName"] , "Pickaxe") ~=nil then --elseif string.find(i.data["debugName"] , "Pickaxe") ~=nil then
				for _, j in pairs(i.data["impactValues"]) do
					if j.type == "keen::impact::DamageTerraformingSetupConfig" then
						for _, k in pairs(j.value["value"]) do
							k = k * pickaxeMulti
						end
					end
				end
				pickCounts = pickCounts + 1
			end
			
		end
	end
	if debugLog then log("Modified " .. tostring(itemCounts) .. " items stack sizes to " .. tostring(maxStack)) end
	if debugLog then log("Modified " .. tostring(axeCounts) .. " axes to x" .. tostring(axeMulti) .. " damage") end
	if debugLog then log("Modified " .. tostring(pickCounts) .. " pickaxes to x" .. tostring(pickaxeMulti) .. " damage") end
end


-- This section is to change terrain that drops items to drop 1:1 
-- and to make unbreakable terrain be hard instead  (from "More Stack Size - Storage Slots - QoL" by KenUaena)
function terrainTweaks()
	local terrainTypes= game.assets.get_resources_by_type("keen::TerraformingEfficiencyRegistryResource")[1].data
	local terrainCount = 0
	for _, i in pairs(terrainTypes) do
		for _,j in pairs(i) do
			if j["terrainPerLootItemExchangeRate"] ~= nil then
				j["terrainPerLootItemExchangeRate"] = terrainTweakValue
				terrainCount = terrainCount + 1
			end
			if j["hardness"] == "Unbreakable" then
				j["hardness"] = "Hard"
			end
		end
	end
	if debugLog then log("Modified " .. tostring(terrainCount) .. " terrain types to drop 1:" .. tostring(terrainTweakValue)) end
end



-- *************************************************************************************
-- **     From Builders Utilities mod by ThePrimoris that was hidden/deleted    **
-- *************************************************************************************
-- This part should unlock all recipes so you don't have to pickup an item first
function recipeTweaks()
	local function set_if(obj, k, v)
		local ok = pcall(function() if obj and obj[k] ~= nil then obj[k] = v end end)
		return ok
	end
	
	local function zero_hash32(h)
		pcall(function() if h and h.value ~= nil then h.value = 0 end end)
	end
	
	
	-- **************************************
	-- This section seems to be for unlocking the recipes
	-- **************************************
	
	local regs = game.assets.get_resources_by_type("keen::RecipeRegistryResource")
		if debugLog then log("recipe registries found: " .. tostring(#regs)) end
		
	local recipeDurationCount = 0
	local total = 0
	for _, reg in pairs(regs) do
		local d = reg and reg.data
		if d and d.recipes then
			local touched = 0
			for _, info in ipairs(d.recipes) do
				if info then
				
					if info["craftingDuration"]["value"] > 0 then
						info["craftingDuration"]["value"] = 1000
						recipeDurationCount = recipeDurationCount + 1
					end
					
					-- sets everything to unlock when the initial flame base item is unlocked(?)("debugName": "Prop_Building_FlameAltar_Small_Build_Base")
					info["knowledgeRequirement"]["id"]["value"] = 1715248921 
					info["completionRequirementQueryId"]["id"]["value"] = 3584013164 
					
					touched = touched + 1
				end
			end
			total = total + touched
			if debugLog then log(("recipes unlocked=%d (running total=%d)"):format(touched, total)) end
			if debugLog then log(("recipes made faster=%d"):format(recipeDurationCount)) end
		end
	end
end

-- should change the factory buildings that have an inventory to act like magic chests and have their inventory available to craft with
function factoryTweaks()
	local templatesInfo = game.assets.get_resources_by_type("keen::ecs::TemplateResource")
	local tempTemplateComponent
	local templateCounts = 0
	
	for _, i in pairs(templatesInfo) do
		if string.find(i.data["name"], "Prop_Decoration_T1_Storage_24_Magic") then
			tempTemplateComponent = i.data["components"][4]
		end
	end
	for _, i in pairs(templatesInfo) do
		if string.find(i.data["name"], "Factory") then
			table.insert(i.data["components"], tempTemplateComponent)
			templateCounts = templateCounts + 1
		end
	end
	if debugLog then log("Modified " .. tostring(templateCounts) .. " factory types to share their inventories like magic chests") end
end

-- should change resources to drop more
function lootPickupTweaks()
	local pickupInfo = game.assets.get_resources_by_type("keen::ecs::DefaultInventoryResource")
	local iInfo = game.assets.get_resources_by_type("keen::ItemInfo")
	local lootInfo = game.assets.get_resources_by_type("keen::LootableItemsResource")
	local defaultLootInfo = game.assets.get_resources_by_type("keen::ecs::DefaultInventoryResource")
	local foundCount = 0
	local iCount = 0	
	local lootCount = 0
	local invCount = 0
	local tempStackables = {}
	
	for _, i in pairs(iInfo) do
		if i.data["maxStackSize"] > 1 then
			tempStackables[i.data["itemId"]["value"]] = 1
		end
	end
	
	for _ , i in pairs(pickupInfo) do
		for _, j in pairs(i.data) do
			for _, k in pairs(j["stacks"]) do
				k["countMin"] = k["countMin"] * resDropMulti
				k["countMax"] = k["countMax"] * resDropMulti
				foundCount = foundCount + 1
			end
		end
	end
	
	for _, i in pairs(iInfo) do
		if i.data["maxStackSize"] > 1 then
			i.data["randomLootStackRange"]["minStackSize"] = i.data["randomLootStackRange"]["minStackSize"] * itemDropMulti
			i.data["randomLootStackRange"]["maxStackSize"] = i.data["randomLootStackRange"]["maxStackSize"] * itemDropMulti
			iCount = iCount + 1
		end
	end
	
	for _, i in pairs(lootInfo) do
		for _, j in pairs(i.data["items"]) do
			if tempStackables[j["itemId"]["value"]] ~= nil then
				j["stackSizeMin"] = j["stackSizeMin"] * itemDropMulti
				j["stackSizeMax"] = j["stackSizeMax"] * itemDropMulti
				j["stackSizeScalable"] = false
				j["stackSizeMaxScaled"] = maxStack
				lootCount = lootCount + 1
			end
		end
	end
	
	for _, i in pairs(defaultLootInfo) do
		for _, j in pairs(i.data["rootGroup"]["stacks"]) do
			if tempStackables[j["item"]["value"]] ~= nil then
				j["countMin"] = j["countMin"] * itemDropMulti
				j["countMax"] = j["countMax"] * itemDropMulti
			end
		end
		
		for _, j in pairs(i.data["rootGroup"]["groups"]) do
			for _, k in pairs(j["stacks"]) do 
				if tempStackables[k["item"]["value"]] ~= nil then
					k["countMin"] = k["countMin"] * itemDropMulti
					k["countMax"] = k["countMax"] * itemDropMulti
				end
			end
		end
		invCount = invCount + 1
	end
	
	if debugLog then log("Modified " .. tostring(foundCount) .. " resources to drop x" .. tostring(resDropMulti)) end
	if debugLog then log("Modified " .. tostring(iCount) .. " items to drop x" .. tostring(itemDropMulti)) end
	if debugLog then log("Modified " .. tostring(lootCount) .. " mob loots to drop x" .. tostring(itemDropMulti)) end
	if debugLog then log("Modified " .. tostring(invCount) .. " default inventories to drop x" .. tostring(itemDropMulti)) end
end

-- should allow for buffs to always be reapplied instead of after they're (nearly)done and set all food buffs to be longer, should have been 24hrs but they aren't ¯\_(ツ)_/¯
function buffTweaks()
	local buffInfo = game.assets.get_resources_by_type("keen::BuffType")
	local foundCount = 0
	local longCount = 0
	local foodInfo = game.assets.get_resources_by_type("keen::ItemInfo")
	local buffList = {}
	local potionList = {}
	local tempFoodBuffDuration = 0
	
	for _, i in pairs(foodInfo) do
		if (string.find(i.data["debugName"], "Food") or string.find(i.data["debugName"], "Potion") or string.find(i.data["debugName"], "Consumable") ) and not(string.find(i.data["debugName"], "_bad_")) and not(tostring(i.data["equipment"]["appliedBuff"]) == "00000000-0000-0000-0000-000000000000") and not (string.find(i.data["debugName"], "UNUSED")) then
			for _, j in pairs(i.data["impactValues"]) do
				if j.type == "keen::impact::TimeImpactConfig" then
					j.value["value"]["value"] = j.value["value"]["value"] * buffMulti
					longCount = longCount + 1
					tempFoodBuffDuration = j.value["value"]["value"]
				else
					tempFoodBuffDuration = 0
				end
			end
			for _, j in pairs(i.data["uiValues"]) do
				if j["valueFormat"] == "Duration" then 
					if tempFoodBuffDuration >= 1000000 then
						j["value"] = tempFoodBuffDuration/1000000
					elseif tempFoodBuffDuration == 0 then
						potionList[i.data["equipment"]["appliedBuff"]] = tempFoodBuffDuration 
					else
						j["value"] = 1
					end
				end
			end
			-- table.insert(buffList, tostring(i.data["equipment"]["appliedBuff"]) .. "=)
			if tempFoodBuffDuration > 0 then 
				buffList[i.data["equipment"]["appliedBuff"]] = tempFoodBuffDuration 
			end
		end
	end
	
	for _, i in pairs(buffInfo) do
		if i.data["applyType"] == "ReplaceAtEnd" then
			i.data["applyType"] = "Replace"
			foundCount = foundCount + 1
		end
		if i.data["slot"] == "Food" then
			i.data["defaultLifeTime"]["value"] = i.data["defaultLifeTime"]["value"] * buffMulti
			longCount = longCount + 1
		end
		for k, j in pairs(buffList) do
			if i.guid == k then
				i.data["defaultLifeTime"]["value"] = j
			end
		end
		for k, j in pairs(potionList) do
			if i.guid == k then
				i.data["defaultLifeTime"]["value"] = i.data["defaultLifeTime"]["value"] * buffMulti
			end
		end
	end
	
	
	if debugLog then log("Modified " .. tostring(foundCount) .. " buffs to replace always") end
	if debugLog then log("Modified " .. tostring(longCount) .. " buffs to be longer?") end
end

-- should double storage slots in all things WIP
function chestTweaks()
	local templateResources = game.assets.get_resources_by_type("keen::ecs::TemplateResource")
	local chestCount = 0
	for _, i in pairs(templateResources) do
		local tempComponents = i.data["components"]
		if (string.find(i.data["name"], "Prop_Decoration_T") or string.find(i.data["name"], "Factory")) and not string.find(i.data["name"], "Base") then
			chestCount = chestCount + 1
			for _, j in pairs(i.data["components"]) do
				if j.type == "keen::ecs::InventorySetup" then
					j.value["genericSlotCount"] = j.value["genericSlotCount"] * 2
					if j.value["genericSlotCount"] > chestMaxSize then j.value["genericSlotCount"] = chestMaxSize end
					j.value["availableSlotCount"] = j.value["availableSlotCount"] * 2
					if j.value["availableSlotCount"] > chestMaxSize then j.value["availableSlotCount"] = chestMaxSize end
				end
			end
		end
	end	
	if debugLog then log("Modified " .. tostring(chestCount) .. " chests to double slots") end
end

-- should make furniture storage act like magic chests
function furnitureTweaks()
	local templatesInfo = game.assets.get_resources_by_type("keen::ecs::TemplateResource")
	local tempTemplateComponent
	local templateCounts = 0
	
	for _, i in pairs(templatesInfo) do
		if string.find(i.data["name"], "Prop_Decoration_T1_Storage_24_Magic") then
			tempTemplateComponent = i.data["components"][4]
		end
	end
	for _, i in pairs(templatesInfo) do
		if string.find(i.data["name"], "Furniture") then
			if not string.find(i.data["name"], "Loot") then -- disable changing loot chests
				table.insert(i.data["components"], tempTemplateComponent)
				templateCounts = templateCounts + 1
			end
		end
	end
	if debugLog then log("Modified " .. tostring(templateCounts) .. " furniture types to share their inventories like magic chests") end
end

-- should be for base tweaks like build area size
function baseTweaks()
	local bTable = game.assets.get_resources_by_type("keen::BalancingTable")[1].data
	local baseSizeCount = 0
	
	for _, i in pairs(bTable["buildzoneSizesPerAltarLevel"]) do
		if i["x"] > 0 then
			i["x"] = i["x"] * baseSizeMulti
			i["y"] = i["y"] * baseSizeMulti
			i["z"] = i["z"] * baseSizeMulti
			baseSizeCount = baseSizeCount + 1
		end
	end
	
	-- remove no build zones
	if bnoNoBuildZones then 
		local sTable = game.assets.get_resources_by_type("keen::SceneResource")
		
		for _, i in pairs(sTable) do
			if i.data["ibl"] == "9743d1a0-007d-4a8a-9088-82d34ce7a697" then 
				i.data["noBuildZones"] = {}
			end
		end
		if debugLog then log("Removed no build zones") end
		
		local iTable = game.assets.get_resources_by_type("keen::ItemInfo")
		local iCount = 0
		for _, i in pairs(iTable) do  
			if bbuildInFog then
				i.data["equipment"]["allowPlacementBelowFog"] = true 
				i.data["equipment"]["checkInhibitBuild"] = "None"
			end
			if bnoBuildZoneNeeded then i.data["equipment"]["buildZoneRequired"] = false end
			iCount = iCount + 1
		end
		if debugLog then log("changed "..tostring(iCount).." items to allow placement in fog, remove inhibits to build, and remove build zone required") end
	end
	
	if debugLog then log("Modified " .. tostring(baseSizeCount) .. " base sizes modified") end
end

-- creative mode crafting
function creativeTweaks()
	local recipeTable = game.assets.get_resources_by_type("keen::RecipeRegistryResource")[1].data
	local creativeCount = 0
	local tempInput = {}
	
	for _, i in pairs(recipeTable["recipes"]) do
		if (string.find(i["debugName"], "Campfire") and string.find(i["debugName"], "Food")) then
			log(i["debugName"])
		else
			i["input"] = tempInput
			creativeCount = creativeCount + 1
		end
	end
	
	if debugLog then log("Modified " .. tostring(creativeCount) .. " items for creative crafting") end
end

-- fog of war Tweaks
function fogOfWarTweaks()
	local templateResource = game.assets.get_resources_by_type("keen::ecs::TemplateResource")
	
	for _, i in pairs(templateResource) do
		-- if i.data["name"] == "1_Player_AG2" or i.data["name"] == "AutomatedPlayer"then
			for _, j in pairs(i.data["components"]) do
				if j.type == "keen::ecs::FogOfWarDiscovery" then
					j.value["discoveryRange"] = fogOfWarRange
				end
			end
		-- end
	end
	if debugLog then log("Modified fog of war to "..tostring(fogOfWarRange)) end
end

-- fast travel to most icons
function fasttravelEveryIcon()
	local mapIcon = game.assets.get_resources_by_type("keen::MapMarkerRegistryResource")

	for _, i in pairs(mapIcon) do
		for k, j in pairs(i.data) do
			if k == "mapMarkers" then 
				for _, l in pairs(j) do
					l["isFastTravelDestination"] = true
				end
			end
		end
	end
	
		if debugLog then log("Modified all map icons to allow fast travel") end
end

-- backpack/inventory Tweaks, wanted to make inventory default bigger, seems that isn't doable?
-- so i made all the backpack items be the same size, defaults to 40(vanilla biggest is 32)
function inventoryTweaks()
	local templateResource = game.assets.get_resources_by_type("keen::ecs::TemplateResource")
	local itemResource = game.assets.get_resources_by_type("keen::ItemInfo")
	
	for _, i in pairs(templateResource) do
		if string.find(i.data["name"], "Backpack") then
			for _, j in pairs(i.data["components"]) do
				if j.type == "keen::ecs::InventorySetup" then 
					j.value["genericSlotCount"] = backpackSize
					j.value["availableSlotCount"] = backpackSize
				end
			end
		end
	end
	
	for _, i in pairs(itemResource) do
		if  string.find(i.data["debugName"], "Backpack") then
			for _, j in pairs(i.data["uiValues"]) do
				j["value"] = backpackSize
			end
		end
	end
	
	if debugLog then log("Modified backpack items to add "..tostring(backpackSize).." slots") end
end

-- skill points blocking(?)
function skillPointsBlock()
	local knowRes = game.assets.get_resources_by_type("keen::GameKnowledgeResource")
	local sCount = 0

	for _, i in pairs(knowRes) do
		for _, j in pairs(i.data["playerKnowledge"]) do
			j["unlockedSkillPoints"] = j["unlockedSkillPoints"] * skillMulti
			sCount = sCount + 1
		end
	end
	if debugLog then log("Modified "..tostring(sCount).." knowledge resource items with a x"..tostring(skillMulti).." multiplier") end
end

-- spell tweaks
function spellstweaks()
	local spellRes = game.assets.get_resources_by_type("keen::ItemInfo")
	local spellCount = 0

	for _, i in pairs(spellRes) do
		if string.find(i.data["debugName"], "Ammo") and string.find(i.data["debugName"], "Spell") then
			spellCount = spellCount + 1
			for k, j in pairs(i.data["impactValues"]) do
				if j.value["valueFormat"] == "Duration" then 
					if  math.type(j.value["value"]) == nil then 
						-- this should be for the spells that have a 2nd duration. I assume this would be spells that summon things
						-- like the shock ball or fire mote things. disabled since the duration for these shouldn't be reduced
						-- **TODO** maybe extend this duration?
						-- j.value["value"]["value"] = math.floor(j.value["value"]["value"] * spellCastTimeMulti)
					else
						j.value["value"] = math.floor(j.value["value"] * spellCastTimeMulti)
					end
				elseif j.value["type"]["value"] == 2556031774 then
					j.value["value"] = math.floor(j.value["value"] * spellManaMulti)
				end
			end
			for k, j in pairs(i.data["uiValues"]) do 
				if j["valueFormat"] == "Duration" then
					j["value"] = math.floor(j["value"] * spellCastTimeMulti)
				else
					j["value"] = math.floor(j["value"] * spellManaMulti)
				end
			end
		end
	end
	if debugLog then log("Modified "..tostring(spellCount).." spells") end
end

if bplayerTweaks then balancingTableTweaks() end
if bitemTweaks then itemInfoTweaks() end
if bterrainTweaks then terrainTweaks() end
if brecipeUnlockTweaks then recipeTweaks() end
if bfactoryTweaks then factoryTweaks() end
if bresourceTweaks then lootPickupTweaks() end
if bbuffTweaks then buffTweaks() end
if bchestSizeTweaks then chestTweaks() end
if bfurnitureMagic then furnitureTweaks() end
if bbaseTweaks then baseTweaks() end
if bcreativeTweaks then creativeTweaks() end
if bfogOfWarTweaks then fogOfWarTweaks() end
if bfasttravelEveryIcon then fasttravelEveryIcon() end
if binventoryTweaks then inventoryTweaks() end
if bskillPointsBlock then skillPointsBlock() end
if bspellstweaks then spellstweaks() end
