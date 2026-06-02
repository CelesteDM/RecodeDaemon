# RecodeDaemon

A media HVEC recoding daemon for queue-based transcoding workflows.

---

This project was born as a solution for my personal home server, where I have tons of series and movies to recode and it takes a ton of time.
I've been doing this manually until now but I wanted a more organized way of creating recoding queues for each each serie, movie or season, so I can create them and forget about them.

---

## Features

- Watches and processes queued media jobs
- FFmpeg-based transcoding
- Python daemonized runtime
- Nix flake + NixOS module support

## Installation

### Nixos with flakes

In your `flake.nix` file add recodeDaemon in your inputs and output declaration:
```
{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";

    recodeDaemon = {
      url = "github:CelesteDM/recodeDaemon";
      inputs.nixpkgs.follows = nixpkgs;
    };
  };

  outputs = { self, nixpkgs, recodeDaemon, ... }: {

    nixosConfigurations.<hostname> = nixpkgs.lib.nixosSystem {
      specialArgs = { inherit inputs; };
      modules = [
        ./configuration.nix
        # Other modules
      ];
    };
  };
}
```

If you are using `specialArgs = { inherit inputs; };` as shown above, you can then access the module from any submodule:
```
{ inputs, ... }:
{
  imports = [ inputs.recodeDaemon.nixosModules.default ];

  services.recodeDaemon = {
    enable = true;

    # Settings for the systemd unit
    daemon = {
      enable = true;
      port = 5300;
      systemService = false;
    };
  };
}
```

If you don't want the systemd service unit, and instead manage the daemon by yourself, you can use only `services.recodeDaemon.enable = true;` without enabling the daemon option, and then manage the daemon in the cli.


### Building from source

Clone the repository and install using pip:
```
$ git clone https://github.com/CelesteDM/RecodeDaemon

$ cd recodeDaemon
```

If you want to build in a virtual environment before installing:
```
$ python -m venv .venv

$ source .venv/bin/activate
```

Finally, build with pip:
```
$ pip install .
```

## Usage
For a full list of options use the `-h / --help` flag in any of the subcommands.

Run the daemon:
```
recoder daemon run
```
Can be also launched as a backbround process using `-d / --daemon` flag.
To stop the daemon, use the `daemon stop` subcommand instead.
Both the daemon and all the cli commands support using a different port with the `-p / --port` flag.

Create a recoding queue:
```
recoder queue create /path/to/files
```
A name can be specified using the `-n / --name` flag, this is not required, and the daemon will try to create a name using the directory basename if a name is not provided.
If no output options are specified, the files will be ovewritten in place, this can be changed using the `-o / --output` flag to specify an output directory, or the `-b / --backup` flag to specify a directory where the original files will be copied to.
Both the preset velocity can be specified using its name with the `-p / --preset` flag.
For a full list of presets, check [the h265 coding docs](https://x265.readthedocs.io/en/stable/presets.html#presets).
An animation flag is available for the [animation tuning](https://x265.readthedocs.io/en/stable/presets.html#tuning).

Check daemon status:
```
recoder status
```
If instead you only need the raw data to use in scripts, use the `-r / --raw` flag.

Delete one or more queues:
```
recoder queue delete <queue-ids>
```
The keyword `active` can be used along other ids as a valid queue-id to delete the current active queue.

List queues:
```
recoder queue list
```
The default option shows the active and waiting queues, the completed queues can be shown adding the `-a / --all` or `-c / --completed` flags.

Pause and resume the daemon:
```
recoder queue pause
recoder queue resume
```
