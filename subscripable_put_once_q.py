import threading

from subscripable_put_q import SubscripablePutQ


class SubscripablePutOnceQ(SubscripablePutQ):
    def __init__(self):
        super().__init__()
        self.all_elements = set()
        self.lock = threading.Lock()
        self.handled_num = 0

    def put(self, element):
        self.lock.acquire()
        if element in self.all_elements:
            self.lock.release()
            return
        self.queue.put(element)
        self.all_elements.add(element)
        self.lock.release()
        self.publish()

    def get_handled_num(self):
        return self.handled_num

    def get(self):
        if not self.queue.empty():
            self.handled_num += 1
        return super().get()


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


    print("Creating and starting subscriber 0")
    s0 = Subscriber(0)
    t0 = threading.Thread(target=s0.receive)
    t0.start()

    print("Creating publisher")
    q = SubscripablePutOnceQ()

    print("putting 'a'")
    q.put('a')

    print("Subscribing subscriber 0")
    q.subscribe(s0)

    print("putting 'a' again")
    q.put('a')

    print("putting 'b'")
    q.put('b')

    print("Creating and starting subscriber 1")
    s1 = Subscriber(1)
    t1 = threading.Thread(target=s1.receive)
    t1.start()

    print("putting 'b' again")
    q.put('b')

    print("putting 'c'")
    q.put('c')

    print("Subscribing subscriber 1")
    q.subscribe(s1)

    print("putting 'a' again")
    q.put('a')

    print("putting 'b' again")
    q.put('b')

    print("putting 'c' again")
    q.put('c')

    print("putting 'd'")
    q.put('d')

    s0.stop()
    s1.stop()

    t0.join()
    t1.join()
