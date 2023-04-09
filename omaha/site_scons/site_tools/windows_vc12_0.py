#!/usr/bin/python2.4
#
# Copyright 2015 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http:#www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ========================================================================

"""Tool-specific initialization for Visual Studio 2013.

NOTE: This tool is order-dependent, and must be run before
any other tools that modify the binary, include, or lib paths because it will
wipe out any existing values for those variables.

There normally shouldn't be any need to import this module directly.
It will usually be imported through the generic SCons.Tool.Tool()
selection method.
"""

import os
import SCons


def _SetMsvcCompiler(
    env, vc_flavor='x86'):
  """When run on a non-Windows system, this function does nothing.

     When run on a Windows system, this function wipes the binary, include
     and lib paths so that any non-hermetic tools won't be used.
     These paths will be set up by target_platform_windows and other tools.
     By wiping the paths here, we make the adding the other tools
     order-independent.
  Args:
    env: The SCons environment in question.
    vc_flavor: Defaults to x86, can be 'x86', 'amd64' or 'x86_amd64'. The
        latter is using the 32-bit executable of the 64-bit compiler.
  Returns:
    Nothing.
  Raises:
    ValueError: An error if vc_flavor is not valid.
  """
  if vc_flavor not in ('x86', 'amd64', 'x86_amd64'):
    raise ValueError('vc_flavor must be one of: amd64, x86, x86_amd64.')

  vc_dir = os.environ.get('VSINSTALLDIR')
  platform_sdk_dir = os.environ.get('OMAHA_PLATFORM_SDK_DIR')

  env['GOOGLECLIENT'] = '$MAIN_DIR/..'
  env['GOOGLE3'] = '$GOOGLECLIENT'
  env['THIRD_PARTY'] = '$GOOGLECLIENT/third_party/'

  env.Replace(
      PLATFORM_SDK_DIR=platform_sdk_dir,
      MSVC_FLAVOR=('amd64', 'x86')[vc_flavor == 'x86'],
      VC12_0_DIR=vc_dir,
      WINDOWS_SDK_8_1_DIR=platform_sdk_dir,
  )

  # Clear any existing paths.
  env['ENV']['PATH'] = ''
  env['ENV']['INCLUDE'] = ''
  env['ENV']['LIB'] = ''

  tools_paths = []
  lib_paths = []
  vc_bin_dir = f'{vc_dir}/vc/bin'
  if vc_flavor == 'amd64':
    vc_bin_dir += '/amd64'
  elif vc_flavor == 'x86_amd64':
    vc_bin_dir += '/x86_amd64'

  tools_paths += [vc_bin_dir,]

  include_paths = [f'{vc_dir}/vc/include']
  if vc_flavor == 'x86':
    lib_paths.append(f'{vc_dir}/vc/lib')
  else:
    lib_paths.append(f'{vc_dir}/vc/lib/amd64')

  # Add explicit location of platform SDK to tools path
  tools_paths.append(f'{platform_sdk_dir}/bin')
  include_paths += [
      f'{platform_sdk_dir}/include',
      f'{platform_sdk_dir}/include/um',
      f'{platform_sdk_dir}/include/shared',
  ]
  if vc_flavor == 'x86':
    lib_paths += [
        f'{platform_sdk_dir}/lib',
        f'{platform_sdk_dir}/lib/winv6.3/um/x86',
    ]
    tools_paths.append(f'{platform_sdk_dir}/bin/x86')
  else:
    lib_paths += [
        f'{platform_sdk_dir}/lib/x64',
        f'{platform_sdk_dir}/lib/winv6.3/um/x64',
    ]
    # VC 12 needs this, otherwise mspdb120.dll will not be found.
    tools_paths.append(f'{vc_dir}/vc/bin')
    tools_paths.append(f'{platform_sdk_dir}/bin/x64')

  for p in tools_paths:
    env.AppendENVPath('PATH', env.Dir(p).abspath)
  for p in include_paths:
    env.AppendENVPath('INCLUDE', env.Dir(p).abspath)
  for p in lib_paths:
    env.AppendENVPath('LIB', env.Dir(p).abspath)


def generate(env):
  _SetMsvcCompiler(
      env=env, vc_flavor='x86')
