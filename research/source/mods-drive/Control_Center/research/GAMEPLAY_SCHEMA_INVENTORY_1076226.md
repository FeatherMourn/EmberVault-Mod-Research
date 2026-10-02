# Gameplay schema inventory — build 1076226

This inventory is reflection/KFC discovery evidence only. It does not prove that a family is loaded, writable, persistent, or multiplayer-authoritative.

## interaction

Reflected struct candidates: 603
Matching KFC archives: 0

- `keen::ActionSequenceEvent` — 0 fields
- `keen::ActionbarSlotSelection` — 1 fields: index
- `keen::ActorActionContainer` — 1 fields: previewAnimationGraph2Info
- `keen::ActorActionContainerRoot` — 0 fields
- `keen::BaseKnowledgeQueryAction` — 1 fields: invert
- `keen::BauActionCacheFile` — 1 fields: entries
- `keen::BauActionCacheFileEntry` — 2 fields: key, value
- `keen::BauActionDefinition` — 7 fields: type, toolPath, referenceObject, requirements, inputs, outputs, parameters
- `keen::BauActionExtraData` — 1 fields: hash
- `keen::BauActionInput` — 3 fields: id, hash, offset
- `keen::BauActionInputDefinition` — 2 fields: id, path
- `keen::BauActionNodeHandle` — 1 fields: value
- `keen::BauActionNodeInfo` — 9 fields: id, creatorNode, tool, parameters, inputCount, outputCount, extraDataCount, createdNodeCount, type
- `keen::BauActionOutput` — 2 fields: id, hash
- `keen::BauActionOutputDefinition` — 2 fields: id, path
- `keen::BauActionRequest` — 3 fields: type, inputs, tool
- `keen::BauActionRequirements` — 2 fields: expectedMemoryUsage, optimalCpuCount
- `keen::BauActionResponse` — 4 fields: version, outputs, actions, extraData
- `keen::BauConverterMessageActionFinished` — 8 fields: id, error, workerIndex, allocationInfo, receiveTime, sendTime, convertStartTime, convertEndTime
- `keen::BauConverterMessageStartAction` — 3 fields: path, id, reduceCpuUsage
- `keen::BauGraphActionNodeId` — 1 fields: value
- `keen::BauGraphActionNodeTypeStatistics` — 7 fields: toolName, parseNodeCount, convertNodeCount, totalInputEdgeCount, totalOuptutEdgeCount, totalExtraContentSize, totalNewActionCount
- `keen::BauGraphQueryActionNode` — 8 fields: id, creatorNode, toolIndex, inputCount, outputCount, minDistance, type, hasError
- `keen::CounterKnowledgeQueryAction` — 5 fields: usePlayerKnowledge, worldKnowledge, playerKnowledge, operation, count
- `keen::CraftingAction` — 2 fields: station, count
- `keen::CraftingQueryAction` — 1 fields: recipe
- `keen::CursorActionConfig` — 3 fields: hideWhenUnused, snapPositionToAddableVoxel, snapPositionToRemovableVoxel
- `keen::DefaultParseActionParameters` — 1 fields: objectId
- `keen::DialogKnowledgeQueryAction` — 1 fields: dialogOption
- `keen::DungeonWhiteboxReplacement` — 2 fields: whiteboxInstanceId, newWhiteboxDefinitionId
- `keen::DungeonWhiteboxReplacements` — 1 fields: replacements
- `keen::FbUiLocaGameplayActionLabels` — 146 fields: locomotionMoveLeft, locomotionMoveRight, locomotionMoveForward, locomotionMoveBackward, locomotionMove, locomotionMoveSlowMode, cameraRotateLeft, cameraRotateRight, cameraRotateUp, cameraRotateDown, cameraRotate, cameraZoomIn, cameraZoomOut, mainHandAction, mainHandActionWhenBuilding, secondaryBuildingAction, secondaryBuildingActionVoxelsAndShapes, secondaryBuildingActionOvergrowthAndDecay, contextualAction, weaponSkill
- `keen::FbUiLocaHudItemUseMessages` — 7 fields: hookshotUseFail, doorOpenFail, gliderUseFail, gliderUseHint, itemMovedToEquipmentSlotByUsing, itemFailedInsufficientStamina, overgrowthMaterialNeedsTool
- `keen::FbUiLocaMenuSettings` — 292 fields: tabGame, tabDisplay, tabSound, tabAccessibility, tabControls, tabLegal, privacyPolicyParagraphs, settingContextual, settingAuto, settingOff, settingOn, settingBoost, settingLowest, settingLow, settingMedium, settingHigh, settingUltra, settingPerformance, settingBalance, settingQuality
- `keen::FbUiLocaUiActionLabels` — 191 fields: recipeUpgrade, repairItem, confirm, finish, cancel, back, openHint, close, leave, join, remove, changeGeneric, secondaryAction, tertiaryAction, quaterneryAction, deleteSaveData, moveObject, navigationMoveUp, navigationMoveDown, navigationMoveLeft
- `keen::FbUiMouseHints` — 18 fields: left, right, middle, button4, button5, wheel, wheelUp, wheelDown, wheelUpDown, wheelLeft, wheelRight, wheelLeftRight, directionalContext, move, moveUp, moveDown, moveLeft, moveRight
- `keen::FbUiSoundsActionbar` — 3 fields: cantUse, moveHighlight, cycleActionbar
- `keen::FbUiStatusEffectsIcons` — 8 fields: gemStormsEye, gemFocusedLight, gemCorruption, gemSoulReaping, gemBleeding, gemBurning, gemPoison, gemPuncturing
- `keen::FbUiUserPermissions` — 6 fields: kickBanPermissionDesc, accessInventoriesPermissionDesc, editBasePermissionDesc, editWorldPermissionDesc, extendBasePermissionDesc, canReceiveEXPPermissionDesc
- `keen::FlameAltarCountQueryAction` — 2 fields: operation, count
- … 563 additional reflected candidates omitted from the compact report

