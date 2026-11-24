from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from mcp import Client
from mcp.client.stdio import StdioServerParameters

from sdlc_manager.config import Settings
from sdlc_manager.domain.enums import KnowledgeScope, ReviewStatus
from sdlc_manager.domain.models import Project
from sdlc_manager.infrastructure.container import build_container
from sdlc_manager.infrastructure.database.migrations import run_migrations
from sdlc_manager.mcp.server import get_server_for_tests

PROJECT_ID = "00e57f27-4f4c-47d0-be96-84f1b7162a99"


def resolve_json_schema(schema: dict, root: dict) -> dict:
    resolved = schema
    while "$ref" in resolved:
        reference = resolved["$ref"]
        definition_name = reference.rsplit("/", maxsplit=1)[-1]
        resolved = root["$defs"][definition_name]
    return resolved


@pytest.mark.asyncio
async def test_mcp_discovers_and_invokes_tools(tmp_path: Path) -> None:
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'mcp.db'}",
        policy_paths=[str(Path(__file__).parents[2] / "knowledge" / "rules")],
        project_root=Path(__file__).parents[2],
    )
    server, _ = get_server_for_tests(settings)
    async with Client(server) as client:
        tools = await client.list_tools()
        names = {tool.name for tool in tools.tools}
        assert {
            "health_check",
            "evaluate_gate",
            "register_evidence",
            "get_sdlc_workflow",
            "register_practice",
        }.issubset(names)
        result = await client.call_tool("health_check", {})
        assert result.is_error is False
        assert result.structured_content["status"] == "ok"
        project_result = await client.call_tool(
            "create_project", {"input": {"name": "MCP workflow project"}}
        )
        workflow_result = await client.call_tool(
            "get_sdlc_workflow",
            {"input": {"project_id": project_result.structured_content["id"]}},
        )
        assert workflow_result.is_error is False
        assert len(workflow_result.structured_content["stages"]) == 9


@pytest.mark.asyncio
async def test_mcp_stdio_transport_discovers_tools(tmp_path: Path) -> None:
    root = Path(__file__).parents[2]
    parameters = StdioServerParameters(
        command=str(root / ".venv" / "bin" / "python"),
        args=["-m", "sdlc_manager"],
        env={
            "SDLC_MANAGER_DATABASE_URL": f"sqlite:///{tmp_path / 'stdio.db'}",
            "SDLC_MANAGER_POLICY_PATHS": json.dumps([str(root / "knowledge" / "rules")]),
            "SDLC_MANAGER_PROJECT_ROOT": str(root),
            "SDLC_MANAGER_AUTO_MIGRATE": "true",
        },
    )
    async with Client(parameters) as client:
        tools = await client.list_tools()
        assert "evaluate_gate" in {tool.name for tool in tools.tools}


@pytest.mark.asyncio
async def test_mcp_stdio_accepts_json_uuid_and_detects_generic_policy(
    tmp_path: Path,
) -> None:
    root = Path(__file__).parents[2]
    database_url = f"sqlite:///{tmp_path / 'uuid.db'}"
    settings = Settings(
        database_url=database_url,
        policy_paths=[str(root / "knowledge" / "rules")],
        project_root=root,
    )
    run_migrations(settings)
    container = build_container(settings, initialize_schema=False)
    container.service.projects.save(Project(id=UUID(PROJECT_ID), name="MCP UUID test"))

    parameters = StdioServerParameters(
        command=str(root / ".venv" / "bin" / "python"),
        args=["-m", "sdlc_manager"],
        env={
            "SDLC_MANAGER_DATABASE_URL": database_url,
            "SDLC_MANAGER_POLICY_PATHS": json.dumps([str(root / "knowledge" / "rules")]),
            "SDLC_MANAGER_PROJECT_ROOT": str(root),
            "SDLC_MANAGER_AUTO_MIGRATE": "true",
        },
    )

    async with Client(parameters) as client:
        tools = await client.list_tools()
        applicable_rules = next(tool for tool in tools.tools if tool.name == "get_applicable_rules")
        schema = applicable_rules.input_schema
        input_schema = resolve_json_schema(schema["properties"]["input"], schema)
        project_schema = resolve_json_schema(input_schema["properties"]["project_id"], schema)
        assert project_schema["type"] == "string"
        assert project_schema["format"] == "uuid"
        event_tool = next(tool for tool in tools.tools if tool.name == "process_sdlc_event")
        event_input = resolve_json_schema(
            event_tool.input_schema["properties"]["input"], event_tool.input_schema
        )
        event_id_schema = resolve_json_schema(
            event_input["properties"]["event_id"], event_tool.input_schema
        )
        assert event_id_schema["type"] == "string"
        assert event_id_schema["format"] == "uuid"

        valid_result = await client.call_tool(
            "get_applicable_rules",
            {
                "input": {
                    "project_id": PROJECT_ID,
                    "event": "file_change",
                    "stage": "implementation",
                    "changed_files": ["artifacts/sample.artifact"],
                    "context": {},
                }
            },
        )
        assert valid_result.is_error is False
        assert "DEMO-001" in {rule["id"] for rule in valid_result.structured_content["rules"]}

        event_id = str(uuid4())
        event_result = await client.call_tool(
            "process_sdlc_event",
            {
                "input": {
                    "event_id": event_id,
                    "event_type": "session_started",
                    "source_client": "mcp-inspector",
                    "timestamp": "2026-11-15T00:00:00Z",
                    "context": {},
                }
            },
        )
        duplicate_event_result = await client.call_tool(
            "process_sdlc_event",
            {
                "input": {
                    "event_id": event_id,
                    "event_type": "session_started",
                    "source_client": "mcp-inspector",
                    "timestamp": "2026-11-15T00:00:00Z",
                    "context": {},
                }
            },
        )
        assert event_result.is_error is False
        assert event_result.structured_content["status"] == "PROCESSED"
        assert duplicate_event_result.structured_content["status"] == "DUPLICATE"

        for invalid_project_id in ("", "not-a-uuid"):
            invalid_result = await client.call_tool(
                "get_applicable_rules",
                {
                    "input": {
                        "project_id": invalid_project_id,
                        "event": "file_change",
                        "stage": "implementation",
                        "changed_files": [],
                        "context": {},
                    }
                },
            )
            assert invalid_result.is_error is True


@pytest.mark.asyncio
async def test_mcp_practices_normalize_file_changed_event(tmp_path: Path) -> None:
    root = Path(__file__).parents[2]
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'practices.db'}",
        policy_paths=[str(root / "knowledge" / "rules")],
        project_root=root,
    )
    run_migrations(settings)
    container = build_container(settings, initialize_schema=False)
    project = container.service.create_project("MCP practice project")
    practice = container.service.register_practice(
        title="Validar campos de texto",
        context="Cambios HTML",
        triggers={"event": "file_change", "file_extensions": [".html"]},
        intervention_message="Prevenir SQL injection",
        severity="HIGH",
        scope=KnowledgeScope.PROJECT,
        project_id=project.id,
    )
    container.service.review_practice(practice.id, ReviewStatus.APPROVED, "reviewer")
    server, _ = get_server_for_tests(settings)

    async with Client(server) as client:
        result = await client.call_tool(
            "get_applicable_practices",
            {
                "input": {
                    "event": "file_changed",
                    "stage": "implementation",
                    "changed_files": ["index.html"],
                    "project_id": str(project.id),
                }
            },
        )

    assert result.is_error is False
    assert [item["id"] for item in result.structured_content["practices"]] == [str(practice.id)]
