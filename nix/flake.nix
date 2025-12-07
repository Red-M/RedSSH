{
  description = "Nix flake for testing";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";

    outoftree = {
      url = "path:./pkgs";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, outoftree, ... }@inputs: let
    pkgs = nixpkgs.legacyPackages.x86_64-linux;
    inherit outoftree;
  in {
    devShells.x86_64-linux.default = pkgs.mkShell {
      buildInputs = [
        outoftree.pkgs.${pkgs.system}.python3Optimized
        outoftree.pkgs.${pkgs.system}.pyPkgs.cmake
        outoftree.pkgs.${pkgs.system}.pyPkgs.cython
        outoftree.pkgs.${pkgs.system}.pyPkgs.virtualenvwrapper
        outoftree.pkgs.${pkgs.system}.pyPkgs.setuptools
        outoftree.pkgs.${pkgs.system}.pyPkgs.readme-renderer

        pkgs.gnumake
        pkgs.ninja
        pkgs.wget
        pkgs.curl
        pkgs.openssh_hpn
        pkgs.git
        pkgs.bashInteractive
        pkgs.busybox

        pkgs.openssl
        pkgs.zlib
        pkgs.krb5
        pkgs.libsodium
        pkgs.pkg-config
        pkgs.softhsm
        pkgs.libssh
      ];
      nativeBuildInputs = [ pkgs.cmake pkgs.pkg-config ];
      nativeCheckInputs = [
        pkgs.softhsm
      ];
      shellHook = ''
        export SYSTEM_LIBSSH=1
        export REDSSH_TESTS_SSHBIN_PATH="${pkgs.openssh_hpn}/bin"
        grep 'sshd' /etc/passwd || echo 'sshd:x:995:992:SSH privilege separation user:/var/empty:/run/current-system/sw/bin/nologin' >> /etc/passwd
        ls /var/empty || mkdir /var/empty
        if [ ! -f ~/.ssh/authorized_keys ]; then
          mkdir ~/.ssh
          cp /build/tests/ssh_host_key.pub ~/.ssh/authorized_keys
          chmod 700 ~/.ssh
          chmod 600 ~/.ssh/authorized_keys
          passwd -u root
          echo -e 'a\ra\r' | passwd root
        fi

        cd /build
        python3 -m venv ~/.py-venv/
        source ~/.py-venv/bin/activate
        pip install git+http://gitlab.bubble-berry/Red_M/redlibssh.git@master
        pip install git+http://gitlab.bubble-berry/Red_M/redlibssh2.git@master
        pip install -e .[tests]
        pip install -e .[docs]
        pip install --upgrade pytest coveralls pytest-cov pytest-xdist paramiko > /dev/null
        py.test --cov redssh --cov-config .coveragerc

        echo "*********** Coverage ***********"
        coverage html
        coverage xml

        # CODE_VALIDATION_PY_FILES="$(find ./ -type f | grep '\.py$' | grep '\./redssh/')" # Ignore tests for now.
        # BANDIT_REPORT=$(tempfile)
        # PYLINT_REPORT=$(tempfile)
        # SAFETY_REPORT=$(tempfile)
        # echo "*********** Bandit ***********"
        # bandit -c ./.bandit.yml -r $${CODE_VALIDATION_PY_FILES} 2>&1 > "$${BANDIT_REPORT}"
        # cat "$${BANDIT_REPORT}"
        #
        # echo "*********** Pylint ***********"
        # pylint $${CODE_VALIDATION_PY_FILES} 2>&1 > "$${PYLINT_REPORT}"
        # cat "$${PYLINT_REPORT}"
        #
        # echo "*********** Safety ***********"
        # safety scan 2>&1 > "$${SAFETY_REPORT}"
        # cat "$${SAFETY_REPORT}"
      '';
    };
  };
}

