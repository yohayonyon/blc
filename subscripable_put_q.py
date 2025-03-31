import threading
from queue import Queue


class SubscripablePutQ:
    def __init__(self):
        self.queue = Queue()
        self.subscribers = []

    def subscribe(self, publish_function):
        self.subscribers.append(publish_function)

    def publish(self):
        for subscriber in self.subscribers:
            subscriber.event.set()

    def put(self, element):
        self.queue.put(element)
        self.publish()

    def get(self):
        return self.queue.get()

    def empty(self):
        return self.queue.empty()

    def __len__(self):
        return self.queue.qsize()


if __name__ == "__main__":

    # a basic test
    class Subscriber:
        def __init__(self, name):
            self.name = name
            self.event = threading.Event()
            self.keep_going = True

        def receive(self):
            while self.keep_going:
                print(f'Subscriber {self.name} is waiting for the publisher.')
                self.event.wait()
                print(f'Subscriber {self.name} got an event from the publisher. Clearing it')
                self.event.clear()

        def stop(self):
            self.keep_going = False


    print("Creating subscriber 0")
    s0 = Subscriber(0)

    print("Creating subscriber 1")
    s1 = Subscriber(1)

    print("Creating publisher")
    q = SubscripablePutQ()

    print("Subscribing subscriber 0")
    q.subscribe(s0)

    print("putting 'a'")
    q.put('a')

    print("s0 receive")
    t0 = threading.Thread(target=s0.receive)
    t0.start()

    print("Subscribing subscriber 1")
    q.subscribe(s1)

    print("s0 receive")
    t1 = threading.Thread(target=s1.receive)
    t1.start()

    print("putting 'b'")
    q.put('b')

    print("putting 'a' again")
    q.put('b')

    s0.stop()
    s1.stop()

    t0.join()
    t1.join()