Next step: select one donor and run a bounded read-only metadata probe.

## ai

Reflected struct candidates: 384
Matching KFC archives: 0

- `keen::CameraCombatAssistanceSettings` — 16 fields: enabled, holdAfterCombatEndDuration, decreaseDelayDuration, increaseLerpSpeed, decreaseLerpSpeed, resetLerpSpeed, maxAdditionalDistance, maxBigTargetsAdditionalDistance, weightAggro, weightDistance, weightLineOfSight, weightAttackToken, weightSoftLockTarget, doScreenHorizontalEdgeAssistance, doScreenVerticalEdgeAssistance, doSilentUpdate
- `keen::CameraCombatHitApproachSettings` — 8 fields: enabled, approachMaxCount, approachMinResultingDistance, approachMaxDistanceOffset, approachLerpSpeed, approachResetLerpSpeed, approachResetTime, onlyWhenNoTargets
- `keen::CombatModifierSettings` — 2 fields: assistanceSettings, hitApproachSettings
- `keen::ContainedWhiteboxSpawnerIds` — 1 fields: ids
- `keen::EnemyPhase` — 0 fields
- `keen::EntitySpawnDefinition` — 3 fields: templateReference, model, color
- `keen::EntitySpawnInfo` — 11 fields: unlockKnowledge, subEntityKnowledgeQueries, knowledgeUnlockOperations, isQuestEntity, isSavePoint, knowledgeQuery, lootContainerId, fogRemovalId, entityAnimation, entityAnimationSlotMask, questItems
- `keen::FbUiHudEnemyAwareness` — 13 fields: iconHeight, fadeOutMinScale, fadeOutMinAlpha, fadeOutRangeXZ, fadeOutRangeY, alertRangeBackground, alertFillOuter, alertFillInner, aggroAddOn, highAlertPulseStrength, alertMinColor, alertMaxColor, aggroColor
- `keen::GenericSpawnerInfo` — 1 fields: supportedContextsPerEntry
- `keen::PrefabEntitySpawn` — 2 fields: objectId, contentPass
- `keen::QuestItemSpawnInfo` — 1 fields: itemId
- `keen::RandomSpawnerBalancing` — 3 fields: fewAmountFactor, manyAmountFactor, extremeAmountFactor
- `keen::SceneEntityChunkSpawn` — 2 fields: index, transform
- `keen::SceneEntitySpawn` — 7 fields: entitySpawnDefinition, templateReference, templatePreviewContentHash, spawnData, storeSceneId, snapToGround, enableFloorMaterial
- `keen::SceneEntitySpawnData` — 21 fields: velocity, tintColor, triggerRange, triggerRange2, triggerRange3, triggerOffset, level, levelOffset, enemySettings, randomSpawnerSettings, enemyTestFlags, npcTestFlags, animalTestFlags, ambience, enemyMarkerTag, teleporterId, teleportTargetId, jumpDistance, jumpHeight, jumpLaunchOffset
- `keen::SceneEntitySpawnResource` — 9 fields: transform, templateReference, spawnData, components, uniqueId, labelCombinationHandle, snapToGround, enableFloorMaterial, hasQueries
- `keen::SceneEntitySpawnTemplate` — 1 fields: defaultEntityTemplate
- `keen::SpawnInfo` — 2 fields: lastVisitedBase, uniqueSceneId
- `keen::SpawnTemplateGuids` — 2 fields: templateGuids, templateCount
- `keen::SpawnTemplateModel` — 2 fields: templateGuid, modelsGuid
- `keen::SpawnTemplateModels` — 2 fields: templateModels, templateCount
- `keen::WeatherSpawnParameters` — 1 fields: eventProbabilityModifier
- `keen::WhiteboxRandomSpawnerData` — 3 fields: whiteboxDefinitionId, description, spawnEntries
- `keen::WhiteboxSpawnerEntry` — 4 fields: entityTemplateId, weight, whiteboxLabels, canContainLoot
- `keen::WhiteboxSpawnerInstanceConvertInfo` — 7 fields: replacementId, parentId, entityTemplateId, whiteboxInstanceId, worldTransform, entitySpawnData, tags
- `keen::actor::ActivateCombatStanceEvent` — 0 fields
- `keen::actor::EnemyCommandEvent` — 1 fields: eventType
- `keen::actor::SpawnCookEntitesEvent` — 0 fields
- `keen::actor::SpawnEntityBaseEvent` — 33 fields: requiredSkill, forbiddenSkill, templateReference, spawnTransform, attachmentSlot, spawnSlot, orientToTargetOnSpawn, useTargetingPosition, orientToTargetOffset, spawnOffset, vfxDirection, providedTarget, consume, onConsumeExchange, addWeaponReference, despawnAfterSequence, endSequenceOnDespawn, transferUsedItem, copyCustomString, destroySpawnerWhenEntityIsDead
- `keen::actor::SpawnEntityCommomEvent` — 4 fields: isProjectile, clearProjectiles, increasesEnemySpawnCount, maxSpawnByEnemyAmount
- `keen::actor::SpawnEntityEvent` — 0 fields
- `keen::actor::SpawnEntityPerAggroTargetEvent` — 4 fields: excludedTargetStates, onlyPlayerTargets, randomPerTargetSpawnRadius, maxTargets
- `keen::actor::SpawnFishingFloatEvent` — 0 fields
- `keen::actor::SpawnImpact` — 6 fields: impact, eventGuid, damageDistribution, colliderData, impactValues, damageDistributionIsSet
- `keen::actor::StoreEnemyMarkerPositionAsTargetEvent` — 2 fields: markerType, targetType
- `keen::debug::EnemyDebugMenu` — 4 fields: entries, lootLabels, filters, maxLevel
- `keen::debug::EnemyDebugMenuFilterEntry` — 2 fields: displayName, filter
- `keen::debug::EnemyLootTagsEntry` — 2 fields: displayName, labelCollection
- `keen::debug::EnemyRuntimeSpawnEntry` — 4 fields: displayName, entity, sortPriority, isAG2
- `keen::debug::EnemySpawnEntry` — 4 fields: displayName, entity, sortPriority, isAG2
- … 344 additional reflected candidates omitted from the compact report

