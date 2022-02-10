import time
from collections import deque
from itertools import islice
from typing import List, Deque, Optional, Iterator, Tuple

class BaseClock:
    
    MAX_REPR_INTERVALS = 5
    
    ''' Base clock the registers time intervals. '''
    
    def __init__(self, max_intervals:int=10) -> None:
        self.intervals: Deque[float] = deque(maxlen=max_intervals)
        
    def min(self) -> float:
        ''' Returns the shortest time interval between the events (in seconds). '''
        return min(self.intervals) if len(self.intervals) > 0 else 0.0
    
    def max(self) -> float:
        ''' Returns the longest time interval between the events (in seconds). '''
        return max(self.intervals) if len(self.intervals) > 0 else 0.0
    
    def mean(self) -> float:
        ''' Returns the mean time interval between the events (in seconds). '''
        return sum(self.intervals) / len(self.intervals) if len(self.intervals) > 0 else 0.0
    
    def freq(self) -> float:
        ''' Returns the mean frequency of the events (in Hertz). '''
        mean = self.mean()
        return 1 / mean if mean > 0 else 0.0

    def _repr_props(self) -> Iterator[str]:
        if self.intervals:
            iv_list = [f'{iv:.4f}' for iv in islice(self.intervals, self.MAX_REPR_INTERVALS)]
            if len(self.intervals) > self.MAX_REPR_INTERVALS:
                iv_list.append('...')
            yield f'intervals=[{", ".join(iv_list)}]'
            yield f'min={self.min():.4f}'
            yield f'mean={self.mean():.4f}'
            yield f'max={self.max():.4f}'
    
    def __repr__(self) -> str:
        elems = [self.__class__.__name__] + list(self._repr_props())
        return '<' + ' '.join(elems) + '>'


class Ticker(BaseClock):
    
    ''' A performance profiler that measures the time interval between repeatedly
    occuring events.
    
    Ticker can also calculate basic statistics of the time intervals.
    
    Example usage:
    ```python
    ticker = Ticker(max_intervals=5)
    for i in range(10):
        ticker.tick()
        time.sleep(random.random() / 10)
    print(ticker)
    ```
    Results:
    ```
    <Ticker intervals=[0.0899, 0.0632, 0.0543, 0.0713, 0.0681] min=0.0543 mean=0.0694 max=0.0899>
    ```

    :ivar max_intervals: Maximum number of time intervals to be recorded. Only the last max_intervals
    number of intervals will be kept.
    :ivar intervals: The recorded intervals in seconds between the successive events.
    '''
    
    def __init__(self, max_intervals:int=10) -> None:
        super().__init__(max_intervals=max_intervals)
        self._last_tick: Optional[float] = None
        
    def tick(self) -> None:
        ''' Registers a tick in this Ticker. '''
        now = time.perf_counter()
        if self._last_tick is not None:
            self.intervals.append(now - self._last_tick)
        self._last_tick = now


