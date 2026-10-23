"""Encrypt a verified checkpoint for an explicitly selected external destination.

Requires a recipient's already imported GPG public key fingerprint. No passwords
or private keys are accepted. A ciphertext hash checks transfer, not restoration;
the recipient must decrypt and run continuity verification to prove recovery.
"""

import argparse
import hashlib
import os
import re
import subprocess
import tarfile
import tempfile
from pathlib import Path

from continuity import ROOT, verify


def encrypt_checkpoint(checkpoint, destination, recipient, *, homedir=None):
    checkpoint, destination = checkpoint.resolve(), destination.resolve()
    if not re.fullmatch(r"[A-Fa-f0-9]{40}|[A-Fa-f0-9]{64}", recipient):
        raise ValueError("Informe o fingerprint completo da chave pública, sem espaços.")
    if destination.is_relative_to(ROOT):
        raise ValueError("O destino deve estar fora da árvore do projeto.")
    if not destination.is_dir():
        raise ValueError("O diretório de destino deve existir e ser selecionado explicitamente.")
    verify(checkpoint)
    target = destination / f"eletroprojeto-{checkpoint.name}.tar.gpg"
    if target.exists():
        raise ValueError("O arquivo de destino já existe; não será sobrescrito.")
    with tempfile.TemporaryDirectory(prefix="eletroprojeto-encrypt-") as directory:
        archive = Path(directory, "checkpoint.tar")
        with tarfile.open(archive, "w") as bundle:
            for name in ("source.zip", "data.sqlite3", "manifest.json", "VERIFIED.json"):
                bundle.add(checkpoint / name, arcname=f"{checkpoint.name}/{name}")
        os.chmod(archive, 0o600)
        ciphertext = Path(directory, "checkpoint.gpg")
        command = ["gpg", "--batch"]
        if homedir:
            command += ["--homedir", str(homedir)]
        command += [
            "--trust-model",
            "always",
            "--recipient",
            recipient,
            "--output",
            str(ciphertext),
            "--encrypt",
            str(archive),
        ]
        subprocess.run(command, check=True, capture_output=True)
        data = ciphertext.read_bytes()
        expected = hashlib.sha256(data).hexdigest()
        try:
            with target.open("xb") as output:
                os.chmod(target, 0o600)
                output.write(data)
                output.flush()
                os.fsync(output.fileno())
            if hashlib.sha256(target.read_bytes()).hexdigest() != expected:
                raise ValueError("Cópia criptografada divergente; não é um backup verificado.")
        except Exception:
            # Keep partial output for inspection; never report it as verified.
            raise
    return {
        "path": str(target),
        "sha256": expected,
        "encrypted": True,
        "transfer_verified": True,
        "recipient_restore_verified": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--recipient", required=True)
    args = parser.parse_args()
    import json

    print(
        json.dumps(encrypt_checkpoint(args.checkpoint, args.destination, args.recipient), indent=2)
    )


if __name__ == "__main__":
    main()
