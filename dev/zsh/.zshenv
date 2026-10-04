# Use Tern's own hooks; do not load personal terminal integrations or aliases.
if [[ -o interactive && $TERM_PROGRAM == tern && -z ${_ksi_loaded-} ]]; then
  if [[ $OSTYPE == darwin* ]]; then
    source "$HOME/Library/Caches/stencil-term/shell-integration/zsh/kitty-integration"
  else
    source "${XDG_CACHE_HOME:-$HOME/.cache}/stencil-term/shell-integration/zsh/kitty-integration"
  fi
fi
