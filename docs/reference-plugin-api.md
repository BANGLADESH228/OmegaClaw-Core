# Reference - Plugin API

OmegaClaw provides the plugin API which allows writing plugins to extend the
agent's functionality. Plugin is a MeTTa or Python module which provides the
entry point - function `loadOmegaClawPlugin`. `loadOmegaClawPlugin` function
calls OmegaClaw plugin API in order to implement new agent's features. Plugin
API provides functions to:
- add communication channel integrations
- add LLM provider integrations
- add new skills or remove added skills
- extend LLM prompt by adding new information or removing it
- etc

In order to be loaded the plugin should be included into
[config/plugins.yaml](/config/plugins.yaml) file. Agent loads each module
listed in this file on the start and calls an entry function of each loaded
module. All communication channels and LLM integrations of the OmegaClaw are
implemented using this API. The full list of plugins available in the OmegaClaw
repository can be found in the [config/plugins.yaml](/config/plugins.yaml)
file.

OmegaClaw plugin API is under construction. This is the reason why some APIs
are available only as the Python modules and other only as the MeTTa modules.
Partially it is because writing some kinds of plugins is simpler using Python.

## Communication channel integration

In order to implement new communication channel one should implement two main
functions:
- "receive" - returns the next message received through communication channel
- "send" - sends the message through communication channel

### Python

In Python one should implement class which inherits from
`channels.CommChannel` and implement at least two methods of the ancestor.

```python
import channels

class ExampleCommChannel(channels.CommChannel):

    def start(self) -> None:
        print("ExampleCommChannel is started")

    def stop(self) -> None:
        print("ExampleCommChannel is stopped")

    def receive(self) -> str:
        return "Received message example" 

    def send(self, message: str) -> None:
        print(f"ExampleCommChannel sends {message}")
```

In order to be able using this communication channel the plugin code should
register the instance of the `ExampleCommChannel` in the system using
`registerCommChannel` function.

```python
def loadOmegaClawPlugin():
    channels.registerCommChannel("Example", ExampleCommChannel())
```

### Using communication channel

The first parameter of the `registerCommChannel` function is a channel id which
should be used as a value for the `commchannel` command line parameter to use
the communication channel with the agent (see
[README.md](/README.md#configuration-options)):

```sh
sh run.sh run.metta commchannel=Example
```

## LLM provider integration

In order to implement new LLM provider integration one should provide
implementation of the single function `chat`. The function takes three
parameters:
- `prompt` - the string which is sent to LLM by agent as a prompt, required
- `max_tokens` - maximum number of tokens can be used by provider to answer the
  prompt, default value is 6000
- `reasoning_mode` - the reasoning mode of the LLM, default value is "medium"

### Python

In Python one should implement class which inherits from
`providers.LLMProvider` and implement at least one method of the ancestor.

```python
import providers

class ExampleLLMProvider(providers.LLMProvider):

    def start(self) -> None:
        print("ExampleLLMProvider is started")

    def stop(self) -> None:
        print("ExampleLLMProvider is stopped")

    def chat(self, prompt: str, max_tokens: int = 6000, reasoning_mode: str = "medium") -> str:
        return "LLM answer example" 
```

In order to be able using this LLM provider integration the plugin code should
register the instance of the `ExampleLLMProvider` in the system using
`registerLLMProvider` function.

```python
def loadOmegaClawPlugin():
    providers.registerLLMProvider("Example", ExampleLLMProvider())
```

### Using LLM provider

The first parameter of the `registerLLMProvider` function is a provider id which
should be used as a value for the `provider` command line parameter to use
the LLM provider with the agent (see [README.md](/README.md#configuration-options)):

```sh
sh run.sh run.metta provider=Example
```

## Other agent related APIs

Plugin can dynamically add new skills or modify the agent's prompt if it is
required. This ability is provided by the following MeTTa functions:
- `(add-skill $function $description $arguments)` - adds the skill
- `(remove-skill $function)` - removes the skill by its function name
- `(add-prompt-extension $handle $text)` - adds text to the prompt
- `(remove-prompt-extension $handle)` - removes text from the prompt by the
  handle

One can look at [source code](/src/skills.metta) for detailed description.
Please also look at [workflow plugin](/plugins/workflow/workflow.metta) for the
example of usage.

One can add the callback which is called on each main agent loop iteration:
- `(add-heartbeat-listener $handle $callback)` - adds heartbeat listener
- `(remove-heartbeat-listener $handle)` - removes heartbeat listener

Callback is called once in the beginning of the each loop iteration and it has
a single parameter which receives the iteration number. Please see [unit
tests](/tests/src_skills.metta) for the example of usage.
