# Writes the ```sh blocks of Documentation/Android.md to doc-steps.sh in order,
# with only the substitutions the doc itself asks for on an x86-64 machine.
import re, sys
# --no-device: drop the emulator and adb commands (for a container without KVM).
no_device = "--no-device" in sys.argv
def drop_device(block):
    keep, skipping = [], False
    for line in block.splitlines():
        if not skipping and re.match(r"(emulator|adb) ", line):
            skipping = True
        if not skipping:
            keep.append(line)
        if skipping and not line.rstrip().endswith("\\"):
            skipping = False
    return "\n".join(keep) + "\n"
doc = open("Documentation/Android.md").read()
blocks = re.findall(r"```sh\n(.*?)```", doc, re.S)
print(f"{len(blocks)} sh blocks", file=sys.stderr)
out = ["set -euxo pipefail"]
for i, b in enumerate(blocks):
    b = b.replace("arm64-v8a", "x86_64")
    # The license prompt needs a "y" from the user; CI has no terminal.
    b = b.replace("sdkmanager --install", "(yes || true) | sdkmanager --install")
    b = b.replace("TRIPLE=aarch64-unknown-linux-android33", "TRIPLE=x86_64-unknown-linux-android33")
    if "{YOURTARGET}" in b:
        runs = []
        targets = ["TestingTests", "TestingMacrosTests", "NonisolatedNonsendingByDefaultTests"] if "list" not in b else ["TestingTests"]
        for t in targets:
            runs.append(b.replace("{YOURTARGET}", t).replace("foodTruckExists", "variadicCStringArguments"))
        b = "\n".join(runs)
    if no_device:
        b = drop_device(b)
    out.append(f"echo '::group::doc block {i}'")
    out.append(b.rstrip())
    out.append("echo '::endgroup::'")
open("doc-steps.sh", "w").write("\n".join(out) + "\n")
