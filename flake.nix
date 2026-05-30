{
  description = "Recode daemon flake";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
  };

  outputs = { self, nixpkgs }: let

    systems = [
      "x86_64-linux"
    ];

    forAllSystems = f:
      nixpkgs.lib.genAttrs systems
        (system:
          f {
            pkgs = import nixpkgs {
              inherit system;
              overlays = [ self.overlays.default ];
            };
          });
  in {
    overlays.default = final: prev: {
      recodeDaemon = final.callPackage ./nix/recodeDaemon.nix {};
    };

    nixosModules.default = import ./nix/module.nix;

    packages = forAllSystems ({ pkgs }: {
      default = pkgs.recodeDaemon;
      inherit (pkgs) recodeDaemon;
    });

    devShells = forAllSystems ({ pkgs }: let
      python = pkgs.python313.withPackages (ps: with ps; [
        python-daemon
      ]);
    in {
      default = pkgs.mkShell {
        packages = [
          python
          pkgs.ffmpeg

          pkgs.git
        ];
      };
    });

    # Test config to debug the nixos module and package
    nixosConfigurations = forAllSystems ({ pkgs }: {
      test = nixpkgs.lib.nixosSystem {
        inherit (pkgs) system;

        modules = [
          ({ pkgs, ... }: {
            nixpkgs.overlays = [
              self.overlays.default
            ];
          })

          self.nixosModules.default

          {
            services.recodeDaemon = {
              enable = true;
              
              daemon = {
                enable = true;
                port = 5300;
                systemService = false;
              };
            };
          }
        ];
      };
    });
  };
}
