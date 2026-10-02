-- User Config Overrides for Ember (Enshrouded Mod Loader)
-- Automatically loaded by EML runtime

-- ========================================
--                 Misc
-- ========================================
Enable_NoIntroVideo = true
Enable_StackSizeTweaks = true
StackSize_MaxStack = 65535
Enable_MagicFurniture = true
Enable_MagicFactories = true

-- ========================================
--             Exploration & World
-- ========================================
Enable_NoBarriers = true
Enable_SlopeTweaks = true
steepFloorAngle = 60.0
slidingAngle = 75.0
fallDamageAngle = 85.0

-- ========================================
--                 Spells & Magic
-- ========================================
Enable_SpellTweaks = true
SpellCastTime_Multiplier = 0.5
SpellManaCost_Multiplier = 0.0

-- ========================================
--             Shroud & Survival
-- ========================================
Enable_BuffReapplication = true
Enable_ShroudTimerTweaks = true
ShroudTimer_Multiplier = 50.0

-- ========================================
--             Flame Altar & Base Building
-- ========================================
Enable_FlameAltarTweaks = true
MaxFlameAltars_Multiplier = 5.0
MaxFlameAltars_Cap = 100

Enable_BaseSizeTweaks = true
BaseSize_Multiplier = 3.0

Enable_PlacementTweaks = true
Enable_BuildingTweaks = true
PlacementTweaks_BuildInFog = true
PlacementTweaks_NoBuildZoneNeeded = true

-- ========================================
--             Crafting & Progression
-- ========================================
Enable_CraftingTweaks = true
CraftingTweaks_UnlockAllRecipes = true
CraftingTweaks_CreativeMode = false -- Handled via Architect Toolkit on-demand

Enable_SkillPointsPerLevel = true
SkillPointsPerLevel = 5

-- ========================================
--             Expanded Game Settings
-- ========================================
Enable_ExpandedGameSettings = true
ExpandedGameSettings_Config = {
    { Name = "playerHealth", Min = 10, Max = 1000, Steps = 20, Enabled = true },
    { Name = "playerMana", Min = 10, Max = 1000, Steps = 20, Enabled = true },
    { Name = "playerStamina", Min = 10, Max = 1000, Steps = 20, Enabled = true },
    { Name = "bodyHeat", Min = 10, Max = 1000, Steps = 20, Enabled = true },
    { Name = "dropAmount", Min = 10, Max = 1000, Steps = 20, Enabled = true },
    { Name = "miningDamage", Min = 10, Max = 1000, Steps = 20, Enabled = true },
    { Name = "plantGrowTime", Min = 10, Max = 200, Steps = 20, Enabled = true },
    { Name = "productionTime", Min = 10, Max = 200, Steps = 20, Enabled = true }
}
