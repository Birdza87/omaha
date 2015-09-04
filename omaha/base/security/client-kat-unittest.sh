// Copyright 2014 Google Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
// ========================================================================

#!/bin/bash
source googletest.sh || exit 1

KEYTOOL=$TEST_SRCDIR/google3/security/util/lite/keytool
TESTCLIENT=$TEST_SRCDIR/google3/security/util/lite/testclient
TESTCONTENT=$TEST_TMPDIR/testcontent
RANDOMSEED="Mon Oct 22 18:43:16 PDT 2007"
KEYVERSION=4
PRIVKEY=$TEST_SRCDIR/google3/security/util/lite/testdata/privatekey

# Known answer test (KAT) of private key to public key format conversion.
$KEYTOOL --key_version $KEYVERSION \
         --private_key_file $PRIVKEY \
         --pubout --output_file $TESTCONTENT \
         --unittest=true \
      || die "Failed to run $KEYTOOL"

# KAT test encryption
ENCRYPTION=`$TESTCLIENT --encrypt "$RANDOMSEED" --seed "$RANDOMSEED"` \
    || die "Failed to run $TESTCLIENT"
EXPECTED="AAAAAAQ0-wpAgncQ457-1yEJ_qeZLNirhvaYAzLKNWPIXkWmb5KLVzX8tEHffxGRK9YeR0DQR5Opkn5jiN0VR50_XoCPiiT_4Kgwow0V-HR79T8K0dzcElXzqQmNIUa1dcOX3h_51zBZGe5e9K9DRP2V-cgeS4LQffDIMXPnnAqDfB56_e6AJYN8POgmnauqPUy79Fh1goKxFU4zBwUSQ_I"

check_eq "$ENCRYPTION" "$EXPECTED"

# Known answers the client should comply with, for a given seed.
CHALLENGE="4:hCjq6Wyx6yVzz1YALTRrFQ"

check_eq "$CHALLENGE" `$TESTCLIENT --seed "$RANDOMSEED" --challenge`

HASH="SXUB9-gk5BfYARXs2ESbJXsqhZk"
SIGNATURE="KprvUUUPkPMH9k8kmGGcUSplD4ww11zzk-eH-rej6NuZQ-jgKL0xqc2iCmXcpOpLLuLUAUtHkSdvhSrw_Hj6r-jRdQIyrOOQ28n2pLHqJPQMpP9xMTCNvH7KY8ZbJSMvW6zT3Pg4JoPMOS2hsM9yFs1OQyCgRd66r8GFTB9htjs"

# Hand fixed signature to client to test, along with content to hash.
# Client will check hash against test content generated by keytool earlier.
$TESTCLIENT --seed "$RANDOMSEED" \
            --signature $SIGNATURE \
            --hash $HASH \
            --input_file $TESTCONTENT --verbose \
         || die "Failed to run $TESTCLIENT"