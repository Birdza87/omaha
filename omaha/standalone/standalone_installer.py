#!/usr/bin/python2.4
# Copyright 2009 Google Inc.
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

"""Builds standalone installers and MSI wrappers around them.

This is very close to the logic within installers\build.scons. The difference
is that we have an additional file standalone_installers.txt. This file
contains a list of standalone installers to create along with necessary values.
For each entry in standalone_installers.txt, we create a corresponding
standalone installer, which is the meta-installer, app installer binaries, and
update response tarred together.
MSI installers that wrap the standalone installer may also be created.
"""

import codecs
import os

from enterprise.installer import build_enterprise_installer
from installers import build_metainstaller
from installers import tag_meta_installers
from installers import tagged_installer
import standalone.utils


class OfflineInstaller(object):
  """Represents the information for a bundle."""

  def __init__(self,
               friendly_product_name,
               exe_base_name,
               binaries,
               msi_base_name,
               custom_tag_params,
               silent_uninstall_args,
               should_build_enterprise_msi,
               msi_installer_data,
               installers_txt_filename):
    self.friendly_product_name = friendly_product_name
    self.exe_base_name = exe_base_name
    self.binaries = binaries
    self.msi_base_name = msi_base_name
    self.custom_tag_params = custom_tag_params
    self.silent_uninstall_args = silent_uninstall_args
    self.should_build_enterprise_msi = should_build_enterprise_msi
    self.msi_installer_data = msi_installer_data
    self.installers_txt_filename = installers_txt_filename


def ReadOfflineInstallersFile(env, offline_installers_file_path):
  """Enumerates the entries in the offline installers file.

  Args:
    env: Environment.
    offline_installers_file_path: Path to file specifying installers to build.

  Returns:
    Returns a list of structures used for creating the prestamped binaries.
  """

  offline_installers = []
  offline_abs_path = env.File(offline_installers_file_path).abspath
  installer_file = codecs.open(offline_abs_path, 'r')
  for line in installer_file:
    line = line.strip()
    if len(line) and not line.startswith('#'):
      (friendly_product_name,
       exe_base_name,
       binaries,
       msi_base_name,
       custom_tag_params,
       silent_uninstall_args,
       should_build_enterprise_msi,
       msi_installer_data,
       installers_txt_filename) = eval(line)
      installer = OfflineInstaller(friendly_product_name,
                                   exe_base_name,
                                   binaries,
                                   msi_base_name,
                                   custom_tag_params,
                                   silent_uninstall_args,
                                   should_build_enterprise_msi,
                                   msi_installer_data,
                                   installers_txt_filename)
      offline_installers.append(installer)
  return offline_installers


def BuildOfflineInstallersVersion(env,
                                  omaha_version_info,
                                  omaha_files_path,
                                  empty_metainstaller_path,
                                  offline_installers_file_path,
                                  manifest_files_path,
                                  prefix='',
                                  is_official=False):
  """Builds all standalone installers specified in offline_installers_file_path.

  Args:
    env: Environment.
    omaha_version_info: info about the version of the Omaha files
    omaha_files_path: Path to the directory containing the Omaha binaries.
    empty_metainstaller_path: Path to empty (no tarball) metainstaller binary.
    offline_installers_file_path: Path to file specifying installers to build.
    manifest_files_path: Path to the directory containing the manifests for the
        apps specified in offline_installers_file_path.
    prefix: Optional prefix for the resulting installer.
    is_official: Whether to build official (vs. test) standalone installers.
  """

  offline_installers = ReadOfflineInstallersFile(env,
                                                 offline_installers_file_path)

  for offline_installer in offline_installers:
    BuildOfflineInstaller(
        env,
        offline_installer,
        omaha_version_info,
        omaha_files_path,
        empty_metainstaller_path,
        offline_installers_file_path,
        manifest_files_path,
        prefix,
        is_official
    )


