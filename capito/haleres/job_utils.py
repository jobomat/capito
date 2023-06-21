from pathlib import Path
from typing import List, Tuple, Dict


def pairwise(iterable):
    """Pair the iterable in packets of 2:
    (s0, s1), (s2, s3), (s4, s5), ...
    """
    a = iter(iterable)
    return zip(a, a)


def get_job_ids(status_text:str) -> Dict[str,str]:
    """Extract all PBS job-files and their corresponding job-ids
    from a jobs status.txt files content
    {job_file: job_id}"""
    lines = status_text.split("\n")

    job_lines = [l for l in lines if l.startswith("    ")]
    return {
        job.split("/")[-1]: job_id.split(".")[0].strip() 
        for job_id, job in pairwise(job_lines)
    }


def create_frame_list(frame_text: str, job_size: int) -> List[Tuple[int,int]]:
    """Takes a text which shows a list of frames
    and returns a list of start-end tuples according to job_size.
    frame_text is a string where frames
    are presented solo
    or as frame ranges (marked by hyphens or colons)
    and are separated either by comma, semicolon or newlines
    """
    if job_size <= 0:
        return []

    frame_text = frame_text.replace("\n", ",").replace(";", ",").replace(":", "-")
    frame_list = [f.strip() for f in frame_text.split(",") if f.strip()]

    frame_range = []
    for frame in frame_list:
        if '-' in frame:
            start, end = map(int, frame.split('-'))
            frame_range.extend(range(start, end + 1))
        else:
            frame_range.append(int(frame))

    frame_range = sorted(list(set(frame_range)))

    if not frame_range:
        return []

    result = []
    job_cycler = 0
    start = frame_range[0]
    last = start
    for f in frame_range:
        if f > last + 1 or job_cycler >= job_size:
            result.append((start, last))
            start = f
            job_cycler = 0
        if f == frame_range[-1]:
            result.append((start, f))
        job_cycler +=1
        last = f
        
    return result
