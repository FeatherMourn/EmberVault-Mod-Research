"""Pure offline safety model for a future GameSettingsAdapter."""
VALID_FIELDS = {
    "playerHealthFactor","playerManaFactor","playerStaminaFactor","playerBodyHeatFactor","playerDivingTimeFactor","enableDurability","enableStarvingDebuff","foodBuffDurationFactor","fromHungerToStarving","shroudTimeFactor","tombstoneMode","enableGliderTurbulences","weatherFrequency","fishingDifficulty","miningDamageFactor","plantGrowthSpeedFactor","resourceDropStackAmountFactor","factoryProductionSpeedFactor","perkUpgradeRecyclingFactor","perkCostFactor","experienceCombatFactor","experienceMiningFactor","experienceExplorationQuestsFactor","randomSpawnerAmount","aggroPoolAmount","enemyDamageFactor","enemyHealthFactor","enemyStaminaFactor","enemyPerceptionRangeFactor","bossDamageFactor","bossHealthFactor","threatBonus","pacifyAllEnemies","tamingStartleRepercussion","dayTimeDuration","nightTimeDuration","curseModifier"
}

def validate_request(field, value, *, bounds=None):
    if field not in VALID_FIELDS: return {"accepted":False,"state":"UNSUPPORTED_FIELD"}
    if isinstance(value,(dict,list)) or value is None: return {"accepted":False,"state":"INVALID_VALUE"}
    if bounds is None: return {"accepted":False,"state":"BOUNDS_UNPROVEN"}
    low,high=bounds
    if not low <= value <= high: return {"accepted":False,"state":"OUT_OF_BOUNDS"}
    return {"accepted":True,"state":"VALIDATED_OFFLINE_ONLY"}

def mutation_result(*, dispatch_proven=False, readback_success=False, restore_success=False):
    if not dispatch_proven: return {"success":False,"state":"DISPATCH_UNPROVEN"}
    if not readback_success: return {"success":False,"state":"READBACK_FAILED","chainAnotherMutation":False}
    if not restore_success: return {"success":False,"state":"RESTORE_UNVERIFIED","chainAnotherMutation":False}
    return {"success":True,"state":"completed"}