class StopWatch(BaseClock):
    
    ''' A simple performance profiler with context managers.
    
    There are two ways to use StopWatch: as a context manager, or with the `tick()`
    method. You can use the same StopWatch object in both ways at the same time.
    
    When used as a context managaer, StopWatch can be used to measure the 
    performance of python code using an elegant API based on context manager. 
    You can measure nested and serial execution.
    
    The second way is to measure the average execution of repeating tasks with 
    the `tick()` function call. After enough data samples were collected with 
    `tick()`, you can calculate the average execution of the task calling
    `mean_tick()`.
    
    Example usage:
    ```python
    import time
    with StopWatch('root') as root:
        with root.child('task1', max_ticks=5) as task:
            time.sleep(0.01)
            with task.child('subtask1.1'):
                time.sleep(0.03)
            with task.child('subtask1.2'):
                time.sleep(0.07)
            with task.child('subtask1.3'):
                time.sleep(0.09)
        with root.child('task2') as task:
            time.sleep(0.17)
    print(root)
    ```
    
    Results:
    ```
    <StopWatch name=root total_elapsed=0.9222 children=[
        <StopWatch name=task1 total_elapsed=0.7520 ticks=[0.0501, 0.0601, 0.0701, 0.0802, 0.0902] mean_tick=0.0701 children=[
            <StopWatch name=subtask1.1 total_elapsed=0.0301>, 
            <StopWatch name=subtask1.2 total_elapsed=0.0701>, 
            <StopWatch name=subtask1.3 total_elapsed=0.0902>
        ]>, 
        <StopWatch name=task2 total_elapsed=0.1702>
    ]>
    ```
    
    :param name: The name of this StopWatch
    :param max_intervals: Maximum number of intervals to be recorded. 
    
    :ivar parent: The parent StopWatch
    :ivar children: The name-indexed dictionary of the children StopWatches
    :ivar intervals: The recorded time intervals in seconds spent in the 
        context. If the same object was used multiple times as a context manager,
        up to max_intervals intervals will be accumulated in this variable.
    '''
    
    def __init__(self, name:str, max_intervals:int=10) -> None:
        super().__init__(max_intervals=max_intervals)
        self.name: str = name
        self.parent: Optional['StopWatch'] = None
        self.children: Dict[str, 'StopWatch'] = {}
        self._start: Optional[float] = None
    
    def child(self, name:str, max_intervals:Optional[int]=None) -> 'StopWatch':
        ''' Creates a new or returns an existing child of this StopWatch. 
        
        :param name: Name of the child StopWatch.
        :param max_intervals: Maximum number of intervals to be recorded in the
            child. If None, max_intervals of the parent (this object) will be used.
        '''
        if name in self.children:
            return self.children[name]
        if max_intervals is None:
            max_intervals = self.intervals.maxlen
        child = StopWatch(name, max_intervals=max_intervals)
        child.parent = self
        self.children[name] = child
        return child
    
    def parents(self) -> Iterator['StopWatch']:
        ''' Returns a generator of all parents of this StopWatch. '''
        current = self
        while True:
            current = current.parent
            if not current:
                break
            yield current
            
    def full_name(self) -> str:
        ''' Returns the fully qualified name of this StopWatch, including
        all parents' name. '''
        family = [self.name]
        family.extend(p.name for p in self.parents())
        return '.'.join(reversed(family))
        
    def __enter__(self) -> 'StopWatch':
        ''' Context manager entry point returning self.'''
        self._start = time.perf_counter()
        return self
    
    def __exit__(self, *_) -> None:
        ''' Context manager exit. '''
        self.intervals.append(time.perf_counter() - self._start)
        self._start = None

    @property
    def level(self) -> int:
        ''' Returns the number of parents. '''
        return len(list(self.parents()))
    
    def _repr_props(self) -> Iterator[str]:
        yield f'name={self.name}'
        for prop in super()._repr_props():
            yield prop

    def __repr__(self) -> str:
        ''' Indented string representation of this StopWatch.'''
        lvl = self.level
        indent = "    " * lvl
        nl = '\n'
        props = list(self._repr_props())
        if self.children:
            props.append(f'children=[{", ".join(repr(c) for c in self.children.values())}\n{indent}]')
        return f'{nl if lvl > 0 else ""}{indent}<{self.__class__.__name__} {" ".join(props)}>'


if __name__ == '__main__':
    import random
    with StopWatch('root') as root:
        with root.child('task1', max_intervals=5) as task1:
            time.sleep(0.01)
            with task1.child('subtask1_1') as subtask1_1:
                time.sleep(0.03)
            with task1.child('subtask1_2'):
                time.sleep(0.07)
            with task1.child('subtask1_3'):
                time.sleep(0.09)
            with subtask1_1:
                time.sleep(0.05)
        with root.child('task2') as task2:
            time.sleep(0.17)
    print(root)

    ticker = Ticker(max_intervals=20)
    for i in range(20):
        ticker.tick()
        time.sleep(random.random() / 10)
    print(ticker)