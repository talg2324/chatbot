import json
import argparse

import requests


def colorize(text, role):
    """Add color formatting based on message role."""
    colors = {
        "system": "\033[93m",  # Yellow
        "user": "\033[94m",    # Blue
        "assistant": "\033[92m",  # Green
        "bold": "\033[1m",     # Bold
        "reset": "\033[0m"     # Reset
    }

    if role in colors:
        return f"{colors[role]}{text}{colors['reset']}"
    return text


class OllamaChat:
    def __init__(self, model, system_prompt_file):
        """Initialize the Ollama chat interface with specified model and settings."""
        self.model = model
        self.api_url = "http://localhost:11434/api/chat"
        with open(system_prompt_file, 'r') as f:
            self.system_prompt = ' '.join(f.read().split('\n'))
        self.messages = [{"role": "system", "content": self.system_prompt}]
        self.role_display = {
            "system": "[System]",
            "user": "[You]",
            "assistant": "[Assistant]"
        }

    def send_message(self, user_message):
        """Send a message to the Ollama API and handle the response."""
        self.messages.append({"role": "user", "content": user_message})

        try:
            payload = {
                "model": self.model,
                "messages": self.messages,
                "stream": True
            }

            full_response = self._stream_response(payload)
            return full_response

        except Exception as e:
            error_msg = f"Error communicating with Ollama: {e}"
            print(error_msg)
            # Remove the user message as it wasn't processed
            self.messages.pop()
            return error_msg

    def _stream_response(self, payload):
        """Stream the response from Ollama and print it chunk by chunk."""
        full_response = ""

        try:
            with requests.post(self.api_url, json=payload, stream=True) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk_data = json.loads(line)
                            if "message" in chunk_data and "content" in chunk_data["message"]:
                                chunk = chunk_data["message"]["content"]
                                print(chunk, end="", flush=True)
                                full_response += chunk
                            if chunk_data.get("done", False):
                                break

                        except json.JSONDecodeError:
                            continue

                self.messages.append({"role": "assistant", "content": full_response})
                return full_response

        except Exception as e:
            error_msg = f"\nError streaming response: {e}"
            print(error_msg)
            return error_msg

    def start_interactive_session(self):
        """Start an interactive chat session in the terminal."""
        start_msg = f"""Starting chat with {self.model}.
        Special commands:
            !clear - clears the conversation (resets model context)
            !exit - ends the session.
            !history - print the entire conversation
        In long chats, you should periodically clear the conversation, otherwise your chat will start to become slow.
        """
        print(colorize(start_msg, 'user'))
        print(f"\n{colorize(self.role_display['system'], 'system')}: {self.system_prompt}")
        print("-" * 50)

        try:
            while True:
                user_input = input(f"\n{colorize('[You]:', 'user')} ").strip()
                if not user_input:
                    continue
                ret_code = self.parse_user_input(user_input)
                if ret_code:
                    break
        except KeyboardInterrupt:
            print("\nEnding chat session.")

    def parse_user_input(self, user_input: str) -> int:
        if user_input == '!exit':
            print("Ending chat session.")
            ret_code = 1
        elif user_input == "!history":
            for msg in self.messages:
                role = msg["role"]
                content = msg["content"]

                print(f"\n{colorize(self.role_display[role], role)}: {content}")
            ret_code = 0
        elif user_input.lower() == "!clear":
            self.messages = [{"role": "system", "content": self.system_prompt}]
            print("Conversation history cleared.")
            ret_code = 0
        else:
            # Process normal message
            print(f"{colorize('[Assistant]:', 'assistant')} ", end="", flush=True)
            self.send_message(user_input)
            print()
            ret_code = 0
        return ret_code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chat with Ollama models from the command line")
    parser.add_argument("--model", "-m", default="gemma3", help="Model name to use (default: gemma3)")
    parser.add_argument("--system-prompt-file", "-s", default="system.txt", help="Path to system prompt file to use")

    args = parser.parse_args()

    chat = OllamaChat(
        model=args.model,
        system_prompt_file=args.system_prompt_file,
    )

    chat.start_interactive_session()
