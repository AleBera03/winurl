[group("build")]
[doc("build core + file manager packages via nfpm (args: [deb|rpm|archlinux|apk...] [core|<file manager>...])")]
build *packages:
    ./package/build.sh {{packages}}
    
[group("release")]
[doc("bump Cargo.toml version, commit, tag and push (args: major|minor|fix)")]
release level:
    ./devutils/release.sh {{level}}
