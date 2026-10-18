"""Builds legal/licenses.json: every npm package whose code ships in the iOS bundle (from the source map),
every npm package with native iOS code, and known native libraries pulled in by CocoaPods. Run from repo root:
  (cd app && npx expo export -p ios --source-maps --output-dir /tmp/et-ios-sm) && python3 legal/tools/licenses.py /tmp/et-ios-sm"""
import json, os, re, sys, glob
APP = os.path.join(os.path.dirname(__file__), "..", "..", "app")
NM = os.path.normpath(os.path.join(APP, "node_modules"))
smdir = sys.argv[1]
src = json.load(open(glob.glob(os.path.join(smdir, "**/*.map"), recursive=True)[0]))["sources"]
pkgs = set()
for s in src:
    m = re.search(r"node_modules/((?:@[^/]+/)?[^/]+)/", s.replace("\\", "/"))
    if m:
        # nested node_modules: take the innermost package path
        parts = s.replace("\\", "/").split("node_modules/")
        inner = parts[-1]; name = "/".join(inner.split("/")[:2]) if inner.startswith("@") else inner.split("/")[0]
        root = "node_modules/".join(parts[:-1]) + "node_modules/" + name
        root = root[root.index("node_modules"):] if "node_modules" in root else root
        pkgs.add(root)
# native modules: packages with a podspec
for d in glob.glob(NM + "/**/*.podspec", recursive=True):
    rel = os.path.relpath(d, os.path.dirname(NM)).replace("\\", "/")
    parts = rel.split("node_modules/"); inner = parts[-1]
    name = "/".join(inner.split("/")[:2]) if inner.startswith("@") else inner.split("/")[0]
    pkgs.add("node_modules/".join(parts[:-1]) + "node_modules/" + name)
FILES = ["LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE", "LICENSE-MIT", "license", "license.md", "LICENSE_FONT", "COPYING"]
out = {}
for p in sorted(pkgs):
    d = os.path.join(os.path.dirname(NM), p)
    pj = os.path.join(d, "package.json")
    if not os.path.exists(pj): continue
    j = json.load(open(pj))
    name, ver = j.get("name"), j.get("version")
    if not name or name in out or name.startswith("ergodic"): continue
    lic = j.get("license") or (j.get("licenses") or [{}])[0].get("type") if isinstance(j.get("licenses"), list) else j.get("license")
    if isinstance(lic, dict): lic = lic.get("type")
    text = ""
    for f in FILES:
        fp = os.path.join(d, f)
        if os.path.exists(fp): text = open(fp, errors="replace").read().strip(); break
    if not text:  # monorepo packages often keep the license at the repo root; fall back to the SPDX name
        text = ""
    out[name] = {"name": name, "version": ver, "license": lic or "See package", "repo": (j.get("repository") or {}).get("url") if isinstance(j.get("repository"), dict) else j.get("repository"), "text": text}
NATIVE = [
    ("RevenueCat (purchases-ios)", "MIT", "Copyright (c) RevenueCat, Inc."),
    ("PurchasesHybridCommon", "MIT", "Copyright (c) RevenueCat, Inc."),
    ("Hermes JavaScript engine", "MIT", "Copyright (c) Meta Platforms, Inc. and affiliates."),
    ("Skia", "BSD-3-Clause", "Copyright (c) 2011 Google Inc. All rights reserved."),
    ("SDWebImage", "MIT", "Copyright (c) 2009-2020 Olivier Poitrey rs@dailymotion.com"),
    ("SDWebImageWebPCoder", "MIT", "Copyright (c) 2018 Bogdan Poplauschi"),
    ("SDWebImageAVIFCoder", "MIT", "Copyright (c) 2019 lizhuoli1126@126.com"),
    ("SDWebImageSVGCoder", "MIT", "Copyright (c) 2018 lizhuoli1126@126.com"),
    ("libwebp", "BSD-3-Clause", "Copyright (c) 2010, Google Inc. All rights reserved."),
    ("libavif", "BSD-2-Clause", "Copyright 2019 Joe Drago. All rights reserved."),
    ("dav1d", "BSD-2-Clause", "Copyright (c) 2018-2019, VideoLAN and dav1d authors. All rights reserved."),
    ("Folly", "Apache-2.0", "Copyright (c) Meta Platforms, Inc. and affiliates."),
    ("Boost", "BSL-1.0", "Boost Software License - Version 1.0"),
    ("glog", "BSD-3-Clause", "Copyright (c) 2008, Google Inc. All rights reserved."),
    ("double-conversion", "BSD-3-Clause", "Copyright 2006-2011, the V8 project authors. All rights reserved."),
    ("fmt", "MIT", "Copyright (c) 2012 - present, Victor Zverovich and {fmt} contributors"),
    ("fast_float", "MIT", "Copyright (c) 2021 The fast_float authors"),
    ("SocketRocket", "BSD-3-Clause", "Copyright (c) 2016-present, Facebook, Inc. All rights reserved."),
]
FONTS = [("Unbounded", "OFL-1.1", "Copyright 2022 The Unbounded Project Authors"),
         ("Michroma", "OFL-1.1", "Copyright 2011 The Michroma Project Authors"),
         ("Manrope", "OFL-1.1", "Copyright 2018 The Manrope Project Authors")]
res = {"generated": True, "packages": sorted(out.values(), key=lambda x: x["name"].lower()),
       "native": [{"name": n, "license": l, "notice": c} for n, l, c in NATIVE],
       "fonts": [{"name": n, "license": l, "notice": c} for n, l, c in FONTS]}
json.dump(res, open(os.path.join(os.path.dirname(__file__), "..", "licenses.json"), "w"), indent=1)
from collections import Counter
print(len(out), "packages;", Counter(p["license"] for p in out.values()).most_common(12))
print("no license text:", [p["name"] for p in out.values() if not p["text"]][:40])
