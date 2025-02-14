#!/usr/bin/python2.4
#
# Copyright 2011 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ========================================================================

"""Generates Omaha build file and Omaha customization unit test file."""

import subprocess
import os


omaha_project_path = os.path.dirname(__file__) + "\\.."
proxy_clsid_file_name = omaha_project_path + "\\proxy_clsids.txt"
customization_ut_file_name = (omaha_project_path +
                              "\\common\\omaha_customization_proxy_clsid.h")


def _GetStatusOutput(cmd):
  """Return (status, output) of executing cmd in a shell."""
  if os.name != "nt":
    return subprocess.getstatusoutput(cmd)
  pipe = os.popen(f"{cmd} 2>&1", "r")
  text = pipe.read()
  sts = pipe.close()
  if sts is None: sts = 0
  if text[-1:] == "\n": text = text[:-1]
  return sts, text


def _GenerateGuid():
  (status, guid) = _GetStatusOutput("uuidgen.exe /c")
  if status != 0:
    raise SystemError(f"Failed to get GUID: {guid}")
  return guid


def _GuidToCStructFormat(guid):
  return ("{0x%s, 0x%s, 0x%s, "
          "{0x%s, 0x%s, 0x%s, 0x%s, 0x%s, 0x%s, 0x%s, 0x%s}}" % (
              guid[:8],
              guid[9:13],
              guid[14:18],
              guid[19:21],
              guid[21:23],
              guid[24:26],
              guid[26:28],
              guid[28:30],
              guid[30:32],
              guid[32:34],
              guid[34:36],
          ))


def _GenerateProxySconsText(machine_proxy_clsid,
                            user_proxy_clsid):
  proxy_clsid_text_format = ("PROXY_CLSID_IS_MACHINE=%s\n"
                             "PROXY_CLSID_IS_USER=%s\n")
  return proxy_clsid_text_format % (_GuidToCStructFormat(machine_proxy_clsid),
                                    _GuidToCStructFormat(user_proxy_clsid))


def _GenerateCustomizationUTText(machine_proxy_clsid, user_proxy_clsid):
  customization_ut_template = (
      "//\n"
      "// !!! AUTOGENERATED FILE. DO NOT HAND-EDIT !!!\n"
      "//\n\n"
      "namespace omaha {\n\n"
      "%s\n%s\n}  // namespace omaha\n")
  customization_ut_machine_proxy_clsid_string = (
      "// PROXY_CLSID_IS_MACHINE = {%s}\n"
      "const GUID kProxyClsidIsMachineGuid =\n"
      "    %s;\n") % (machine_proxy_clsid,
                      _GuidToCStructFormat(machine_proxy_clsid))

  customization_ut_user_proxy_clsid_string = (
      "// PROXY_CLSID_IS_USER = {%s}\n"
      "const GUID kProxyClsidIsUserGuid =\n"
      "    %s;\n") % (user_proxy_clsid,
                      _GuidToCStructFormat(user_proxy_clsid))

  return customization_ut_template % (
      customization_ut_machine_proxy_clsid_string,
      customization_ut_user_proxy_clsid_string)


def _GenerateProxyClsidFile(machine_proxy_clsid,
                            user_proxy_clsid):
  proxy_clsid_output = _GenerateProxySconsText(machine_proxy_clsid,
                                               user_proxy_clsid)
  with open(proxy_clsid_file_name, "w") as f_out:
    f_out.write(proxy_clsid_output)


def _GenerateCustomizationUnitTestFile(machine_proxy_clsid,
                                       user_proxy_clsid):
  customization_ut_output = _GenerateCustomizationUTText(machine_proxy_clsid,
                                                         user_proxy_clsid)
  with open(customization_ut_file_name, "w") as f_out:
    f_out.write(customization_ut_output)


def _GenerateProxyClsidsFiles():
  if (os.path.isfile(proxy_clsid_file_name) and
      os.path.isfile(customization_ut_file_name)):
    return

  machine_proxy_clsid = _GenerateGuid()
  user_proxy_clsid = _GenerateGuid()

  _GenerateProxyClsidFile(machine_proxy_clsid, user_proxy_clsid)
  _GenerateCustomizationUnitTestFile(machine_proxy_clsid,
                                     user_proxy_clsid)


def _GetProxyClsidsFromFile(target_proxy_clsid):
  proxy_clsid = ""
  with open(proxy_clsid_file_name, "r") as f:
    for line in f:
      if not line.startswith("#") and target_proxy_clsid in line:
        proxy_clsid = line[len(target_proxy_clsid):].rstrip()
        break
  if not proxy_clsid:
    raise StandardError("Failed to get auto-generated proxy CLSID")

  return proxy_clsid


def GetMachineProxyClsid():
  """Loads machine proxy CLSID from the generated file."""
  return _GetProxyClsidsFromFile("PROXY_CLSID_IS_MACHINE=")


def GetUserProxyClsid():
  """Loads user proxy CLSID from the generated file."""
  return _GetProxyClsidsFromFile("PROXY_CLSID_IS_USER=")


def _Main():
  """Generates proxy_clsids.txt and customization unit test file."""
  _GenerateProxyClsidsFiles()


if __name__ == "__main__":
  _Main()