def _GenerateUpdateResponseFile(target, source, env):
  """Legacy scons wrapper for utils.GenerateUpdateResponseFile()."""
  local_env = env.Clone()

  if version_list := local_env['INSTALLER_VERSIONS']:
    standalone.utils.GenerateUpdateResponseFile(
        str(target[0]), [str(s) for s in source], version_list,
        has_x64_binaries=False)
  else:
    raise Exception('INSTALLER_VERSIONS is missing from environment.')


def BuildOfflineInstaller(
    env,
    offline_installer,
    omaha_version_info,
    omaha_files_path,
    empty_metainstaller_path,
    offline_installers_file_path,
    manifest_files_path,
    prefix='',
    is_official=False,
    installers_sources_path='$MAIN_DIR/installers',
    enterprise_installers_sources_path='$MAIN_DIR/enterprise/installer',
    lzma_path='$THIRD_PARTY/lzma/files/lzma.exe',
    resmerge_path='$MAIN_DIR/tools/resmerge'):
  """Builds the standalone installers specified by offline_installer.

  Args:
    env: Environment.
    offline_installer: OfflineInstaller containing the information about the
        standalone installer to build.
    omaha_version_info: info about the version of the Omaha files
    omaha_files_path: Path to the directory containing the Omaha binaries.
    empty_metainstaller_path: Path to empty (no tarball) metainstaller binary.
    offline_installers_file_path: Path to file specifying installers to build.
    manifest_files_path: Path to the directory containing the manifests for the
        apps specified in offline_installers_file_path.
    prefix: Optional prefix for the resulting installer.
    is_official: Whether to build official (vs. test) standalone installers.
    installers_sources_path: path to the directory containing the source files
        for building the metainstaller
    enterprise_installers_sources_path: path to the directory containing the
        source files for building enterprise installers
    lzma_path: path to lzma.exe
    resmerge_path: path to resmerge.exe

  Returns:
    Target nodes.

  Raises:
    Exception: Missing or invalid data specified in offline_installer.
  """
  standalone_installer_base_name = offline_installer.exe_base_name
  if not standalone_installer_base_name:
    raise Exception('Product name not specified.')

  output_dir = '$STAGING_DIR'
  if not is_official:
    standalone_installer_base_name = ('UNOFFICIAL_' +
                                      standalone_installer_base_name)
    output_dir = '$TARGET_ROOT/Test_Installers'

  target_base = prefix + standalone_installer_base_name
  target_name = target_base + '.exe'
  log_name = target_base + '_Contents.txt'

  # Write Omaha's version.
  log_text = '*** Omaha Version ***\n\n'
  log_text += omaha_version_info.GetVersionString() + '\n'

  # Rename the checked in binaries by adding the application guid as the
  # extension. This is needed as the meta-installer expects the
  # extension.
  # Also, log information about each app.
  additional_payload_contents = []
  if not offline_installer.binaries:
    raise Exception('No binaries specified.')

  manifest_source = []
  version_list = []
  for binary in offline_installer.binaries:
    (version, installer_path, guid) = binary
    if not installer_path or not guid or not version:
      raise Exception('Application specification is incomplete.')

    installer_path_modified = os.path.basename(installer_path) + '.' + guid
    # Have to use Command('copy') here instead of replicate, as the
    # file is being renamed in the process.
    env.Command(
        target=installer_path_modified,
        source=installer_path,
        action='@copy /y $SOURCES $TARGET'
    )

    manifest_source.extend([
        manifest_files_path + '/' + guid + '.gup', installer_path_modified])
    version_list.append(version)
    additional_payload_contents.append(installer_path_modified)

    # Log info about the app.
    log_text += '\n\n*** App: ' + guid + ' ***\n'
    log_text += '\nVersion:' + version + '\n'
    log_text += '\nINSTALLER:\n' + installer_path + '\n'

  # Place the generated manifests in a subdirectory. This allows a single
  # build to generate installers for multiple versions of the same app.
  manifest_file_path = env.Command(
      target=target_name + '_manifest/OfflineManifest.gup',
      source=manifest_source,
      action=[_GenerateUpdateResponseFile],
      INSTALLER_VERSIONS=version_list
      )

  # Use the BCJ2 tool from the official build we're using to generate this
  # metainstaller, not the current build directory.
  bcj2_path = omaha_files_path + '/bcj2.exe'

  additional_payload_contents.append(manifest_file_path)

  def WriteLog(target, source, env):
    """Legacy scons wrapper for utils.WriteInstallerLog()."""
    return standalone.utils.WriteInstallerLog(
        str(target[0]), env['write_data'], str(source[0]))

  env.Command(
      target='%s/%s' % (output_dir, log_name),
      source=manifest_file_path,
      action=WriteLog,
      write_data=log_text
  )

  results = []
  results += build_metainstaller.BuildMetaInstaller(
      env=env,
      target_name=target_name,
      omaha_version_info=omaha_version_info,
      empty_metainstaller_path=empty_metainstaller_path,
      omaha_files_path=omaha_files_path,
      prefix=prefix,
      suffix='_' + standalone_installer_base_name,
      additional_payload_contents=additional_payload_contents,
      additional_payload_contents_dependencies=offline_installers_file_path,
      output_dir=output_dir,
      installers_sources_path=installers_sources_path,
      lzma_path=lzma_path,
      resmerge_path=resmerge_path,
      bcj2_path=bcj2_path
  )

  standalone_installer_path = '%s/%s' % (output_dir, target_name)

  # Build an enterprise installer.
  if offline_installer.should_build_enterprise_msi:
    # TODO(omaha): Add support for bundles here and to
    #   BuildEnterpriseInstallerFromStandaloneInstaller().
    # TODO(omaha): Determine how product_version should be decided for MSI in
    #   bundle scenarios.
    # TODO(omaha): custom tag, silent uninstall args, distribution data may need
    #   to be made per-app.
    if 1 < len(offline_installer.binaries):
      raise Exception('Enterprise installers do not currently support bundles.')
    (product_version, installer_path, product_guid) = offline_installer.binaries[0]

    # Note: msi_base_name should not include version info and cannot change!
    friendly_product_name = offline_installer.friendly_product_name
    msi_base_name = offline_installer.msi_base_name
    custom_tag_params = offline_installer.custom_tag_params
    silent_uninstall_args = offline_installer.silent_uninstall_args
    msi_installer_data = offline_installer.msi_installer_data

    # custom_tag_params and msi_installer_data are optional.
    if (not product_version or not friendly_product_name or not msi_base_name or
        not silent_uninstall_args):
      raise Exception('Field required to build enterprise MSI is missing.')

    if not is_official:
      msi_base_name = ('UNOFFICIAL_' + msi_base_name)

    results += (build_enterprise_installer.
                BuildEnterpriseInstallerFromStandaloneInstaller(
                    env,
                    friendly_product_name,
                    product_version,
                    product_guid,
                    custom_tag_params,
                    silent_uninstall_args,
                    msi_installer_data,
                    standalone_installer_path,
                    omaha_files_path + '/msi_custom_action.dll',
                    prefix + msi_base_name,
                    enterprise_installers_sources_path,
                    output_dir=output_dir
                    ))

  # Tag the meta-installer if an installers.txt file was specified.
  if offline_installer.installers_txt_filename:
    installers_txt_path = env.File(
        offline_installer.installers_txt_filename).abspath
    app_bundles = tag_meta_installers.ReadBundleInstallerFile(
        installers_txt_path)

    bundles = {}
    for (key, bundle_list) in app_bundles.items():
      if not bundle_list or not key:
        continue
      if not key in bundles:
        bundles[key] = bundle_list
      else:
        new_bundles_list = bundles[key] + bundle_list
        bundles[key] = new_bundles_list

    tag_meta_installers.SetOutputFileNames(target_name, bundles, '')
    for bundles_lang in bundles.itervalues():
      for bundle in bundles_lang:
        results += tagged_installer.TagOneBundle(
            env=env,
            bundle=bundle,
            untagged_binary_path=standalone_installer_path,
            output_dir='$TARGET_ROOT/Tagged_Offline_Installers',
        )

  return results
