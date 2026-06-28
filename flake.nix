{
  description = "WhisperCPP to type whatever you say";
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
  };

  outputs =
    { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs {
        inherit system;
      };

      pythonEnv = pkgs.python3.withPackages (
        ps: with ps; [
          faster-whisper
          sounddevice
          numpy
        ]
      );

      whisper-type = pkgs.writeShellApplication {
        name = "whisper-type";
        runtimeInputs = with pkgs; [
          portaudio
          libnotify
          ydotool
        ];
        text = ''
          exec ${pythonEnv}/bin/python ${./main.py} "$@"
        '';
      };
    in
    {
      packages.${system}.default = whisper-type;

      apps.${system}.default = {
        type = "app";
        program = "${whisper-type}/bin/whisper-type";
      };

      devShells.${system}.default = pkgs.mkShell {
        packages = with pkgs; [
          pythonEnv
          uv
          basedpyright
          black
          portaudio
          gcc
          openssl
          libnotify
        ];
        # shellHook = ''
        #   export LD_LIBRARY_PATH="${pkgs.portaudio}/lib:$LD_LIBRARY_PATH"
        # '';
      };
    };
}