Next step: select one donor and run a bounded read-only metadata probe.

## quest

Reflected struct candidates: 136
Matching KFC archives: 0

- `keen::CompletableJournalCollection` — 3 fields: questSource, type, hideInUi
- `keen::CompletableJournalEntry` — 0 fields
- `keen::DevJournalRegistryResource` — 0 fields
- `keen::FbUiJournalBaseInfo` — 4 fields: iconFlameAltar, iconNpc, iconNpcBed, iconAnimal
- `keen::FbUiLocaMenuJournal` — 90 fields: page, pageNavigation, pagesUnlocked, rewards, activeQuest, objective, location, completed, documentItem, loreCategoryUnsorted, loreCategoryUndiscovered, noUncompletedMainQuestsHint, noUncompletedSideQuestsHint, noUncompletedQuestsHint, noUncompletedFlamebornQuestsHint, noUncompletedMissedQuestsHint, noCompletedQuestsHint, questCategoryActive, questCategoryInactive, noActiveQuestSelected
- `keen::FbUiQuestlogNpcViews` — 11 fields: blacksmith, alchemist, huntress, farmer, carpenter, cryptKeeper, bard, chineseNewYearTrader, barber, fisher, ancientResearcher
- `keen::FbUiSoundsMenuJournal` — 5 fields: openTile, closeTile, openLoreTile, closeLoreTile, setQuestActive
- `keen::FbUiWorldEvent` — 9 fields: eventId, mainTexture, ornament, initialColor, secondaryColor, rippleColor, imageSize, sfx, text
- `keen::FbUiWorldEvents` — 0 fields
- `keen::GiCullRequestedAmbientRaysWithRayBudgetParameters` — 5 fields: cascadeOriginAndSpacing, maxRayCount, maxProbeCount, rayBatchSize, debugEnabled
- `keen::GiCullRequestedRaysWithRayBudgetParameters` — 10 fields: spatialCache, maxRaysPerProbe, maxRayCount, frustumRaysScaleUpBudgetThreshold, rayBatchSize, maxProbeCount, debugEnabled, sortRaysIntoBins, rayBinCascadeStartOffset, useRayCache
- `keen::HolisticBauFileInfoRequest` — 1 fields: path
- `keen::HolisticFindMultiReferenceRequest` — 1 fields: objectIds
- `keen::HolisticFindReferenceRequest` — 1 fields: objectId
- `keen::HolisticGetObjectDescriptionRequest` — 1 fields: objectId
- `keen::HolisticGetObjectHistoryRequest` — 3 fields: objectId, includeDirectChildren, includeAllChildren
- `keen::HolisticGetTestObjectIdsRequest` — 1 fields: testTagId
- `keen::HolisticResourceGraphRequest` — 3 fields: rootResourceType, blackListResourceTypes, platformId
- `keen::JournalCollection` — 0 fields
- `keen::JournalCollectionBase` — 3 fields: name, referencedDocumentName, priority
- `keen::JournalCollectionResource` — 7 fields: entryId, loreCategory, name, referencedDocumentName, priority, isTutorial, entries
- `keen::JournalCompletionRequirement` — 0 fields
- `keen::JournalDirectory` — 0 fields
- `keen::JournalEntry` — 1 fields: voiceover
- `keen::JournalEntryBase` — 6 fields: name, text, mapMarkerReference, itemIcon, speaker, locaDirectionNote
- `keen::JournalEntryLevel` — 1 fields: recommendedLevel
- `keen::JournalEntryResource` — 10 fields: entryId, name, text, mapMarkerReference, knowledgeRequirement, completionRequirement, progressStepsRequirement, voiceover, itemIconId, recommendedLevel
- `keen::JournalExperienceReward` — 1 fields: experience
- `keen::JournalItemReward` — 1 fields: item
- `keen::JournalItemSet` — 1 fields: setName
- `keen::JournalItemSetCategory` — 1 fields: categoryName
- `keen::JournalItemSetCategoryResource` — 2 fields: categoryName, entries
- `keen::JournalItemSetDirectory` — 0 fields
- `keen::JournalItemSetEntry` — 5 fields: itemRef, lockedImageOverride, questDocumentRef, questPageRef, recipeReference
- `keen::JournalItemSetEntryCollectiblePropRef` — 2 fields: collectibleDisplayProp, hasVariants
- `keen::JournalItemSetEntryHintResource` — 6 fields: hintStateKnowledgeQuery, completionStateKnowledgeQuery, objective, hintDescription, mapMarkerReference, recommendedLevel
- `keen::JournalItemSetEntryResource` — 9 fields: entryId, itemId, lockedImageOverride, completionKnowledgeQuery, questReference, recipeId, collectibleDisplayProp, hasMultipleDisplayProps, hints
- `keen::JournalItemSetInfo` — 6 fields: debugName, setId, experienceValueId, completionKnowledgeQuery, unlockKnowledgeQuery, entryQueries
- `keen::JournalItemSetRecipeReward` — 1 fields: recipeReward
- `keen::JournalItemSetResource` — 7 fields: setId, setName, experienceValueId, entries, recipeRewards, completionKnowledgeQuery, unlockKnowledgeQuery
- … 96 additional reflected candidates omitted from the compact report

