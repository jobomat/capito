import copy
from pathlib import Path
import re
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


def _count_generator(reader):
    """Helper function for count_lines"""
    b = reader(1024 * 1024)
    while b:
        yield b
        b = reader(1024 * 1024)


def count_lines(file:Path):
    """Fast line counting for a given file."""
    with file.open('rb') as fp:
        c_generator = _count_generator(fp.raw.read)
        count = sum(buffer.count(b'\n') for buffer in c_generator)
        return count + 1


def is_valid_frame_list(frame_text: str) -> bool:
    # Define the regex pattern to match frame lists
    pattern = r'^\d+(-\d+)?(?:[,;\n]\s*\d+(-\d+)?)*$'
    
    # Check if the frame_text matches the pattern
    return bool(re.match(pattern, frame_text))


def create_flat_frame_list(frame_text:str):
    frame_text = frame_text.replace("\n", ",").replace(";", ",").replace(":", "-")
    frame_list = [f.strip() for f in frame_text.split(",") if f.strip()]

    frame_range = []
    for frame in frame_list:
        if '-' in frame:
            start, end = map(int, frame.split('-'))
            frame_range.extend(range(start, end + 1))
        else:
            frame_range.append(int(frame))
    
    return sorted(list(set(frame_range)))


def create_frame_tuple_list(frame_text: str, job_size: int) -> List[Tuple[int,int]]:
    """Takes a text which shows a list of frames
    and returns a list of start-end tuples according to job_size.
    frame_text is a string where frames:
      - are presented solo
      - or as frame ranges (marked by hyphens or colons)
      - and are separated either by comma, semicolon or newlines
    """
    if job_size <= 0:
        return []

    frame_range = create_flat_frame_list(frame_text)

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


def get_job_limit_map(free_nodes: int, pending_job_map: Dict[str, int]) -> Dict[str, int]:
    """
    pending_job_map is a map of jobnames and pending jobfiles for this jobname.
    A jobname is put together py the share (cg1, 2, 3) plus the actual jobname.
    e.g. {"cg1/shot01": 25, "cg1/shot3": 5, "cg3/shot12": 10, ...}

    returns a dict with the suggested limits for each jobname.
    e.g. {"cg1/shot01": 10, "cg1/shot3": 5, "cg3/shot12": 10, ...}

    these limits can be used as first parameter of the submit.sh script.
    """
    pending_jobs = sum(pending_job_map.values())
    limit_map = {jobname: 0 for jobname in pending_job_map}

    while free_nodes > 0 and pending_jobs > 0:
        num_jobs = sum(n != 0 for n in pending_job_map.values())
        even_share = int(free_nodes / num_jobs) or 1
        # even_share = even_share or 1

        for job, num in pending_job_map.items():
            chunk = min(num, even_share, free_nodes)
            limit_map[job] += chunk
            pending_job_map[job] -= chunk
            free_nodes -= chunk
            pending_jobs -= chunk

    return limit_map


def extract_variables_from_template(template:str) -> list:
    """Extracts python placeholder like variables from template.
    Example:
        "I am %(name)s. I'm %(age)s years old."
        returns: ['name', 'age']
    """
    pattern = r"%\((\w+)\)s"
    matches = re.findall(pattern, template)
    return matches


def check_template_with_data(template:str, data:dict):
    """Get information about keys in a template."""
    for var in extract_variables_from_template(template):
        if var not in data.keys():
            print(f"Key '{var}' missing in data.")


def create_missing_keys(template:str, data:dict):
    """For a given template and data-dict
    returns a new data dict with all keys of the original data-dict
    plus keys for each additionally found variable in template
    containing the key as python variable notation itself.
    Example:
        template = "I am %(name)s. I'm %(age)s years old.",
        data = {"name": "Max"}
        returns: {"name": "Max", "age": "%(age)"}  
    """
    data_copy = copy.deepcopy(data)
    for var in extract_variables_from_template(template):
        if var not in data.keys():
            data_copy[var] = f"%({var})s"
    return data_copy


def replace(template, data):
    """Replace all python placeholder strings found in data.keys
    but preserve not found placeholders as they were."""
    data = create_missing_keys(template, data)
    return template % data