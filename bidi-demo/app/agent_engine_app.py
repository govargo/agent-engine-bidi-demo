# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import logging
import os
from typing import Any, AsyncIterable
import asyncio

import vertexai
from dotenv import load_dotenv
from google.adk.artifacts import GcsArtifactService, InMemoryArtifactService
from google.adk.sessions import InMemorySessionService, VertexAiSessionService
from google.cloud import logging as google_cloud_logging
from vertexai.agent_engines.templates.adk import AdkApp
from vertexai.preview.reasoning_engines import AdkApp as PreviewAdkApp

from app.agent import app as adk_app, run_config
from app.app_utils.telemetry import setup_telemetry
from app.app_utils.typing import Feedback

# Load environment variables from .env file at runtime
load_dotenv()


class ConfigInjectingQueue(asyncio.Queue):
    """Queue wrapper that injects run_config into the first item."""

    def __init__(self, original_queue: asyncio.Queue, config: Any):
        self._original_queue = original_queue
        self._config = config
        self._first_item_processed = False

    async def get(self) -> Any:
        item = await self._original_queue.get()
        if not self._first_item_processed:
            self._first_item_processed = True
            if isinstance(item, dict):
                item["run_config"] = self._config.model_dump(mode="json")
        return item


class AgentEngineApp(AdkApp):
    def set_up(self) -> None:
        """Initialize the agent engine app with logging and telemetry."""
        # Patch app name if running in Agent Engine to satisfy VertexAiSessionService
        agent_engine_id = os.environ.get("GOOGLE_CLOUD_AGENT_ENGINE_ID")
        if agent_engine_id and self._tmpl_attrs.get("app"):
            self._tmpl_attrs["app"].name = agent_engine_id

        vertexai.init()
        setup_telemetry()
        super().set_up()
        logging.basicConfig(level=logging.INFO)
        logging_client = google_cloud_logging.Client()
        self.logger = logging_client.logger(__name__)
        if gemini_location:
            os.environ["GOOGLE_CLOUD_LOCATION"] = gemini_location

    def register_feedback(self, feedback: dict[str, Any]) -> None:
        """Collect and log feedback."""
        feedback_obj = Feedback.model_validate(feedback)
        self.logger.log_struct(feedback_obj.model_dump(), severity="INFO")

    def register_operations(self) -> dict[str, list[str]]:
        """Registers the operations of the Agent."""
        operations = super().register_operations()
        operations[""] = operations.get("", []) + ["register_feedback"]
        # Add bidi_stream_query for adk_live
        operations["bidi_stream"] = ["bidi_stream_query"]
        return operations

    async def bidi_stream_query(
        self,
        request_queue: Any,
    ) -> AsyncIterable[Any]:
        """Bidi streaming query the ADK application with injected run_config."""
        wrapped_queue = ConfigInjectingQueue(request_queue, run_config)
        async for event in PreviewAdkApp.bidi_stream_query(self, wrapped_queue):
            yield event


def get_session_service():
    """Builds the session service based on the environment."""
    agent_engine_id = os.environ.get("GOOGLE_CLOUD_AGENT_ENGINE_ID")
    if agent_engine_id:
        # Patch app name to match Agent Engine ID for Vertex AI Session Service
        adk_app.name = agent_engine_id
        return VertexAiSessionService(
            project=os.environ.get("GOOGLE_CLOUD_PROJECT"),
            location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"),
        )
    return InMemorySessionService()


gemini_location = os.environ.get("GOOGLE_CLOUD_LOCATION")
logs_bucket_name = os.environ.get("LOGS_BUCKET_NAME")
agent_engine = AgentEngineApp(
    app=adk_app,
    artifact_service_builder=lambda: GcsArtifactService(bucket_name=logs_bucket_name)
    if logs_bucket_name
    else InMemoryArtifactService(),
    session_service_builder=get_session_service,
)
