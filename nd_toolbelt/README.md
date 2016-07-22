# nd-toolbelt

A tool for centralizing and executing developer commands in your path.
It finds and autocompletes commands beginning with 'nd-', and supports
help for commands within its namespaces. The toolbelt attempts to
automatically update itself every hour, and also checks the system clock
every 10 minutes to warn the user if their clock is 120 seconds out of
date.

## Developer Setup

Run `make init` to install the tools you need.

## Installation

Clone the repo and then run `pip install -e <repo>`.  By cloning it,
nd-toolbelt will auto-update.

To set up autocomplete, run `eval "$(nd init -)"`.

## Usage

Run commands with nd `<command>`.  Run `nd help` to see a list of
available commands. Autocomplete and discover commands by trying
standard auto completion within the nd namespace.

## Creating Toolbelt Commands

Adding a command to nd-toolbelt is as simple as including it to your
path. You can add a command to nextdoor.com by including the your
command or a link to your command under `$NEXTDOOR_ROOT/tools/bin.`

Your toolbelt command must start with `nd-`. The following rules also
apply:

* Namespaces must be separated by **`~`**'s. e.g.: `nd dev migrate`
should be named `nd-dev~migrate`
* Commands starting with `_` aren't shown in autocomplete options.
e.g.: `nd-_help-helper`
* Commands starting with `.` are run before every command in its
namespace and child namespaces. e.g.: `nd-dev~.check`. Dot commands are
run alphabetically. If a dot command fails to execute
successfully, **no further dot commands nor the target command will
be executed.**
