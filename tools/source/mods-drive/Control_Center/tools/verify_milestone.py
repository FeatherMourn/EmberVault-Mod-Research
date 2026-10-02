"""Run the current offline milestone quality gates and emit one JSON result."""
from __future__ import annotations

import json
import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(label: str, args: list[str], extra_env: dict[str, str] | None = None) -> dict[str, object]:
    environment = os.environ.copy()
    if extra_env:
        environment.update(extra_env)
    try:
        result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, env=environment, timeout=180)
    except subprocess.TimeoutExpired as exc:
        return {"name": label, "passed": False, "returncode": None,
                "stdout_tail": str(exc.stdout or "")[-4000:],
                "stderr_tail": (str(exc.stderr or "") + "\nTimed out after 180 seconds.")[-4000:]}
    # Keep enough of the test runner's tail to retain its authoritative
    # ``Ran N tests`` summary as the suite grows.  The old 1200-character
    # window could discard that line and silently write a stale test count.
    return {"name": label, "passed": result.returncode == 0,
            "returncode": result.returncode,
            "stdout_tail": result.stdout[-4000:], "stderr_tail": result.stderr[-4000:]}


def extract_test_count(result: dict[str, object]) -> int | None:
    for line in str(result.get("stderr_tail", "")).splitlines():
        if line.startswith("Ran ") and " tests" in line:
            try:
                return int(line.split(" tests", 1)[0].split()[-1])
            except ValueError:
                return None
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        help="also write the JSON gate result to a versioned evidence file")
    args = parser.parse_args()
    tests_gate = run("tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"], {"CONTROL_CENTER_GATE_RUN": "1"})
    snapshot_args = [sys.executable, "tools/report_capability_snapshot.py"]
    snapshot_args.extend(["--output", "research/CAPABILITY_SNAPSHOT_20260928.json"])
    test_count = extract_test_count(tests_gate)
    if test_count is not None:
        snapshot_args.extend(["--test-count", str(test_count)])
    gates = [
        tests_gate,
        run("compile", [sys.executable, "-m", "compileall", "-q", "core", "gui", "tools"]),
        run("eml_metadata_api", [sys.executable, "tools/verify_eml_metadata_api.py"]),
        run("probe_generator_safety", [sys.executable, "tools/verify_probe_generators.py"]),
        run("interaction_probe_safety", [sys.executable, "tools/verify_interaction_probe.py",
                                          "research/probes/interaction_donor_probe_example/mod.json",
                                          "--expected-build", "1076226"]),
        run("localization_evidence", [sys.executable, "tools/verify_localization_evidence.py", "research/localization_probe_results_1076226.json"]),
        run("localization_session_evidence", [sys.executable, "tools/verify_localization_session_evidence.py", "research/probe_sessions/localization_cycle_20260928_r2/fresh_session_evidence.json", "--expected-build", "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z"]),
        run("localization_boundary", [sys.executable, "tools/verify_localization_boundary_report.py", "research/localization_boundary_reports/latest_stable_check.json"]),
        run("visual_reference_evidence", [sys.executable, "tools/verify_visual_reference_evidence.py", "research/probe_sessions/item_visual_reference_159b_live_20260927.json"]),
        run("registered_visual_evidence", [sys.executable, "tools/verify_visual_reference_evidence.py", "research/probe_sessions/registered_visual_substitution_1076226.json"]),
        run("visual_substitution_session", [sys.executable, "tools/verify_visual_substitution_session.py", "research/probe_sessions/registered_visual_substitution_manual_session_20260928.json", "--expected-build", "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z"]),
        run("visual_evidence_builder", [sys.executable, "-m", "unittest", "tests.test_build_visual_substitution_evidence", "-q"]),
        run("gameplay_feasibility", [sys.executable, "tools/verify_gameplay_feasibility.py", "research/feasibility_reports/builder_placement_2940001508_20260927.json"]),
        run("gameplay_schema_inventory", [sys.executable, "tools/verify_gameplay_schema_inventory.py", "research/GAMEPLAY_SCHEMA_INVENTORY_1076226.json", "--expected-build", "1076226"]),
        run("capability_audit", [sys.executable, "tools/verify_capability_audit.py", "research/CAPABILITY_AUDIT_20260927.json"]),
        run("completion_audit", [sys.executable, "tools/verify_completion_audit.py", "--no-milestone", "--output", "research/COMPLETION_AUDIT_SNAPSHOT_20260928.json"]),
        run("capability_snapshot", snapshot_args),
        run("capability_snapshot_provenance", [sys.executable, "tools/verify_capability_snapshot.py", "research/CAPABILITY_SNAPSHOT_20260928.json"]),
        run("documentation_audit", [sys.executable, "tools/audit_documentation.py"]),
        run("authoring_templates", [sys.executable, "tools/verify_authoring_templates.py", "research/templates"]),
        run("world_generation_plan_validation", [sys.executable, "tools/validate_world_generation_plan.py",
                                                   "research/templates/world_generation_plan_template.json",
                                                   "--expected-build", ""]),
        run("asset_import_boundary", [sys.executable, "tools/verify_asset_import_boundary.py", "research/ORIGINAL_ASSET_IMPORT_BOUNDARY_20260928.md"]),
        run("blender_export_validator", [sys.executable, "-m", "unittest", "tests.test_blender_export_validator", "-q"]),
        run("blender_runtime_evidence", [sys.executable, "-m", "unittest", "tests.test_blender_runtime_evidence", "-q"]),
        run("blender_runtime_log", [sys.executable, "tools/verify_blender_runtime_log.py",
                                      "H:/SteamLibrary/steamapps/common/Enshrouded/logs/2026-09-28.eml.log"]),
        run("asset_container_validation", [sys.executable, "-m", "unittest", "tests.test_asset_pipeline", "-q"]),
        run("tuning_coverage", [sys.executable, "tools/verify_tuning_coverage.py", "research/TUNING_RESEARCH_QUEUE_20260928.json", "--expected-build", "1076226"]),
        run("tuning_runtime_evidence", [sys.executable, "tools/verify_tuning_runtime_evidence.py", "research/probe_sessions/balancing_table_scalar_write_safe_20260929_evidence.json", "--expected-build", "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z"]),
        run("catalog_preview_batch_safety", [sys.executable, "tools/verify_catalog_preview_batch.py",
                                               "research/probe_sessions/catalog_preview_batch_plan_20260928.json",
                                               "research/templates/catalog_preview_probe_matrix.json",
                                               "--expected-build",
                                               "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z"]),
        run("catalog_icon_runtime_evidence", [sys.executable, "tools/verify_catalog_icon_runtime_evidence.py",
                                                "research/probe_sessions/catalog_icon_fallback_runtime_evidence_20260928_r2.json"]),
        run("typed_color_combination_evidence", [sys.executable, "tools/verify_typed_color_combination_evidence.py",
                                                    "research/probe_sessions/typed_color_combination_runtime_evidence_20260930.json",
                                                    "--expected-build",
                                                    "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z"]),
        run("catalog_preview_runtime_evidence", [sys.executable, "tools/verify_catalog_preview_runtime_evidence.py",
                                                  "research/probe_sessions/catalog_preview_image_only_cycle_20260928_r6/runtime_evidence.json"]),
        run("visual_substitution_matrix", [sys.executable, "tools/verify_visual_substitution_matrix.py",
                                             "research/templates/visual_substitution_probe_matrix.json"]),
        run("visual_substitution_batch_plan", [sys.executable, "-m", "unittest",
                                                  "tests.test_plan_visual_substitution_batch", "-q"]),
        run("visual_substitution_batch_safety", [sys.executable, "tools/verify_visual_substitution_batch.py",
                                                   "research/probe_sessions/visual_substitution_batch_plan_20260928.json"]),
        run("multiplayer_authority_report", [sys.executable, "tools/verify_multiplayer_authority_report.py",
                                                "research/MULTIPLAYER_AUTHORITY_FEASIBILITY_20260928.md"]),
        run("metadata_policy", [sys.executable, "tools/verify_metadata_policy.py", "research/SAFE_METADATA_RESOURCE_TYPES_20260928.json"]),
        run("furniture_donor_matrix_evidence", [sys.executable, "tools/verify_furniture_matrix_evidence.py", "research/probe_sessions/furniture_donor_matrix_runtime_evidence_20260928.json"]),
        run("furniture_donor_coverage", [sys.executable, "tools/verify_furniture_donor_coverage.py", "research/content_clone_candidates"]),
        run("furniture_clone_runtime_evidence", [sys.executable, "tools/verify_furniture_clone_runtime_evidence.py", "research/probe_sessions/chair_stool_clone_runtime_evidence_20260930.json"]),
        run("bench_clone_runtime_evidence", [sys.executable, "tools/verify_furniture_clone_runtime_evidence.py", "research/probe_sessions/bench_clone_runtime_evidence_20260930.json"]),
        run("recipe_customization_evidence", [sys.executable, "tools/verify_recipe_customization_evidence.py", "research/probe_sessions/recipe_knowledge_requirement_runtime_evidence_r2_20260928.json"]),
        run("recipe_knowledge_replacement_evidence", [sys.executable, "tools/verify_recipe_customization_evidence.py", "research/probe_sessions/recipe_knowledge_replacement_runtime_evidence_20260928.json"]),
        run("quest_prototype_evidence", [sys.executable, "tools/verify_quest_prototype_evidence.py",
                                           "research/probe_sessions/journal_quest_resource_create_cycle_20260928_edit_evidence.json",
                                           "research/probe_sessions/journal_registry_identity_clone_cycle_20260928_typed_array_evidence.json",
                                           "research/probe_sessions/journal_registry_identity_clone_cycle_20260928_live_attach_evidence.json",
                                           "research/probe_sessions/journal_quest_resource_create_cycle_20260928_edit_restore.json",
                                           "research/probe_sessions/journal_registry_identity_clone_cycle_20260928_typed_array_restore.json",
                                           "research/probe_sessions/journal_registry_identity_clone_cycle_20260928_live_attach_restore.json",
                                           "--expected-build", "1076226"]),
        run("ai_sequence_evidence", [sys.executable, "tools/verify_ai_sequence_evidence.py",
                                        "research/probe_sessions/actor_sequence_event_graph_cycle_20260928/evidence.json",
                                        "research/probe_sessions/actor_sequence_identity_clone_cycle_20260928/evidence.json",
                                        "research/probe_sessions/actor_sequence_identity_clone_cycle_20260928/attachment_evidence.json",
                                        "research/probe_sessions/actor_sequence_identity_clone_cycle_20260928/restore.json",
                                        "research/probe_sessions/actor_sequence_identity_clone_cycle_20260928/restore_attachment.json",
                                        "--expected-build", "1076226"]),
        run("animation_world_metadata_evidence", [sys.executable, "tools/verify_animation_world_metadata_evidence.py",
                                                     "research/probe_sessions/animation_world_metadata_runtime_evidence_20260928.json",
                                                     "--expected-build", "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z",
                                                     "--expected-api", "1.2"]),
        run("animation_graph_donor_evidence", [sys.executable, "tools/verify_animation_graph_donor_evidence.py",
                                                  "research/probe_sessions/animation_graph_single_donor_runtime_evidence_20260928.json",
                                                  "--expected-build", "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z",
                                                  "--expected-api", "1.2"]),
        run("animation_graph_dependency_evidence", [sys.executable, "tools/verify_animation_graph_dependency_evidence.py",
                                                       "research/probe_sessions/animation_graph_dependency_runtime_evidence_20260928.json",
                                                       "--expected-build", "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z",
                                                       "--expected-api", "1.2"]),
        run("animation_dependency_type_evidence", [sys.executable, "tools/verify_animation_dependency_type_evidence.py",
                                                      "research/probe_sessions/animation_dependency_type_runtime_evidence_20260928.json",
                                                      "--expected-build", "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z",
                                                      "--expected-api", "1.3"]),
        run("animation_graph_clone_evidence", [sys.executable, "tools/verify_animation_graph_clone_evidence.py",
                                                  "research/probe_sessions/animation_graph_identity_clone_runtime_evidence_20260928.json",
                                                  "--expected-build", "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z",
                                                  "--expected-api", "1.3"]),
        run("animation_graph_attachment_evidence", [sys.executable, "tools/verify_animation_graph_attachment_evidence.py",
                                                       "research/probe_sessions/animation_graph_npc_attachment_runtime_evidence_20260928.json",
                                                       "--expected-build", "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z",
                                                       "--expected-api", "1.3"]),
        run("animation_graph_edit_evidence", [sys.executable, "tools/verify_animation_graph_edit_evidence.py",
                                                 "research/probe_sessions/animation_graph_idle_variant_runtime_evidence_20260928.json",
                                                 "--expected-build", "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z",
                                                 "--expected-api", "1.3"]),
        run("voxel_world_donor_evidence", [sys.executable, "tools/verify_voxel_world_donor_evidence.py",
                                               "research/probe_sessions/voxel_world_single_donor_runtime_evidence_20260928.json",
                                               "--expected-build", "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z",
                                               "--expected-api", "1.3"]),
        run("voxel_world_dependency_map", [sys.executable, "tools/verify_voxel_world_dependency_map.py",
                                               "research/VOXEL_WORLD_DEPENDENCY_MAP_1076226.json"]),
        run("voxel_material_guid_evidence", [sys.executable, "tools/verify_voxel_material_guid_evidence.py",
                                                 "research/probe_sessions/voxel_material_guid_type_runtime_evidence_20260928.json",
                                                 "--expected-build", "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z",
                                                 "--expected-api", "1.3"]),
        run("voxel_material_full_evidence", [sys.executable, "tools/verify_voxel_material_full_evidence.py",
                                                 "research/probe_sessions/voxel_material_full_metadata_runtime_evidence_20260928.json",
                                                 "--expected-build", "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z",
                                                 "--expected-api", "1.3"]),
        run("scene_voxel_pair_evidence", [sys.executable, "tools/verify_scene_voxel_pair_evidence.py",
                                              "research/probe_sessions/scene_voxel_pair_runtime_evidence_20260928.json",
                                              "--expected-build", "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z",
                                              "--expected-api", "1.3"]),
        run("scene_resource_family_evidence", [sys.executable, "tools/verify_scene_resource_family_evidence.py",
                                                   "research/probe_sessions/scene_resource_family_metadata_runtime_evidence_20260928.json",
                                                   "--expected-build", "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z",
                                                   "--expected-api", "1.3"]),
        run("water_world_donor_evidence", [sys.executable, "tools/verify_water_world_donor_evidence.py",
                                               "research/probe_sessions/water_world_single_donor_runtime_evidence_20260928.json",
                                               "--expected-build", "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z",
                                               "--expected-api", "1.3"]),
        run("water_displacing_evidence", [sys.executable, "tools/verify_water_displacing_evidence.py",
                                               "research/probe_sessions/water_displacing_runtime_evidence_20260928.json",
                                               "--expected-build", "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z",
                                               "--expected-api", "1.3"]),
        run("water_chunk_metadata_evidence", [sys.executable, "tools/verify_water_chunk_metadata_evidence.py",
                                                   "research/probe_sessions/water_chunk_metadata_runtime_evidence_20260928.json",
                                                   "--expected-build", "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z",
                                                   "--expected-api", "1.3"]),
        run("fog_voxel_mapping_evidence", [sys.executable, "tools/verify_fog_voxel_mapping_evidence.py",
                                                "research/probe_sessions/fog_voxel_mapping_runtime_evidence_20260928.json",
                                                "--expected-build", "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z",
                                                "--expected-api", "1.3"]),
        run("research_cycle_validator", [sys.executable, "-m", "unittest", "tests.test_verify_research_cycle", "-q"]),
        run("release_manifest", [sys.executable, "tools/verify_release.py", "--manifest", "packaging/RELEASE_MANIFEST_1.0.2.json"]),
        run("installer_source", [sys.executable, "tools/verify_installer_source.py", "packaging/EnshroudedModHub.iss"]),
        run("installer_smoke", [sys.executable, "tools/verify_installer_smoke.py",
                                "packaging/Output/EnshroudedModHub-1.0.2-Setup.exe",
                                "--expected-portable", "dist/EnshroudedModHub.exe"]),
        run("portable_launch_smoke", [sys.executable, "tools/verify_portable_launch_smoke.py", "research/PORTABLE_LAUNCH_SMOKE_PROCESS_TREE_20260928.json"]),
        run("eml_build_evidence", [sys.executable, "tools/verify_eml_build_evidence.py", "research/EML_BUILD_VERIFICATION_20260928.json"]),
        run("eml_api_runtime_evidence", [sys.executable, "tools/verify_loader_api_runtime.py",
                                             "--evidence", "research/EML_API_VERSION_RUNTIME_EVIDENCE_20260928.json",
                                             "--expected-build", "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z",
                                             "--expected-api", "1.3"]),
        run("post_rollback_stable_launch", [sys.executable, "tools/verify_post_rollback_stable_launch.py",
                                                "research/POST_ROLLBACK_STABLE_LAUNCH_EVIDENCE_20260928.json",
                                                "--expected-build",
                                                "1076226|^/game38/branches/ea_update_08|2026-06-29T10:27:39.052394Z"]),
        run("research_session_launch", [sys.executable, "tools/verify_research_session_launch.py",
                                          "research/probe_sessions/stable_launcher_readiness_20260930.json"]),
        run("save_backup_evidence", [sys.executable, "tools/verify_save_backup_evidence.py",
                                      "research/probe_sessions/save_backup_evidence_20260928.json"]),
    ]
    gates.append(run("update_recovery_workflow", [sys.executable, "-m", "unittest", "tests.test_update_recovery", "-q"]))
    gates.append(run("update_recovery_cli", [sys.executable, "-m", "unittest", "tests.test_plan_update_recovery", "-q"]))
    report = {"schema": "control_center.milestone_verification.v1", "passed": all(item["passed"] for item in gates), "gates": gates}
    if args.output:
        destination = args.output.resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        temporary.replace(destination)
        # The completion audit is intentionally skipped inside the gate list to
        # avoid reading a half-written/self-referential milestone report.  Once
        # the aggregate is authoritative, refresh the public audit against it.
        completion = run("completion_snapshot_refresh", [
            sys.executable, "tools/verify_completion_audit.py",
            "--milestone", str(destination),
            "--output", "research/COMPLETION_AUDIT_SNAPSHOT_20260928.json",
        ])
        if not completion["passed"]:
            report["passed"] = False
            report["gates"].append(completion)
            temporary.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            temporary.replace(destination)
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
