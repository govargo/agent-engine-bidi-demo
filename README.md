# agent-engine-bidi-demo

ADK & Agent Engine Bidi-Streaming demo Using agent-starter-pack 

### Prepare

```
python -m venv .venv
source .venv/bin/activate
pip install agent-starter-pack
pip install uv
```

### Create project

```
agent-starter-pack create bidi-demo -a adk_live -d agent_engine
```

### Compile

```
cd bidi-demo & make install
```

Note: This project is already committed with custom code after first agent-starter-pack creation

You need to create & deploy voice file for ReplicatedVoice of Live API.
Replace the following section of codes.

```
# app/agent.py

# Put the wav file and replace this section with file name
with open(<WAV_FILE_NAME>, "rb") as f:
```

```
# app/app_utils/deploy.py
source_packages_list.append("custom-voice_consent-voice_20260123_211819.wav")

# Replace this section with file name
source_packages_list.append(<WAV_FILE_NAME>)
```

### Local Test

```
make playground
```

### Deploy to Agent Engine

```
make deploy
```

### Test with Agent Engine

```
make playground-remote
```
