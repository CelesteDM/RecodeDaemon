{
  python313Packages,
  ffmpeg,
  lib,
}:

python313Packages.buildPythonPackage rec {
  pname = "recodeDaemon";
  version = "0.1.0";

  src = ../.;
  pyproject = true;
  build-system = with python313Packages; [ setuptools ];

  propagatedBuildInputs = [
    python313Packages.python-daemon
    python313Packages.psutil
    ffmpeg
  ];

  meta = with lib; {
    homepage = "https://github.com/CelesteDM/RecodeDaemon";
    description = "Recoding daemon for media services";
    license = licenses.mit;
    platforms = lib.platforms.linux;
    mainProgram = "recoder";
  };
}
