#!/usr/bin/python

import re
import subprocess
from ansible.module_utils.basic import AnsibleModule

def get_pid_by_name(process_name):
  try:
    pid_list = subprocess.check_output(['pgrep', '-f', process_name]).decode().splitlines()
    if pid_list:
      return pid_list[0]
  except subprocess.CalledProcessError:
    return None

def get_jstat_output(pid):
  """Return jstat -gc output for given PID, or None if failed."""
  try:
    output = subprocess.check_output(['jstat', '-gc', pid], stderr=subprocess.DEVNULL).decode()
    return output
  except subprocess.CalledProcessError:
    return None

def parse_heap(jstat_output):
  """Parse used and max heap from jstat output."""
  lines = jstat_output.strip().splitlines()
  if len(lines) < 2:
      return None, None
  values = lines[-1].split()
  try:
    used = float(values[2]) + float(values[3]) + float(values[5]) + float(values[7])
    max_heap = float(values[0]) + float(values[1]) + float(values[4]) + float(values[6])
    return used, max_heap
  except (IndexError, ValueError):
    return None, None

def main():
  module_args= dict(
    process = dict(type='str', required=True)  
  )

  module = AnsibleModule(
    argument_spec=module_args,
    supports_check_mode=True
  )

  process_name = module.params['process']

  try:
    pid = get_pid_by_name(process_name)

    if not pid:
      module.fail_json(msg=f"No PID found for given process name {process_name}")

    jstat_output = get_jstat_output(pid)

    if not jstat_output:
      module.fail_json(msg=f"No jstat ouput for given pid {pid}")

    used_heap, max_heap = parse_heap(jstat_output)

    if used_heap is None or max_heap is None:
      module.fail_json(msg=f"Cannot parse heap from jstat_output")

    result = dict(used_heap = used_heap, max_heap = max_heap)
    module.exit_json(**result)

  except Exception as ex:
    module.fail_json(msg=str(ex))
  
  module.exit_json(**result)

if __name__ == '__main__':
  main()
