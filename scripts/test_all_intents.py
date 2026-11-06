
import requests
import json

MODEL = "phi3.5:latest"

SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {
            "type": "string",
            "enum": [
                "alarm_set", "alarm_query",
                "calendar_set", "calendar_query",
                "calendar_remove", "weather_query",
                "datetime_query", "recommendation_events"
            ]
        },
        "date": {"type": ["string", "null"]},
        "time": {"type": ["string", "null"]},
        "place": {"type": ["string", "null"]}
    },
    "required": ["intent", "date", "time", "place"],
    "additionalProperties": False
}

EXAMPLES = """
Command: set an alarm for seven am tomorrow in London
Output: {"intent":"alarm_set","date":"tomorrow","time":"seven am","place":"London"}

Command: what time is my alarm set for tomorrow
Output: {"intent":"alarm_query","date":"tomorrow","time":null,"place":null}

Command: schedule a meeting on Friday at three pm in London
Output: {"intent":"calendar_set","date":"Friday","time":"three pm","place":"London"}

Command: do i have any meetings scheduled the weekend after next
Output: {"intent":"calendar_query","date":"the weekend after next","time":null,"place":null}

Command: cancel my meeting on Monday
Output: {"intent":"calendar_remove","date":"Monday","time":null,"place":null}

Command: what is the weather in Paris tomorrow
Output: {"intent":"weather_query","date":"tomorrow","time":null,"place":"Paris"}

Command: what time is it in Tokyo
Output: {"intent":"datetime_query","date":null,"time":null,"place":"Tokyo"}

Command: what time is it in London
Output: {"intent":"datetime_query","date":null,"time":null,"place":"London"}

Command: tell me the current time in Delhi
Output: {"intent":"datetime_query","date":null,"time":null,"place":"Delhi"}

Command: recommend events in London this weekend
Output: {"intent":"recommendation_events","date":"this weekend","time":null,"place":"London"}
"""

TESTS = [
    ("set an alarm for seven am tomorrow in London",
     {"intent":"alarm_set","date":"tomorrow","time":"seven am","place":"London"}),

    ("what time is my alarm set for tomorrow",
     {"intent":"alarm_query","date":"tomorrow","time":None,"place":None}),

    ("schedule a meeting on Friday at three pm in London",
     {"intent":"calendar_set","date":"Friday","time":"three pm","place":"London"}),

    ("do i have any meetings scheduled the weekend after next",
     {"intent":"calendar_query","date":"the weekend after next","time":None,"place":None}),

    ("cancel my meeting on Monday",
     {"intent":"calendar_remove","date":"Monday","time":None,"place":None}),

    ("what is the weather in Paris tomorrow",
     {"intent":"weather_query","date":"tomorrow","time":None,"place":"Paris"}),

    ("what time is it in Tokyo",
     {"intent":"datetime_query","date":None,"time":None,"place":"Tokyo"}),

    ("recommend events in London this weekend",
     {"intent":"recommendation_events","date":"this weekend","time":None,"place":"London"})
]

passed = 0

for i, (command, expected) in enumerate(TESTS, 1):

    prompt = f"""You are an accurate command parser.
Learn the exact pattern from these examples:

{EXAMPLES}

IMPORTANT RULES:
1. Select exactly one allowed intent.
2. Copy date, time and place exactly as written in the command.
3. Never convert words into numbers or dates.
4. Never invent missing values.
5. Missing values must always be JSON null.
6. Never use empty strings or "not specified".
7. For datetime_query commands:
   - The city after "in" is always the place.
   - The city must NEVER be placed in the time field.
   - For "what time is it in Tokyo":
     date = null, time = null, place = "Tokyo".
8. The word "time" in a question does not mean that the time slot is provided.
9. Return only valid JSON with exactly four keys.

NEW COMMAND: {command}
"""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": MODEL,
                "prompt": prompt,
                "format": SCHEMA,
                "stream": False,
                "options": {
                    "temperature": 0,
                    "seed": 42
                }
            },
            timeout=120
        )

        response.raise_for_status()
        output = response.json()["response"]

        print(f"\nTEST {i}: {command}")
        print("Output:", output)

        actual = json.loads(output)

        if actual == expected and set(actual.keys()) == set(expected.keys()):
            passed += 1
            print("Result: PASS")
        else:
            print("Result: FAIL")
            print("Expected:", expected)

    except Exception as error:
        print(f"Result: ERROR - {error}")

print("\n------------------------------")
print(f"FINAL SCORE: {passed}/8")
print(f"PASSED: {passed} | FAILED: {8-passed}")
print("------------------------------")
