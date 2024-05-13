import threading
import time


class PromptStream:
    def __init__(self):
        self.data = []
        self.index = 0
        self.lock = threading.Lock()
        self.condition = threading.Condition(lock=self.lock)
        self.stream_open = True

    def __iter__(self):
        return self

    def __next__(self):
        with self.lock:
            while self.index >= len(self.data) and self.stream_open:
                self.condition.wait()
            if self.index >= len(self.data):
                raise StopIteration
            value = self.data[self.index]
            self.index += 1
            return value

    def add_data(self, data):
        with self.lock:
            self.data.append(data)
            self.condition.notify()

    def close_stream(self):
        with self.lock:
            self.stream_open = False
            self.condition.notify_all()


class Prompt:
    def __init__(self, prompt):
        self.prompt = prompt
        self.stream = PromptStream()

    def perform_prompt(self):
        repeated = 0
        while True:
            if repeated >= 3:
                break
            repeated += 1

            time.sleep(0.5)
            new_prompt = "New prompt"
            self.stream.add_data(new_prompt)

        self.stream.close_stream()

    def start(self):
        calculation_thread = threading.Thread(target=self.perform_prompt, args=())
        calculation_thread.start()
        return self.stream


prompt_instance = Prompt("What is the capital of the United States?")
stream = prompt_instance.start()

for chunk in stream:
    print(chunk)

print("Stream stopped.")
