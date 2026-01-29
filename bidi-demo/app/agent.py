# ruff: noqa
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
import base64

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.agents.run_config import RunConfig
from google.adk.models import Gemini
from google.genai import types

import os
import google.auth
import vertexai

_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

vertexai.init(project=project_id, location="us-central1")


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


class RootAgent(Agent):
    pass


root_agent = RootAgent(
    name="root_agent",
    model=Gemini(
        model="gemini-live-2.5-flash-native-audio",
        retry_options=types.HttpRetryOptions(attempts=3),
        generate_content_config=types.GenerateContentConfig(
            temperature=0.7,
        ),
    ),
    instruction="You are a helpful AI assistant designed to provide accurate and useful information.",
    tools=[get_weather],
)

app = App(root_agent=root_agent, name="app")

with open(<WAV_FILE_NAME>, "rb") as f:
    wav_data = f.read()

run_config = RunConfig(
    response_modalities=["AUDIO"],
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            # prebuilt_voice_config=types.PrebuiltVoiceConfig(
            #     voice_name="Puck",
            # ),
            replicated_voice_config=types.ReplicatedVoiceConfig(
                mime_type="audio/pcm;rate=24000",
                voice_sample_audio=base64.b64encode(wav_data).decode('utf-8'),
            )
        )
    ),
)
