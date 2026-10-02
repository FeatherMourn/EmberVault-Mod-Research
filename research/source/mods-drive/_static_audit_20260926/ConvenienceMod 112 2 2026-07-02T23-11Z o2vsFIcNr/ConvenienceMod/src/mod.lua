-- NOTE: be warned that this mod has only been tested in single player, and only by one person.
-- I have no idea how, or if, it works in multiplayer.
-- While i have not encountered any issues with any of the modifications so far, i cannot guarantee that they won't cause any for you.
-- I will try to fix any issues you might encounter, but i may not be able to fix all of them.
-- Also note that large updates may break the mod or parts of it.

-- USE AT YOUR OWN RISK
-- AND MAKE SURE TO MAKE AND KEEP BACKUPS OF YOUR SAVES AND CHARACTERS BEFORE USING THE MOD.

-- Credits to antisocialian on nexusmods and the "antisocialian's tweaks" mod, which the structure of this mod is based on.

-- *****************************************************************************************
-- Weapons and armor changes section
-- *****************************************************************************************

GearChanges = false	-- Enables or disables all changes in this section.

WoodDamageWeaponMult = 5.0 		-- Multiplier on the damage wands and melee weapons deal to WOOD objects. (doors, furniture, trees etc.)
StoneDamageWeaponMult = 5.0 	-- Multiplier on the damage wands and melee weapons deal to STONE objects. (doors, furniture, pillars etc.)
MetalDamageWeaponMult = 5.0 	-- Multiplier on the damage wands and melee weapons deal to METAL objects. (doors, furniture, cages etc.)
-- These multipliers do not apply to staff or bow weapons.

WeaponsSkillGainChanges = false	-- If true, enables changing how fast weapons build up special attacks.
WeaponsSkillGain = 100 		-- Default value: 3 - How fast the special attack meter builds up, at 100 it fills up in a single attack. You still need the relevant skills unlocked to fill the meter.

ChangeBowDrawSpeed = false	-- If true, enables the multiplier for bow draw speed below.
DrawSpeedMult = 0.5 -- LOWER IS FASTER, multiplier for the draw speed of bows.
-- note the values displayed in the UI are rounded down, so they might not be accurate.

ChangeMaxLevelOnGear = false -- If true, enables the MaxItemLevel option below. Default max level is 50, and the max level i have tested is 100, but it might work up to 150.
MaxItemlevel = 100	-- Default value: 50 - Sets the maximum item level for weapons and equipment WITH A LEVEL RANGE (i.e. max level > min level).
-- there are other mods out there that does the same but for all items instead, they will not necessarily conflict with this option, but can potentially override it, if set to a different level than this.

CraftMaxRarityGear = false -- If true, crafted armor, offhands and weapons will be the maximum rarity they can be by default, in most cases this is legenedary, but there are some exceptions.
-- this DOESN'T apply to tools, which are controlled by the related option below, and involves changes to the tools themselves beyond their default rarity, because they are normally limited to the rare rarity.
-- It also doesn't apply to things where rarity is purely visual, as with consumables like scrolls and improved bandages.

UnderwaterWeapons = false -- If true, allows weapons to be used underwater. Note that there are not proper animations for this, and that melee weapons are unreliable underwater.

-- *****************************************************************************************
-- Tool changes section
-- *****************************************************************************************

ToolChanges = false	  -- Enables or disables all changes in this section, except for the "LegendaryTools" option at the bottom.

useAllToolsAnywhere = false  -- If true, Makes tools work underwater, and above water for the sieve. Note that animations won't play normally underwater, but the tool still works like normal.

AxeChanges = false	-- Enables or disables the changes below related to woodcutting axes.
ReplaceAxeChopWithWideSwing = false	-- If true, the normal wood chopping "attack" of axes will be replaced with a wide swing attack, the same one they use when used against enemies.
WoodDamageAxeMult = 3.0 	-- Multiplier on the damage woodcutting axes deal to WOOD objects. (doors, furniture, trees etc.)
StoneDamageAxeMult = 6.0 	-- Multiplier on the damage woodcutting axes deal to STONE objects. (doors, furniture, pillars etc.)
MetalDamageAxeMult = 6.0 	-- Multiplier on the damage woodcutting axes deal to METAL objects. (doors, furniture, cages etc.)
AxeSkillGain = 3 			-- Default value: 3 - How fast the special attack meter builds up, at 100 it fills up in a single attack, you still need the relevant skills unlocked to fill the meter.

PickaxeChanges = false	-- Enables or disables the changes below related to pickaxes.
PickaxeTformDamageMult = 3.0 	-- Multiplier on the damage pickaxes deal to terrain materials and blocks, higher values mean fewer hit are need to mine a single block/terrain voxel. Note that it does not affect damage dealt to objects.
PickaxeTformSizeMult = 1.5 		-- Multiplier on the size of the area pickaxes terraforms with each hit, values above 2 makes pickaxes increasingly glitchy, until they stop working as intended entirely.
PickaxeDistance = 5.0 			-- Default value: 5.0 - Max terraforming circle distance (from the player) with the pickaxe.
PickaxeHorizontalDist = 8.0 	-- Default value: 8.0 - Same as above, but horizontal? I'm not exactly sure what this does if anything, but you can experiment with it if you want.
PickaxeMinMaxHeightMult = 1.0 	-- Default values are  -1.0(min) and 1.0(max) - This multiplies the min/max heights, again im not too sure what this actually does, but you can experiment with or just leave it at 1.
PickaxeSkillGain = 3 			-- Default value: 3 - How fast the special attack meter builds up, at 100 it fills up in a single attack, you still need the relevant skills unlocked to fill the meter.

RakeChanges = false 	-- Enables or disables the changes below related to rakes.
RakeNoRestrictions = false 		-- If true, allows you to use the rake ANYWHERE, including outside of buildzones and in the shroud.
RakeNoStamUsage = false 		-- If true, the rake will no longer use stamina.
RakeTerraformRangeMult = 3.0 	-- Multiplies the area the rake terraforms. The rake tolerates larger values than the pickaxe fine, and can also be scaled ingame, so at 3 the smallest scaling option is the same as the largest vanilla scale.
RakeDistance = 8.0 				-- Default value: 8.0 - Same as the pickaxe distance value, but for the rakes instead.
RakeHorizontalDist = 8.0 		-- Default value: 8.0 - Same as the pickaxe distance value, but for the rake instead
RakeHeightMult = 1.0 			-- Same as the height option for the pickaxe. Doesn't really seem to change anything ingame.

