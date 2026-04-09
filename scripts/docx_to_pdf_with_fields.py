"""Convert a docx to PDF with fields refreshed on export.

LibreOffice's headless `--convert-to pdf` does NOT update fields by default,
so a TOC field renders its placeholder text instead of the real entries.
This script does two things to force a TOC update:

  1. Writes a one-shot soffice user profile whose registrymodifications.xcu
     sets `UpdateFromTemplate` and `FieldUpdate` flags so fields refresh on
     load.
  2. Runs soffice headless against that profile and converts the docx.

Usage:
    python docx_to_pdf_with_fields.py <input.docx> <output.pdf>
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


SOFFICE = "/opt/homebrew/bin/soffice"

# User-profile registry settings that turn on field/index update on load
# and on print/export. Names mirror the Tools > Options dialog entries:
#   Writer > General > Update Links when Loading: Always
#   Writer > General > Update Fields automatically: on
#   Writer > General > Update Charts automatically: on
#   Writer > Print > Other > Update fields: on
REGMOD_XCU = """<?xml version='1.0' encoding='UTF-8'?>
<oor:items xmlns:oor="http://openoffice.org/2001/registry"
           xmlns:xs="http://www.w3.org/2001/XMLSchema"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <item oor:path="/org.openoffice.Office.Writer/Content/Update"><prop oor:name="Field" oor:op="fuse"><value>true</value></prop></item>
  <item oor:path="/org.openoffice.Office.Writer/Content/Update"><prop oor:name="Chart" oor:op="fuse"><value>true</value></prop></item>
  <item oor:path="/org.openoffice.Office.Writer/Content/Update"><prop oor:name="Link" oor:op="fuse"><value>2</value></prop></item>
  <item oor:path="/org.openoffice.Office.Writer/Print/Other"><prop oor:name="Field" oor:op="fuse"><value>true</value></prop></item>
</oor:items>
"""


def run(input_docx: Path, output_pdf: Path) -> int:
    input_docx = input_docx.resolve()
    output_pdf = output_pdf.resolve()

    # Copy to a temp dir without spaces so soffice has no path-quoting issues.
    work_dir = Path(tempfile.mkdtemp(prefix="lo_work_"))
    work_in = work_dir / "in.docx"
    shutil.copy2(input_docx, work_in)

    profile_dir = Path(tempfile.mkdtemp(prefix="lo_profile_"))
    user_dir = profile_dir / "user"
    user_dir.mkdir(parents=True, exist_ok=True)
    (user_dir / "registrymodifications.xcu").write_text(REGMOD_XCU)

    cmd = [
        SOFFICE,
        "--headless",
        "--norestore",
        "--nologo",
        "--nofirststartwizard",
        f"-env:UserInstallation=file://{profile_dir}",
        "--convert-to",
        "pdf:writer_pdf_Export",
        "--outdir",
        str(work_dir),
        str(work_in),
    ]
    print("Running soffice on temp path:", work_in)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.stdout.strip():
        print("stdout:", result.stdout[:500])
    if result.stderr.strip():
        print("stderr:", result.stderr[:500])

    work_out = work_dir / "in.pdf"
    if work_out.exists():
        shutil.copy2(work_out, output_pdf)
    shutil.rmtree(profile_dir, ignore_errors=True)
    shutil.rmtree(work_dir, ignore_errors=True)

    if not output_pdf.exists():
        print("ERROR: output PDF was not created")
        return 1
    print(f"Wrote {output_pdf} ({output_pdf.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(run(Path(sys.argv[1]), Path(sys.argv[2])))
