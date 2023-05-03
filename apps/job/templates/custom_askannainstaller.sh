#!/bin/sh

exists() {
  command -v "$1" >/dev/null 2>&1
}

# first check whether we have `apk` or `apt` or `apt-get`
# APP_MANAGER=apk

if exists apt-get; then
  APP_MANAGER=apt-get
  if exists apt; then
    APP_MANAGER=apt
  fi
fi
if exists apk; then
  APP_MANAGER=apk
fi

sh "askanna_installer_"${APP_MANAGER}.sh

if ! exists python; then
  echo "" >&2
  echo "Python 3 is not found on this image. Please install with:" >&2
  if [ "$APP_MANAGER" = "apt" ]; then
    echo "  apt install python3" >&2
  fi
  if [ "$APP_MANAGER" = "apt-get" ]; then
    echo "  apt-get install python3" >&2
  fi
  if [ "$APP_MANAGER" = "apk" ]; then
    echo "  apk install python3" >&2
  fi
  echo "" >&2
  exit 1
fi

if ! exists askanna-run-utils; then
  # try to install askanna
  pip3 install askanna

  # check again
  if ! exists askanna-run-utils; then
    echo "" >&2
    echo "askanna-run-utils is not found on this image. Please install with:" >&2
    echo "  pip3 install askanna" >&2
    echo "" >&2
    exit 1
  fi
fi

# clean the pip cache directory
rm -rf /root/.cache