Next step: select one donor and run a bounded read-only metadata probe.

## animation

Reflected struct candidates: 251
Matching KFC archives: 0

- `keen::AnimGraphPreviewSeqence` — 1 fields: entries
- `keen::AnimGraphPreviewSeqenceEntry` — 3 fields: eventType, timeFromStart, selectedIndex
- `keen::Animation` — 20 fields: animation_node, hierarchy, modelHint, modelHintSet, clothCollider, startFrame, endFrame, refFrame, space, xanimScale, visualToleranceMeters, loopType, autoLoopEpsilon, loopLve, exportJointAnimation, exportLveAnimation, exportRootMotionRotation, exportSequenceData, exportDebugData, ignoreForGenderMapping
- `keen::AnimationConverterConfiguration` — 2 fields: checkParentNames, checkMatrixDecomposition
- `keen::AnimationEventSequence` — 2 fields: hierarchyPreviewSettings, previewClothCollider
- `keen::AnimationGraphBoolInput` — 1 fields: value
- `keen::AnimationGraphFloatInput` — 1 fields: value
- `keen::AnimationGraphIdInput` — 1 fields: value
- `keen::AnimationGraphInfo` — 8 fields: id, postProcessId, nodes, floatInputs, uintInputs, boolInputs, overlays, modelHierarchy
- `keen::AnimationGraphInputBase` — 1 fields: hash
- `keen::AnimationGraphInputs` — 7 fields: floatInputs, uintInputs, boolInputs, intInputs, idInputs, overlayInputs, rootMotionConfig
- `keen::AnimationGraphIntInput` — 1 fields: value
- `keen::AnimationGraphUintInput` — 1 fields: value
- `keen::AnimationInfo` — 12 fields: length, jointCount, frameCount, modelHint, modelHintSet, hierarchy, hasRootMotion, useRootMotionRotation, hasSequences, loops, space, name
- `keen::AnimationJoint` — 3 fields: orientation, position, scale
- `keen::AnimationJointQuality` — 2 fields: trackName, quality
- `keen::AnimationSequenceContainer` — 1 fields: sequences
- `keen::AnimationSequenceEvent` — 0 fields
- `keen::EntityAnimationPath` — 12 fields: slot, useConstantVelocity, constantVelocity, fixedDurationInSeconds, easeInSeconds, easeOutSeconds, constantRotationSpeedX, constantRotationSpeedY, constantRotationSpeedZ, loop, pingPong, close
- `keen::EntityAnimationPathPoint` — 5 fields: offset, orientation, waitInSeconds, easeIn, easeOut
- `keen::FbUiAltarAttentionMarkerAnim` — 9 fields: altarAttentionMarkerFadeIn, altarAttentionMarkerFadeOut, altarAttentionMarkerSecondPingDelay, altarAttentionMarkerAnimDelay, altarAttentionMarkerGrow, altarAttentionMarkerPingSize, altarAttentionMarkerMinAlpha, altarAttentionMarkerPingStartAlpha, altarAttentionMarkerPingEndAlpha
- `keen::FbUiAnimatedHealthBarColors` — 6 fields: frameColor, rangeColor, fillColor, fillEndColor, damageColor, healColor
- `keen::FbUiHudAnimalTaming` — 7 fields: tamingIconEmpty, tamingIconPending, tamingIconFull, tamingAttention, tamingAlert, tamingAlertOutline, tamingIconColor
- `keen::FoliageAnimationAdvancedParameters` — 4 fields: branchPhaseOffset, detailFrequency, edgeAmplitude, branchAmplitude
- `keen::FoliageAnimationModelParameters` — 3 fields: assetHeightFactor, globalStiffnessFactor, advancedParameters
- `keen::FoliageAnimationShaderParameters` — 5 fields: flags, precomputedBendScale, globalStiffnessFactor, advancedParameters, pushBack
- `keen::GrassAnimationModelParameters` — 2 fields: largeDisplacementWeight, smallDisplacementWeight
- `keen::GrassAnimationShaderParameters` — 5 fields: flags, largeDisplacementWeight, smallDisplacementWeight, oneOverModelHeight, pushBack
- `keen::JointAnimation` — 10 fields: hierarchyHash, positionFactor, positionTangent, scaleFactor, headers, data, fps, frameCount, jointCount, flags
- `keen::JointAnimationHeader` — 9 fields: dataOffset, startTime, endTime, usedOrientationJoints, nonConstOrientationJoints, usedPositionJoints, nonConstPositionJoints, usedScaleJoints, nonConstScaleJoints
- `keen::LveAnimation` — 7 fields: trackName, orientationKeys, positionKeys, startToEnd, fps, frameCount, flags
- `keen::PreviewAnimGraph2` — 2 fields: animGraphId, useFemaleAnimation
- `keen::RootMotionAnimation` — 5 fields: orientations, positions, startToEnd, fps, frameCount
- `keen::SourceFileSceneInfoAnimationNode` — 1 fields: name
- `keen::SourceFileXanimInfo` — 3 fields: startFrame, endFrame, timeSpans
- `keen::SourceFileXanimInfoTimeSpan` — 3 fields: name, startFrame, endFrame
- `keen::actor::AnimationEventInputFloatId` — 2 fields: parameterId, parameterValue
- `keen::actor::AnimationEventInputParameterId` — 2 fields: parameterId, parameterValue
- `keen::actor::PetAnimalEvent` — 0 fields
- `keen::actor::SetAnimationEvent` — 5 fields: animationName, usePureLveLocomotion, alignLveLocomotionToFloor, scaleLveWithMovementInput, retriggerAnimation
- … 211 additional reflected candidates omitted from the compact report