-- I've changed this to a separate option that applies independently of other options, so it will apply if set to true, even if the rest of this section is disabled. 
-- Setting it to false should likewise disable it regardless of other options.
-- It is still under this section since it applies to tools.
LegendaryTools = false	-- If true, Makes all non-stone pickaxes and axes (crafted AFTER enabling this) legendary. The two final upgrades are NOT vanilla upgrades, and without this mod, the tools most likely revert to being rare, as they do not have vanilla 4th or 5th upgrades.

-- *****************************************************************************************
-- Terrain changes section
-- *****************************************************************************************

TerrainMaterialChanges = false  -- Enables or disables all changes in this section.

AllTerrainIsBreakable = false  	-- If true, makes terrain and blocks that is normally unbreakable be breakable.
AddDamageSusceptibility = false -- If true, makes terrain and blocks that is normally not affected by the mason/prospector skills, like dirt, snow and unbreakable materials, be affected by the mason skill.
FlattenMoreTerrainTypes = false -- If true, allows you to flatten all kinds of rubble (normally most of them cannot be flattened), mycelium and mud.
FlattenAnythingCheat = false  	-- If true, the rake will be able to flatten ANY terrain material, including ores, magma and otherwise normally indestructible terrain.
HarmlessTerrain = false  		-- If true, mud and snow will not slow you down, you won't drown in tar, ice doesn't make you slide, magma doesn't deal any damage, and the red shroud "water" doesn't drain the shroud timer.

-- The option below is essentially a cheat option, and can allow you to get far more materials back from blocks than it would take to craft them.
ChangeItemDropRateForBlocks = false -- if true, enables the value below to override vanilla drop rates for block materials.
BlocksPerItemDrop = 1 -- Minimum is 1, this determines the number of blocks you have to MINE (not deconstruct with the hammer) to get 1 item of whatever it drops.

-- *****************************************************************************************
-- Loot changes section
-- *****************************************************************************************

LootChanges = false -- Enables or disables all changes in this section.

ChangeLootSlotRanges = false -- If true, enables the loot slot values below, note that it applies to both chests and bosses, in some cases making loot appear in places that normally doesn't have any.
-- The numbers below are added to whatever the vanilla values are for a given loot source, so some chests/bosses still drop more than others.
RandomLootSlotsMin = 1 -- Minimum number of ADDITIONAL items looted from bosses and chests, 0 means the default minimums are used. Should not be greater than the maximum below.
RandomLootSlotsMax = 3 -- Same as above, but for the maximum number instead, it should be equal to or greater than the number used above.

ChangeLevelOffsetRanges = false -- If true, enables the level offset values below, these apply to things looted from bosses and chests, but NOT crafted items or gear dropped by "common" non-boss enemies. Certain static drops are also unaffected, notably lore items and some armors.
-- The way it works is fairly simple, if chest somewhere in the game would normally drop a level 1 weapon, and you set the minimum below to be 40, then that same chest will instead drop a level 41 weapon, and if you set the maximum to 55 then it can potentially be a level 46 weapon.
-- This only works up to whatever level limit the looted gear has, which by default is 50 in most cases, so even if you set these to 50+ without changing that limit, you would still only get level 50 gear.
ExtraLevelOffsetMin = 5 -- Minimum additional levels.
ExtraLevelOffsetMax = 10 -- Maximum additional levels.

ChangeDroppedStackCounts = false -- If true, enables the multipliers below for the number of items stacks certain objects and enemies drop, specifically trees and the floating eyes found in shroud lairs.
-- It ONLY changes the total number of stacks dropped. It does NOT change the size of the stacks that drop.
-- For specifically the archaic essence dropped when attacking floating shroud eyes, there is also a multiplier for the stack sizes.
-- Unfortunately i couldn't get it to work for anything else, otherwise it would've been an option for other things as well.

DroppedStackCountMult = 3 -- Multiplier for the number of item stacks dropped by trees and posssibly other objects.
-- It doesn't seem to apply to anything other than trees, but if something else suddenly seems to drop more with this enabled, this would be the multiplier that affects it.

