import time

from typing import Tuple

# Dummy functions
def first_function() -> Tuple[bool, int]:
    print("First function.")
    return (False, 0)


def second_function() -> Tuple[bool, int]:
    print("Second function.")
    return (True, 5)


def third_function() -> Tuple[bool, int]:
    print("Third function.")
    return (False, 0)


# Event Loop
class EventLoop():

    def __init__(self):
        self.tasks = []

    def add_task(self, task):
        self.tasks.append((task, time.time()))

    def run(self):
        while self.tasks:
            self.tasks.sort(key=lambda task: task[1]) # ineffecient for now
            current_task, task_time = self.tasks[0]
            if time.time() >= task_time:
                self.tasks.pop(0)
                is_reschedule, delay_in_seconds = current_task()
                if is_reschedule:
                    task_new_time = task_time + delay_in_seconds
                    self.tasks.append((current_task, task_new_time))


# Execution
event_loop = EventLoop()
event_loop.add_task(first_function)
event_loop.add_task(second_function)
event_loop.add_task(third_function)
event_loop.run()
