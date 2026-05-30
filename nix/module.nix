{ config, lib, pkgs, ...}:
let
  cfg = config.services.recodeDaemon;
  inherit (lib) mkIf mkEnableOption mkOption;
in
{
  options.services.recodeDaemon = {
    enable = mkEnableOption "recodeDaemon-service";

    daemon = {
      enable = mkEnableOption "recodeDaemon-unit";

      port = mkOption {
        description = "The port in which the socket will run";
        default = 5300;
        type = lib.types.int;
      };

      systemService = mkOption {
        description = "Whether the service should run as a system service";
        default = false;
        type = lib.types.bool;
      };
    };
  };

  config = mkIf cfg.enable {

    systemd = let
      service = {
        description = "Recoding daemon for media services";
        unitConfig = {
          execStart = ''
            ${pkgs.recodeDaemon}/bin/recoder \
              -p ${toString cfg.port} \
              daemon run
          '';
        };
        preStop = ''
          ${pkgs.recodeDaemon}/bin/recoder \
            -p ${toString cfg.port} \
            daemon stop
        '';
        wantedBy =
          if cfg.systemService
          then ["multi-user.target"]
          else ["default.target"];
      };
    in
      lib.mkMerge [
        (mkIf cfg.daemon.enable (mkIf (cfg.systemService) {
          services.recodeDaemon = service;
        }))

        (mkIf cfg.daemon.enable (mkIf (!cfg.systemService) {
          user.services.recodeDaemon = service;
        }))
        
        {
          environment.systemPackages = [ pkgs.recodeDaemon ];
        }
      ];
  };
}