-- The two multipliers below should only apply to the floating eyes (they're named "FogNestDrone" in the game files).
DroneDroppedStackCountMult = 3 -- Multiplier for the number of stacks of archaic essence dropped by the floating shroud eyes.
DroneDroppedStackSizeMult = 3 -- Multiplier for the stack sizes of archaic essence dropped by the floating shroud eyes.

-- *****************************************************************************************
-- Fishing changes section
-- *****************************************************************************************

FishingChanges = false  -- Enables or disables all changes in this section.

RemoveTrashJunkDrops = false  -- If true, "junk" caught while fishing will always be either a ring or a gem, note this does not change boot drops which are a separate category from the other "junk" drops.
BasicRodJunkOnly = false  -- If true, the basic fishing rod will always catch "junk", except for boots.
LuckyRodJunkOnly = false  -- If true, the lucky fishing rod will always catch "junk", except for boots.
CursedRodBootOnly = false  -- If true, the cursed fishing rod will always catch wet boots.

FishingRodStatChanges = false -- If true, enables the changes below to the stats of fishing rods.
FishingRodStrengthMult = 8.0 -- Multiplies the strength stat on all fishing rods with this number.
FishingRodEndMult = 4.0 -- Multiplies the endurance stat on all fishing rods with this number.

FishBehaviorChanges = false  -- If true, enables the options related to the fishing minigame.
minFishBiteAttempts = 0 		-- Default value: 1, minimum is 0 - Minimum number of "fake" bites fish will do before actually getting hooked.
maxFishBiteAttempts = 1 		-- Default value: 10, minimum is 0 - Maximum number of "fake" bites fish will do before actually getting hooked.
FishEnduranceMult = 0.5 		-- Multiplies the endurance stat of all fish.
FishPowerMult = 0.5				-- Multiplies the power stat of all fish.
FishSpeedMult = 0.5 			-- Multiplies the speed stat of all fish.
FishOutbreakDurationMult = 1.5 	-- Multiplies the time between the fish changing direction during the minigame.
FishTimeUntilVisibleMult = 0.1	-- Multiplies the time it takes for a fish to appear in the water while fishing.
FishQTEDurationMult = 2.0 		-- Multiplies the duration of the right click QTE event during fishing.

FishProbabilityTweaks = false  -- If true multiplies the chances of certain fish appearing while fishing. Chances still depend on which bait is used, this just multiplies those chances.
CommonFishMult = 0.25 	 	 -- Shimmerfin and Lakehopper
CommonFishRareMult = 0.75  	 -- Silverback
UncommonFishMult = 0.5  	 -- Sunscale and Stripetail
UncommonFishRareMult = 0.75  -- Whiskerfin
RareFishMult = 0.75  		 -- Emberfin and Waveleaper
RareFishRareMult = 0.75 	 -- Crimsonback and Shadowtail
EpicFishMult = 3.0 		 	 -- Shockfin, Thornridge and Yellowfin

-- *****************************************************************************************
-- Farm animal changes section
-- *****************************************************************************************
-- this section contains options that change the how much farm animals produce, and how many items they can hold.
-- I've separated yaks for initially testing purposes, and kept it separate due to how buggy their pathing is currently.

FarmAnimalChanges = false  -- Enables or disables all changes in this section.

QuickTame = false -- If true, wild animals will be tamed after being fed and petted once (like springlands goats are).

-- changes for all farm animals except yaks.
FarmAnimalWaitTimeMult = 0.5 -- A multiplier for the time it takes for an animal to produce items once.
FarmAnimalRefillCount = 5 -- The number of items animals produce each time they produce items.
FarmAnimalMaxItemCount = 65000 -- The maximum number of items they can store before they stop producing more items. I'm guessing the limit for this is 65535, same as the stack size limit, at least 65000 worked normally for me during testing.
FarmAnimalReproductionRateMult = 0.5 -- LOWER IS FASTER, a multiplier on how long it takes for farm animals to produce baby animals when conditions for it are met.

-- changes for specifically yaks only.
-- they are otherwise functionally identical to the options above.
YakWaitTimeMult = 0.5
YakRefillCount = 50
YakMaxItemCount = 65000
YakReproductionRateMult = 0.5

-- *****************************************************************************************
-- Interaction changes section
-- *****************************************************************************************
-- This section contains changes to the duration various actions have.
-- The way it actually works is difficult to explain, but basically some actions have a hidden duration, limiting how fast they can be repeated.
-- This means looting/harvesting can feel very slow and inconsistent, but it can be made faster to improve that.
-- I suspect these options may potentially affect performance on weaker systems, and they may also affect stability at low values.

InteractionChanges = false  -- Enables or disables all changes in this section.

FastLooting = false  -- If true, enables the change to the time it takes to pick loot up below.
LootingDurationMult = 0.5  -- LOWER IS FASTER, minimum limit of 0.35, any lower than that and things begin to behave wierdly, like having to press twice to pick up items.
-- This also applies to harvesting and repotting plants and crops.
-- If looting/harvesting behaves wierdly for you with the 0.35 multiplier, you can try raising it to 0.5, which is still very fast, but gives the game a bit more time to process things.

FasterLockpicking = false  -- If true, enables the option to make lockingpicking faster below.
LockpickingDurationMult = 0.5  -- LOWER IS FASTER, unsure if the strict minimum is 0.35, but i've limited it to that for stability, you can try raising it if you run into problems with lockpicking with this enabled.

FasterMining = false  -- If true, enables the option to make mining with pickaxes faster below. May or may not apply to the mining sieve (underwater mining tool).
MiningDurationMult = 0.75  -- LOWER IS FASTER, so 0.75 = mining is 1.5x faster, i recommend 0.75, but you can go down to 0.35 (i've set that as the minimum, to prevent instability).
-- Note that the animation doesn't sync well with this below 0.75, but functionally it still works fine.

FasterFlattening = false  -- If true, enables the option to make flattening with rakes faster below. It changes how frequently the rake actually flattens terrain, but it does not change player animations when using the rake.
FlatteningDurationMult = 0.5  -- LOWER IS FASTER, so 0.35 = ~3x faster, also set to a minimum of 0.35 for stability.


-- *****************************************************************************************
-- Misc changes section
-- *****************************************************************************************

MiscChanges = false  -- Enables or disables all changes in this section.

ChangeSkillNodeMaxLevel = false -- If true, enables the option for changing the max level skills with multiple levels can be upgraded to.
SkillNodeMaxLevel = 7 -- Default value: 3 - The limit for this seems to be 7, trying to level above that seems to reset the skill to zero and return the skill points.
-- Gear bonuses on items to skill levels are separate and not affected by this, and they still work beyond this limit (even beyond the level 7 limit mentioned above).
-- Note that some skills were clearly not meant to have 7 levels (if you set the limit to that), like the quick charge skill giving -120% charge time.
-- This can potentailly cause some strange or unintended things, so keep that in mind ingame.

ChangeGemForgeLevels = false -- If true, enables the option for changing the max levels of gem forges.
-- I made it a multiplier so that it would be possible to either make all gem forges be max level or simply increasing their level cap while keeping progression in place.
GemForgeLevelMult = 3.0 -- Multiplies the level of a given gem forge by this number, rounded down, for reference the lowest level forges have a max level of 10, so if you want all gem forges to be level 50, set this to 5 and the value below to 50.
GemForgeLevelCap = 150 -- The cap of the multiplier above, be warned that values above 150 may cause instability.

ChangeComfortSetup = false -- If true, enables the options for changing how long the rested buff lasts and how it scales with comfort level.
-- it doesn't change the comfort levels of furniture, but rather what they actually do for the rested buff.
ComfortSetupBaseMult = 3.0 -- Increasing this will make the comfort buff longer in general.
ComfortSetupFactorMult = 3.0 -- Increasing this will make the effects of comfort levels stronger.

ChangeDurabilitySetup = false -- If true, enables the options for changing the durability of items with it, and how much it scales with the level of the item.
DurabilityStartMult = 3.0 -- Increasing this will multiply the base amount of durability items have at level 1.
DurabilityGrowthMult = 3.0 -- Increasing this will make the durability increase with item level larger.

-- Below are some options for water containers, note that they apply to ALL water containers, both as inventory items and props (including crafting stations) in the world, including props you didn't place yourself.

-- Pick one (or neither) of the two options below, if both are enabled, the max capacity will be applied.
DoubleContainerCapacity = false -- If true, doubles the capacity of all water containers, does NOT require you to craft/place new ones to work, neither does the option below.
AllContainersAreMaxCapicity = false -- If true, sets the capacity of all water containers to 1000 units of water, for reference, water pumps and improved wells have a capacity of 500 units.
-- As a side note, the maximum possible capacity (that works ingame) seems to be 1023 based on some limited testing, which is fairly low, thats why these options are not configurable.
-- The option below works both by itself and with either of the two options above.
WaterContainersStartFull = false -- If true, newly crafted/placed/spawned water containers (except water skins dropped as loot) will start out being full.
-- For items placed in the world, it applies when the object is placed down, regardless of everything else, meaning if you pick up an empty well, water barrel or crafting station and place it back down again, it would be full again.

-- *****************************************************************************************
-- End of configuration
-- *****************************************************************************************
-- DO NOT CHANGE THE CODE BELOW
-- DOING SO WILL BREAK THINGS
-- *****************************************************************************************

function bGearChanges()
	local itemInfoTable = game.assets.get_resources_by_type("keen::ItemInfo")
	local BalanceTable = game.assets.get_resources_by_type("keen::BalancingTable")[1].data
	
	if ChangeMaxLevelOnGear then
		BalanceTable["itemLevelCap"] = MaxItemlevel
		for _, i in ipairs(itemInfoTable) do
			if i.data["category"] == "Weapons" or i.data["category"] == "Equipment" and i.data["itemLevelRange"]["maxLevel"] > i.data["itemLevelRange"]["minLevel"] and not (string.find(i.data["debugName"], "Material")) then
				i.data["itemLevelRange"]["maxLevel"] = MaxItemlevel
			end
		end
	end
	
	for _, i in ipairs(itemInfoTable) do
		if  i.data["category"] == "Weapons" then
			i.data["damageSetup"]["distribution"]["woodDamage"] = math.floor(i.data["damageSetup"]["distribution"]["woodDamage"] * WoodDamageWeaponMult)
			i.data["damageSetup"]["distribution"]["stoneDamage"] = math.floor(i.data["damageSetup"]["distribution"]["stoneDamage"] * StoneDamageWeaponMult)
			i.data["damageSetup"]["distribution"]["metalDamage"] = math.floor(i.data["damageSetup"]["distribution"]["metalDamage"] * MetalDamageWeaponMult)
			if WeaponsSkillGainChanges then
				for _, j in pairs(i.data["impactValues"]["simple"]) do
					if j.value["configId"]["value"] == 1236200858 then
						j.value["value"] = WeaponsSkillGain
					end
				end	
			end	
			if UnderwaterWeapons then
				if i.data["equipment"]["waterUsability"]["outsideBuildzone"]["allowInsideWater"] == false then
					i.data["equipment"]["waterUsability"]["outsideBuildzone"]["allowInsideWater"] = true 
				end	
				if i.data["equipment"]["waterUsability"]["insideBuildzone"]["allowInsideWater"] == false then
					i.data["equipment"]["waterUsability"]["insideBuildzone"]["allowInsideWater"] = true 
				end	
			end	
		end
		if CraftMaxRarityGear then
			if i.data["category"] == "Weapons" or i.data["category"] == "Equipment" then
				if i.data["perkIds"][2].value > 0 then
					i.data["rarity"] = "Uncommon" 
				end
				if i.data["perkIds"][3].value > 0 then
					i.data["rarity"] = "Rare" 
				end
				if i.data["perkIds"][4].value > 0 then
					i.data["rarity"] = "Epic" 
				end
				if i.data["perkIds"][5].value > 0 then
					i.data["rarity"] = "Legendary" 
				end
			end
		end
		if ChangeBowDrawSpeed then
			if i.data["ammunitionType"] == "Arrow" then
				for _, j in pairs(i.data["impactValues"]["simple"]) do
					if j.value["valueFormat"] == "Duration" then 
						j.value["value"] = math.floor(j.value["value"] * DrawSpeedMult)
					end
				end
				for _, j in pairs(i.data["uiValues"]) do
					if j["valueFormat"] == "Duration" then
						j["value"] = math.floor(j["value"] * DrawSpeedMult)
					end	
				end
			end
		end
	end
end
		
function bToolChanges()
	local itemInfoTable = game.assets.get_resources_by_type("keen::ItemInfo")
	
	for _, i in ipairs(itemInfoTable) do
		if RakeChanges then 
			if i.data["category"] == "BuildTools" and string.find(i.data["debugName"], "Rake") then 
				i.data["equipment"]["maxDistance"] = RakeDistance
				i.data["equipment"]["maxHorizontalDistance"] = RakeHorizontalDist
				i.data["equipment"]["minVerticalRelativeHeight"] = i.data["equipment"]["minVerticalRelativeHeight"] * RakeHeightMult
				i.data["equipment"]["maxVerticalRelativeHeight"] = i.data["equipment"]["maxVerticalRelativeHeight"] * RakeHeightMult
				
				if RakeNoRestrictions then 
					i.data["equipment"]["waterUsability"]["outsideBuildzone"]["allowOutsideWater"] = true 
					i.data["equipment"]["waterUsability"]["outsideBuildzone"]["allowInsideWater"] = true 
					i.data["equipment"]["buildZoneRequired"] = false
					i.data["equipment"]["allowPlacementBelowFog"] = true 
					i.data["equipment"]["checkInhibitBuild"] = "None"
				end			
				for _, j in pairs(i.data["impactValues"]["simple"]) do
					if j.value["configId"]["value"] == 1437161420 then
						j.value["value"] = j.value["value"] * RakeTerraformRangeMult
					end
					if j.value["configId"]["value"] == 1381503774 then
						j.value["value"] = j.value["value"] * RakeTerraformRangeMult
					end
					if RakeNoStamUsage and j.value["configId"]["value"] == 1920827256 then
						j.value["value"] = 0
					end
				end
			end
		end
		if i.data["category"] == "Tools" and string.find(i.data["debugName"], "_Axe_") then
			if useAllToolsAnywhere then
				i.data["equipment"]["waterUsability"]["outsideBuildzone"]["allowInsideWater"] = true 
				i.data["equipment"]["waterUsability"]["outsideBuildzone"]["allowOutsideWater"] = true 
				i.data["equipment"]["waterUsability"]["insideBuildzone"]["allowInsideWater"] = true 
				i.data["equipment"]["waterUsability"]["insideBuildzone"]["allowOutsideWater"] = true 
			end
			if AxeChanges then
				i.data["damageSetup"]["distribution"]["woodDamage"] = math.floor(i.data["damageSetup"]["distribution"]["woodDamage"] * WoodDamageAxeMult)
				i.data["damageSetup"]["distribution"]["stoneDamage"] = math.floor(i.data["damageSetup"]["distribution"]["stoneDamage"] * StoneDamageAxeMult)
				i.data["damageSetup"]["distribution"]["metalDamage"] = math.floor(i.data["damageSetup"]["distribution"]["metalDamage"] * MetalDamageAxeMult)
				for _, j in pairs(i.data["impactValues"]["simple"]) do
					if j.value["configId"]["value"] == 1236200858 then
						j.value["value"] = AxeSkillGain
					end
				end
				if ReplaceAxeChopWithWideSwing then
					for _, j in pairs(i.data["sequences"]) do
						if j["sequenceId"]["value"] == 1659104355 then
							j["sequenceId"]["value"] = 952468128
							j["sequence"] = "673a64e1-3536-4df8-ba4a-76c33d1778ee"
						end
					end	
				end	
			end
		end
		if i.data["category"] == "BuildTools" and string.find(i.data["debugName"], "Pickaxe") or string.find(i.data["debugName"], "Sieve") then 
			if useAllToolsAnywhere then
				i.data["equipment"]["waterUsability"]["outsideBuildzone"]["allowInsideWater"] = true 
				i.data["equipment"]["waterUsability"]["outsideBuildzone"]["allowOutsideWater"] = true 
				i.data["equipment"]["waterUsability"]["insideBuildzone"]["allowInsideWater"] = true 
				i.data["equipment"]["waterUsability"]["insideBuildzone"]["allowOutsideWater"] = true 
			end
			if PickaxeChanges then 
				i.data["equipment"]["maxDistance"] = PickaxeDistance
				i.data["equipment"]["maxHorizontalDistance"] = PickaxeHorizontalDist
				i.data["equipment"]["minVerticalRelativeHeight"] = i.data["equipment"]["minVerticalRelativeHeight"] * PickaxeMinMaxHeightMult
				i.data["equipment"]["maxVerticalRelativeHeight"] = i.data["equipment"]["maxVerticalRelativeHeight"] * PickaxeMinMaxHeightMult
				for _, j in pairs(i.data["impactValues"]["simple"]) do
					if j.type == "keen::impact::DamageTerraformingSetupConfig" then
						j.value["value"]["softDamage"] = j.value["value"]["softDamage"] * PickaxeTformDamageMult
						j.value["value"]["slightlyHardDamage"] = j.value["value"]["slightlyHardDamage"] * PickaxeTformDamageMult
						j.value["value"]["moderatelyHardDamage"] = j.value["value"]["moderatelyHardDamage"] * PickaxeTformDamageMult
						j.value["value"]["hardDamage"] = j.value["value"]["hardDamage"] * PickaxeTformDamageMult
						j.value["value"]["veryHardDamage"] = j.value["value"]["veryHardDamage"] * PickaxeTformDamageMult
					end
					if j.value["configId"]["value"] == 1381503774 then
						j.value["value"] = j.value["value"] * PickaxeTformSizeMult
					end
					if j.value["configId"]["value"] == 3911595120 then
						j.value["value"] = j.value["value"] * PickaxeTformSizeMult
					end
					if j.value["configId"]["value"] == 1236200858 then
						j.value["value"] = PickaxeSkillGain
					end
				end
			end
		end
	end
end
		
function bLegendaryTools()
	local itemInfoTable = game.assets.get_resources_by_type("keen::ItemInfo")
	
	for _, i in ipairs(itemInfoTable) do
		if i.data["category"] == "BuildTools" or i.data["category"] == "Tools" then
			if string.find(i.data["debugName"], "_Axe_") and not string.find(i.data["debugName"], "T0") then
				i.data["rarity"] = "Legendary" 
				i.data["perkReferences"][4] = "94527392-4714-4e9d-866e-37ddd8da6e00" 
				i.data["perkIds"][4].value = 2581344338
				i.data["perkReferences"][5] = "94527392-4714-4e9d-866e-37ddd8da6e00" 
				i.data["perkIds"][5].value = 2581344338
			end
			if string.find(i.data["debugName"], "Pickaxe") and not string.find(i.data["debugName"], "T0") then
				i.data["rarity"] = "Legendary" 
				i.data["perkReferences"][4] = "dd044daf-784c-46bd-a17b-fca84f903e8b" 
				i.data["perkIds"][4].value = 2028179973
				i.data["perkReferences"][5] = "3b809c7c-f888-4cf0-bcac-16d51c90f347" 
				i.data["perkIds"][5].value = 2665227267
			end
		end
	end
end	

function bTerrainMaterialChanges()
	local TerraformingEfficiencyRegistryTable = game.assets.get_resources_by_type("keen::TerraformingEfficiencyRegistryResource")[1].data
	
	for _, i in pairs(TerraformingEfficiencyRegistryTable) do
		for _,j in pairs(i) do
			if ChangeItemDropRateForBlocks and j["blocksPerLootItemExchangeRate"] ~= nil then
				j["blocksPerLootItemExchangeRate"] = BlocksPerItemDrop
			end
			if AllTerrainIsBreakable and j["hardness"] == "Unbreakable" then
				j["hardness"] = "ModeratelyHard"
			end
			if AddDamageSusceptibility and j["damageSusceptibility"] == "None" then
				j["damageSusceptibility"] = "Stone"
			end
			if FlattenMoreTerrainTypes then
				if j["terrainItem"] == "bef75256-bbd5-45ce-b8d8-eede3d82fbfd" or j["terrainItem"] == "689fce88-018b-4b0f-9b28-2cc478e0c0e6" or j["terrainItem"] == "20292e7b-858b-4e5f-bdc8-e921190eb0f4" or j["maxSubmergePercentage"] == 0.25 then
					j["canBeFlattened"] = true
				end
			end	
			if FlattenAnythingCheat then
				if j["canBeFlattened"] == false then
					j["canBeFlattened"] = true
				end
			end	
			if HarmlessTerrain then
				if j["maxSubmergePercentage"] == 0.25 then
					j["buffReference"] = "6c539793-7021-4cbf-8c9e-cfb2c50f08e1"
					j["maxSubmergeDepth"] = 0.0
					j["maxSubmergePercentage"] = 0.0
				end
				if j["isSlidingMaterial"] == true then
					j["isSlidingMaterial"] = false
					j["frictionFactor"] = 1.0
				end
				if j["terrainItem"] == "9a459ec5-b9c3-4a5d-8df1-b153531a9d55" then
					j["buffReference"] = "6c539793-7021-4cbf-8c9e-cfb2c50f08e1"
				end
				if j["terrainItem"] == "1af1de41-7ad5-4484-8cde-0dc07f63bed6" then
					j["buffReference"] = "6c539793-7021-4cbf-8c9e-cfb2c50f08e1"
					j["maxSubmergeDepth"] = 0.0
					j["maxSubmergePercentage"] = 0.0
				end
				if j["buffReference"] == "60d5ff8d-676d-48a1-b937-78302a7a8dc8" or j["buffReference"] == "61baf0ae-4aab-4d93-a614-35556da385f5" or j["buffReference"] == "07ce9bed-4357-4d22-a919-7af53e4509b9" then
					j["buffReference"] = "6c539793-7021-4cbf-8c9e-cfb2c50f08e1"
					j["maxSubmergeDepth"] = 0.0
					j["minSubmergePercentage"] = 0.0
					j["maxSubmergePercentage"] = 0.0
				end
			end
		end
	end
end

function bLootChanges()
	local LootLabelCollectionTable = game.assets.get_resources_by_type("keen::DefaultLootLabelCollectionResource")
	local SceneRandomLootTable = game.assets.get_resources_by_type("keen::SceneRandomLootResource")
	local TemplateResourcesTable = game.assets.get_resources_by_type("keen::ecs::TemplateResource")
	
	if ChangeLevelOffsetRanges then
		for _ , i in ipairs(LootLabelCollectionTable) do
			for _, j in pairs(i.data["lootSettings"]) do
				if j["modifier"]["levelOffsetRangeMin"] ~= nil then
					j["modifier"]["levelOffsetRangeMin"] = j["modifier"]["levelOffsetRangeMin"] + ExtraLevelOffsetMin
				end
				if j["modifier"]["levelOffsetRangeMax"] ~= nil then
					j["modifier"]["levelOffsetRangeMax"] = j["modifier"]["levelOffsetRangeMax"] + ExtraLevelOffsetMax
				end
			end
		end
		for _ , i in ipairs(SceneRandomLootTable) do
			for _, j in pairs(i.data["lootSettings"]) do
				if j["modifier"]["levelOffsetRangeMin"] ~= nil then
					j["modifier"]["levelOffsetRangeMin"] = j["modifier"]["levelOffsetRangeMin"] + ExtraLevelOffsetMin
				end
				if j["modifier"]["levelOffsetRangeMax"] ~= nil then
					j["modifier"]["levelOffsetRangeMax"] = j["modifier"]["levelOffsetRangeMax"] + ExtraLevelOffsetMax
				end
			end
		end
	end
	
	for _ , i in pairs(TemplateResourcesTable) do
		for _, j in pairs(i.data["components"]) do
			if ChangeDroppedStackCounts then
				if not string.find(i.data["name"], "FogNestDrone") then
					if j.type == "keen::ecs::MiningNode" then
						j.value["aliveDropCount"] = math.floor(j.value["aliveDropCount"] * DroppedStackCountMult)
						j.value["numberOfDrops"] = math.floor(j.value["numberOfDrops"] * DroppedStackCountMult)
					end
					if j.type == "keen::ecs::ResourceNodePickupDrops" then
						j.value["numberOfDrops"] = math.floor(j.value["numberOfDrops"] * DroppedStackCountMult)
					end
				end
				if string.find(i.data["name"], "FogNestDrone") then
					if j.type == "keen::ecs::MiningNode" then
						j.value["aliveDropCount"] = math.floor(j.value["aliveDropCount"] * DroneDroppedStackCountMult)
						j.value["numberOfDrops"] = math.floor(j.value["numberOfDrops"] * DroneDroppedStackCountMult)
					end
					if j.type == "keen::ecs::ResourceNodePickupDrops" then
						for _, k in pairs(j.value["drops"]) do
							k["stackAmount"] = math.floor(k["stackAmount"] * DroneDroppedStackSizeMult)
						end
						j.value["numberOfDrops"] = math.floor(j.value["numberOfDrops"] * DroneDroppedStackCountMult)
					end
				end
			end
			if ChangeLootSlotRanges then
				if j.type == "keen::ecs::RandomLootSlotCount" then
					j.value["slotsMin"] = j.value["slotsMin"] + RandomLootSlotsMin
					j.value["slotsMax"] = j.value["slotsMax"] + RandomLootSlotsMax		
				end
			end
		end
	end
	
end

function bFishingChanges()
	local FishSpawnTable = game.assets.get_resources_by_type("keen::fishing::FishSpawnTableResource")
	local itemInfoTable = game.assets.get_resources_by_type("keen::ItemInfo")
	local fishingTrashTable = game.assets.get_resources_by_type("keen::fishing::TrashLootTableResource")
	local TemplateResources = game.assets.get_resources_by_type("keen::ecs::TemplateResource")

	for _, i in ipairs(itemInfoTable) do
		if BasicRodJunkOnly and string.find(i.data["debugName"], "T1_FishingRod_basic") then 
			i.data["fishingRodItemSetup"]["shoeWeightFactor"] = 0.0
			i.data["fishingRodItemSetup"]["trashWeightFactor"] = 100.0
		end
		if LuckyRodJunkOnly and string.find(i.data["debugName"], "Tool_T6_FishingRod_epic_lucky") then 
			i.data["fishingRodItemSetup"]["shoeWeightFactor"] = 0.0
			i.data["fishingRodItemSetup"]["trashWeightFactor"] = 100.0
		end
		if CursedRodBootOnly and string.find(i.data["debugName"], "Tool_T3_FishingRod_cursed_Loot") then 
			i.data["fishingRodItemSetup"]["shoeWeightFactor"] = 100.0
			i.data["fishingRodItemSetup"]["trashWeightFactor"] = 0.0
		end
		if FishingRodStatChanges and i.data["category"] == "FishingRod" then 
			for _, j in pairs(i.data["impactValues"]["simple"]) do
				if j.value["configId"]["value"] == 416472931 then
					j.value["value"] = j.value["value"] * FishingRodStrengthMult
				end
				if j.value["configId"]["value"] == 1873310336 then
					j.value["value"] = j.value["value"] * FishingRodEndMult
				end
			end
			for _, j in pairs(i.data["uiValues"]) do
				if j["locaId"]["value"] == 3282930761 then
					j["value"] = math.floor(j["value"] * FishingRodStrengthMult)
				end
				if j["locaId"]["value"] == 1302818897 then
					j["value"] = math.floor(j["value"] * FishingRodEndMult)
				end
			end
		end
	end
	
	if RemoveTrashJunkDrops then
		for _, i in ipairs(fishingTrashTable) do
			for _, j in pairs(i.data["entries"]) do
				if j["weight"] == 125.0 then
					j["weight"] = 0.0
				end
				if j["weight"] == 50.0 then
					j["weight"] = 0.0
				end
				if j["weight"] == 81.25 then
					j["weight"] = 0.0
				end
				if j["weight"] == 33.0 then
					j["weight"] = 100.0
				end
				if j["weight"] == 25.0 then
					j["weight"] = 100.0
				end
			end
		end
	end
	
	if FishBehaviorChanges then
		for _ , i in pairs(TemplateResources) do
			for _, j in pairs(i.data["components"]) do
				if j.type == "keen::ecs::Fishable" then
					j.value["minBiteAttempts"] = minFishBiteAttempts
					j.value["maxBiteAttempts"] = maxFishBiteAttempts	
					j.value["endurance"] = j.value["endurance"] * FishEnduranceMult
					j.value["power"] = j.value["power"] * FishPowerMult
					j.value["speed"] = j.value["speed"] * FishSpeedMult
					j.value["minOutbreakDuration"]["value"] = math.floor(j.value["minOutbreakDuration"]["value"] * FishOutbreakDurationMult)
					j.value["maxOutbreakDuration"]["value"] = math.floor(j.value["maxOutbreakDuration"]["value"] * FishOutbreakDurationMult)
					j.value["minTimeUntilVisible"]["value"] = math.floor(j.value["minTimeUntilVisible"]["value"] * FishTimeUntilVisibleMult)
					j.value["maxTimeUntilVisible"]["value"] = math.floor(j.value["maxTimeUntilVisible"]["value"] * FishTimeUntilVisibleMult)
					j.value["quickTimeEventTimeFrame"]["value"] = math.floor(j.value["quickTimeEventTimeFrame"]["value"] * FishQTEDurationMult)
				end
			end
		end
	end
	
	if FishProbabilityTweaks then
		for _ , i in pairs(FishSpawnTable) do
			for _, j in pairs(i.data["fishEntries"]) do
				if j["item"]["value"] == 2004880509 or j["item"]["value"] == 3480216747  then
					j["weight"] = j["weight"] * CommonFishMult
				end	
				if j["item"]["value"] == 2586083671 then
					j["weight"] = j["weight"] * CommonFishRareMult
				end	
				if j["item"]["value"] == 887847819 or j["item"]["value"] == 3445329106 then
					j["weight"] = j["weight"] * UncommonFishMult
				end	
				if j["item"]["value"] == 1216878011 then
					j["weight"] = j["weight"] * UncommonFishRareMult
				end	
				if j["item"]["value"] == 3419031428 or j["item"]["value"] == 3653119547 then
					j["weight"] = j["weight"] * RareFishMult
				end	
				if j["item"]["value"] == 817023891 or j["item"]["value"] == 1675072409 then
					j["weight"] = j["weight"] * RareFishRareMult
				end	
				if j["item"]["value"] == 780626079 or j["item"]["value"] == 2176589336 or j["item"]["value"] == 4044713321 then
					j["weight"] = j["weight"] * EpicFishMult
				end	
			end
		end	
	end	
	
end

function bFarmAnimalChanges()
	local FarmAnimalTable = game.assets.get_resources_by_type("keen::ecs::TemplateResource")
	
	for _, i in ipairs(FarmAnimalTable) do
		if QuickTame then
			for _, j in pairs(i.data["components"]) do
				if j.type == "keen::ecs::Wildlife" then
					j.value["tamingSetup"]["necessaryTamingSteps"] = 1
				end
			end	
		end
		if i.data["family"] == "Animal" and string.find(i.data["name"], "Farm") and not string.find(i.data["name"], "Yak") then
			for _, j in pairs(i.data["components"]) do
				if j.type == "keen::ecs::InteractionLootRefill" then
					j.value["waitTime"]["value"] = math.floor(j.value["waitTime"]["value"] * FarmAnimalWaitTimeMult)
					for _, k in pairs(j.value["items"]) do
						k["refillCount"] = FarmAnimalRefillCount
						k["maxCount"] = FarmAnimalMaxItemCount
					end
				end
				if j.type == "keen::ecs::Animal" then
					j.value["reproductionSetup"]["reproductionRate"]["value"] = math.floor(j.value["reproductionSetup"]["reproductionRate"]["value"] * FarmAnimalReproductionRateMult)
				end
			end
		end
		if i.data["family"] == "Animal" and string.find(i.data["name"], "Farm") and string.find(i.data["name"], "Yak") then
			for _, j in pairs(i.data["components"]) do
				if j.type == "keen::ecs::InteractionLootRefill" then
					j.value["waitTime"]["value"] = math.floor(j.value["waitTime"]["value"] * YakWaitTimeMult)
					for _, k in pairs(j.value["items"]) do
						k["refillCount"] = YakRefillCount
						k["maxCount"] = YakMaxItemCount
					end
				end
				if j.type == "keen::ecs::Animal" then
					j.value["reproductionSetup"]["reproductionRate"]["value"] = math.floor(j.value["reproductionSetup"]["reproductionRate"]["value"] * YakReproductionRateMult)
				end
			end
		end
	end
	
end

function bInteractionChanges()
local ActorSequenceTable = game.assets.get_resources_by_type("keen::actor::ActorSequenceResource")
local SequenceTable = game.assets.get_resources_by_type("keen::SequenceResource")

	for _, i in ipairs(ActorSequenceTable) do
		for _, j in pairs(i.data["subSequences"]) do	
			if FastLooting and string.find(j["name"], "Interaction_Loot") or string.find(j["name"], "Interaction_InventoryUi_Chest") then
				j["length"]["value"] = math.ceil(j["length"]["value"] * math.max(0.35, LootingDurationMult))
				for _, k in pairs(j["events"]) do	
					if k.value["time"]["value"] > 1 then
						k.value["time"]["value"] = math.floor(k.value["time"]["value"] * math.max(0.35, LootingDurationMult))
					end
					if k.value["duration"]["value"] > 1 then
						k.value["duration"]["value"] = math.floor(k.value["duration"]["value"] * math.max(0.35, LootingDurationMult))
					end
				end
			end	
			if FasterLockpicking and string.find(j["name"], "Interaction_Lockpicking") then
				j["length"]["value"] = math.ceil(j["length"]["value"] * math.max(0.35, LockpickingDurationMult))
				for _, k in pairs(j["events"]) do	
					if k.value["time"]["value"] > 1 then
						k.value["time"]["value"] = math.floor(k.value["time"]["value"] * math.max(0.35, LockpickingDurationMult))
					end
					if k.value["duration"]["value"] > 1 then
						k.value["duration"]["value"] = math.floor(k.value["duration"]["value"] * math.max(0.35, LockpickingDurationMult))
					end
				end
			end
			if FasterMining and string.find(j["name"], "Mine_Terraforming_Ore_Interaction") and not string.find(j["name"], "DEPRECATED_") then
				j["length"]["value"] = math.ceil(j["length"]["value"] * math.max(0.35, MiningDurationMult))
				for _, k in pairs(j["events"]) do	
					if k.value["time"]["value"] > 1 then
						k.value["time"]["value"] = math.floor(k.value["time"]["value"] * math.max(0.35, MiningDurationMult))
					end
					if k.value["duration"]["value"] > 1 then
						k.value["duration"]["value"] = math.floor(k.value["duration"]["value"] * math.max(0.35, MiningDurationMult))
					end
				end
			end
			if FasterFlattening and string.find(j["name"], "Mine_Terraforming_Rake") then
				j["length"]["value"] = math.ceil(j["length"]["value"] * math.max(0.35, FlatteningDurationMult))
				for _, k in pairs(j["events"]) do	
					if k.value["time"]["value"] > 1 then
						k.value["time"]["value"] = math.floor(k.value["time"]["value"] * math.max(0.35, FlatteningDurationMult))
					end
					if k.value["duration"]["value"] > 1 then
						k.value["duration"]["value"] = math.floor(k.value["duration"]["value"] * math.max(0.35, FlatteningDurationMult))
					end
				end
			end
		end
	end	

	for _, i in ipairs(SequenceTable) do
		if FasterMining and string.find(i.data["name"], "_pickaxe_work") or string.find(i.data["name"], "_pickaxe_sneak_work") then
			i.data["length"]["value"] = math.ceil(i.data["length"]["value"] * math.max(0.35, MiningDurationMult))
			for _, j in pairs(i.data["events"]) do	
				if j.value["time"]["value"] > 1 then
					j.value["time"]["value"] = math.floor(j.value["time"]["value"] * math.max(0.35, MiningDurationMult))
				end
				if j.value["duration"]["value"] > 1 then
					j.value["duration"]["value"] = math.floor(j.value["duration"]["value"] * math.max(0.35, MiningDurationMult))
				end
			end
		end
	end

end

function bMiscChanges()
	local SkillTreeTable = game.assets.get_resources_by_type("keen::SkillTreeResource")[1].data
	local BalanceTable = game.assets.get_resources_by_type("keen::BalancingTable")[1].data
	local TemplateResourcesTable = game.assets.get_resources_by_type("keen::ecs::TemplateResource")
	
	for _ , i in pairs(TemplateResourcesTable) do
		for _, j in pairs(i.data["components"]) do
			if ChangeGemForgeLevels then
				if j.type == "keen::ecs::ShroudForge" then
					j.value["maxGemLevel"] = math.min(GemForgeLevelCap, math.floor(j.value["maxGemLevel"] * GemForgeLevelMult))	
				end
			end
			if j.type == "keen::ecs::FuelSetup" then
				if WaterContainersStartFull then
					j.value["initialFuelPercentage"] = 100.0
				end
				if DoubleContainerCapacity and j.value["maxFuelCharges"] > 0 and not AllContainersAreMaxCapicity then
					j.value["maxFuelCharges"] = math.min(1000, j.value["maxFuelCharges"] * 2)
				end
				if AllContainersAreMaxCapicity and j.value["maxFuelCharges"] > 0 then
					j.value["maxFuelCharges"] = 1000
				end
			end
		end
	end
	
	if ChangeSkillNodeMaxLevel then
		for _, i in ipairs(SkillTreeTable["nodes"]) do
			if i["maxLevel"] > 2 then
				i["maxLevel"] = SkillNodeMaxLevel
			end
		end
	end
	
	if ChangeComfortSetup then
		BalanceTable["comfortSetup"]["base"] = math.floor(BalanceTable["comfortSetup"]["base"] * ComfortSetupBaseMult)
		BalanceTable["comfortSetup"]["factor"] = BalanceTable["comfortSetup"]["factor"] * ComfortSetupFactorMult
	end
	
	if ChangeDurabilitySetup then
		BalanceTable["durabilityStart"] = BalanceTable["durabilityStart"] * DurabilityStartMult
		BalanceTable["durabilityGrowth"] = BalanceTable["durabilityGrowth"] * DurabilityGrowthMult
	end
	
end

if GearChanges then bGearChanges() end
if ToolChanges then bToolChanges() end
if LegendaryTools then bLegendaryTools() end
if TerrainMaterialChanges then bTerrainMaterialChanges() end
if LootChanges then bLootChanges() end
if FishingChanges then bFishingChanges() end
if FarmAnimalChanges then bFarmAnimalChanges() end
if InteractionChanges then bInteractionChanges() end
if MiscChanges then bMiscChanges() end

