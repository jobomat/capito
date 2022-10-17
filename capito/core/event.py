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

def unsubscribe_by_name(event_type: str, func_name: str):
    if event_type in subscribers:
        to_remove = []
        for subscriber in subscribers[event_type]:
            if subscriber.__name__ == func_name:
                to_remove.append(subscriber)        
        for func in to_remove:
            subscribers[event_type].remove(func)

def unsubscribe_by_qualname(event_type: str, qualname: str):
    if event_type in subscribers:
        to_remove = []
        for subscriber in subscribers[event_type]:
            if subscriber.__qualname__ == qualname:
                to_remove.append(subscriber)        
        for func in to_remove:
            subscribers[event_type].remove(func)

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
