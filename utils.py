from threading import Timer
import logging

run = True


def set_interval(func, interval):
    global run

    def func_wrapper():
        set_interval(func, interval)
        func()
    if run:
        return Timer(interval, func_wrapper).start()


# Should be intervals - run is global - not ideal
def stop_interval():
    global run
    run = False
    logging.info(f"stopping interval...")