Next step: select one donor and run a bounded read-only metadata probe.

## world_generation

Reflected struct candidates: 302
Matching KFC archives: 0

- `keen::BakeWorldTriangleMaterialDataTriangleShaderParameters` — 8 fields: triangleCount, vertexOffset, indexOffset, perVertexBakingDataOffset, translationAndScale, bakedTriangleMaterialDataOffset, feedbackDataOffset, debug
- `keen::BakeWorldTriangleMaterialDataVertexShaderParameters` — 5 fields: layerCount, vertexCount, vertexOffset, perVertexBakingDataOffset, translationAndScale
- `keen::BaseFogVoxelMaterial` — 2 fields: sideDisplacement, topDisplacement
- `keen::BaseVoxelMaterial` — 0 fields
- `keen::BiomeMap` — 1 fields: baseBiome
- `keen::BiomeMapInfo` — 2 fields: size, data
- `keen::BiomeMapLayer` — 1 fields: biome
- `keen::BiomeVoxelMaterial` — 8 fields: grassland, desert, wetland, steppes, deepforest, coldheights, talltrees, ancientland
- `keen::BiomeVoxelMaterialMapping` — 2 fields: id, biomes
- `keen::BrickVoxelDilateShaderParameters` — 2 fields: dwordCount, innerSize
- `keen::BrickVoxelMaterialCopyShaderParameters` — 2 fields: dwordCount, buildingMaterialLayerCount
- `keen::ChangeVoxelData` — 3 fields: isBuildingVoxel, placeVoxelMaterial, placeVoxelMaterialId
- `keen::ConditionalVoxelMaterialBuffType` — 2 fields: minSubmergePercentage, buffType
- `keen::CountingWorldKnowledgeObject` — 1 fields: generateAdditionalPlayerKnowledge
- `keen::DecorativeFogVoxelMaterial` — 0 fields
- `keen::DetailScatterCullVoxelParameters` — 2 fields: showDetailScatterVoxels, showDetailScatterBricks
- `keen::FbUiSharedWorldTag` — 1 fields: tagLabel
- `keen::FbUiSharedWorldTags` — 0 fields
- `keen::FogVoxelMappingInfo` — 4 fields: type, level, removalId, boundingBox
- `keen::FogVoxelMappingResource` — 1 fields: mapping
- `keen::FogVoxelMaterial` — 1 fields: level
- `keen::FogVoxelMaterialResolved` — 3 fields: id, type, level
- `keen::FogVoxelMaterialResolvedList` — 1 fields: fogMaterials
- `keen::GameKnowledgeGenerationScope` — 1 fields: knowledgeTypes
- `keen::GiPopulateWorldCacheRayListParameters` — 11 fields: spatialCache, maxRayCount, maxProbeCount, rayBatchSize, frameId, rotateRays, randomDirectionScale, sortRaysIntoBins, rayBinCascadeStartOffset, atlasSizeX, atlasSizeY
- `keen::GiProbeBlendWorldCacheRadianceParameters` — 5 fields: maxProbeCount, maxRayRadiance, debugProbeIndex, previousExposureInverse, exposure
- `keen::GiVoxelBuildingMaterial` — 3 fields: top, side, bottom
- `keen::GiVoxelBuildingMaterialResource` — 2 fields: dataBlock, materialCount
- `keen::GiVoxelMaterial` — 11 fields: albedo, roughness, emissive, emissiveGiFactor, emissiveExposureCorrectionFactor, emissiveFactor, metallic, reflectance, tilingFactor, emissiveMap, albedoMap
- `keen::GiWorldCacheBlendSphericalHarmonicsIrradianceParameters` — 2 fields: maxProbeCount, debugEnabled
- `keen::PackedShaderWorldPositionUniform` — 1 fields: position
- `keen::PackedShaderWorldTransform` — 3 fields: position, scale, orientation
- `keen::PbrTerrainMaterialBlendingSmoothness` — 3 fields: position, smoothness, heightBias
- `keen::PbrTerrainMaterialCenterBlendingSmoothness` — 2 fields: smoothness, heightBias
- `keen::PbrTerrainMaterialLayer` — 6 fields: albedoMap, roughnessMap, normalMap, heightMap, aoMap, tilingSize
- `keen::PrefabVoxelWorldSceneContent` — 6 fields: whiteboxes, voxelObjects, voxelBrushes, destructionBubbles, roads, tunnels
- `keen::SceneVoxelBrush` — 10 fields: model, color, material, disableDisplacement, resolveBiomePerVoxel, paintMaterialOnly, blitFunction, allowNonManifold, removableFogId, addDestructionEdge
- `keen::SceneVoxelBrushTemplate` — 1 fields: defaultModel
- `keen::SceneVoxelContent` — 5 fields: passes, destructionBubbles, surfaceMaterialBubbles, nonConnectingRoads, displacementBlockers
- `keen::SceneVoxelContentPass` — 10 fields: passIndex, blockOuts, voxelObjects, voxelBrushes, caves, tunnels, roads, instances, dungeonRoomInstances, proceduralLayers
- … 262 additional reflected candidates omitted from the compact report

