# 🔝 `yt-mpv`

Watch a YouTube video without ads, while archiving to archive.org.

# todo

## yt-mpv is an installer

* `pip install yt-mpv` should install the *installer* which is what this package is.
* `uvx yt-mpv` should work too.
* `ty-mpv --help` etc should work, and list `install` `remove` `setup` and `launch`
* takes a `prefix` which defaults to `$HOME/.local`

## install

* create a venv in `f"{prefix}/bin/yt-mpv.venv` or wherever this should go?
* use `freeze_one.freeze_one("yt_mvp")` to get a string for the current install
* install it into the venv (launch `bash -c`, source the activate and do pip install)
* write the launch script to `{prefix}/bin`
  * This sources `../share/yt-mpv/.venv/bin/activate` then runs
    `yt-mpv launch $1`
* copy the `.desktop` file into the prefix too
* run the xdg update on the dir where the .desktop was installed
* run the setup process

## uninstall

* remove the yt-mpv desktop file, the binary and the prefix

## setup

* run the internet archive config
* open the html file in a browser so the user can copy the bookmarklet javascript
* print a warning if mpv is not found on the path, prompting the user to install it

## launch

* update yt-dlp using uv (because it's fast)
* don't include other modules that would slow down the launch
* extract URL from the URI
* run the internet archiver stuff
  * need to come up with a good prefix format
* make notifications more specific to the application

## check

* check for a given URL by searching internet archive metadata
* print the IA archive URL and exit 0, or exit 1
