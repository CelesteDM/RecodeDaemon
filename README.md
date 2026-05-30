# recodeDaemon

A media recoding daemon for queue-based transcoding workflows.

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
      systemService = False;
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