Next step: select one donor and run a bounded read-only metadata probe.

## multiplayer_authority

Reflected struct candidates: 148
Matching KFC archives: 0

- `keen::DebugServerKnowledgeMessage` — 4 fields: changeCounter, playerIndex, isPlayerKnowledge, unlockedKnowledge
- `keen::DebugServerRemovePlayerKnowledgeMessage` — 1 fields: playerIndex
- `keen::ExtendedServerSaveGame` — 3 fields: version, sceneOffsetChangeCounter, dayTime
- `keen::FbUiHudServerPerformance` — 8 fields: badPerformanceHintDuration, badPerformanceHintInterval, criticalPerformanceHintDuration, criticalPerformanceHintInterval, badPerformanceBgColor, badPerformanceTextColor, criticalPerformanceBgColor, criticalPerformanceTextColor
- `keen::FbUiLocaHudServerPerformance` — 10 fields: performanceBad, performanceBadHost, performanceBadDesc, performanceBadDescHost, performanceCritical, performanceCriticalHost, performanceCriticalDesc, performanceCriticalDescHost, currentServerPerformance, currentServerPerformanceHost
- `keen::FbUiNetworkQualityColors` — 3 fields: good, acceptable, bad
- `keen::FbUiPermissionIcons` — 12 fields: kick, editBase, editWorld, upgradeBase, accessStorage, canReceiveEXP, kickNotSet, editBaseNotSet, editWorldNotSet, upgradeBaseNotSet, accessStorageNotSet, canReceiveEXPNotSet
- `keen::FbUiServerRole` — 3 fields: type, roleName, permissions
- `keen::FbUiServerRoleSettings` — 2 fields: defaultServerRoles, serverRoleIcons
- `keen::Game38ServerResources` — 3 fields: shared, emotes, gameKnowledgeQueryTriggerResource
- `keen::ItemPermissionSetup` — 2 fields: permissions, isSet
- `keen::ServerSaveGame` — 6 fields: version, bases, entities, progressEntity, entitySerializationContext, playTime
- `keen::ServerSaveGameMeta` — 10 fields: version, saveGameId, lastPlayTime, progressLevel, name, playTime, gameSettingsPreset, lastUsedBaseId, sharedScreenShots, activeAltarCount
- `keen::ds::DebugServerKnowledgeMessage` — 4 fields: changeCounter, playerIndex, isPlayerKnowledge, unlockedKnowledge
- `keen::ds::DebugServerRemovePlayerKnowledgeMessage` — 1 fields: playerIndex
- `keen::ds::ExtendedServerSaveGame` — 3 fields: version, sceneOffsetChangeCounter, dayTime
- `keen::ds::FbUiHudServerPerformance` — 8 fields: badPerformanceHintDuration, badPerformanceHintInterval, criticalPerformanceHintDuration, criticalPerformanceHintInterval, badPerformanceBgColor, badPerformanceTextColor, criticalPerformanceBgColor, criticalPerformanceTextColor
- `keen::ds::FbUiLocaHudServerPerformance` — 10 fields: performanceBad, performanceBadHost, performanceBadDesc, performanceBadDescHost, performanceCritical, performanceCriticalHost, performanceCriticalDesc, performanceCriticalDescHost, currentServerPerformance, currentServerPerformanceHost
- `keen::ds::FbUiNetworkQualityColors` — 3 fields: good, acceptable, bad
- `keen::ds::FbUiPermissionIcons` — 12 fields: kick, editBase, editWorld, upgradeBase, accessStorage, canReceiveEXP, kickNotSet, editBaseNotSet, editWorldNotSet, upgradeBaseNotSet, accessStorageNotSet, canReceiveEXPNotSet
- `keen::ds::FbUiServerRole` — 3 fields: type, roleName, permissions
- `keen::ds::FbUiServerRoleSettings` — 2 fields: defaultServerRoles, serverRoleIcons
- `keen::ds::Game38ServerResources` — 3 fields: shared, emotes, gameKnowledgeQueryTriggerResource
- `keen::ds::ItemPermissionSetup` — 2 fields: permissions, isSet
- `keen::ds::ServerSaveGame` — 6 fields: version, bases, entities, progressEntity, entitySerializationContext, playTime
- `keen::ds::ServerSaveGameMeta` — 10 fields: version, saveGameId, lastPlayTime, progressLevel, name, playTime, gameSettingsPreset, lastUsedBaseId, sharedScreenShots, activeAltarCount
- `keen::ds::ecs::AggroTargetNetworkData` — 2 fields: state, entityId
- `keen::ds::ecs::BaseServerConsumedPlayerInput` — 1 fields: inputConsumer
- `keen::ds::ecs::BuffNetworkData` — 4 fields: lifeTime, endOfLife, buffTypeId, level
- `keen::ds::ecs::DynamicNetworkLocomotion` — 9 fields: floorNormal, desiredWorldLookDirection, desiredLeanDirection, state, flags, lastStateSwitchTime, currentIdleAnimation, currentWalkAnimation, gliderTurbulenceScreenShakeIntensity
- `keen::ds::ecs::DynamicServerProgress` — 1 fields: preferredSpawnAltar
- `keen::ds::ecs::NetworkActor` — 10 fields: sequenceRuntimeId, currentAbilityMask, currentState, setStateMask, unsetStateMask, interactionHostId, currentActionEntityTags, usedItemId, triggerType, currentActionState
- `keen::ds::ecs::NetworkAggro` — 1 fields: targets
- `keen::ds::ecs::NetworkCameraControl` — 3 fields: isCameraIdLocked, lockedCameraId, cameraOverride
- `keen::ds::ecs::NetworkComfort` — 2 fields: hearthEntityId, level
- `keen::ds::ecs::NetworkConsumedPlayerInput` — 0 fields
- `keen::ds::ecs::NetworkCookingData` — 2 fields: cookingHearthEntityId, mask
- `keen::ds::ecs::NetworkCursor` — 9 fields: currentBuildingItemId, currentBuildingItemPIDE, randomYawAngleOffset, cursorEntityId, hoveredObjectId, selectedObjectId, selectedObjectDismantleMethod, serverFlags, isInPropVariationSequence
- `keen::ds::ecs::NetworkDurability` — 2 fields: durability, durabilityMax
- `keen::ds::ecs::NetworkFishing` — 21 fields: state, lastError, lastErrorCounter, stateStartTime, outbreakDirection, chargeProgression, lineEndurancePercentage, fishEndurancePercentage, fightsToPlay, currentRound, minigameId, directionDuration, floatId, fishId, selectedFishable, fishableRarity, flags, minigameInputState, fishHookedTime, quickTimeEventStartTime
- … 108 additional reflected candidates omitted from the compact report

Next step: select one donor and run a bounded read-only metadata probe.
