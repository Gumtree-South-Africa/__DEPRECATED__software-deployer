#!/bin/bash

# helper script to release a new version

if git checkout master && git pull --rebase
then
  LATEST=$( dpkg-parsechangelog | awk '/^Version: / { print $NF; }' )

  # create new version string by incrementing the minor version number:
  minor=${LATEST##*.}
  pre_minor=${LATEST%.*}
  if ! echo "$minor" | grep -qE '^[0-9]+$'
  then
    echo "Last part of '$LATEST' is not numeric, cannot auto-increment minor version number"
    exit 1
  fi

  (( minor++ ))
  NEW_V="$pre_minor.$minor"

  echo "New version: $NEW_V"

  GIT_DCH="git-dch --auto -N $NEW_V --release"

  read -p "About to call '$GIT_DCH' now.
  This will open the debian/changelog in an editor
  for you to review and edit if needed. Continue? [Y/n]: " reply

  if [[ -z "$reply" ]]
  then
    reply='Y'
  fi

  case $reply in
    [Yy]*)
      git-dch --auto -N "$NEW_V" --release

      read -p "Ready to commit and push? [y/N]" reply

      case $reply in
        [yY]*)
          git commit -a -m "Release version $NEW_V"
          git push -v --tags origin master
          ;;
        *)
          echo "Skipping commit and push"
          ;;
      esac
      ;;
    *)
      echo "Not running git-dch, then, as you wish."
      ;;
  esac
fi
