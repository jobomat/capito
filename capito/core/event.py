subscribers = {}

def subscribe(event_type: str, fn):
    if not event_type in subscribers:
        subscribers[event_type] = []
    if not fn in subscribers[event_type]:
        subscribers[event_type].append(fn)

def unsubscribe(event_type: str, fn):
    if event_type in subscribers:
        if fn in subscribers[event_type]:
            subscribers[event_type].remove(fn)

def post(event_type: str, *args, **kwargs):
    if not event_type in subscribers:
        return
    for fn in subscribers[event_type]:
        fn(*args, **kwargs)

def list_events():
    return list(subscribers.keys())

def list_event_subscribers(event_type: str):
    return [s.__name__ for s in subscribers[event_type]]

def list_all():
    return {
        e: [s.__name__ for s in s_list] for e, s_list in subscribers.items()
    }
