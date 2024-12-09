{
  outputs = { self, nixpkgs }: {
    overlay = final: prev: {
      python3Optimized = prev.pkgs.python3Full.overrideAttrs {
        enableOptimizations = true;
        reproducibleBuild = false;
      };
      pyPkgs = nixpkgs.python3Optimized.pkgs;
    };

    pkgs.x86_64-linux.python3Optimized = nixpkgs.legacyPackages.x86_64-linux.python3Full.overrideAttrs {
      enableOptimizations = true;
      reproducibleBuild = false;
    };
    pkgs.x86_64-linux.pyPkgs = self.pkgs.x86_64-linux.python3Optimized.pkgs;


    pkgs.aarch64-linux.python3Optimized = self.pkgs.x86_64-linux.python3Optimized.python3Full;
    pkgs.aarch64-linux.pyPkgs = self.pkgs.aarch64-linux.python3Optimized.pkgs;

  };
}

