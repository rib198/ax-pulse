#!/usr/bin/env bash
set -e
set -o pipefail
cd "$(dirname "$0")"

echo ""
echo "  AX Safari X Capture"
echo "  ───────────────────"
echo "  تأكد أن تبويب X مفتوح في Safari ويعرض التغريدات."
echo ""

JS_FILE="$(pwd)/tools/safari_x_capture.js"
JXA_FILE="/tmp/ax_capture_safari.js"

cat > "$JXA_FILE" <<JXA
const Safari = Application('Safari');
Safari.includeStandardAdditions = true;
if (Safari.documents.length === 0) {
  throw new Error('No Safari window is open.');
}
const doc = Safari.documents[0];
const url = String(doc.url());
if (!url.includes('x.com') && !url.includes('twitter.com')) {
  throw new Error('Front Safari tab is not X/Twitter. Open X and run again. Current: ' + url);
}
const jsCode = Safari.doShellScript('cat ' + JSON.stringify('$JS_FILE'));
doc.doJavaScript(jsCode);
JXA

osascript -l JavaScript "$JXA_FILE" | python3 tools/import_x_visible.py

echo ""
echo "  عرض آخر الإشارات:"
./x-collect show --last 8
